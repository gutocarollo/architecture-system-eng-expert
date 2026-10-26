import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { JSDOM } from 'jsdom'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const htmlRoot = process.env.COURSE_HTML_ROOT || path.join(root, 'out')
const baseline = JSON.parse(await readFile(path.join(root, 'tests/case-navigation-baseline.json'), 'utf8'))
const stages = ['Explicação', 'Tutorial', 'Guia', 'Referência']
const ids = ['explanation', 'tutorial', 'guide', 'reference']

test('the coverage inventory includes every case and every facet directory', async () => {
  const expected = baseline.cases.map(entry => entry.id).sort()
  for (const category of ['explicacoes', 'tutoriais', 'guias', 'referencia']) {
    const directories = await readdir(path.join(root, 'content', category, 'casos'), { withFileTypes: true })
    assert.deepEqual(directories.filter(item => item.isDirectory()).map(item => item.name).sort(), expected)
  }
})

async function withDocument(route, check) {
  const html = await readFile(path.join(htmlRoot, route, 'index.html'), 'utf8')
  const window = new JSDOM(html).window
  try { await check(window.document) } finally { window.close() }
}

for (const entry of baseline.cases) {
  test(`${entry.id}: full case, breadcrumb, blue links and ordered workflow`, async () => {
    await withDocument(`jornadas/${entry.id}/`, document => {
      const main = document.querySelector('main')
      const breadcrumb = main.querySelector('[data-case-breadcrumb]')
      assert.ok(breadcrumb, 'Restore the case breadcrumb')
      assert.match(breadcrumb.textContent, /Siga um caso completo/)
      assert.ok(breadcrumb.textContent.includes(entry.title))
      assert.equal(main.querySelectorAll('h1').length, 1)
      assert.ok(![...main.querySelectorAll('a[href]')].some(link =>
        ['explicacoes', 'tutoriais', 'guias', 'referencia'].some(category =>
          link.getAttribute('href').startsWith(`/${category}/casos/${entry.id}/`))),
      'References to this case must stay in its complete journey, including links inside the content')
      for (const [index, id] of ids.entries()) {
        const section = main.querySelector(`section[data-case-facet="${id}"]`)
        assert.ok(section, `The complete ${id} facet must exist in this journey`)
        assert.ok(section.textContent.length > 300, 'A teaser does not replace a facet')
        const next = section.querySelector('[data-case-pager] a[rel="next"]')
        if (index < 3) {
          assert.ok(next)
          assert.equal(next.getAttribute('href'), `#${ids[index + 1]}`)
          assert.ok(next.textContent.includes(stages[index + 1]))
        }
      }
      const navigation = main.querySelector(`[data-case-navigation="${entry.id}"]`)
      assert.ok(navigation)
      assert.deepEqual([...navigation.querySelectorAll('a')].map(a => a.getAttribute('href')),
        ['#overview', ...ids.map(id => `#${id}`)])
      const sequence = main.querySelector('[data-case-sequence]')
      assert.ok(sequence, 'The page footer must show the four stages, not global neighbours')
      assert.deepEqual([...sequence.querySelectorAll('a')].map(a => a.textContent.trim()), stages)
      for (const link of main.querySelectorAll('[data-case-navigation] a, [data-case-choices] a, [data-case-sequence] a')) {
        assert.ok(link.classList.contains('x:text-primary-600'), `Missing blue link styling: ${link.textContent}`)
        assert.ok(link.classList.contains('x:underline'), `Missing link affordance: ${link.textContent}`)
        assert.ok(link.getAttribute('href').startsWith('#'))
      }
      const allIds = [...main.querySelectorAll('[id]')].map(e => e.id)
      assert.equal(new Set(allIds).size, allIds.length, 'No duplicate anchors in the composed document')
      for (const link of document.querySelectorAll('nav[aria-label="table of contents"] a[href^="#"]')) {
        assert.ok(document.getElementById(decodeURIComponent(link.hash.slice(1))), `Broken TOC: ${link.hash}`)
      }
      assert.ok(![...document.querySelectorAll('article a')].some(a =>
        a.textContent.trim() === 'Conceitos e prática'), 'Global pagination must not replace the case workflow')
    })
  })

  test(`${entry.id}: direct facets and legacy fragments retain the case context`, async () => {
    for (let index = 0; index < entry.facets.length; index++) {
      const facet = entry.facets[index]
      await withDocument(facet.route, document => {
        const main = document.querySelector('main')
        const breadcrumb = main.querySelector('[data-case-breadcrumb]')
        assert.ok(breadcrumb)
        assert.ok(breadcrumb.textContent.includes(entry.title))
        assert.ok(breadcrumb.textContent.includes(stages[index]))
        const links = [...main.querySelectorAll('[data-case-navigation] a')]
        assert.deepEqual(links.map(a => a.getAttribute('href')),
          ['overview', ...ids].map(id => `/jornadas/${entry.id}/#${id}`))
        const pager = main.querySelector('[data-case-pager]')
        assert.ok(pager)
        const next = pager.querySelector('a[rel="next"]')
        if (index < 3) {
          assert.ok(next, 'Offer the next stage of this same case')
          assert.equal(next.getAttribute('href'), `/jornadas/${entry.id}/#${ids[index + 1]}`)
          assert.ok(next.textContent.includes(stages[index + 1]))
        }
        for (const fragment of facet.fragments) assert.ok(document.getElementById(fragment), `Lost ${facet.route}#${fragment}`)
        const allIds = [...main.querySelectorAll('[id]')].map(e => e.id)
        assert.equal(new Set(allIds).size, allIds.length)
      })
    }
  })

  test(`${entry.id}: journey and optional concepts preserve their existing anchors`, async () => {
    for (const page of entry.supportingPages) {
      await withDocument(page.route, document => {
        for (const fragment of page.fragments) assert.ok(document.getElementById(fragment), `Lost ${page.route}#${fragment}`)
        if (page.kind === 'concepts') {
          assert.ok(document.querySelector('main [data-case-breadcrumb]'))
          assert.ok(document.querySelector('main [data-case-sequence]'))
          assert.ok(![...document.querySelectorAll('article a')].some(a => a.textContent.trim() === 'Conceitos e prática'))
        }
      })
    }
  })
}
