export const caseEntries = Object.freeze([
  {
    "id": "single-flight-cancel",
    "title": "Cancelamento de uma busca compartilhada"
  },
  {
    "id": "early-refresh",
    "title": "A lista continua disponível durante a renovação"
  },
  {
    "id": "date-only",
    "title": "A emissão continua no mesmo dia em São Paulo"
  },
  {
    "id": "opportunity-entry",
    "title": "A oportunidade existente conserva sua identidade"
  },
  {
    "id": "order-boundaries",
    "title": "Uma ordem atravessa fronteiras sem espalhar regras"
  },
  {
    "id": "order-delivery",
    "title": "A repetição de uma ordem produz um único efeito"
  },
  {
    "id": "reservation",
    "title": "Dois operadores disputam a mesma reserva"
  },
  {
    "id": "consensus",
    "title": "Uma partição separa os escritórios da corretora"
  },
  {
    "id": "queue-workflow",
    "title": "Uma fila absorve trabalho e recupera falhas"
  },
  {
    "id": "cache-policy",
    "title": "A consulta de posição envelhece de forma controlada"
  },
  {
    "id": "ledger-projection",
    "title": "O histórico reconstrói a posição do cliente"
  },
  {
    "id": "storage-partitions",
    "title": "A posição cresce e a consulta precisa encontrar seus dados"
  },
  {
    "id": "safe-release",
    "title": "A corretora troca uma versão sem perder o contrato"
  },
  {
    "id": "access-policy",
    "title": "A permissão acompanha a ordem e a identidade"
  },
  {
    "id": "diagnostics",
    "title": "A equipe descobre onde a ordem parou"
  },
  {
    "id": "query-grain-postgres",
    "title": "A comissão de R$ 100 aparece como R$ 200"
  },
  {
    "id": "revision-cas-postgres",
    "title": "Uma única versão atual ainda pode perder uma alteração"
  },
  {
    "id": "airflow-lock-retry",
    "title": "Uma falha de lock derruba a tarefa do Airflow"
  }
])

export const caseFacets = Object.freeze([
  { id: 'overview', label: 'Visão do caso', title: 'Visão do caso' },
  { id: 'explanation', label: 'Entender', title: 'Explicação' },
  { id: 'tutorial', label: 'Praticar', title: 'Tutorial' },
  { id: 'guide', label: 'Aplicar', title: 'Guia' },
  { id: 'reference', label: 'Consultar', title: 'Referência' }
])

export function getCourseCase(caseId) {
  const entry = caseEntries.find(item => item.id === caseId)
  if (!entry) throw new Error('Unknown course case: ' + caseId)
  return { ...entry, href: '/jornadas/' + entry.id + '/', facets: caseFacets }
}
