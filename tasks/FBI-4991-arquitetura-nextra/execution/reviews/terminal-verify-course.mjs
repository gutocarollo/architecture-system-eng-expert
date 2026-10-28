import { createHash } from 'node:crypto'
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createProcessor } from '@mdx-js/mdx'
import remarkFrontmatter from 'remark-frontmatter'
import remarkGfm from 'remark-gfm'
import GithubSlugger from 'github-slugger'

const repositoryRoot = '/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991'
const taskRoot = path.join(repositoryRoot, 'tasks', 'architecture-course-2026-10-14')
const contentRoot = path.join(repositoryRoot, 'content')
const matrixPath = path.join(taskRoot, 'evidence', 'coverage.json')
const defaultReportPath = path.join(taskRoot, 'artifacts', 'course-verification.json')
const expectedConceptCount = 310
const expectedPriorityCount = 40

const proseExcludedTypes = new Set(['list', 'listItem', 'table', 'tableRow', 'tableCell', 'blockquote'])
const semanticPriorityParts = new Set(['definition', 'problem_story', 'benefit', 'cost', 'limit', 'evidence_scope'])

function sha256(value) {
  return createHash('sha256').update(value).digest('hex')
}

function toPosix(value) {
  return value.split(path.sep).join('/')
}

function normalizeText(value) {
  return String(value)
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('en-US')
    .replace(/&/g, ' and ')
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim()
}

function headingKey(value) {
  const withoutPrefix = value.trim().replace(/^\d+(?:\.\d+)*[.)]?\s+/, '')
  const withoutTagline = withoutPrefix.split(/\s+[—–:]\s+/u, 1)[0]
  return normalizeText(withoutTagline)
}

function headingVariants(value) {
  const withoutPrefix = value.trim().replace(/^\d+(?:\.\d+)*[.)]?\s+/, '')
  return [...new Set([
    normalizeText(withoutPrefix),
    ...withoutPrefix.split(/\s+[—–:]\s+/u).map(normalizeText)
  ].filter(Boolean))]
}

function normalizedAnchorKey(value) {
  return normalizeText(value).replace(/\s+/g, '-')
}

function walk(node, visit, parent = null) {
  if (!node || typeof node !== 'object') return
  visit(node, parent)
  for (const child of node.children ?? []) walk(child, visit, node)
}

function nodeText(node, includeInlineCode = false) {
  if (!node || typeof node !== 'object') return ''
  if (node.type === 'text') return node.value ?? ''
  if (node.type === 'inlineCode') return includeInlineCode ? node.value ?? '' : ''
  if (node.type === 'code' || node.type === 'mdxTextExpression') return ''
  return (node.children ?? []).map(child => nodeText(child, includeInlineCode)).join(' ')
}

