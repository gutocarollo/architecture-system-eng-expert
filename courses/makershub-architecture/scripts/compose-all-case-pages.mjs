import { readFile, writeFile, mkdir, access } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createHash } from 'node:crypto'
import { createProcessor } from '@mdx-js/mdx'
import remarkFrontmatter from 'remark-frontmatter'
import remarkGfm from 'remark-gfm'
import Slugger from 'github-slugger'
import { caseEntries, caseFacets } from '../case-content/cases.js'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const receiptPath = path.join(root, 'tasks/FBI-4991-case-navigation-all/migration.json')
try { await access(receiptPath); throw new Error('Migration already applied. Edit the canonical bodies instead of rerunning it.') } catch (error) { if (error.code !== 'ENOENT') throw error }
const parser = createProcessor({ remarkPlugins: [remarkFrontmatter, remarkGfm] })
const categories = ['explicacoes', 'tutoriais', 'guias', 'referencia']
const writes = new Map()
const report = []
const textOf = node => node.value ?? (node.children || []).map(textOf).join('')
const walk = (node, callback) => { callback(node); for (const child of node.children || []) walk(child, callback) }
const hash = text => createHash('sha256').update(text).digest('hex')
const parse = source => parser.parse(source)
const raw = (source, node) => source.slice(node.position.start.offset, node.position.end.offset)
function edit(source, edits) { for (const item of edits.sort((a,b) => b.start - a.start)) source = source.slice(0,item.start) + item.value + source.slice(item.end); return source }
const replace = (node, value = '') => ({ start: node.position.start.offset, end: node.position.end.offset, value })
function headingInfo(tree) {
  const slugger = new Slugger(), result = []
  walk(tree, node => { if (node.type !== 'heading' || node.depth === 1) return
    const value = textOf(node), custom = value.match(/\s*\[#([^\]]+)\]\s*$/)
    result.push({ node, id: slugger.slug(custom ? custom[1] : value), text: value.replace(/\s*\[#[^\]]+\]\s*$/, '') })
  }); return result
}
function navigationParagraph(node, caseId) {
  if (node.type !== 'paragraph') return false
  const text = textOf(node)
  if (!/^(Continue o mesmo caso:|Você já observou a diferença\. Continue o mesmo caso:|Para continuar o mesmo problema,|Quando precisar da explicação ou dos passos,|Retorne ao caso)/.test(text)) return false
  const urls = []; walk(node, item => { if (item.type === 'link') urls.push(item.url) })
  const allowed = [`/jornadas/${caseId}/`, ...categories.map(category => `/${category}/casos/${caseId}/`)]
  return urls.length >= 4 && urls.includes(allowed[0]) && urls.every(url => allowed.includes(url))
}
function semantic(source) {
  return edit(source, headingInfo(parse(source)).map(({node,text}) => replace(node, `HEADING ${text}`))).replace(/\s+/g, ' ').trim()
}
function signatures(tree) {
  const code = [], tables = []
  walk(tree, node => { if (node.type === 'code') code.push([node.lang,node.value]); if (node.type === 'table') tables.push(textOf(node)) })
  return { code: hash(JSON.stringify(code)), tables: hash(JSON.stringify(tables)) }
}
function retargetCaseLinks(source, caseId) {
  const edits = []
  walk(parse(source), node => {
    if (node.type !== 'link') return
    for (let index = 0; index < categories.length; index++) {
      const previous = `/${categories[index]}/casos/${caseId}/`
      if (node.url === previous) {
        edits.push(replace(node, raw(source,node).replace(previous, `/jornadas/${caseId}/#${caseFacets[index+1].id}`)))
      }
    }
  })
  return edit(source, edits)
}
function frontmatter(source, tree, searchable) {
  const yaml = tree.children.find(node => node.type === 'yaml')
  let value = raw(source, yaml)
  if (searchable === false) value = value.includes('searchable:') ? value.replace(/^searchable:.*$/m,'searchable: false') : value.replace(/\n---$/, '\nsearchable: false\n---')
  return value
}

for (const entry of caseEntries) {
  const journeyPath = `content/jornadas/${entry.id}/index.mdx`
  const journey = await readFile(path.join(root,journeyPath),'utf8'), journeyTree = parse(journey)
  const oldSections = journeyTree.children.filter(node => node.type === 'mdxJsxFlowElement' && node.name === 'section' && node.attributes.some(attr => attr.name === 'data-case-facet'))
  const overviewHeadings = new Set(journeyTree.children.filter(node => node.type === 'heading' && node.depth > 1).map(node => headingInfo({type:'root',children:[node]})[0].id))
  const bodyImports = [], sectionBlocks = []
  for (let index=0;index<4;index++) {
    const facet = caseFacets[index+1], routePath = `content/${categories[index]}/casos/${entry.id}/index.mdx`
    const original = await readFile(path.join(root,routePath),'utf8'), originalTree = parse(original)
    const title = raw(original, originalTree.children.find(node => node.type === 'heading' && node.depth === 1)).replace(/^#\s+/, '')
    const sharedPath = `case-content/${entry.id}/${facet.id}.mdx`
    let body, alreadyShared = entry.id === 'early-refresh'
    if (alreadyShared) body = await readFile(path.join(root,sharedPath),'utf8')
    else body = edit(original, originalTree.children.filter(node => node.type === 'yaml' || (node.type === 'heading' && node.depth === 1) || navigationParagraph(node,entry.id)).map(node => replace(node))).trim()+'\n'
    const before = body, changes = []
    for (const heading of headingInfo(parse(body))) {
      const depth = alreadyShared ? heading.node.depth : heading.node.depth + 1
      let content = raw(body,heading.node).replace(/^#{2,6}\s+/, '')
      if (facet.id === 'guide' && heading.id === 'antes-de-começar' && overviewHeadings.has(heading.id)) content = heading.text + ' [#guide-before-start]'
      changes.push(replace(heading.node, '#'.repeat(depth)+' '+content))
    }
    body = edit(body,changes).trim()+'\n'
    if (semantic(before) !== semantic(body)) throw new Error('Content changed while extracting '+routePath)
    const beforeSignature = signatures(parse(before)), afterSignature = signatures(parse(body))
    if (JSON.stringify(beforeSignature)!==JSON.stringify(afterSignature)) throw new Error('Code or table changed: '+routePath)
    writes.set(sharedPath,body)
    const provenanceImport = alreadyShared ? "import { EarlyRefreshProvenance } from '../../../../components/EarlyRefreshFacts.jsx'\n" : ''
    const provenance = alreadyShared ? '<EarlyRefreshProvenance />\n\n' : ''
    const wrapper = `${frontmatter(original,originalTree,false)}\n\nimport CaseBody from '../../../../${sharedPath}'\nimport { CaseBreadcrumb, CaseNavigation, CaseNext, CaseSequence } from '../../../../components/CaseNavigation.jsx'\nimport { legacyCaseHeadings } from '../../../../components/LegacyCaseHeadings.jsx'\n${provenanceImport}\n<CaseBreadcrumb caseId="${entry.id}" current="${facet.id}" />\n\n# ${title}\n\n<CaseNavigation caseId="${entry.id}" current="${facet.id}" />\n\n${provenance}## ${facet.title}\n\n<CaseBody components={legacyCaseHeadings} />\n\n<CaseNext caseId="${entry.id}" current="${facet.id}" />\n\n<CaseSequence caseId="${entry.id}" current="${facet.id}" />\n`
    writes.set(routePath,wrapper)
    const name = facet.id[0].toUpperCase()+facet.id.slice(1)
    bodyImports.push(`import ${name} from '../../../${sharedPath}'`)
    sectionBlocks.push(`<section data-case-facet="${facet.id}">\n\n## ${facet.title} [#${facet.id}]\n\n<${name} />\n\n<CaseNext caseId="${entry.id}" current="${facet.id}" withinPage />\n\n</section>`)
    report.push({case_id:entry.id,facet:facet.id,source:routePath,body:sharedPath,source_sha256:hash(original),normalized_content_equal:true,code_blocks_unchanged:true,tables_unchanged:true})
  }
  const edits = oldSections.map(node => replace(node))
  for (const node of journeyTree.children) {
    if (oldSections.includes(node)) continue
    if (node.type==='yaml' || (node.type==='heading' && node.depth===1)) edits.push(replace(node))
    if (node.type==='mdxjsEsm' && /CaseNavigation|CaseNext|case-content\/early-refresh\//.test(raw(journey,node))) edits.push(replace(node))
    if (node.type==='mdxJsxFlowElement' && ['CaseNavigation','CaseNext','CaseBreadcrumb','CaseSequence'].includes(node.name)) edits.push(replace(node))
    if (node.type==='mdxJsxFlowElement' && node.name==='span' && node.attributes.some(attr=>attr.name==='id'&&attr.value==='overview')) edits.push(replace(node))
    if (node.type==='mdxJsxFlowElement' && node.name==='CaseChoices') edits.push(replace(node,`<CaseChoices caseId="${entry.id}" withinPage />`))
    if (node.type==='table') {
      let table=raw(journey,node)
      for(let i=0;i<4;i++)table=table.replaceAll(`/${categories[i]}/casos/${entry.id}/`,`#${caseFacets[i+1].id}`)
      edits.push(replace(node,`<div data-case-choices="${entry.id}">\n\n${table}\n\n</div>`))
    }
  }
  let overview = edit(journey,edits).trim()
  const title = raw(journey,journeyTree.children.find(node=>node.type==='heading'&&node.depth===1)).replace(/^#\s+/,'')
  const insertion = overview.search(/^(?:Quando terminar a prática|Depois de concluir este caso|## Conceitos deste caso)/m)
  if (insertion<0) overview += '\n\n'+sectionBlocks.join('\n\n')
  else overview = overview.slice(0,insertion)+sectionBlocks.join('\n\n')+'\n\n'+overview.slice(insertion)
  const factsImport = entry.id==='early-refresh' ? "import { EarlyRefreshFact, EarlyRefreshProvenance } from '../../../components/EarlyRefreshFacts.jsx'\n" : ''
  // The early-refresh fact import remains only once after removing the original import.
  overview = overview.replace(/^import \{[^\n]+\} from '[^']*EarlyRefreshFacts.jsx'\n?/gm,'')
  writes.set(journeyPath,`${frontmatter(journey,journeyTree)}\n\n${bodyImports.join('\n')}\nimport { CaseBreadcrumb, CaseNavigation, CaseNext, CaseSequence, CaseChoices } from '../../../components/CaseNavigation.jsx'\n${factsImport}\n<CaseBreadcrumb caseId="${entry.id}" />\n\n<span id="overview" className="case-legacy-anchor" />\n\n# ${title}\n\n<CaseNavigation caseId="${entry.id}" withinPage />\n\n${overview}\n\n<CaseSequence caseId="${entry.id}" withinPage />\n`)
  const conceptsPath=`content/jornadas/${entry.id}/conceitos.mdx`
  try {
    const source=await readFile(path.join(root,conceptsPath),'utf8'),tree=parse(source),headings=new Set(headingInfo(tree).map(item=>item.id))
    const removals=tree.children.filter(node=>node.type==='mdxJsxFlowElement'&&node.name==='span'&&node.attributes.some(attr=>attr.name==='id'&&headings.has(attr.value))).map(node=>replace(node))
    let text=retargetCaseLinks(edit(source,removals),entry.id)
    const frontEnd=text.indexOf('\n---',4)+4
    text=text.slice(0,frontEnd)+`\n\nimport { CaseBreadcrumb, CaseNavigation, CaseSequence } from '../../../components/CaseNavigation.jsx'\n\n<CaseBreadcrumb caseId="${entry.id}" current="concepts" />\n`+text.slice(frontEnd)
    text=text.replace(/^(# .+)$/m,`$1\n\n<CaseNavigation caseId="${entry.id}" current="concepts" />`)
    text+=`\n\n<CaseSequence caseId="${entry.id}" />\n`
    writes.set(conceptsPath,text)
  } catch(error) { if(error.code!=='ENOENT')throw error }
}
for(const directory of ['jornadas',...categories.map(category=>category+'/casos')]){
 const filename=`content/${directory}/_meta.js`,meta=(await import(pathToFileURL(path.join(root,filename)).href)).default
 for(const entry of caseEntries){const old=meta[entry.id];meta[entry.id]={...(typeof old==='string'?{title:old}:old),theme:{...(old?.theme||{}),breadcrumb:false,pagination:false}}}
 writes.set(filename,'export default '+JSON.stringify(meta,null,2)+'\n')
}
for(const entry of caseEntries){const filename=`content/jornadas/${entry.id}/_meta.js`;try{const meta=(await import(pathToFileURL(path.join(root,filename)).href)).default;for(const key of Object.keys(meta)){const old=meta[key];meta[key]={...(typeof old==='string'?{title:old}:old),theme:{...(old?.theme||{}),breadcrumb:false,pagination:false}}}writes.set(filename,'export default '+JSON.stringify(meta,null,2)+'\n')}catch(error){if(error.code!=='ERR_MODULE_NOT_FOUND'&&error.code!=='ENOENT')throw error}}
for(const [filename,source]of writes){await mkdir(path.dirname(path.join(root,filename)),{recursive:true});await writeFile(path.join(root,filename),source)}
await writeFile(receiptPath,JSON.stringify({baseline_commit:'ef5bd78bd0224571ccfde49873ac1b16489b59c1',cases:caseEntries.length,facets:report.length,files_written:writes.size,facets_checked:report},null,2)+'\n')
console.log(JSON.stringify({cases:caseEntries.length,facets:report.length,files_written:writes.size,normalized_bodies_unchanged:true}))
