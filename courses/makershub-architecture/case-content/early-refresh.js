const decimal = value => new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2
}).format(value)

const ttlSeconds = 1
const earlyTtlSeconds = 0.5
const firstReadSeconds = 0.6
const boundaryReadSeconds = 1.05
const producerCalls = 2

export const earlyRefresh = Object.freeze({
  id: 'early-refresh',
  title: 'A lista continua disponível durante a renovação',
  command: 'python3 labs/architecture/early-refresh/run.py',
  inputs: `TTL ${decimal(ttlSeconds)}, janela antecipada ${decimal(earlyTtlSeconds)}, instantes 0,0; ${decimal(firstReadSeconds)}; ${decimal(boundaryReadSeconds)} e respostas calls-v1/calls-v2.`,
  before: `Com relógio em ${decimal(firstReadSeconds)} e TTL ${decimal(ttlSeconds)}, a versão anterior não inicia a renovação. A leitura em ${decimal(boundaryReadSeconds)} fica esperando o produtor.`,
  mechanism: `A versão nova usa early_ttl_seconds=${earlyTtlSeconds}. A leitura em ${decimal(firstReadSeconds)} devolve calls-v1 e inicia a renovação compartilhada. O roteiro libera essa renovação antes de avançar para ${decimal(boundaryReadSeconds)}.`,
  outcome: `A leitura em ${decimal(boundaryReadSeconds)} recebe calls-v2 sem esperar. As duas versões realizam ${producerCalls === 2 ? 'duas' : producerCalls} buscas no cenário concluído.`,
  limits: 'O relógio e o produtor são controlados. Se a renovação ainda estiver lenta quando houver expiração dura, a versão nova também pode precisar esperar. Não se provou uma redução de latência em produção.',
  expectedOutput: [
    `before: early_started=False boundary_blocked=True result=calls-v2 producer_calls=${producerCalls}`,
    `after: early_started=True boundary_blocked=False result=calls-v2 producer_calls=${producerCalls}`,
    'comparison=PASS evolution=True slow_refresh_can_still_block_after_hard_ttl=True'
  ].join('\n'),
  issueUrl: 'https://fazcapital.atlassian.net/browse/FBI-2331',
  pullRequestUrl: 'https://bitbucket.org/fazcapital/makershub/pull-requests/51',
  beforeUrl: 'https://bitbucket.org/fazcapital/makershub/src/f34e4d3d22d9dcdb53074332dcbf7a48c254c221/backend/app/utils/single_flight.py',
  afterUrl: 'https://bitbucket.org/fazcapital/makershub/src/a8bb7023f1ad080cb899cccfb73225231b28e235/backend/app/utils/single_flight.py',
  facets: Object.freeze([
    { id: 'overview', label: 'Visão do caso', href: '/jornadas/early-refresh/' },
    { id: 'explanation', label: 'Entender', href: '/explicacoes/casos/early-refresh/' },
    { id: 'tutorial', label: 'Praticar', href: '/tutoriais/casos/early-refresh/' },
    { id: 'guide', label: 'Aplicar', href: '/guias/casos/early-refresh/' },
    { id: 'reference', label: 'Consultar', href: '/referencia/casos/early-refresh/' }
  ])
})
