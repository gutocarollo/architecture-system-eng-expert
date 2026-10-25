import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { JSDOM } from 'jsdom'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const htmlRoot = process.env.EARLY_REFRESH_HTML_ROOT || path.join(root, 'out')
const legacyAnchors = JSON.parse(await readFile(path.join(root, 'tests/legacy-anchors.json'), 'utf8'))
const routes = Object.keys(legacyAnchors)
const facetIds = ['overview', 'explanation', 'tutorial', 'guide', 'reference']
const canonicalPath = '/jornadas/early-refresh/'

async function documentFor(route) {
  const html = await readFile(path.join(htmlRoot, route, 'index.html'), 'utf8')
  return new JSDOM(html).window.document
}

for (const route of routes) {
  test(`${route} reaches every facet of the complete case`, async () => {
    const document = await documentFor(route)
    const navigation = document.querySelector('main nav[data-case-navigation="early-refresh"]')
    assert.ok(navigation, 'The reader needs case navigation inside the article')
    assert.match(navigation.textContent, /A lista continua disponível durante a renovação/)
    const withinPage = route === 'jornadas/early-refresh/'
    const expectedLinks = facetIds.map(id => `${withinPage ? '' : canonicalPath}#${id}`)
    assert.deepEqual([...navigation.querySelectorAll('a')].map(link => link.getAttribute('href')), expectedLinks)
    const active = navigation.querySelectorAll('[aria-current="location"]')
    assert.equal(active.length, withinPage ? 0 : 1)
    if (!withinPage) assert.equal(active[0].getAttribute('href'), `${canonicalPath}#${facetIds[routes.indexOf(route)]}`)
    assert.equal(navigation.getAttribute('aria-label'), 'Navegação do caso early-refresh')
  })

  test(`${route} preserves shared fragments and a valid document outline`, async () => {
    const document = await documentFor(route)
    assert.equal(document.querySelectorAll('main h1').length, 1)
    for (const anchor of legacyAnchors[route]) {
      assert.ok(document.getElementById(anchor), `Shared fragment disappeared: #${anchor}`)
    }
    const ids = [...document.querySelectorAll('main [id]')].map(element => element.id)
    assert.equal(new Set(ids).size, ids.length, 'IDs must be unique within the final document')
    for (const link of document.querySelectorAll('nav[aria-label="table of contents"] a[href^="#"]')) {
      assert.ok(document.getElementById(decodeURIComponent(link.hash.slice(1))), `Broken TOC: ${link.hash}`)
    }
  })

  test(`${route} does not present another case as its article pagination`, async () => {
    const document = await documentFor(route)
    const links = [...document.querySelectorAll('article a')].map(link => link.getAttribute('href'))
    assert.ok(!links.some(href => /\/(single-flight-cancel|date-only)\//.test(href || '')),
      'The article pagination must continue this case rather than change cases')
  })
}
