# S5 — reparo delimitado para a rechecagem Grok

O escopo inicial autorizou as duas páginas de cache. A mensagem posterior da raiz acrescentou somente a explicação de capacidade, para corrigir a falha semântica do fence 2 e sua política de retry. A raiz mantém a mesma rechecagem Grok para os três documentos; S5 não despachou outro modelo ou revisor.

## O que mudou

G1 foi corrigido no fence 4 da explicação de cache. O ramo de sucesso agora mostra uma leitura antes do novo limiar e a resposta com o novo valor. O ramo de falha conserva o limite do TTL antigo; somente o bloco condicional de expiração sem renovação bem-sucedida mostra uma nova carga. Não há mais uma falta incondicional depois dos dois ramos. A elegibilidade por leitura e a ausência de cron continuam explícitas.

G2 foi corrigido nos verbetes Two-Level Cache e Cache Warming. A referência passou da página comercial redisson.pro para implementação e uso no repositório comunitário fixado em SHA. O método getAsync procura a cópia local e, no modo que inclui Redis, consulta o mapa remoto quando necessário. testLoadAllCache configura loader, chama loadAll(false, 2) e inspeciona o mapa e getCachedMap. A classificação REF corresponde a código de uso em teste lido, sem execução nesta autoria ou implantação de uma aplicação cliente inferida.

G7, de severidade média, foi preenchido dentro da referência de cache autorizada. Read Through agora cita implementação e teste Caffeine. Write Through e Write Behind citam os ramos reais de RedissonMap, as configurações comunitárias dos testes e MapWriteBehindTask. TTL e Negative Caching citam CoreDNS item, handler e ResponseWriter. A política opcional serve_stale foi preservada; os testes citados foram lidos e não executados.

G6, também médio, ganhou uma explicação da geração de autorização na chave, do bump antes da exclusão e da reconciliação na recuperação. O texto limita essa proteção à autorização e não promete invalidação de todos os indicadores ou proteção completa de todos os chamadores.

No escopo ampliado, G3/G4 foram corrigidos na explicação de capacidade. A política cita 429, 502/503/504, Retry-After numérico positivo e a lista exata de exceções repetíveis. O fence 2 separa resposta HTTP de erro de timeout local sem resposta confirmada; o segundo ramo informa efeito remoto desconhecido e reconciliação pela identidade. O texto registra que _request pode repetir POST e que essa política não comprova idempotência do trigger de DAG.

## Hashes de documentos para a rechecagem

Medição em 2026-10-14 19:25 UTC. O hash anterior vem de reviews/grok-initial-input.json, que foi conferido contra os hashes da resposta original.

| Documento | SHA-256 anterior | SHA-256 atual |
|---|---|---|
| `content/explicacoes/cache/index.mdx` | `c5fe5f3df7d17260fd80143ac2b70e48bb6d7199d73ac9f29a8d63ed28517be7` | `b29d777d61aadd2c848bbacf864aed57f7fb71d2ed0cc70a4fad93e69a85abba` |
| `content/explicacoes/capacity/index.mdx` | `b2516379d27b4d79e13675e620afc86ea96a87f5789480dde6f59ad517df0aa1` | `13e50ee708d19e8a7510b8a3b1f91fe40f3505e4323b232a00faadeb703e5e9c` |
| `content/referencia/catalogo/06-cache.mdx` | `94188b17bca9c5d82a2ccc2ccb7e746b042a63fe2dc9cbc8018f9b4080bce8cd` | `9fe451b92984d4ccde8a9c8c402b38ac345dea2d223c1ab48b316095ac766707` |

## Fences alterados

Os hashes abaixo são SHA-256 do corpo entre os fences Mermaid, incluindo sua quebra de linha final. A extração usou a mesma expressão no conteúdo anterior guardado e no arquivo atual.

| Documento | Índice do fence | Corpo anterior | Corpo atual |
|---|---:|---|---|
| `content/explicacoes/cache/index.mdx` | 4 | `26c8c1971ca7e714dbd9237f31883c37798c692321e94be052c79c7fcccc3f46` | `95e1f2f866f66148eba2aff10990df6b5d1756c61cd731d11ed99fd80a1a5337` |
| `content/explicacoes/capacity/index.mdx` | 2 | `b36cf29b4f337e3d366f44347430e2aaaa9410117a59feb8f4d8595222d6f5a9` | `fb3993990146a4093bc7da11f862dd33f28a5cce4aa73c3e29b2f6701330a7a0` |