function countWords(value) {
  return value.match(/[\p{L}\p{N}]+(?:['’][\p{L}\p{N}]+)*/gu)?.length ?? 0
}

function countSentences(value) {
  return (value.match(/[.!?]+(?=\s|$)/gu) ?? []).length
}

function collectParagraphs(nodes, insideExcludedBlock = false, output = []) {
  for (const node of nodes ?? []) {
    const excluded = insideExcludedBlock || ['list', 'listItem', 'table', 'tableRow', 'tableCell', 'blockquote'].includes(node.type)
    if (node.type === 'paragraph' && !excluded) {
      const text = nodeText(node).replace(/\s+/g, ' ').trim()
      if (text) output.push({ text, words: countWords(text), sentences: countSentences(text) })
      continue
    }
    if (!excluded && node.type !== 'heading') collectParagraphs(node.children, false, output)
  }
  return output
}

function assessProse(paragraphs, minimumParagraphs, minimumWords) {
  const words = paragraphs.reduce((total, item) => total + item.words, 0)
  const sentences = paragraphs.reduce((total, item) => total + item.sentences, 0)
  return {
    paragraph_count: paragraphs.length,
    word_count: words,
    sentence_count: sentences,
    meets_structural_threshold: paragraphs.length >= minimumParagraphs && words >= minimumWords && sentences >= 2
  }
}

async function listFiles(directory) {
  let entries
  try {
    entries = await readdir(directory, { withFileTypes: true })
  } catch (error) {
    if (error.code === 'ENOENT') return []
    throw error
  }

  const files = []
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const absolutePath = path.join(directory, entry.name)
    if (entry.isDirectory()) files.push(...await listFiles(absolutePath))
    else if (entry.isFile()) files.push(absolutePath)
  }
  return files
}

function paragraphsInRange(root, startLine, endLine) {
  const paragraphs = []
  function visit(node, excluded = false) {
    const skip = excluded || proseExcludedTypes.has(node.type)
    if (node.type === 'paragraph' && !skip) {
      const line = node.position?.start?.line ?? 0
      if (line > startLine && (endLine == null || line < endLine)) {
        const text = nodeText(node).replace(/\s+/g, ' ').trim()
        if (text) paragraphs.push({ text, words: countWords(text), sentences: countSentences(text), line })
      }
      return
    }
    if (!skip) for (const child of node.children ?? []) visit(child, false)
  }
  visit(root)
  return paragraphs.sort((left, right) => left.line - right.line)
}

function astSection(root, headingNode, headingNodes) {
  const startLine = headingNode.position?.start?.line ?? null
  if (startLine == null) return null
  const nextHeading = headingNodes
    .filter(node => (node.position?.start?.line ?? 0) > startLine && node.depth <= headingNode.depth)
    .sort((left, right) => left.position.start.line - right.position.start.line)[0]
  const endLine = nextHeading?.position?.start?.line ?? null
  return {
    start_line: startLine,
    end_line: endLine,
    paragraphs: paragraphsInRange(root, startLine, endLine)
  }
}

function getAttribute(node, name) {
  const attribute = (node.attributes ?? []).find(item => item.type === 'mdxJsxAttribute' && item.name === name)
  return attribute?.value
}

function addId(ids, value) {
  if (typeof value === 'string' && value.trim()) ids.add(value.trim())
}

function makePageRecord(filePath, source, tree) {
  const relativePath = toPosix(path.relative(repositoryRoot, filePath))
  const headings = []
  const anchors = new Set()
  const explicitAnchors = []
  const headingNodes = []
  const slugger = new GithubSlugger()
  const links = []
  const definitions = new Map()
  const mermaid = []

  walk(tree, node => {
    if (node.type === 'heading') headingNodes.push(node)
  })

  walk(tree, node => {
    if (node.type === 'definition' && node.identifier && node.url) {
      definitions.set(normalizeText(node.identifier), { url: node.url, label: nodeText(node, true) })
    }
  })

  walk(tree, node => {
    if (node.type === 'heading') {
      const title = nodeText(node, true).replace(/\s+/g, ' ').trim()
      const anchor = slugger.slug(title)
      addId(anchors, anchor)
      headings.push({
        title,
        normalized_title: headingKey(title),
        normalized_titles: headingVariants(title),
        anchor,
        depth: node.depth,
        line: node.position?.start?.line ?? null,
        section: astSection(tree, node, headingNodes)
      })
    }
    if (node.type === 'mdxJsxFlowElement' || node.type === 'mdxJsxTextElement') {
      const id = getAttribute(node, 'id')
      addId(anchors, id)
      if (typeof id === 'string' && id.trim()) explicitAnchors.push({ id: id.trim(), line: node.position?.start?.line ?? null })
      if (node.name === 'a') {
        const href = getAttribute(node, 'href')
        const label = nodeText(node, true).replace(/\s+/g, ' ').trim()
        if (typeof href === 'string') links.push({ href, label, line: node.position?.start?.line ?? null, kind: 'jsx-anchor' })
        else if (href != null) links.push({ href: null, label, line: node.position?.start?.line ?? null, kind: 'dynamic-jsx-anchor' })
      }
    }
    if (node.type === 'link') links.push({ href: node.url, label: nodeText(node, true).replace(/\s+/g, ' ').trim(), line: node.position?.start?.line ?? null, kind: 'markdown-link' })
    if (node.type === 'linkReference') {
      const definition = definitions.get(normalizeText(node.identifier))
      links.push({ href: definition?.url ?? null, label: nodeText(node, true).replace(/\s+/g, ' ').trim(), line: node.position?.start?.line ?? null, kind: definition ? 'markdown-reference-link' : 'unresolved-reference-link' })
    }
    if (node.type === 'code' && String(node.lang ?? '').toLocaleLowerCase('en-US') === 'mermaid') {
      const start = node.position?.start?.offset
      const end = node.position?.end?.offset
      const rawFence = Number.isInteger(start) && Number.isInteger(end) ? source.slice(start, end) : null
      mermaid.push({
        page: relativePath,
        page_index: mermaid.length + 1,
        line: node.position?.start?.line ?? null,
        sha256: sha256(rawFence ?? node.value ?? ''),
        hash_basis: rawFence === null ? 'parsed_code_value' : 'exact_fence_source',
        source: node.value ?? ''
      })
    }
  })

  const anchorSections = new Map(headings.map(heading => [heading.anchor, heading]))
  for (const heading of headings) {
    const normalizedAnchor = normalizedAnchorKey(heading.anchor)
    if (!anchorSections.has(normalizedAnchor)) anchorSections.set(normalizedAnchor, heading)
  }
  for (const anchor of explicitAnchors) {
    const followingHeading = headings
      .filter(heading => heading.line != null && anchor.line != null && heading.line >= anchor.line)
      .sort((left, right) => left.line - right.line)[0]
    const precedingHeading = headings
      .filter(heading => heading.line != null && anchor.line != null && heading.line <= anchor.line && (heading.section?.end_line == null || anchor.line < heading.section.end_line))
      .sort((left, right) => right.line - left.line)[0]
    const associated = followingHeading && anchor.line != null && followingHeading.line - anchor.line <= 2
      ? followingHeading
      : precedingHeading ?? followingHeading
    if (associated || !anchorSections.has(anchor.id)) anchorSections.set(anchor.id, associated ?? null)
    const normalizedId = normalizedAnchorKey(anchor.id)
    if (!anchorSections.has(normalizedId)) anchorSections.set(normalizedId, associated ?? null)
  }

  return {
    path: relativePath,
    route: routeForFile(filePath),
    source,
    source_sha256: sha256(source),
    tree,
    headings,
    anchors,
    anchorSections,
    explicitAnchors,
    links,
    mermaid
  }
}

function routeForFile(filePath) {
  const relative = toPosix(path.relative(contentRoot, filePath)).replace(/\.(md|mdx)$/i, '')
  const route = relative === 'index' ? '' : relative.replace(/\/index$/i, '')
  return normalizeRoute(`/${route}`)
}

function normalizeRoute(route) {
  const normalized = path.posix.normalize(route || '/')
  const rooted = normalized.startsWith('/') ? normalized : `/${normalized}`
  return rooted.length > 1 ? rooted.replace(/\/+$/, '') : '/'
}

function resolveRoute(sourceRoute, hrefPath) {
  const decodedPath = decodeURIComponent(hrefPath)
  const combined = decodedPath.startsWith('/')
    ? decodedPath
    : path.posix.join(path.posix.dirname(sourceRoute), decodedPath)
  const route = path.posix.normalize(combined)
  return route.startsWith('/') ? route : `/${route}`
}

function isExternalUrl(href) {
  return /^(?:[a-z][a-z\d+.-]*:|\/\/)/iu.test(href)
}

function pageFromRoute(route, pageByRoute) {
  const withoutExtension = route.replace(/\.(?:md|mdx)$/iu, '').replace(/\/index\/?$/iu, '') || '/'
  return pageByRoute.get(normalizeRoute(withoutExtension))
}

function targetFileFromRoute(route) {
  const cleanRoute = route.replace(/^\/+/, '')
  const safeRelative = path.posix.normalize(cleanRoute)
  if (safeRelative === '..' || safeRelative.startsWith('../')) return null
  return path.join(contentRoot, ...safeRelative.split('/'))
}

async function inspectLink(link, page, pageByRoute, pageByPath) {
  const result = { page: page.path, line: link.line, href: link.href, kind: link.kind, status: 'unchecked' }
  if (link.href === null) {
    result.status = link.kind === 'unresolved-reference-link' ? 'unresolved_reference' : 'unverifiable_dynamic'
    return result
  }
  if (/^\/(?:Users|home|private|Volumes)\//iu.test(link.href)) {
    result.status = 'nonportable_filesystem_path'
    return result
  }
  if (isExternalUrl(link.href)) {
    let externalUrl
    try {
      externalUrl = new URL(link.href)
    } catch {
      result.status = 'invalid_url'
      return result
    }
    result.status = ['http:', 'https:'].includes(externalUrl.protocol) ? 'unverifiable_external' : 'unverifiable_non_http_external'
    return result
  }

  let parsed
  try {
    parsed = new URL(link.href, `https://course.invalid${page.route === '/' ? '/' : page.route}`)
  } catch {
    result.status = 'invalid_url'
    return result
  }
  if (parsed.origin !== 'https://course.invalid') {
    result.status = 'external'
    return result
  }

  const rawPath = link.href.split(/[?#]/u, 1)[0]
  if (rawPath && !rawPath.startsWith('/')) {
    let decodedPath
    try {
      decodedPath = decodeURIComponent(rawPath)
    } catch {
      result.status = 'invalid_url'
      return result
    }
    const relativeBase = path.resolve(repositoryRoot, path.dirname(page.path), decodedPath)
    const extension = path.extname(relativeBase).toLocaleLowerCase('en-US')
    const relativeCandidates = extension
      ? [relativeBase]
      : [relativeBase, `${relativeBase}.mdx`, `${relativeBase}.md`, path.join(relativeBase, 'index.mdx'), path.join(relativeBase, 'index.md')]
    for (const candidate of relativeCandidates) {
      const relativeToRoot = path.relative(repositoryRoot, candidate)
      if (relativeToRoot === '..' || relativeToRoot.startsWith(`..${path.sep}`) || path.isAbsolute(relativeToRoot)) continue
      const targetPage = pageByPath.get(candidate)
      if (targetPage) {
        if (parsed.hash) {
          let anchor
          try {
            anchor = decodeURIComponent(parsed.hash.slice(1))
          } catch {
            result.status = 'invalid_url'
            return result
          }
          result.target = targetPage.path
          result.anchor = anchor
          result.status = targetPage.anchors.has(anchor) ? 'valid' : 'missing_anchor'
        } else {
          result.target = targetPage.path
          result.status = 'valid'
        }
        return result
      }
      try {
        await readFile(candidate)
        result.target = toPosix(relativeToRoot)
        result.status = 'valid_local_file'
        return result
      } catch {
        // Try the next source-relative page or local asset form.
      }
    }
    result.status = 'missing_target'
    return result
  }

  let route
  let exactTarget
  try {
    route = resolveRoute(page.route, parsed.pathname)
    exactTarget = pageByPath.get(path.resolve(repositoryRoot, decodeURIComponent(parsed.pathname).replace(/^\//, '')))
  } catch {
    result.status = 'invalid_url'
    return result
  }
  const targetPage = parsed.pathname === page.route || parsed.pathname === '' ? page : pageFromRoute(route, pageByRoute)
  const resolvedPage = targetPage ?? exactTarget ?? null

  if (resolvedPage) {
    if (parsed.hash) {
      let anchor
      try {
        anchor = decodeURIComponent(parsed.hash.slice(1))
      } catch {
        result.status = 'invalid_url'
        return result
      }
      result.target = resolvedPage.path
      result.anchor = anchor
      result.status = resolvedPage.anchors.has(anchor) ? 'valid' : 'missing_anchor'
      return result
    }
    result.target = resolvedPage.path
    result.status = 'valid'
    return result
  }

  const candidates = [
    targetFileFromRoute(route),
    targetFileFromRoute(`${route.replace(/^\//, '')}.mdx`),
    targetFileFromRoute(`${route.replace(/^\//, '')}.md`),
    targetFileFromRoute(`${route.replace(/^\//, '')}/index.mdx`),
    targetFileFromRoute(`${route.replace(/^\//, '')}/index.md`),
    path.join(repositoryRoot, 'public', ...route.replace(/^\//, '').split('/'))
  ].filter(Boolean)

  for (const candidate of candidates) {
    try {
      await readFile(candidate)
      result.target = toPosix(path.relative(repositoryRoot, candidate))
      result.status = 'valid_local_file'
      return result
    } catch {
      // Continue through the small set of Nextra page and public-file candidates.
    }
  }

  result.status = 'missing_target'
  return result
}

function buildSafeAliases(matrix) {
  const concepts = matrix.concepts ?? []
  const owners = new Map()
  for (const concept of concepts) {
    for (const label of [concept.canonical_name, ...(concept.aliases ?? [])]) {
      const key = headingKey(label)
      const ids = owners.get(key) ?? new Set()
      ids.add(concept.concept_id)
      owners.set(key, ids)
    }
  }

  const blockedAliases = new Set()
  for (const note of matrix.alias_scope_notes ?? []) {
    if (note.alias) blockedAliases.add(headingKey(note.alias))
    if (note.catalog_label) {
      const concept = concepts.find(item => headingKey(item.canonical_name) === headingKey(note.catalog_label))
      for (const alias of concept?.aliases ?? []) blockedAliases.add(headingKey(alias))
    }
  }

  return new Map(concepts.map(concept => [
    concept.concept_id,
    (concept.aliases ?? []).filter(alias => {
      const key = headingKey(alias)
      return owners.get(key)?.size === 1 && !blockedAliases.has(key)
    })
  ]))
}

function mentionExists(page, term) {
  return normalizeText(page.source).includes(normalizeText(term))
}

function sectionMatches(page, { canonicalName, aliases = [], anchorIds = [] }) {
  const labels = new Map([[headingKey(canonicalName), 'canonical_heading']])
  for (const alias of aliases) labels.set(headingKey(alias), 'unambiguous_alias')
  const matches = []
  const seen = new Set()

  for (const heading of page.headings) {
    const locator = (heading.normalized_titles ?? [heading.normalized_title]).map(key => labels.get(key)).find(Boolean)
    if (!locator) continue
    const key = `${heading.anchor}:${heading.line}`
    seen.add(key)
    matches.push({
      page: page.path,
      title: heading.title,
      anchor: heading.anchor,
      line: heading.line,
      locator,
      actual_anchor: heading.anchor,
      anchor_exact: true,
      section: heading.section
    })
  }

  for (const anchorEntry of anchorIds) {
    const anchorId = typeof anchorEntry === 'string' ? anchorEntry : anchorEntry?.id
    if (!anchorId) continue
    const heading = page.anchorSections.get(anchorId)
    const key = heading ? `${heading.anchor}:${heading.line}` : `anchor:${anchorId}`
    if (seen.has(key)) continue
    seen.add(key)
    matches.push({
      page: page.path,
      title: heading?.title ?? null,
      anchor: anchorId,
      line: heading?.line ?? page.explicitAnchors.find(item => item.id === anchorId)?.line ?? null,
      locator: typeof anchorEntry === 'string' ? (heading ? 'explicit_anchor' : 'unresolved_anchor') : anchorEntry.locator ?? 'explicit_anchor',
      actual_anchor: heading?.anchor ?? null,
      anchor_exact: page.anchors.has(anchorId),
      section: heading?.section ?? null
    })
  }

  return matches
}

function linksWithinSection(page, section) {
  if (!section) return []
  return page.links.filter(link =>
    link.line != null && link.line >= section.start_line &&
    (section.end_line == null || link.line < section.end_line)
  )
}

function expectedReferenceTerms(value) {
  if (!value) return []
  const codeTerms = [...String(value).matchAll(/`([^`]+)`/gu)].map(match => match[1])
  const plainTerms = String(value).replace(/`[^`]+`/gu, '').split(/[;,/+]+/u)
  return [...new Set([...codeTerms, ...plainTerms].map(term => term.trim()).filter(term => term.length >= 4 && !/^REF$/iu.test(term)))]
}

function referencePartStatus(page, section, part, priority) {
  const links = linksWithinSection(page, section)
  const candidateLinks = links.slice(0, 5).map(link => ({ href: link.href, label: link.label, line: link.line }))
  if (part === 'applicable_skill') {
    const skillLink = links.find(link =>
      typeof link.href === 'string' && /\/referencia\/skills-e-projetos\/?(?:#.*)?$/iu.test(link.href) && Boolean(link.label?.trim())
    )
    return {
      status: skillLink ? 'LINK_PRESENT_UNVERIFIED' : 'UNVERIFIABLE',
      reason: skillLink ? 'The MDX contains a labeled link to the skills registry; applicability needs human review.' : 'No labeled skills-registry link was observed in this section; council review is required.',
      link: skillLink ? { href: skillLink.href, label: skillLink.label, line: skillLink.line } : null,
      candidate_links: candidateLinks
    }
  }

  const metadata = priority.framework_reference ?? {}
  const raw = part === 'mature_base_framework' ? metadata.base_frameworks : metadata.oss_reference
  const terms = expectedReferenceTerms(raw)
  if (!terms.length) return { status: 'UNVERIFIABLE', reason: 'The matrix supplies no usable reference name.', candidate_links: candidateLinks }

  const sectionText = normalizeText((section?.paragraphs ?? []).map(item => item.text).join(' '))
  const normalizedLinks = links.map(link => normalizeText(`${link.label ?? ''} ${link.href ?? ''}`))
  const matchingLink = links.find((link, index) => terms.some(term => normalizedLinks[index].includes(normalizeText(term))))
  const textMention = terms.find(term => sectionText.includes(normalizeText(term)))
  const alternateLink = part === 'oss_reference_application'
    ? links.find(link => /^https?:\/\/github\.com\//iu.test(link.href ?? '') && Boolean(link.label?.trim()))
    : links.find(link => /^https?:\/\/docs\./iu.test(link.href ?? '') && Boolean(link.label?.trim()))
  return {
    status: matchingLink
      ? 'LINK_PRESENT_UNVERIFIED'
      : textMention
        ? 'TEXT_PRESENT_LINK_UNVERIFIED'
        : alternateLink
          ? 'ALTERNATIVE_LINK_NEEDS_HUMAN_REVIEW'
          : 'UNVERIFIABLE',
    reason: matchingLink || textMention || alternateLink
      ? 'A candidate reference appears in the authored section; source quality and suitability need human review.'
      : 'No exact mapped reference was observed in this section; do not infer absence or acceptance from matrix metadata.',
    matched_term: matchingLink ? terms.find(term => normalizeText(`${matchingLink.label ?? ''} ${matchingLink.href ?? ''}`).includes(normalizeText(term))) : textMention ?? null,
    link: (matchingLink ?? alternateLink) ? { href: (matchingLink ?? alternateLink).href, label: (matchingLink ?? alternateLink).label, line: (matchingLink ?? alternateLink).line } : null,
    candidate_links: candidateLinks
  }
}

function getPartStatus(page, section, part, priority) {
  if (part === 'mermaid_diagram') {
    const diagrams = page.mermaid.filter(item => item.line >= section.start_line && (section.end_line == null || item.line < section.end_line))
    return {
      status: diagrams.length ? 'PRESENT' : 'UNVERIFIABLE',
      diagram_indices: diagrams.map(item => item.page_index),
      reason: diagrams.length ? null : 'No Mermaid fence was located inside this section. The matrix requests one per priority, while the authoring contract describes preferred diagram use without requiring one heading or fence per priority; council review decides.'
    }
  }

  if (part === 'mature_base_framework' || part === 'oss_reference_application' || part === 'applicable_skill') {
    return referencePartStatus(page, section, part, priority)
  }

  if (semanticPriorityParts.has(part)) {
    const prose = assessProse(section.paragraphs ?? [], 1, 1)
    return {
      status: 'UNVERIFIABLE',
      reason: prose.paragraph_count ? 'Prose exists, but semantic fit requires human review.' : 'No prose was located; the section boundary or content needs human review.',
      prose
    }
  }

  return { status: 'UNVERIFIABLE', reason: 'No deterministic structural rule is defined for this required part.' }
}

function validateMatrix(matrix) {
  const errors = []
  const concepts = matrix.concepts ?? []
  const priorities = matrix.priority_entries ?? []
  const conceptIds = concepts.map(item => item.concept_id)
  const priorityIds = priorities.map(item => item.priority_id)
  const knownConceptIds = new Set(conceptIds)

  if (concepts.length !== expectedConceptCount) errors.push(`Expected ${expectedConceptCount} concepts, found ${concepts.length}.`)
  if (priorities.length !== expectedPriorityCount) errors.push(`Expected ${expectedPriorityCount} priority entries, found ${priorities.length}.`)
  if (new Set(conceptIds).size !== conceptIds.length) errors.push('Concept IDs are not unique.')
  if (new Set(priorityIds).size !== priorityIds.length) errors.push('Priority IDs are not unique.')
  if (matrix.summary?.canonical_catalog_concepts !== concepts.length) errors.push('Coverage summary concept count does not match concepts[].')
  if (matrix.summary?.priority_entries !== priorities.length) errors.push('Coverage summary priority count does not match priority_entries[].')
  for (const priority of priorities) {
    for (const conceptId of priority.concept_ids ?? []) {
      if (!knownConceptIds.has(conceptId)) errors.push(`Priority ${priority.priority_id} references unknown concept ${conceptId}.`)
    }
  }

  return errors
}

function inspectMetaConvention(files) {
  const names = files.map(file => path.basename(file))
  const globalMeta = names.filter(name => /^_meta\.global\.(?:js|jsx|ts|tsx)$/iu.test(name))
  const localMeta = names.filter(name => /^_meta\.(?:js|jsx|ts|tsx)$/iu.test(name))
  return {
    global_meta_files: globalMeta.sort(),
    colocated_meta_files: localMeta.sort(),
    conflict: globalMeta.length > 0 && localMeta.length > 0
  }
}

function parseArguments() {
  const args = process.argv.slice(2)
  const outputIndex = args.indexOf('--out')
  const inlineOutput = args.find(argument => argument.startsWith('--out='))
  const rawOutput = outputIndex >= 0 ? args[outputIndex + 1] : inlineOutput?.slice('--out='.length)
  return rawOutput ? path.resolve(process.cwd(), rawOutput) : defaultReportPath
}

function outputPathIsAllowed(outputPath) {
  const relative = path.relative(path.join(repositoryRoot, 'tasks/FBI-4991-arquitetura-nextra/execution/reviews'), outputPath)
  return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative)
}

async function writeReport(report, outputPath) {
  if (!outputPathIsAllowed(outputPath)) throw new Error('Report output must stay under the task artifacts directory.')
  await mkdir(path.dirname(outputPath), { recursive: true })
  await writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
}

async function main() {
  const outputPath = parseArguments()
  if (!outputPathIsAllowed(outputPath)) throw new Error('Report output must stay under the task artifacts directory.')

  const allContentFiles = await listFiles(contentRoot)
  const contentFiles = allContentFiles.filter(file => /\.(?:md|mdx)$/iu.test(file)).sort()
  const mdxFiles = contentFiles.filter(file => /\.mdx$/iu.test(file))
  if (mdxFiles.length === 0) {
    process.stdout.write(`${JSON.stringify({
      schema_version: 1,
      status: 'NOT_RUN',
      reason: 'No MDX pages exist under content/; the course population is empty.',
      counts: { mdx_pages: 0, markdown_pages: contentFiles.length },
      artifact_written: false
    }, null, 2)}\n`)
    process.exitCode = 1
    return
  }

  const matrixBytes = await readFile(matrixPath)
  const matrix = JSON.parse(matrixBytes.toString('utf8'))
  const matrixErrors = validateMatrix(matrix)
  const frontmatterPlugins = [remarkFrontmatter, remarkGfm]
  const mdxProcessor = createProcessor({ format: 'mdx', remarkPlugins: frontmatterPlugins })
  const markdownProcessor = createProcessor({ format: 'md', remarkPlugins: frontmatterPlugins })
  const pages = []
  const parseErrors = []

  for (const filePath of contentFiles) {
    const source = await readFile(filePath, 'utf8')
    try {
      const processor = filePath.endsWith('.mdx') ? mdxProcessor : markdownProcessor
      const tree = processor.parse({ path: filePath, value: source })
      pages.push(makePageRecord(filePath, source, tree))
    } catch (error) {
      parseErrors.push({ path: toPosix(path.relative(repositoryRoot, filePath)), message: error.message })
    }
  }

  const pageByRoute = new Map()
  const pageByPath = new Map()
  const duplicateRoutes = []
  for (const page of pages) {
    if (pageByRoute.has(page.route)) duplicateRoutes.push({ route: page.route, pages: [pageByRoute.get(page.route).path, page.path] })
    else pageByRoute.set(page.route, page)
    pageByPath.set(path.resolve(repositoryRoot, page.path), page)
  }

  const linkResults = []
  for (const page of pages) {
    for (const link of page.links) linkResults.push(await inspectLink(link, page, pageByRoute, pageByPath))
  }
  linkResults.sort((left, right) => `${left.page}:${left.line}:${left.href}`.localeCompare(`${right.page}:${right.line}:${right.href}`))

  const pagesByPath = new Map(pages.map(page => [page.path, page]))
  const safeAliases = buildSafeAliases(matrix)
  const priorityByConcept = new Map()
  for (const priority of matrix.priority_entries ?? []) {
    for (const conceptId of priority.concept_ids ?? []) {
      const current = priorityByConcept.get(conceptId) ?? []
      current.push(priority)
      priorityByConcept.set(conceptId, current)
    }
  }

  const conceptResults = (matrix.concepts ?? []).map(concept => {
    const declaredPaths = [...new Set([concept.explanation_path, ...(concept.reference_paths ?? [])].filter(Boolean))]
    const priorityEntries = priorityByConcept.get(concept.concept_id) ?? []
    const priorityPaths = priorityEntries.flatMap(item => [item.explanation_path, item.reference_path]).filter(Boolean)
    const mappedPaths = [...new Set([...declaredPaths, ...priorityPaths])].sort()
    const matches = []
    let foundMention = false
    const canonicalAnchor = new GithubSlugger().slug(concept.canonical_name)
    const anchorIds = [concept.concept_id, canonicalAnchor]
    for (const priority of priorityEntries) {
      if (priority.explanation_anchor) {
        anchorIds.push({
          id: priority.explanation_anchor,
          locator: (priority.concept_ids ?? []).length > 1 ? 'composite_priority_anchor' : 'priority_anchor'
        })
      }
    }

    for (const mappedPath of mappedPaths) {
      const page = pagesByPath.get(mappedPath)
      if (!page) continue
      foundMention ||= mentionExists(page, concept.canonical_name)
      const pageMatches = sectionMatches(page, {
        canonicalName: concept.canonical_name,
        aliases: safeAliases.get(concept.concept_id) ?? [],
        anchorIds
      })
      const compositeLines = new Set(priorityEntries
        .filter(priority => (priority.concept_ids ?? []).length > 1 && priority.explanation_path === mappedPath && priority.explanation_anchor)
        .map(priority => page.anchorSections.get(priority.explanation_anchor)?.line)
        .filter(Number.isInteger))
      for (const match of pageMatches) {
        if (match.line != null && compositeLines.has(match.line)) match.locator = 'composite_priority_anchor'
      }
      matches.push(...pageMatches)
    }

    const structuralMatches = matches.map(match => ({
      page: match.page,
      title: match.title,
      anchor: match.anchor,
      actual_anchor: match.actual_anchor ?? null,
      anchor_exact: match.anchor_exact ?? false,
      line: match.line,
      locator: match.locator,
      prose: assessProse(match.section?.paragraphs ?? [], 1, 35)
    }))
    const sectionEvidence = structuralMatches.filter(match => match.title || match.prose.paragraph_count > 0)
    const strongMatches = structuralMatches.filter(match =>
      match.locator !== 'composite_priority_anchor' && match.prose.meets_structural_threshold
    )
    const compositeOnly = sectionEvidence.length > 0 && sectionEvidence.every(match => match.locator === 'composite_priority_anchor')
    const structureStatus = strongMatches.length
      ? 'DEDICATED_PROSE_SECTION_CANDIDATE'
      : compositeOnly
        ? 'COMPOSITE_SECTION_NEEDS_HUMAN_REVIEW'
        : sectionEvidence.length
          ? 'SECTION_PRESENT_BUT_PROSE_THRESHOLD_UNMET'
          : foundMention
            ? 'MENTION_OR_LIST_ONLY'
            : 'MISSING_SECTION'
    const status = ['DEDICATED_PROSE_SECTION_CANDIDATE', 'COMPOSITE_SECTION_NEEDS_HUMAN_REVIEW', 'SECTION_PRESENT_BUT_PROSE_THRESHOLD_UNMET'].includes(structureStatus)
      ? 'UNVERIFIABLE'
      : structureStatus

    return {
      concept_id: concept.concept_id,
      canonical_name: concept.canonical_name,
      mapped_paths: mappedPaths,
      section_matches: structuralMatches,
      structure_status: structureStatus,
      status
    }
  }).sort((left, right) => left.concept_id.localeCompare(right.concept_id))

  const priorityResults = (matrix.priority_entries ?? []).map(priority => {
    const page = pagesByPath.get(priority.explanation_path)
    if (!page) {
      return {
        priority_id: priority.priority_id,
        original_label: priority.original_label,
        concept_ids: priority.concept_ids,
        mapped_path: priority.explanation_path,
        status: 'MISSING_SECTION',
        missing_required_parts: priority.required_parts ?? []
      }
    }

    const headingMatches = sectionMatches(page, {
      canonicalName: priority.original_label,
      anchorIds: priority.explanation_anchor ? [{ id: priority.explanation_anchor, locator: 'priority_anchor' }] : []
    })
    const anchorHeading = priority.explanation_anchor ? page.anchorSections.get(priority.explanation_anchor) : null
    const anchorResolution = priority.explanation_anchor ? {
      requested: priority.explanation_anchor,
      exact_in_page: page.anchors.has(priority.explanation_anchor),
      status: page.anchors.has(priority.explanation_anchor)
        ? 'EXACT_ANCHOR'
        : anchorHeading
          ? 'NORMALIZED_HEADING_MATCH'
          : 'UNRESOLVED',
      resolved_heading: anchorHeading?.title ?? null,
      actual_anchor: anchorHeading?.anchor ?? null
    } : null
    const summarizedMatches = headingMatches.map(match => ({
      page: match.page,
      title: match.title,
      anchor: match.anchor,
      line: match.line,
      locator: match.locator,
      prose: assessProse(match.section?.paragraphs ?? [], 2, 60)
    }))
    const substantiveSection = headingMatches.find(match =>
      assessProse(match.section?.paragraphs ?? [], 2, 60).meets_structural_threshold
    )
    const parts = {}
    if (substantiveSection?.section) {
      for (const part of priority.required_parts ?? []) parts[part] = getPartStatus(page, substantiveSection.section, part, priority)
    } else {
      for (const part of priority.required_parts ?? []) parts[part] = { status: 'UNVERIFIABLE', reason: 'No mapped section met the structural prose threshold.' }
    }
    const missingRequiredParts = Object.entries(parts).filter(([, result]) => result.status === 'MISSING').map(([part]) => part)
    const mermaidUnverifiable = parts.mermaid_diagram?.status === 'UNVERIFIABLE'
    const structureStatus = !headingMatches.length
      ? 'UNVERIFIABLE_SECTION_LOCATION'
      : !substantiveSection
        ? 'UNVERIFIABLE_SHORT_OR_UNRESOLVED_SECTION'
        : missingRequiredParts.length
          ? 'UNVERIFIABLE_REQUIRED_REFERENCE_CONTENT'
          : mermaidUnverifiable
            ? 'EXPLANATION_CANDIDATE_WITH_DIAGRAM_REVIEW'
            : 'EXPLANATION_SECTION_CANDIDATE'

    return {
      priority_id: priority.priority_id,
      original_label: priority.original_label,
      concept_ids: priority.concept_ids,
      mapped_path: priority.explanation_path,
      explanation_anchor: priority.explanation_anchor ?? null,
      anchor_resolution: anchorResolution,
      section_matches: summarizedMatches,
      structure_status: structureStatus,
      status: structureStatus === 'EXPLANATION_SECTION_CANDIDATE' || structureStatus.startsWith('EXPLANATION_CANDIDATE') || structureStatus.startsWith('UNVERIFIABLE') ? 'UNVERIFIABLE' : structureStatus,
      required_parts: parts,
      missing_required_parts: missingRequiredParts,
      human_review_required: ['definition', 'problem_story', 'benefit', 'cost', 'limit', 'evidence_scope', 'reference_suitability']
    }
  }).sort((left, right) => left.priority_id - right.priority_id)

  const metaFiles = allContentFiles.filter(file => /^_meta(?:\.global)?\.(?:js|jsx|ts|tsx)$/iu.test(path.basename(file)))
  const metaConvention = inspectMetaConvention(metaFiles)
  const diagrams = pages.flatMap(page => page.mermaid).map((diagram, index) => ({ index: index + 1, ...diagram }))
  const invalidLinks = linkResults.filter(link => ['invalid_url', 'missing_anchor', 'missing_target', 'unresolved_reference', 'nonportable_filesystem_path'].includes(link.status))
  const dynamicLinks = linkResults.filter(link => link.status === 'unverifiable_dynamic')
  const unverifiedExternalLinks = linkResults.filter(link => ['unverifiable_external', 'unverifiable_non_http_external'].includes(link.status))
  const missingConcepts = conceptResults.filter(item => ['MISSING_SECTION', 'MENTION_OR_LIST_ONLY'].includes(item.structure_status))
  const shortConceptSections = conceptResults.filter(item => item.structure_status === 'SECTION_PRESENT_BUT_PROSE_THRESHOLD_UNMET')
  const incompletePriorities = priorityResults.filter(item => item.structure_status === 'STRUCTURAL_GAP')
  const unverifiablePriorities = priorityResults.filter(item => item.status === 'UNVERIFIABLE')
  const errors = [
    ...matrixErrors,
    ...parseErrors.map(item => `MDX parse failed for ${item.path}: ${item.message}`),
    ...duplicateRoutes.map(item => `Duplicate Nextra route ${item.route}: ${item.pages.join(', ')}`),
    ...(metaConvention.conflict ? ['Nextra metadata mixes colocated _meta files with _meta.global.'] : []),
    ...(diagrams.length === 0 ? ['No Mermaid code fences were found.'] : []),
    ...(invalidLinks.length ? [`${invalidLinks.length} local links or anchors failed validation.`] : []),
    ...(dynamicLinks.length ? [`${dynamicLinks.length} dynamic JSX links could not be validated.`] : []),
    ...(missingConcepts.length ? [`${missingConcepts.length} of ${conceptResults.length} concepts have no dedicated prose section candidate; mentions and lists do not count.`] : []),
    ...(incompletePriorities.length ? [`${incompletePriorities.length} priority sections have a deterministic structural gap.`] : [])
  ]
  const requiredPartStatusCounts = {}
  for (const priority of priorityResults) {
    for (const [part, evidence] of Object.entries(priority.required_parts ?? {})) {
      const counts = requiredPartStatusCounts[part] ?? {}
      counts[evidence.status] = (counts[evidence.status] ?? 0) + 1
      requiredPartStatusCounts[part] = counts
    }
  }
  const priorityAnchorResolutionCounts = priorityResults.reduce((counts, item) => {
    const status = item.anchor_resolution?.status ?? 'NO_MATRIX_ANCHOR'
    counts[status] = (counts[status] ?? 0) + 1
    return counts
  }, {})
  const sourceRelativeLinks = linkResults.filter(link =>
    ['valid', 'valid_local_file'].includes(link.status) && /^(?:\.\/|\.\.\/)/u.test(link.href ?? '')
  )

  const report = {
    schema_version: 1,
    status: errors.length ? 'FAIL' : unverifiedExternalLinks.length || dynamicLinks.length || unverifiablePriorities.length ? 'REVIEW_REQUIRED' : 'PASS_STRUCTURAL_CHECKS',
    assessment_limit: 'Structural checks locate dedicated prose sections and content links. Meaning, pedagogical quality, framework suitability, evidence scope, remote URL availability, runtime behavior, Mermaid rendering, and diagram semantics remain for human review.',
    link_validation_scope: 'Markdown links, Markdown reference links, and literal JSX href attributes in .md/.mdx pages. Internal routes and anchors are checked locally; dynamic JSX hrefs and external URLs remain unverified.',
    checker_analysis: {
      role: 'Checker diagnosis only; this report does not independently accept authored documentation.',
      repaired_behaviors: [
        'Normalize Nextra routes with or without a trailing slash.',
        'Resolve relative Markdown links against the source content file before checking route targets.',
        'Locate priority sections by explanation_anchor, canonical headings, safe aliases, title segments, and JSX id attributes.',
        'Use true heading boundaries across the MDX AST; do not require ten fixed subheadings per priority.'
      ],
      jsx_id_support: 'Literal id attributes on MDX JSX flow and text elements, including span and anchor elements, are indexed and associated with nearby heading sections. Local fragment validation still requires an exact rendered id.',
      priority_part_policy: 'Mermaid fences and actual link candidates are reported structurally. Definition, story, benefit, cost, limits, evidence scope, and reference suitability remain UNVERIFIABLE for human review.',
      external_link_policy: 'HTTP(S) targets are recorded as unverified; no remote request was made.',
      observations: {
        invalid_local_links: invalidLinks.length,
        external_links_unverified: unverifiedExternalLinks.length,
        source_relative_local_links: sourceRelativeLinks.length,
        priority_anchor_resolution_counts: priorityAnchorResolutionCounts,
        normalized_priority_anchor_matches: priorityResults.filter(item => item.anchor_resolution?.status === 'NORMALIZED_HEADING_MATCH').map(item => ({ priority_id: item.priority_id, requested: item.anchor_resolution.requested, actual: item.anchor_resolution.actual_anchor })),
        required_part_status_counts: requiredPartStatusCounts,
        concept_sections_requiring_composite_review: conceptResults.filter(item => item.structure_status === 'COMPOSITE_SECTION_NEEDS_HUMAN_REVIEW').map(item => item.concept_id),
        priority_sections_without_mermaid_fence: priorityResults.filter(item => item.required_parts?.mermaid_diagram?.status === 'UNVERIFIABLE').map(item => item.priority_id)
      },
      acceptance: 'NOT_EVALUATED'
    },
    input: {
      coverage_matrix: toPosix(path.relative(repositoryRoot, matrixPath)),
      coverage_matrix_sha256: sha256(matrixBytes),
      content_root: 'content/'
    },
    counts: {
      mdx_pages: mdxFiles.length,
      markdown_pages: contentFiles.filter(file => file.endsWith('.md')).length,
      concepts_expected: expectedConceptCount,
      concepts_checked: conceptResults.length,
      concepts_with_dedicated_prose_section_candidate: conceptResults.filter(item => item.structure_status === 'DEDICATED_PROSE_SECTION_CANDIDATE').length,
      concepts_unverifiable_for_human_review: conceptResults.filter(item => item.status === 'UNVERIFIABLE').length,
      concepts_missing_dedicated_section: missingConcepts.length,
      concepts_with_short_or_composite_section_review: shortConceptSections.length + conceptResults.filter(item => item.structure_status === 'COMPOSITE_SECTION_NEEDS_HUMAN_REVIEW').length,
      priorities_expected: expectedPriorityCount,
      priorities_checked: priorityResults.length,
      priorities_with_explanation_section_candidate: priorityResults.filter(item => ['EXPLANATION_SECTION_CANDIDATE', 'EXPLANATION_CANDIDATE_WITH_DIAGRAM_REVIEW'].includes(item.structure_status)).length,
      priorities_with_mermaid_fence_in_section: priorityResults.filter(item => item.required_parts?.mermaid_diagram?.status === 'PRESENT').length,
      priorities_with_mermaid_fence_unverifiable: priorityResults.filter(item => item.required_parts?.mermaid_diagram?.status === 'UNVERIFIABLE').length,
      priorities_unverifiable_for_human_review: unverifiablePriorities.length,
      priorities_with_structural_gaps: incompletePriorities.length,
      links_checked: linkResults.length,
      invalid_links: invalidLinks.length,
      dynamic_links_unverifiable: dynamicLinks.length,
      external_links_unverified: unverifiedExternalLinks.length,
      mermaid_fences: diagrams.length
    },
    files: pages.map(page => ({ path: page.path, route: page.route, sha256: page.source_sha256 })).sort((left, right) => left.path.localeCompare(right.path)),
    meta_convention: metaConvention,
    concepts: conceptResults,
    priority_entries: priorityResults,
    links: linkResults,
    mermaid_fences: diagrams,
    parse_errors: parseErrors,
    errors
  }

  await writeReport(report, outputPath)
  process.stdout.write(`${JSON.stringify({ status: report.status, report: toPosix(path.relative(repositoryRoot, outputPath)), counts: report.counts, errors: report.errors }, null, 2)}\n`)
  if (errors.length) process.exitCode = 1
}

main().catch(error => {
  process.stderr.write(`${error.stack ?? error.message}\n`)
  process.exitCode = 1
})
