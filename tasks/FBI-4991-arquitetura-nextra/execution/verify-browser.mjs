import puppeteer from 'puppeteer-core'
import { readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = process.cwd()
const task = path.join(root, 'tasks/FBI-4991-arquitetura-nextra/execution')
const environment = JSON.parse(await readFile(path.join(task, 'environment.json'), 'utf8'))
const base = `http://127.0.0.1:${environment.port}`
const matrix = JSON.parse(await readFile(path.join(task, 'learning/families.json'), 'utf8'))
matrix.families.push(...JSON.parse(await readFile(path.join(task, 'postgres-learning/families.json'), 'utf8')).families)
matrix.families.push(...JSON.parse(await readFile(path.join(task, 'airflow-learning/families.json'), 'utf8')).families)
const content = JSON.parse(await readFile(path.join(root, 'tasks/architecture-course-2026-10-14/artifacts/fbi4991-execution-validation.json'), 'utf8'))
const report = { observedAt: new Date().toISOString(), base, routeResults: [], journeys: [], pageErrors: [], failures: [] }

for (let index = 0; index < content.files.length; index += 5) {
  const group = content.files.slice(index, index + 5)
  report.routeResults.push(...await Promise.all(group.map(async file => {
    const response = await fetch(base + file.route)
    return { route: file.route, status: response.status }
  })))
}
if (report.routeResults.some(item => item.status !== 200)) report.failures.push('A content route did not return HTTP 200')

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
  defaultViewport: { width: 1440, height: 1050 },
  args: ['--no-first-run', '--no-default-browser-check']
})
try {
  const page = await browser.newPage()
  page.on('pageerror', error => report.pageErrors.push(error.message))
  await page.goto(base, { waitUntil: 'networkidle0' })
  await page.waitForSelector('main h1')
  report.homeHeading = await page.$eval('main h1', element => element.textContent)
  await page.keyboard.press('/')
  report.searchShortcutFocus = await page.$eval('input[type="search"]', input => input === document.activeElement)
  await page.type('input[type="search"]', 'cancelamento')
  await page.waitForFunction(() => document.querySelectorAll('.nextra-search-results [role="option"]').length > 0, { timeout: 15000 })
  report.searchResults = await page.$$eval('.nextra-search-results [role="option"]', elements => elements.map(element => ({ href: element.getAttribute('href'), text: element.textContent })))
  const selected = await page.$eval('.nextra-search-results [role="option"]', element => element.getAttribute('href'))
  await page.screenshot({ path: path.join(task, 'search-new-course.png') })
  await page.click('.nextra-search-results [role="option"]')
  await page.waitForFunction(target => location.pathname === new URL(target, location.origin).pathname, {}, selected)
  report.searchNavigation = { selected, actual: page.url() }

  for (const family of matrix.families) {
    const step = { caseId: family.case_id, destinations: [] }
    const destinationValues = Object.values(family.destinations)
    for (const [kind, destination] of Object.entries(family.destinations)) {
      await page.goto(base + destination, { waitUntil: 'networkidle0' })
      await page.waitForSelector('main h1')
      const state = await page.$eval('main', element => ({
        heading: element.querySelector('h1')?.textContent,
        links: [...element.querySelectorAll('a[href]')].map(link => new URL(link.href).pathname.replace(/\/$/, '') || '/')
      }))
      const expected = destinationValues.filter(value => value !== destination).map(value => value.replace(/\/$/, '') || '/')
      const missing = expected.filter(value => !state.links.includes(value))
      step.destinations.push({ kind, route: destination, heading: state.heading, missingSiblingLinks: missing })
      if (missing.length) report.failures.push(`${family.case_id}/${kind} lacks ${missing.join(', ')}`)
    }
    report.journeys.push(step)
  }

  report.clickedJourneys = []
  for (const caseId of ['single-flight-cancel', 'query-grain-postgres', 'revision-cas-postgres', 'airflow-lock-retry']) {
  const family = matrix.families.find(item => item.case_id === caseId)
  await page.goto(base + family.destinations.journey, { waitUntil: 'networkidle0' })
  const clickedJourney = { caseId, steps: [] }
  for (const key of ['explanation', 'tutorial', 'how_to', 'reference', 'journey']) {
    const target = family.destinations[key]
    await page.$$eval('main a[href]', (elements, destination) => {
      const normalized = destination.replace(/\/$/, '')
      const selected = elements.find(element => new URL(element.href).pathname.replace(/\/$/, '') === normalized)
      if (!selected) throw new Error(`The rendered journey lacks ${destination}`)
      selected.click()
    }, target)
    await page.waitForFunction(targetPath => location.pathname.replace(/\/$/, '') === targetPath.replace(/\/$/, ''), {}, target)
    await page.waitForSelector('main h1')
    clickedJourney.steps.push({ destination: key, url: page.url(), title: await page.$eval('main h1', element => element.textContent) })
  }
  report.clickedJourneys.push(clickedJourney)
  await page.screenshot({ path: path.join(task, `connected-${caseId}.png`) })
  }
} catch (error) {
  report.failures.push(error.stack ?? String(error))
} finally {
  await browser.close()
}
report.completedAt = new Date().toISOString()
report.verdict = report.failures.length || report.pageErrors.length ? 'FAIL' : 'PASS'
await writeFile(path.join(task, 'browser-review.json'), JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify({ verdict: report.verdict, routes: report.routeResults.length, journeys: report.journeys.length, errors: report.pageErrors, failures: report.failures }))
process.exitCode = report.verdict === 'PASS' ? 0 : 1
