import { readdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const content = path.join(root, 'content')
const changed = []

async function prepare(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isDirectory()) await prepare(path.join(directory, entry.name))
  }
  if (directory === content || !entries.some(entry => entry.name === 'index.mdx')) return
  const indexPath = path.join(directory, 'index.mdx')
  const source = await readFile(indexPath, 'utf8')
  if (!source.startsWith('---\n')) throw Error(`Missing frontmatter: ${indexPath}`)
  if (!/^asIndexPage:\s*true\s*$/m.test(source.split('\n---')[0])) {
    await writeFile(indexPath, source.replace(/^---\n/, '---\nasIndexPage: true\n'))
    changed.push(path.relative(root, indexPath))
  }
  if (!entries.some(entry => entry.name === '_meta.js')) return
  const metaPath = path.join(directory, '_meta.js')
  const { default: meta } = await import(pathToFileURL(metaPath).href)
  if (!Object.hasOwn(meta, 'index')) return
  if (typeof meta.index !== 'string') throw Error(`Index metadata needs explicit preservation: ${metaPath}`)
  const { index, ...rest } = meta
  await writeFile(metaPath, `export default ${JSON.stringify(rest, null, 2)}\n`)
  changed.push(path.relative(root, metaPath))
}

await prepare(content)
console.log(JSON.stringify({ prepared: changed.length, changed }))
