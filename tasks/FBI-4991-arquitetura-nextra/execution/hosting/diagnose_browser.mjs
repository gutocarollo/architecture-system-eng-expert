import { readFile, writeFile } from 'node:fs/promises'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import path from 'node:path'
import puppeteer from 'puppeteer-core'

const root = process.cwd()
const folder = path.join(root, 'tasks/FBI-4991-arquitetura-nextra/execution/hosting')
const identity = JSON.parse(await readFile(path.join(folder, 'site-identity.json'), 'utf8'))
const origin = new URL(identity.expected_url).origin
const manifest = JSON.parse(await readFile(path.join(folder, 'asset-manifest.json'), 'utf8'))
const credentials = JSON.parse(execFileSync('python3', [path.join(folder, 'keychain_secrets.py'), '--process-export'], { encoding: 'utf8' }))
const privateMode = process.argv.includes('--private-service-access')
const labelIndex = process.argv.indexOf('--receipt-label')
const receiptLabel = labelIndex >= 0 ? process.argv[labelIndex + 1] : (privateMode ? 'private' : 'public')
if (!/^[a-z0-9-]+$/.test(receiptLabel || '')) throw new Error('Invalid receipt label')
let privateToken
if (privateMode) {
  process.stdin.setRawMode?.(true)
  process.stdout.write('Ready for private Site access JSON on stdin (input is hidden).\n')
  const value = await new Promise((resolve, reject) => {
    let input = ''
    process.stdin.on('data', chunk => {
      input += chunk.toString()
      if (input.includes('\n')) { process.stdin.pause(); resolve(input.split('\n')[0]) }
    })
    process.stdin.on('end', () => reject(new Error('Private access input missing')))
    process.stdin.resume()
  })
  process.stdin.setRawMode?.(false)
  privateToken = JSON.parse(value).service_access_token
  if (!privateToken) throw new Error('Private Site service access is missing')
}

const report = { startedAt: new Date().toISOString(), origin, releaseId: manifest.release_id,
  privateNativeBoundary: privateMode, diagnosticOnly: true, failures: [], anonymous: [], readBack: [], consoleErrors: [], pageErrors: [] }
const scrub = text => Object.values(credentials).concat(privateToken || []).reduce((value, secret) => value.replaceAll(secret, '[redacted]'), String(text))
function headers(cookie) {
  return { ...(privateToken ? { 'OAI-Sites-Authorization': `Bearer ${privateToken}` } : {}), ...(cookie ? { Cookie: cookie } : {}) }
}
async function eachBounded(items, operation, concurrency = 12) {
  let cursor = 0
  await Promise.all(Array.from({ length: concurrency }, async () => {
    while (cursor < items.length) {
      const index = cursor++
      await operation(items[index])
    }
  }))
}

await eachBounded(manifest.files.filter(item => ['index.html', '_pagefind/pagefind.js', 'downloads/architecture-labs.zip'].includes(item.path)), async item => {
  const url = new URL('/' + item.path, origin)
  if (url.origin !== origin) throw new Error('Unexpected asset origin')
  const response = await fetch(url, { headers: headers(), redirect: 'manual' })
  const location = response.headers.get('location')
  const allowed = response.status === 401 || (response.status === 303 && location?.startsWith('/login'))
  report.anonymous.push({ path: item.path, status: response.status })
  if (!allowed) report.failures.push(`Anonymous asset was not denied: ${item.path}/${response.status}`)
  await response.body?.cancel()
})
console.log(JSON.stringify({ anonymousChecked: report.anonymous.length, failures: report.failures.length }))

