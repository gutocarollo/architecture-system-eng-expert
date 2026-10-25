import { earlyRefresh } from '../case-content/early-refresh.js'

function destinationFor(facet, withinPage) {
  const fragment = `#${facet.id}`
  return withinPage ? fragment : `${earlyRefresh.facets[0].href}${fragment}`
}

export function CaseNavigation({ current, withinPage = false }) {
  const active = earlyRefresh.facets.find(facet => facet.id === current)
  if (!active) throw new Error(`Unknown early-refresh facet: ${current}`)

  return (
    <nav
      className="case-navigation"
      aria-label="Navegação do caso early-refresh"
      data-case-navigation={earlyRefresh.id}
      data-pagefind-ignore="all"
    >
      <p className="case-navigation-identity">
        <span>Neste caso</span>
        <strong>{earlyRefresh.title}</strong>
      </p>
      <ul>
        {earlyRefresh.facets.map(facet => (
          <li key={facet.id}>
            <a href={destinationFor(facet, withinPage)} aria-current={!withinPage && facet.id === current ? 'location' : undefined}>
              {facet.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

export function CaseNext({ current, withinPage = false }) {
  const destinations = {
    overview: ['explanation', 'reference'],
    explanation: ['tutorial', 'reference'],
    tutorial: ['reference', 'guide'],
    guide: ['reference', 'tutorial'],
    reference: ['tutorial', 'explanation']
  }
  return (
    <div className="case-next" data-pagefind-ignore="all">
      <p>Continue neste caso:</p>
      {destinations[current].map(id => {
        const facet = earlyRefresh.facets.find(item => item.id === id)
        return <a key={id} href={destinationFor(facet, withinPage)}>{facet.label}</a>
      })}
    </div>
  )
}

export function CaseChoices({ withinPage = false }) {
  const purposes = {
    explanation: ['Você quer entender por que acontece.', 'Você identifica o mecanismo e o limite da proteção.'],
    tutorial: ['Você quer aprender fazendo.', 'Você repete entradas conhecidas e compara as duas condições.'],
    guide: ['Você já conhece o assunto e precisa resolver a tarefa.', 'Você prepara o recorte, coleta a prova e decide se a proteção atende o problema.'],
    reference: ['Você procura nomes, parâmetros e contratos.', 'Você consulta os localizadores e as garantias deste caso.']
  }
  return (
    <table>
      <thead><tr><th>Sua necessidade</th><th>Destino deste caso</th><th>O que você obterá</th></tr></thead>
      <tbody>
        {earlyRefresh.facets.filter(facet => facet.id !== 'overview').map(facet => (
          <tr key={facet.id}>
            <td>{purposes[facet.id][0]}</td>
            <td><a href={destinationFor(facet, withinPage)}>{facet.label}</a></td>
            <td>{purposes[facet.id][1]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
