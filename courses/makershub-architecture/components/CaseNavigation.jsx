import { useMDXComponents as getThemeComponents } from 'nextra-theme-docs'
import { getCourseCase } from '../case-content/cases.js'

const { a: CourseLink, table: CourseTable, tr: Row, th: HeaderCell, td: Cell } = getThemeComponents()

function destinationFor(courseCase, facet, withinPage) {
  return `${withinPage ? '' : courseCase.href}#${facet.id}`
}

export function CaseBreadcrumb({ caseId = 'early-refresh', current = 'overview' }) {
  const courseCase = getCourseCase(caseId)
  const facet = courseCase.facets.find(item => item.id === current)
  const label = current === 'concepts' ? 'Conceitos deste caso' : facet?.title
  if (!label) throw new Error(`Unknown case facet: ${current}`)
  return (
    <nav className="case-breadcrumb" aria-label="Caminho do caso" data-case-breadcrumb={caseId} data-pagefind-ignore="all">
      <ol>
        <li><CourseLink href="/jornadas/">Siga um caso completo</CourseLink></li>
        <li><span aria-hidden="true">›</span>{current === 'overview'
          ? <span aria-current="page">{courseCase.title}</span>
          : <CourseLink href={courseCase.href}>{courseCase.title}</CourseLink>}</li>
        {current !== 'overview' && <li><span aria-hidden="true">›</span><span aria-current="page">{label}</span></li>}
      </ol>
    </nav>
  )
}

export function CaseNavigation({ caseId = 'early-refresh', current = 'overview', withinPage = false }) {
  const courseCase = getCourseCase(caseId)
  if (current !== 'concepts' && !courseCase.facets.some(item => item.id === current)) throw new Error(`Unknown case facet: ${current}`)
  return (
    <nav className="case-navigation" aria-label={`Navegação do caso ${caseId}`} data-case-navigation={caseId} data-pagefind-ignore="all">
      <p className="case-navigation-identity"><span>Neste caso</span><strong>{courseCase.title}</strong></p>
      <ul>{courseCase.facets.map(facet => <li key={facet.id}>
        <CourseLink href={destinationFor(courseCase, facet, withinPage)} aria-current={!withinPage && facet.id === current ? 'location' : undefined}>{facet.label}</CourseLink>
      </li>)}</ul>
    </nav>
  )
}

export function CaseNext({ caseId = 'early-refresh', current, withinPage = false }) {
  const courseCase = getCourseCase(caseId)
  const index = courseCase.facets.findIndex(facet => facet.id === current)
  if (index < 0) throw new Error(`Unknown case facet: ${current}`)
  const previous = courseCase.facets[index - 1]
  const next = courseCase.facets[index + 1]
  return (
    <nav className="case-next" aria-label={`Etapas do caso ${caseId}`} data-case-pager={caseId} data-pagefind-ignore="all">
      {previous && <CourseLink rel="prev" href={destinationFor(courseCase, previous, withinPage)}><span>Anterior</span><strong>← {previous.title}</strong></CourseLink>}
      {next && <CourseLink rel="next" href={destinationFor(courseCase, next, withinPage)}><span>Próximo</span><strong>{next.title} →</strong></CourseLink>}
    </nav>
  )
}

export function CaseSequence({ caseId = 'early-refresh', current, withinPage = false }) {
  const courseCase = getCourseCase(caseId)
  return (
    <nav className="case-sequence" aria-label={`Percurso do caso ${caseId}`} data-case-sequence={caseId} data-pagefind-ignore="all">
      <p>Continue neste caso</p>
      <ol>{courseCase.facets.slice(1).map((facet, index) => <li key={facet.id}>
        {index > 0 && <span aria-hidden="true">→</span>}
        <CourseLink href={destinationFor(courseCase, facet, withinPage)} aria-current={facet.id === current ? 'location' : undefined}>{facet.title}</CourseLink>
      </li>)}</ol>
    </nav>
  )
}

export function CaseChoices({ caseId = 'early-refresh', withinPage = false }) {
  const courseCase = getCourseCase(caseId)
  const purposes = {
    explanation: ['Você quer entender por que acontece.', 'Você identifica o mecanismo e o limite da proteção.'],
    tutorial: ['Você quer aprender fazendo.', 'Você repete entradas conhecidas e compara as duas condições.'],
    guide: ['Você já conhece o assunto e precisa resolver a tarefa.', 'Você prepara o recorte, coleta a prova e decide se a proteção atende o problema.'],
    reference: ['Você procura nomes, parâmetros e contratos.', 'Você consulta os localizadores e as garantias deste caso.']
  }
  return (
    <CourseTable data-case-choices={caseId}>
      <thead><Row><HeaderCell>Sua necessidade</HeaderCell><HeaderCell>Destino deste caso</HeaderCell><HeaderCell>O que você obterá</HeaderCell></Row></thead>
      <tbody>{courseCase.facets.slice(1).map(facet => <Row key={facet.id}>
        <Cell>{purposes[facet.id][0]}</Cell><Cell><CourseLink href={destinationFor(courseCase, facet, withinPage)}>{facet.title}</CourseLink></Cell><Cell>{purposes[facet.id][1]}</Cell>
      </Row>)}</tbody>
    </CourseTable>
  )
}
