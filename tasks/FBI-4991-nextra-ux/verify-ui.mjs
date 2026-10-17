import puppeteer from 'puppeteer-core'
import { readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const port = (await readFile('.env.local', 'utf8')).match(/^PORT=(\d+)$/m)?.[1]
const hosted = process.argv.includes('--hosted')
const origin = hosted ? 'https://hub-makershub-architecture-course.6bv96u.easypanel.host' : `http://127.0.0.1:${port}`
const label = hosted ? 'hosted-ui' : 'ui'
const credentials = hosted ? JSON.parse(execFileSync('python3', ['tasks/FBI-4991-easypanel/keychain_secrets.py', '--process-export'], { encoding: 'utf8' })) : {}
const assets = hosted ? JSON.parse(await readFile('tasks/FBI-4991-nextra-ux/evidence/asset-manifest.json', 'utf8')).files : []
async function batch(items, action) { let cursor=0; await Promise.all(Array.from({length:12},async()=>{while(cursor<items.length)await action(items[cursor++])})) }
const folder = path.join(root, 'tasks/FBI-4991-nextra-ux/evidence')
const report = { startedAt: new Date().toISOString(), origin, measurements: [], failures: [], pageErrors: [] }
const assert = (value, message) => { if (!value) report.failures.push(message) }
const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true,
  timeout: 60000, args: ['--no-first-run', '--no-default-browser-check'] })
