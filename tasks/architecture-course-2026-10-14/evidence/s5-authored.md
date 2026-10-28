# S5 — autoria dos dez arquivos

A autoria produziu cinco explicações e cinco referências nos paths atribuídos. O conteúdo reutiliza S2, S3, S4, S5 e os auxiliares L5A/L5B/L5C, o contrato de autoria e os dois snapshots GitHub. Os exemplos têm escopo de código local, histórico ou proposta; esta nota não dá aceite independente.

## Artefatos no momento da leitura

Os hashes abaixo foram calculados em 2026-10-14 18:41 UTC. Eles identificam exatamente o conteúdo para o council. Não incluem navegação, índices, coverage ou arquivos de outros autores.

| Arquivo | SHA-256 | Fences Mermaid |
|---|---|---:|
| `content/explicacoes/cache/index.mdx` | `202efe7cd0c6dce9b2f5c851a928b25a561893d44b6a3d5f924a1da1eb5cdd11` | 4 |
| `content/explicacoes/concurrency/index.mdx` | `b6a84807c9d0a7581d7777d6016491bf9054cdfa966ca4a241b47769a079b272` | 2 |
| `content/explicacoes/capacity/index.mdx` | `1b2ccd703433dc62f43a6a951d547d81232cc04fd97735bf7593849e21c485f5` | 5 |
| `content/explicacoes/api-integration/index.mdx` | `c0b17a4e4893c83d23db59ccf22963d038faaa131a18dd6227cd48a78ff34bae` | 3 |
| `content/explicacoes/observability/index.mdx` | `bed03cea54757384ec3451783d0c81292e0853e42663fc1285379d5d85c3d401` | 2 |
| `content/referencia/catalogo/06-cache.mdx` | `f2c79d26bc6911d237c0cd28de289ce89350e6c02cba832c7a8055287aeccf26` | 0 |
| `content/referencia/catalogo/07-resiliencia.mdx` | `0cd5c56dc9c46dd49cef2a64462448f0e9c19e545334b3f548690c93b4ae214d` | 0 |
| `content/referencia/catalogo/08-concorrencia.mdx` | `5930d7c3f187855179ab62c196a5777c13aaa5a0e6e4505564a3983a24c43a54` | 0 |
| `content/referencia/catalogo/09-apis-e-integracao.mdx` | `57ee9466a4fcd928a90f9a69fa1a7a6d450baa78cb79e3d99eda02f982a554e7` | 0 |
| `content/referencia/catalogo/15-observabilidade.mdx` | `33167f5f02d6114ba5a04b948dd823d61cc1deca040b2806972819ba226ef5f7` | 0 |

## Mapa dos prioritários

| Prioritário | Rota e anchor escritos |
|---|---|
| 14 | `/explicacoes/cache/#pattern-14` |
| 15 | `/explicacoes/cache/#pattern-15` |
| 16 | `/explicacoes/capacity/#pattern-16` |
| 17 | `/explicacoes/capacity/#pattern-17` |
| 18 | `/explicacoes/capacity/#pattern-18` |
| 19 | `/explicacoes/capacity/#pattern-19` |
| 20 | `/explicacoes/capacity/#pattern-20` |
| 21 | `/explicacoes/api-integration/#pattern-21` |
| 22 | `/explicacoes/api-integration/#pattern-22` |
| 29 | `/explicacoes/concurrency/#pattern-29` |
| 33 | `/explicacoes/concurrency/#pattern-33` |
| 37 | `/explicacoes/api-integration/#pattern-37` |

A raiz precisa reconciliar no coverage os antigos paths de páginas próprias com estes anchors. S5 não alterou o mapa compartilhado.

## Cobertura e limites

A leitura mecânica de coverage e dos headings encontrou 90 labels exatos e 90 IDs: 14 do grupo 6, 19 do grupo 7, 22 do grupo 8, 23 do grupo 9 e 12 do grupo 15. São 90 ocorrências, preservando repetições entre grupos. Há 12 anchors prioritários e 16 fences Mermaid. Essa contagem não prova qualidade pedagógica, compilação, renderização ou fidelidade semântica dos desenhos.

Cada verbete inclui definição, problema aplicado, limite, skill e base/aplicação OSS com fonte ou qualificação explícita do alcance. O catálogo não chama REF didática de PROD. Caffeine refresh exige leitura elegível; Redisson fornece REF de duas camadas/carga; Resilience4j fornece REF de fallback; Tornado fornece long polling; Probot fornece receptor webhook; Dapr fornece chamada via sidecar para comparar Ambassador. eShopOnContainers é referência histórica arquivada, fixada em c09191fb78e400e7e4cd2efb6c13201f71da37b8. Wait-free usa o benchmark e wfqueue do projeto autor, sem prova formal feita por S5.

O código MakersHub continua apresentado como snapshot lido às 16:16 UTC em main@e233fb046ec333982cd1547171b0f0bd8d8d92ee, sem confirmação de deploy. Os diffs a304a4e/a8bb702/84ef5d4 são históricos ancestrais daquele HEAD local. A ponte do Request ID com o ContextVar Airflow não foi comprovada, e os spans OTel são blueprint. Calendar é adaptação Next/Azure/Graph; agregação Call Sprint é proposta. SlotLock compara propriedade, sem fence monotônico externo comprovado; concorrência financeira por versão é hipotética. Tickets fixa Marten 8.22.0, com ressalva de Rich mode e mudança do padrão em v9.

As fontes novas foram abertas em 14/10/2026 durante a autoria: Caffeine Population; Hazelcast MapStore 5.7; CoreDNS cache; docs Python de asyncio/futures; APIs Java SE 25; PostgreSQL s_lock e locks 16; Pekko tutorial; Redisson collections; docs Resilience4j; Kubernetes probes; systemd service.c; Chaos Toolkit; padrões Azure; Apollo Federation; RFC 6202; gRPC deadlines; Spring HATEOAS; Fielding; OTel Demo/logs/metrics; USE; Google SRE; Loki; node_exporter/blackbox_exporter; APISIX; Probot; Tornado; Dapr quickstart; SSE-Starlette; Prometheus; Marten e os dois códigos históricos/benchmark citados. Branches main/master podem mudar; fontes vendorizadas têm os hashes do pacote L5C. Nenhuma estrela foi recontada ou promovida a tendência.

## Recibos

- [2026-10-14 18:10 UTC] worktree de arquitetura — pwd -P, branch e SHA → perfect-citizen-a30f5998, 23d5d158d3a964dceba296296368ec14bcd8970b.
- [2026-10-14 18:41 UTC] dez MDX — leitura de bytes, SHA-256 e extração de headings/IDs → files=10; exact_labels=90; entry_ids=90; priority_anchors=12; mermaid_fences=16.

Não houve testes, build, renderização, escrita em sistemas fonte, commit, push, merge ou deploy. Índices, navegação, coverage e os gates de council permanecem sob ownership da raiz. A autoria está encerrada nesta versão; o próximo passo é revisão independente dos hashes.