A explicação de cache conserva quatro fences e a de capacidade conserva cinco. Os outros fences desses arquivos são idênticos ao input anterior. A referência de cache não contém Mermaid. Os sete documentos fora do reparo coincidem com os hashes anteriores: other_seven_match_initial=true.

## Código comunitário efetivamente lido

A API oficial GitHub devolveu HTTP 200 em 14/10/2026 às 19:12 UTC para o HEAD de Redisson, Caffeine e CoreDNS. Os SHAs fixados são, respectivamente, 016cf1465277409787216ea07dc5ba40696f2efd, 6bfe815f0f6a2daba967385d02c52890c33d8142 e 3580a2996e989a80930391b301453a9c52339fac. A API informou Apache-2.0 para os três repositórios; os cabeçalhos das implementações Redisson e Caffeine foram lidos com essa identificação. Nenhum recurso PRO foi inferido a partir do nome da biblioteca.

Os bytes completos foram recebidos por HTTP de raw.githubusercontent.com, mantidos em memória para SHA-256 e leitura numerada, sem escrita em repositório externo ou arquivo adicional. Os spans abaixo identificam o conteúdo usado na decisão e as URLs dos documentos apontam ao SHA, não a master mutável.

| Fonte pública fixada | Path no repositório | Spans lidos | SHA-256 dos bytes | Papel |
|---|---|---|---|---|
| [Redisson: RedissonLocalCachedMap.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/main/java/org/redisson/RedissonLocalCachedMap.java) | `redisson/src/main/java/org/redisson/RedissonLocalCachedMap.java` | 1–16; 285–316 | `5cedb19b8f3cd6bb7ebb266ce7b411bf7fdf5fec749983d7c9e0161bd88c3891` | base de leitura local/remota |
| [Redisson: RedissonLocalCachedMapTest.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/test/java/org/redisson/RedissonLocalCachedMapTest.java) | `redisson/src/test/java/org/redisson/RedissonLocalCachedMapTest.java` | 123–140; 275–310 | `16925bb86ac126e3eb8192ae4346d4d2ebde93ec4ec4164d40a35708e44c3b61` | uso REF de carga e cópia local |
| [Redisson: RedissonMap.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/main/java/org/redisson/RedissonMap.java) | `redisson/src/main/java/org/redisson/RedissonMap.java` | 663–697; 1233–1270; 1314–1339 | `bcdb451bc89bf286fbb52f0fbdb9911d2c29bcd9e0a08217b91ee5fc6726ac9e` | base de loader e de dois modos de writer |
| [Redisson: RedissonMapTest.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/test/java/org/redisson/RedissonMapTest.java) | `redisson/src/test/java/org/redisson/RedissonMapTest.java` | 154–194; 213–231 | `87d932ae16d62def44de5add43af264ae4b0e7a1c182340ef377c3d550cc9e05` | uso REF que configura loader e writer |
| [Redisson: BaseMapTest.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/test/java/org/redisson/BaseMapTest.java) | `redisson/src/test/java/org/redisson/BaseMapTest.java` | 1161–1192; 1382–1398; 1694–1715 | `7021514cb3bd49f1cf0f20680b38d87889dc6cc2943fa1b83ab375338d2bce02` | uso REF e expectativas de persistência |
| [Redisson: MapWriteBehindTask.java](https://github.com/redisson/redisson/blob/016cf1465277409787216ea07dc5ba40696f2efd/redisson/src/main/java/org/redisson/MapWriteBehindTask.java) | `redisson/src/main/java/org/redisson/MapWriteBehindTask.java` | 1–25; 70–166 | `4a1ba7bb160e3d2156cb35352c0511205b77afdec92aeb8e6a2ebdf9afb02a5f` | processamento posterior da tarefa de escrita |
| [Caffeine: LocalLoadingCache.java](https://github.com/ben-manes/caffeine/blob/6bfe815f0f6a2daba967385d02c52890c33d8142/caffeine/src/main/java/com/github/benmanes/caffeine/cache/LocalLoadingCache.java) | `caffeine/src/main/java/com/github/benmanes/caffeine/cache/LocalLoadingCache.java` | 1–17; 45–60 | `7082666a286d114347b9cd2cf9b6e41746c67df78af3eebea593398e64b7a90e` | base comunitária de read-through |
| [Caffeine: LoadingCacheTest.java](https://github.com/ben-manes/caffeine/blob/6bfe815f0f6a2daba967385d02c52890c33d8142/caffeine/src/test/java/com/github/benmanes/caffeine/cache/LoadingCacheTest.java) | `caffeine/src/test/java/com/github/benmanes/caffeine/cache/LoadingCacheTest.java` | 154–160; 327–337 | `8da5a8395147a36127e3c5a62391d35e1c5e5a67201b1535a54b9df3c0ee4b42` | uso REF de uma leitura ausente |
| [CoreDNS: cache.go](https://github.com/coredns/coredns/blob/3580a2996e989a80930391b301453a9c52339fac/plugin/cache/cache.go) | `plugin/cache/cache.go` | 430–463; 484–531 | `2c7181e41a5137b79e1c0c0f237e4fca685bd5eb6de20706ff2a11c2d24560fb` | aplicação de cache negativo com validade própria |
| [CoreDNS: handler.go](https://github.com/coredns/coredns/blob/3580a2996e989a80930391b301453a9c52339fac/plugin/cache/handler.go) | `plugin/cache/handler.go` | 239–282 | `8a9b74f8de6cfcc817d9a44e09baa95117a2d2d50a21435adc042b860cccae98` | aplicação que decide validade e serve_stale |
| [CoreDNS: item.go](https://github.com/coredns/coredns/blob/3580a2996e989a80930391b301453a9c52339fac/plugin/cache/item.go) | `plugin/cache/item.go` | 109–115 | `ae417c2a90f2d8bebc25d6b6d40c0f429d437a914ba59bb6627622b4abb8f255` | cálculo do TTL restante |

Alguns trechos literais que decidem as alegações:

- RedissonLocalCachedMap.java:289–309 lê `cache.get(cacheKey)`, retorna o acerto e chama `super.getAsync((K) key, threadId)` no ramo remoto.
- RedissonLocalCachedMapTest.java:133 chama `map.loadAll(false, 2)`; :140 contém a expectativa `assertThat(map.getCachedMap()).containsKey("" + i)`.
- RedissonMap.java:664–667 seleciona `WriteMode.WRITE_BEHIND` e adiciona a tarefa; :673–697 compõe a chamada ao writer com a conclusão retornada.
- MapWriteBehindTask.java:101 chama `options.getWriter().write(addedMap)`; :154–162 agenda processamento usando writeBehindDelay.
- LocalLoadingCache.java:58–59 implementa get com `cache().computeIfAbsent(key, mappingFunction())`.
- CoreDNS cache.go:443–445 distingue `response.NameError, response.NoData`; :522 chama `w.ncache.Add(key, i)`. item.go:113 subtrai tempo decorrido do TTL original; handler.go:258 também contempla a política explícita de validade antiga.

## Recibos locais e mecânicos

- [2026-10-14 19:12 UTC] worktree do curso — pwd -P, git branch --show-current e git rev-parse HEAD → perfect-citizen-a30f5998, 23d5d158d3a964dceba296296368ec14bcd8970b.
- [2026-10-14 19:15 UTC] Redisson/CoreDNS, raw.githubusercontent.com nos SHAs fixados — urllib.request.urlopen, SHA-256 e leitura numerada → HTTP 200, hashes e spans acima.
- [2026-10-14 19:18 UTC] Caffeine e BaseMapTest Redisson, raw.githubusercontent.com nos SHAs fixados — urllib.request.urlopen, SHA-256 e leitura numerada → HTTP 200, hashes e spans acima.
- [2026-10-14 19:20–19:21 UTC] BaseMapTest e MapWriteBehindTask no mesmo SHA — leitura numerada → testWriteBehindFastRemove em 1176–1192 e writer em 70–166, com os mesmos hashes acima.
- [2026-10-14 19:16 UTC] MakersHub — git rev-parse HEAD e leitura de airflow_client.py:270–275,356–359 → e233fb046ec333982cd1547171b0f0bd8d8d92ee; `status_code in _RETRYABLE_STATUS or status_code == 429`; `delay = retry_after if retry_after > 0 else _compute_backoff(attempt)`.
- [2026-10-14 19:23 UTC] comparação dos MDX com o conteúdo anterior guardado — extração dos corpos Mermaid, H1 e labels → changed_fences(cache)=[4]; changed_fences(capacity)=[2]; H1_preserved=true nos três arquivos; cache_labels=14; cache_ids=14; redisson.pro_present=false; other_seven_match_initial=true.

Este recibo não é aprovação semântica independente. Não houve teste, build, renderer Mermaid ou chamada às integrações do produto nesta frente. A raiz fará os recibos novos de sintaxe/render e a única rechecagem Grok dos três hashes atuais. Não resta bloqueio de acesso a código para G1/G2; o aceite permanece com o reviewer.
