# S6 — autoria das páginas de plataforma, mudanças e segurança

A autoria foi concluída nos sete caminhos atribuídos à frente. A raiz conserva a responsabilidade pela integração, pelo build Nextra, pela renderização e pelo council independente. Esta frente não emite aprovação própria.

O checkout permaneceu em `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. Foram reutilizados `s6-platform.md`, os deltas `l6a-platform.md`, `l6b-curation.md`, `l6c-release-security.md`, `github-snapshot.json` e `github-snapshot-supplement.json`. Os casos de runtime mantêm seus horários originais entre 16:10 e 16:16 UTC de 14/10/2026; não houve nova varredura do cluster ou do banco para autoria.

As três explicações desenvolvem as relações de configuração do Airflow, maioria Raft, Lease e fencing proposto; a replicação síncrona do metadata com seus limites; o sidecar real git-sync; mesh como blueprint; migração sem efeitos duplicados; compatibilidade de consumidores; Blue/Green, Canary e flags como propostas; identidade e autorização. O histórico de qualificação do S2 é usado como evolução de contrato, sem atribuir intenção histórica de Expand/Contract. O exemplo de mudança de campo é fictício. O core 37 recebe ligação para a autoria S5, sem apropriar seu conteúdo.

## Cobertura

Os quatro catálogos possuem 59 entradas: 13 do grupo 11, 12 do grupo 12, 17 do grupo 13 e 17 do grupo 14. Cada entrada tem o ID original da matriz como âncora, uma definição, caso ou aplicação delimitada, benefício, custo ou limite. A contagem não comprova revisão pedagógica independente. Os caminhos locais de skills aparecem como texto; a navegação de curadoria usa `/referencia/skills-e-projetos`.

## Hashes dos sete MDX

| Caminho | SHA-256 |
|---|---|
| `content/explicacoes/availability/index.mdx` | `bf54f77c4043e97b05c59f33f03f8b0c2715376e80fa37ec03b8c01aada53908` |
| `content/explicacoes/safe-change/index.mdx` | `ae62d79a2abf9a0e861ad3c94de878d84bd51cf9ea14ba6c8727b1efb71431d2` |
| `content/explicacoes/security/index.mdx` | `ddc600a30732ae53d5046c98173844dd318bd4f72896b610d3dd427d44363318` |
| `content/referencia/catalogo/11-padroes-para-decompor-sistemas.mdx` | `7c9d6277537cbf5e27953fbd1fb760a4200664c74ab4cb17de32b9a5ddba29cc` |
| `content/referencia/catalogo/12-deploy-e-releases.mdx` | `1150c352ab56db43907d71284da179c17e4ac25e32a9c1bef9785f024d879e00` |
| `content/referencia/catalogo/13-alta-disponibilidade.mdx` | `451bad235c8f5c0cbccb2daad9f6e304ccc6eb014060686e1b8f05b9538b1be7` |
| `content/referencia/catalogo/14-seguranca.mdx` | `3988a713445026162f0e69db50caece2e1cb43a0a8bf39fd3db8d72f5613f723` |

## priorityAnchorMap

As nove seções abaixo pertencem à autoria S6. O core 37 aponta para a seção adjudicada com S5; sua existência final e renderização precisam ser conferidas pela integração.

```json
{
  "23": "/explicacoes/safe-change/#pattern-23",
  "24": "/explicacoes/safe-change/#pattern-24",
  "25": "/explicacoes/safe-change/#pattern-25",
  "26": "/explicacoes/safe-change/#pattern-26",
  "27": "/explicacoes/safe-change/#pattern-27",
  "28": "/explicacoes/availability/#pattern-28",
  "30": "/explicacoes/availability/#pattern-30",
  "35": "/explicacoes/availability/#pattern-35",
  "36": "/explicacoes/availability/#pattern-36",
  "37": "/explicacoes/api-integration/#pattern-37"
}
```

## Verificações locais

- [2026-10-14 18:35:32 UTC] sete arquivos MDX — `@mdx-js/mdx.compile(source)` por arquivo → `MDX_COMPILE_PASS` nos sete paths da tabela. A verificação usa o compilador local, sem afirmar build ou renderização Nextra.
- [2026-10-14 18:35:32 UTC] três explicações — `mermaid.parse(source)` em Node com JSDOM local → `TOTAL_MERMAID_PARSED 12`, exit code `0`. Isso comprova aceitação sintática pelo parser local; não é renderização no host final.
- [2026-10-14 18:35:32 UTC] contrato Mermaid v2 — `normalize_document(spec); _semantic_diagnostics(document)` em memória → `CANONICAL_V2_NORMALIZE_PASS 12`, `SEMANTIC_DIAGNOSTICS []`. Nenhum JSON temporário foi gravado fora do escopo. A tentativa CLI com `/dev/stdin` foi recusada por tratar a entrada como link simbólico, e foi substituída pela validação em memória.
- [2026-10-14 18:35:32 UTC] catálogos e `coverage.json` — conferência de `entry_ids` e headings → `11:13/13; 12:12/12; 13:17/17; 14:17/17; missing_ids=[]` em cada grupo.

A autoria não executou uma revisão independente, um teste de failover ou restore, um deploy ou uma DAG. Os limites de evidência permanecem nos textos e no pacote S6.