try {
  const page = await browser.newPage()
  page.on('pageerror', error => report.pageErrors.push(error.message))
  if (hosted) {
    report.anonymousDenied = 0
    await batch(assets, async item => { const r=await fetch(origin+'/'+item.path,{redirect:'manual'}); if(r.status===401||r.status===303&&r.headers.get('location')?.startsWith('/login'))report.anonymousDenied++; else report.failures.push(`Anonymous access ${item.path}/${r.status}`); await r.body?.cancel() })
    await page.goto(origin+'/login',{waitUntil:'domcontentloaded'})
    await page.type('input[name="password"]','incorrect-course-password')
    await Promise.all([page.waitForNavigation({waitUntil:'networkidle2'}),page.click('button[type="submit"]')])
    report.wrongPasswordRejected=!!await page.$('[role="alert"]')
    assert(report.wrongPasswordRejected,'Wrong password accepted')
    await page.goto(origin+'/login',{waitUntil:'domcontentloaded'})
    await page.type('input[name="password"]',credentials.COURSE_PASSWORD)
    await Promise.all([page.waitForNavigation({waitUntil:'networkidle2'}),page.click('button[type="submit"]')])
    const cookieList=await page.cookies(origin)
    const session=cookieList.find(x=>x.name==='__Host-course_session')
    report.cookieFlags=session?{secure:session.secure,httpOnly:session.httpOnly,sameSite:session.sameSite}:null
    assert(session?.secure&&session.httpOnly&&session.sameSite==='Lax','Session cookie flags differ')
  }
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'dark' }, { name: 'prefers-reduced-motion', value: 'no-preference' }])
  for (const width of [2048, 1440, 1024, 390]) {
    await page.setViewport({ width, height: 1000 })
    await page.goto(origin + '/referencia/prioritarios', { waitUntil: 'networkidle2' })
    const measured = await page.evaluate(() => {
      const table = document.querySelector('main table')
      const article = document.querySelector('article')
      return { width: innerWidth, title: document.title, heading: document.querySelector('main h1')?.textContent,
        documentWidth: document.documentElement.scrollWidth, articleWidth: article.getBoundingClientRect().width,
        padding: getComputedStyle(article).paddingInlineStart, contentMaximum: getComputedStyle(document.documentElement).getPropertyValue('--nextra-content-width'),
        tableClient: table.clientWidth, tableScroll: table.scrollWidth, tableRight: table.getBoundingClientRect().right,
        rows: table.tBodies[0].rows.length, columns: table.tHead.rows[0].cells.length,
        scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior }
    })
    report.measurements.push(measured)
    assert(measured.heading === 'Arquitetura na prática: Makershub', `Heading differs at ${width}`)
    assert(measured.title === 'Arquitetura na prática: Makershub', `Browser title differs at ${width}`)
    assert(measured.documentWidth <= width + 1, `Page overflows at ${width}`)
    assert(measured.rows === 40 && measured.columns === 6, `Table structure differs at ${width}`)
    if (width >= 1440) assert(measured.tableScroll <= measured.tableClient + 2, `Desktop table needs horizontal scrolling at ${width}`)
    await page.screenshot({ path: path.join(folder, `${label}-priority-${width}.png`) })
  }
  await page.setViewport({ width: 1440, height: 1000 })
  await page.goto(origin + '/jornadas/reservation/conceitos', { waitUntil: 'networkidle2' })
  const group = await page.$(':is(.nextra-sidebar a[href="/jornadas/reservation"], .nextra-sidebar a[href="/jornadas/reservation/"])')
  assert(Boolean(group), 'Reservation group is not a native link')
  if (group) {
    await group.evaluate(element => element.scrollIntoView({ block: 'center' }))
    await page.evaluate(() => {
      window.scrollTo({ top: 650, behavior: 'instant' })
      window.__courseScroll = [scrollY]
      const start = performance.now()
      const record = () => { window.__courseScroll.push(scrollY); if (performance.now() - start < 1800) requestAnimationFrame(record) }
      requestAnimationFrame(record)
    })
    await group.click()
    await page.waitForFunction(() => location.pathname.replace(/\/$/, '') === '/jornadas/reservation' && document.querySelector('main h1')?.textContent.includes('Dois operadores'), { timeout: 15000 })
    await new Promise(resolve => setTimeout(resolve, 1800))
    report.groupClick = { url: page.url(), heading: await page.$eval('main h1', e => e.textContent), scroll: await page.evaluate(() => window.__courseScroll || []) }
    assert(report.groupClick.scroll.some(y => y > 0 && y < 640), 'Page click did not expose an intermediate scroll position')
    assert(report.groupClick.scroll.at(-1) <= 1, 'Page click did not finish at the top')
    const landedGroup = await page.$(':is(.nextra-sidebar a[href="/jornadas/reservation"], .nextra-sidebar a[href="/jornadas/reservation/"])')
    const arrow = await landedGroup.$('svg')
    if (arrow) {
      const before = await landedGroup.evaluate(element => element.parentElement.className)
      const priorUrl = page.url()
      await arrow.click()
      await new Promise(resolve => setTimeout(resolve, 350))
      const after = await page.$eval(':is(.nextra-sidebar a[href="/jornadas/reservation"], .nextra-sidebar a[href="/jornadas/reservation/"])', element => element.parentElement.className)
      report.arrow = { before, after, urlUnchanged: priorUrl === page.url(), transition: await page.$eval(':is(.nextra-sidebar a[href="/jornadas/reservation"], .nextra-sidebar a[href="/jornadas/reservation/"]) svg', element => getComputedStyle(element).transitionDuration) }
      assert(before !== after && report.arrow.urlUnchanged, 'The arrow did not toggle independently')
    }
  }
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }])
  report.reducedMotion = await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)
  assert(report.reducedMotion === 'auto', 'Reduced motion does not disable smooth scrolling')
  await page.screenshot({ path: path.join(folder, `${label}-reservation-click.png`) })
  if(hosted){
    await page.keyboard.press('/')
    await page.type('input[type="search"]','dual write')
    await page.waitForFunction(()=>document.querySelectorAll('.nextra-search-results [role="option"]').length>0,{timeout:20000})
    report.searchResults=await page.$$eval('.nextra-search-results [role="option"]',nodes=>nodes.map(n=>n.getAttribute('href')))
    await page.keyboard.press('Escape')
    const cookie=(await page.cookies(origin)).map(x=>x.name+'='+x.value).join('; ')
    report.hashesMatched=0;report.transportRetries=0
    await batch(assets,async item=>{for(let attempt=1;attempt<=3;attempt++){try{const r=await fetch(origin+'/'+item.path,{headers:{Cookie:cookie},redirect:'manual',signal:AbortSignal.timeout(20000)});const hash=createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex');if(r.status===200&&hash===item.sha256)report.hashesMatched++;else report.failures.push(`Authenticated bytes ${item.path}/${r.status}`);return}catch(error){if(attempt===3){report.failures.push(`Read ${item.path}: ${error}`);return}report.transportRetries++;await new Promise(resolve=>setTimeout(resolve,500*attempt))}}})
    await page.evaluate(async()=>{await fetch('/logout',{method:'POST',redirect:'manual'})})
    await page.goto(origin,{waitUntil:'domcontentloaded'})
    report.logoutRedirected=new URL(page.url()).pathname==='/login'
    report.afterLogoutDenied=0
    await batch(assets,async item=>{const r=await fetch(origin+'/'+item.path,{redirect:'manual'});if(r.status===401||r.status===303&&r.headers.get('location')?.startsWith('/login'))report.afterLogoutDenied++;else report.failures.push(`Access after logout ${item.path}/${r.status}`);await r.body?.cancel()})
    assert(report.anonymousDenied===assets.length&&report.hashesMatched===assets.length&&report.afterLogoutDenied===assets.length&&report.logoutRedirected,'Asset/session checks incomplete')
  }
} catch (error) { report.failures.push(String(error.stack || error)) }
finally { await browser.close() }
report.completedAt = new Date().toISOString()
report.pass = report.failures.length === 0 && report.pageErrors.length === 0
let serialized=JSON.stringify(report,null,2); for(const secret of Object.values(credentials))serialized=serialized.replaceAll(secret,'[redacted]'); await writeFile(path.join(folder, `${label}-verification.json`),serialized+'\n')
console.log(serialized)
process.exitCode = report.pass ? 0 : 1
