import puppeteer from 'puppeteer-core'
import { writeFile } from 'node:fs/promises'

const outputDirectory = new URL('./', import.meta.url)
const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
  args: ['--no-first-run', '--no-default-browser-check'],
  defaultViewport: { width: 1440, height: 1050 }
})
const report = {
  measuredAt: new Date().toISOString(),
  url: 'http://127.0.0.1:59024',
  browser: await browser.version(),
  mode: 'headless',
  errors: [],
  indexRequests: []
}
try {
  const page = await browser.newPage()
  page.on('pageerror', error => report.errors.push(error.message))
  page.on('response', response => {
    if (response.url().includes('/_pagefind/')) {
      report.indexRequests.push({ url: response.url(), status: response.status() })
    }
  })
  const response = await page.goto(report.url, { waitUntil: 'networkidle0' })
  report.homeStatus = response.status()
  await page.waitForSelector('input[type="search"]')
  report.search = await page.$eval('input[type="search"]', input => ({
    placeholder: input.placeholder,
    role: input.getAttribute('role'),
    lang: document.documentElement.lang,
    shortcut: input.parentElement.querySelector('kbd')?.textContent,
    top: Math.round(input.getBoundingClientRect().top),
    left: Math.round(input.getBoundingClientRect().left)
  }))
  await page.keyboard.press('/')
  report.slashFocus = await page.$eval('input[type="search"]', input => input === document.activeElement)
  await page.evaluate(() => document.activeElement.blur())
  await page.keyboard.down('Meta')
  await page.keyboard.press('k')
  await page.keyboard.up('Meta')
  report.commandKFocus = await page.$eval('input[type="search"]', input => input === document.activeElement)
  await page.type('input[type="search"]', 'outbox')
  await page.waitForFunction(() => document.querySelectorAll('.nextra-search-results [role="option"]').length > 0, { timeout: 15000 })
  report.outboxResults = await page.$$eval('.nextra-search-results [role="option"]', options => options.map(option => ({
    title: option.querySelector('div')?.textContent,
    href: option.getAttribute('href'),
    excerpt: option.textContent
  })))
  report.outboxPageCount = await page.evaluate(async () => (await window.pagefind.search('outbox')).results.length)
  await page.screenshot({ path: new URL('outbox-search.png', outputDirectory).pathname })
  const targetSelector = '.nextra-search-results [role="option"][href^="/tutoriais/outbox"]'
  await page.waitForSelector(targetSelector, { timeout: 15000 })
  const targetHref = await page.$eval(targetSelector, link => link.getAttribute('href'))
  await page.click(targetSelector)
  await page.waitForFunction(() => location.pathname === '/tutoriais/outbox', { timeout: 15000 })
  await page.waitForSelector('main h1')
  report.navigation = {
    clickedHref: targetHref,
    url: page.url(),
    title: await page.$eval('main h1', heading => heading.textContent)
  }
  await page.screenshot({ path: new URL('outbox-destination.png', outputDirectory).pathname })
  await page.goto(report.url, { waitUntil: 'networkidle0' })
  await page.type('input[type="search"]', 'refresh')
  await page.waitForFunction(() => document.querySelectorAll('.nextra-search-results [role="option"]').length > 0, { timeout: 15000 })
  report.refreshResults = await page.$$eval('.nextra-search-results [role="option"]', options => options.map(option => ({
    title: option.querySelector('div')?.textContent,
    href: option.getAttribute('href')
  })))
  report.completedAt = new Date().toISOString()
  await writeFile(new URL('browser-receipt.json', outputDirectory), JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify(report, null, 2))
} finally {
  await browser.close()
}
