import fs from 'node:fs/promises'
import path from 'node:path'
import crypto from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { compile, createProcessor } from '@mdx-js/mdx'
import GithubSlugger from 'github-slugger'

const base = "/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991/tasks/FBI-4991-arquitetura-nextra/execution/curation"
const root = path.resolve(base, '../../../..')
const contentRoot = path.join(root, 'content')
const files = async directory => {
  const entries = await fs.readdir(directory, { withFileTypes: true })
  const nested = await Promise.all(entries.map(entry => entry.isDirectory()
    ? files(path.join(directory, entry.name)) : [path.join(directory, entry.name)]))
  return nested.flat().filter(file => /\.mdx?$/.test(file))
}
const walk = (node, fn) => {
  fn(node)
  for (const child of node.children ?? []) walk(child, fn)
}
const nodeText = node => node.value ?? (node.children ?? []).map(nodeText).join('')
const routeFor = file => '/' + path.relative(contentRoot, file)
  .replace(/\\/g, '/').replace(/\.mdx?$/, '').replace(/\/index$/, '').replace(/^index$/, '')
const allFiles = await files(contentRoot)
const pages = new Map()
const errors = []
const receipts = []
for (const file of allFiles) {
  const text = await fs.readFile(file, 'utf8')
  let tree
  try { tree = createProcessor().parse(text) } catch (error) {
    if (file.startsWith(path.join(contentRoot, 'referencia') + path.sep)) {
      errors.push({ file: path.relative(root, file), kind: 'MDX_PARSE', message: error.message })
    }
    continue
  }
  const slugger = new GithubSlugger()
  const anchors = new Set()
  const links = []
  walk(tree, node => {
    if (node.type === 'heading') anchors.add(slugger.slug(nodeText(node)))
    if (node.type === 'link') links.push(node.url)
    for (const attribute of node.attributes ?? []) {
      if (attribute.name === 'id' && typeof attribute.value === 'string') anchors.add(attribute.value)
      if (attribute.name === 'href' && typeof attribute.value === 'string') links.push(attribute.value)
    }
  })
  pages.set(routeFor(file).replace(/\/$/, '') || '/', { file, text, anchors, links })
}
for (const [route, page] of pages) {
  if (!page.file.startsWith(path.join(contentRoot, 'referencia') + path.sep)) continue
  try { await compile(page.text) } catch (error) {
    errors.push({ file: path.relative(root, page.file), kind: 'MDX_COMPILE', message: error.message })
  }
  for (const href of page.links) {
    if (/^(?:https?:|mailto:|tel:|data:)/.test(href)) continue
    const resolved = new URL(href, 'https://course.invalid' + route + '/')
    const destinationRoute = decodeURIComponent(resolved.pathname).replace(/\.(md|mdx)$/, '')
      .replace(/\/index\/?$/, '').replace(/\/$/, '') || '/'
    const destination = pages.get(destinationRoute)
    if (!destination) {
      const asset = path.join(root, 'public', decodeURIComponent(resolved.pathname))
      try { await fs.access(asset) } catch {
        errors.push({ file: path.relative(root, page.file), kind: 'LINK_TARGET', href, destinationRoute })
      }
      continue
    }
    if (resolved.hash && !destination.anchors.has(decodeURIComponent(resolved.hash.slice(1)))) {
      errors.push({ file: path.relative(root, page.file), kind: 'LINK_ANCHOR', href, destinationRoute })
    }
  }
  receipts.push({ file: path.relative(root, page.file), sha256: crypto.createHash('sha256').update(page.text).digest('hex') })
}
const result = { observed_utc: new Date().toISOString(), scope: 'Read-only MDX parse, compile and links of content/referencia against the current content tree.', files: receipts.length, errors, receipts }
await fs.writeFile(path.join("/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991/tasks/FBI-4991-arquitetura-nextra/execution/reviews", 'curation-independent.mdx.json'), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify({ files: result.files, errors: result.errors.length, examples: errors.slice(0, 8) }))
process.exitCode = errors.length ? 1 : 0
