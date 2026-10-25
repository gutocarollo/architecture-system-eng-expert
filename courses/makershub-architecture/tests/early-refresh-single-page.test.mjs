import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { JSDOM } from 'jsdom'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const htmlRoot = process.env.EARLY_REFRESH_HTML_ROOT || path.join(root, 'out')
const html = await readFile(path.join(htmlRoot, 'jornadas/early-refresh/index.html'), 'utf8')
const document = new JSDOM(html).window.document
const facets = [
  ['explanation', ['a-condição-anterior', 'o-mecanismo-que-muda-a-condição', 'o-benefício-o-custo-e-o-limite']],
  ['tutorial', ['1-prepare-o-ambiente-isolado', '3-execute-as-duas-condições', '4-compare-a-saída', '7-reinicie-e-conclua']],
  ['guide', ['guide-before-start', '1-fixe-o-contrato-e-a-fronteira', '5-feche-a-decisão-com-seu-limite', 'localizadores-de-consulta']],
  ['reference', ['entradas-e-ambiente', 'versões-e-fronteiras-da-reprodução', 'garantia-parâmetros-e-limites', 'recibo-e-rastreabilidade']]
]

for (const [facet, headings] of facets) {
  test(`the journey contains the complete ${facet} facet in the same document`, () => {
    const section = document.querySelector(`main section[data-case-facet="${facet}"]`)
    assert.ok(section, `${facet} must be readable here, not reached through another page`)
    assert.equal(section.querySelector('h2')?.id, facet)
    assert.ok(section.textContent.length > 600, 'A link or teaser does not replace the full facet')
    for (const id of headings) {
      assert.ok(section.querySelector(`h3[id="${id}"]`), `Missing full-content heading: ${id}`)
    }
  })
}

test('the journey navigation and continuation links stay on the current page', () => {
  const navigation = document.querySelector('main nav[data-case-navigation="early-refresh"]')
  assert.ok(navigation)
  assert.deepEqual([...navigation.querySelectorAll('a')].map(link => link.getAttribute('href')),
    ['#overview', '#explanation', '#tutorial', '#guide', '#reference'])
  for (const link of document.querySelectorAll('main nav a, main .case-next a')) {
    const href = link.getAttribute('href')
    assert.ok(href.startsWith('#'), `This case must not require changing pages: ${href}`)
    assert.ok(document.getElementById(href.slice(1)), `Missing destination: ${href}`)
  }
  assert.ok(![...document.querySelectorAll('main a')].some(link =>
    /^\/(explicacoes|tutoriais|guias|referencia)\/casos\/early-refresh\//.test(link.getAttribute('href') || '')))
})

test('the journey provides practice and reference without leaving the case', () => {
  const tutorial = document.querySelector('[data-case-facet="tutorial"]')
  const reference = document.querySelector('[data-case-facet="reference"]')
  assert.ok(tutorial?.querySelector('a[href="/downloads/early-refresh.zip"]'))
  assert.match(tutorial.textContent, /python3 labs\/architecture\/early-refresh\/run\.py/)
  assert.match(reference?.textContent || '', /early_ttl_seconds=0\.5/)
  assert.match(reference.textContent, /comparison=PASS/)
  assert.match(reference.textContent, /expiração dura/)
})

test('the compiled table of contents includes every facet and its subsections', () => {
  const toc = document.querySelector('nav[aria-label="table of contents"]')
  assert.ok(toc)
  const links = [...toc.querySelectorAll('a[href^="#"]')].map(link => decodeURIComponent(link.hash.slice(1)))
  for (const [facet, headings] of facets) {
    for (const id of [facet, ...headings]) assert.ok(links.includes(id), `TOC omitted ${id}`)
  }
})
