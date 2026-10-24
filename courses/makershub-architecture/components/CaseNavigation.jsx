import { earlyRefresh } from '../case-content/early-refresh.js'

export function CaseNavigation({ current }) {
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
            <a href={facet.href} aria-current={facet.id === current ? 'page' : undefined}>
              {facet.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

export function CaseNext({ current }) {
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
        return <a key={id} href={facet.href}>{facet.label}</a>
      })}
    </div>
  )
}

export function CaseChoices() {
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
            <td><a href={facet.href}>{facet.label}</a></td>
            <td>{purposes[facet.id][1]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