const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true, timeout: 60000, defaultViewport: { width: 1440, height: 1050 }, args: ['--no-first-run', '--no-default-browser-check'] })
try {
  const page = await browser.newPage()
  if (privateToken) {
    await page.setRequestInterception(true)
    page.on('request', request => {
      const requestHeaders = request.headers()
      for (const key of Object.keys(requestHeaders)) {
        if (['oai-sites-authorization', 'authorization'].includes(key.toLowerCase())) delete requestHeaders[key]
      }
      const additions = new URL(request.url()).origin === origin ? headers() : {}
      request.continue({ headers: { ...requestHeaders, ...additions } }).catch(() => {})
    })
  }
  report.httpErrors = []
  page.on('response', response => { if (response.status() >= 400) report.httpErrors.push({ path: new URL(response.url()).pathname, origin: new URL(response.url()).origin, method: response.request().method(), status: response.status() }) })
  page.on('pageerror', error => report.pageErrors.push(scrub(error.message)))
  page.on('console', message => { if (message.type() === 'error') report.consoleErrors.push(scrub(message.text())) })
  await page.goto(origin, { waitUntil: 'networkidle0' })
  report.anonymousEntry = { url: page.url(), heading: await page.$eval('h1', node => node.textContent) }
  if (new URL(page.url()).pathname !== '/login' || !report.anonymousEntry.heading.includes('Acesso ao curso')) throw new Error('Anonymous entry did not reach the course password form')
  await page.screenshot({ path: path.join(folder, `${receiptLabel}-login.png`) })
  await page.type('input[name="password"]', 'invalid-course-password')
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('button[type="submit"]')])
  report.wrongPasswordRejected = Boolean(await page.$('[role="alert"]'))
  if (!report.wrongPasswordRejected) throw new Error('An incorrect password was not rejected')
  report.consoleErrors = []
  await page.goto(origin + '/login', { waitUntil: 'networkidle0' })
  await page.type('input[name="password"]', credentials.COURSE_PASSWORD)
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('button[type="submit"]')])
  await page.waitForSelector('main h1')
  report.authenticatedHeading = await page.$eval('main h1', node => node.textContent)
  if (report.authenticatedHeading.includes('Acesso ao curso')) throw new Error('The correct password did not open Nextra')
  const cookies = await page.cookies(origin)
  const session = cookies.find(cookie => cookie.name === '__Host-course_session')
  report.sessionFlags = session ? { secure: session.secure, httpOnly: session.httpOnly, sameSite: session.sameSite } : null
  if (!session?.secure || !session.httpOnly || session.sameSite !== 'Lax') throw new Error('Required session cookie flags missing')
  const cookie = cookies.map(item => `${item.name}=${item.value}`).join('; ')
  await eachBounded(manifest.files.filter(item => ['index.html', '_pagefind/pagefind.js', 'downloads/architecture-labs.zip'].includes(item.path)), async item => {
    const response = await fetch(new URL('/' + item.path, origin), { headers: headers(cookie), redirect: 'manual' })
    const digest = createHash('sha256').update(Buffer.from(await response.arrayBuffer())).digest('hex')
    const match = response.status === 200 && digest === item.sha256
    report.readBack.push({ path: item.path, status: response.status, sha256Matches: match })
    if (!match) report.failures.push(`Authenticated bytes differ: ${item.path}/${response.status}`)
  })
  console.log(JSON.stringify({ authenticatedReadBack: report.readBack.length, failures: report.failures.length }))
  report.anonymousAfterWarm = []
  await eachBounded(manifest.files.filter(item => ['index.html', '_pagefind/pagefind.js', 'downloads/architecture-labs.zip'].includes(item.path)), async item => {
    const response = await fetch(new URL('/' + item.path, origin), { headers: headers(), redirect: 'manual' })
    const denied = response.status === 401 || (response.status === 303 && response.headers.get('location')?.startsWith('/login'))
    report.anonymousAfterWarm.push({ path: item.path, status: response.status })
    if (!denied) report.failures.push(`Warmed cache leaked an asset: ${item.path}/${response.status}`)
    await response.body?.cancel()
  })
  await page.keyboard.press('/')
  await page.type('input[type="search"]', 'cancelamento')
  await page.waitForFunction(() => document.querySelectorAll('.nextra-search-results [role="option"]').length > 0, { timeout: 20000 })
  const selected = await page.$eval('.nextra-search-results [role="option"]', node => node.getAttribute('href'))
  await page.click('.nextra-search-results [role="option"]')
  await page.waitForFunction(target => location.pathname.replace(/\/$/, '') === new URL(target, location.origin).pathname.replace(/\/$/, ''), {}, selected)
  report.search = { selected, actual: page.url() }
  await page.goto(origin + '/jornadas/airflow-lock-retry/', { waitUntil: 'networkidle0' })
  await page.waitForSelector('main h1')
  report.caseHeading = await page.$eval('main h1', node => node.textContent)
  await page.screenshot({ path: path.join(folder, `${receiptLabel}-nextra.png`) })
  const signOut = await page.evaluate(async () => {
    const response = await fetch('/logout', { method: 'POST', redirect: 'manual' })
    return response.status
  })
  await page.goto(origin, { waitUntil: 'networkidle0' })
  report.logout = { requestStatus: signOut, redirectedToLogin: new URL(page.url()).pathname === '/login' }
  if (!report.logout.redirectedToLogin) throw new Error('Logout left the course readable')
} catch (error) {
  report.failures.push(scrub(error.stack || error))
} finally {
  await browser.close()
}
report.completedAt = new Date().toISOString()
report.verdict = report.failures.length || report.pageErrors.length || report.consoleErrors.length ? 'FAIL' : 'PASS'
await writeFile(path.join(folder, `${receiptLabel}-verification.json`), JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify({ verdict: report.verdict, anonymous: report.anonymous.length, readBack: report.readBack.length,
  failures: report.failures, pageErrors: report.pageErrors, consoleErrors: report.consoleErrors }))
process.exitCode = report.verdict === 'PASS' ? 0 : 1
