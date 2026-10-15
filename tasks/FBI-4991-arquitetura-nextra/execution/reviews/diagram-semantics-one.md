# Revisão semântica dos diagramas da lane 1

Veredito: **corrigir um HIGH**. Foram julgados os 46 diagramas da atribuição: 45 PASS_BOUNDED e 1 HIGH. Os dois achados MEDIUM ficam no backlog. A fonte de conteúdo é `623ae1d3d34143df53c571327a508de47ab58951`, na branch `docs/FBI-4991-arquitetura-aplicada`.

O diagrama72 omite uma etapa real do snapshot de linhagem: ranking recebe de `dbt.fct_advisor_dashboard`, que recebe de `dbt.fct_captacao`. O Mermaid desenha captação diretamente para ranking. A correção delimitada é trocar `Model --> Ranking` por `Dashboard --> Ranking`. O retorno ao revisor deve conferir somente esse HIGH com hashes e PNG novos.

A leitura de FazGraph desta rodada confirmou o mesmo snapshot construído em 13/10 às 03:08:04 UTC. Em seguida, o PostgreSQL confirmou a identidade 137:5432/faz_capital e o tipo r da tabela. O recibo bruto está em `diagram-semantics-one-graph-primary.json`. Isso não afirma execução atual de DAG ou atualidade do dashboard. Os grafos de etcd/CNPG foram comparados com os comandos e saídas datados em `s6-platform.md`; não houve nova medição desses runtimes nem acesso a segredos.

Os46 corpos e suas páginas completas foram lidos; os 46 PNGs foram inspecionados. O código e os modelos locais têm caminhos, hashes e trechos em `diagram-semantics-one-primary.json`. O arquivo `diagram-semantics-one-readings.json` preserva os corpos e recortes de contexto. Os checks de hash apenas ligam o parecer aos bytes. Nenhum laboratório ou teste aceito foi reexecutado.

## Parecer por diagrama

**diagram-1 — PASS_BOUNDED** (content/explicacoes/api-integration/index.mdx; doc `6cb5b9dce9c6`, corpo `04659328ef25`). A entrada decide políticas gerais antes de rotear; a API conserva a decisão de acesso ao objeto e a recusa. Não identifica o gateway implantado nem certifica APISIX ou a configuração de produção. Fonte: modelo hipotético explicitado no JSON.

**diagram-3 — PASS_BOUNDED** (content/explicacoes/api-integration/index.mdx; doc `6cb5b9dce9c6`, corpo `cb30812e4374`). O contrato local só alcança a regra após reconhecer identidade e significado; a falha exige investigar a origem. Não prova que esse mapeamento completo esteja implementado no dispatcher. Fonte: modelo hipotético explicitado no JSON.

**diagram-5 — PASS_BOUNDED** (content/explicacoes/availability/index.mdx; doc `c5677cb7589d`, corpo `456cc4b989b5`). O desenho conserva os três votantes, o líder .75 no termo 8 e a maioria de dois descritos no recibo literal. A captura documental não é um ensaio de falha; dois sobreviventes ainda precisam comunicar-se. Não se atribui esse estado a 15/10. Fonte: s6_capture:[(27, 29), (99, 100)].

**diagram-7 — PASS_BOUNDED** (content/explicacoes/availability/index.mdx; doc `c5677cb7589d`, corpo `2ae49e992ccd`). As duas confirmações são alternativas elegíveis para ANY 1, compatíveis com synchronous_commit=on e number=1 no recibo. A resposta não exige ambos os standbys; não prova replay na hora do commit, failover ou RPO futuro. O raw de execução separado não está no pacote. Fonte: s6_capture:[(25, 25), (96, 97)].

**diagram-9 — PASS_BOUNDED** (content/explicacoes/availability/index.mdx; doc `c5677cb7589d`, corpo `51383952fb5e`). A identidade de transporte pode ser recusada pelo proxy de destino; a telemetria acompanha as duas fronteiras. Não demonstra Istio, Linkerd, Envoy ou mTLS implantado e não concede autorização de negócio. Fonte: modelo hipotético explicitado no JSON.

**diagram-11 — PASS_BOUNDED** (content/explicacoes/business-rules/index.mdx; doc `55d471bca1aa`, corpo `ba77e697bfd2`). As relações pontilhadas dizem a confirmar ou a definir; o mapa não converte pastas em acordos de negócio já existentes. A aprovação é do mapa de estudo, sem reconhecer donos ou contratos organizacionais. Fonte: modelo hipotético explicitado no JSON.

**diagram-13 — PASS_BOUNDED** (content/explicacoes/business-rules/index.mdx; doc `55d471bca1aa`, corpo `83978b75cc49`). A tradução recusada torna ausência e ambiguidade explícitas antes da regra; corrigir o de-para reinicia a tradução. Não certifica um de-para real, nem trata uma mera cópia de schema como tradução semântica. Fonte: modelo hipotético explicitado no JSON.

**diagram-15 — PASS_BOUNDED** (content/explicacoes/cache/index.mdx; doc `b29d777d61aa`, corpo `7a4e5d99f444`). O get consulta Redis quando disponível; na indisponibilidade shared_only impede o fallback LRU e devolve falta. O desenho não descreve L1 seguido sempre de L2, nem garante que todos os chamadores consultem a origem com a política correta. Fonte: cache:[(128, 172)].

**diagram-17 — PASS_BOUNDED** (content/explicacoes/cache/index.mdx; doc `b29d777d61aa`, corpo `95e1f2f866f6`). O valor ainda válido pode ser devolvido sem aguardar o produtor; somente sucesso renova os dois prazos e a leitura após expiração espera carga. É coordenação local. A sequência abstrai o agendamento: o código agenda o refresh antes de retornar; não há promessa de ordem global entre resposta e execução da task. Fonte: singleflight:[(75, 106), (108, 154)].

**diagram-19 — PASS_BOUNDED** (content/explicacoes/capacity/index.mdx; doc `13e50ee708d1`, corpo `fb3993990146`). O desenho distingue resposta HTTP de erro de timeout local e conserva a incerteza sobre o efeito remoto. As duas tentativas ilustradas são um orçamento didático; não pretendem enumerar as três tentativas máximas do cliente Airflow nem provar POST idempotente. Fonte: modelo hipotético explicitado no JSON.

**diagram-21 — PASS_BOUNDED** (content/explicacoes/capacity/index.mdx; doc `13e50ee708d1`, corpo `882bdb8727b5`). A admissão recusa trabalho quando falta capacidade e faz o produtor esperar ou reduzir ritmo; o consumidor libera vaga. Não descreve a admissão da fila Redis observada, nem fornece durabilidade ao trabalho recusado. Fonte: modelo hipotético explicitado no JSON.

**diagram-23 — PASS_BOUNDED** (content/explicacoes/casos/access-policy/index.mdx; doc `c38e421bcf2d`, corpo `2c439e7bdc2c`). O papel sozinho permite o contraexemplo; papel, tenant e conta recusam o acesso cruzado, e as verificações de audience, prazo e chave são representadas. O gráfico compõe probes independentes da função; não implementa uma cadeia criptográfica, OAuth, firewall ou política real da Faz. Fonte: financial:[(431, 443)].

**diagram-26 — PASS_BOUNDED** (content/explicacoes/casos/consensus/index.mdx; doc `942512b4ae79`, corpo `ca8a23b1b082`). A partição A/B satisfaz dois de três, a minoria C não; os vetores concorrentes e a espera por decisão têm os limites declarados. Contar maioria e comparar vetores em probes não implementa log, termos, Raft/Paxos ou linearizabilidade. Fonte: financial:[(143, 160)].

**diagram-28 — PASS_BOUNDED** (content/explicacoes/casos/diagnostics/index.mdx; doc `c062c1456a03`, corpo `c24d2f3a5b2d`). Os três spans reúnem duas requests da ORDER-1, com um erro e maior duração de 800 ms; a probe da ordem pode falhar com health ok. Não é OpenTelemetry real nem estabelece percentil, SLO ou causa de produção. Fonte: financial:[(446, 462)].

**diagram-30 — PASS_BOUNDED** (content/explicacoes/casos/ledger-projection/index.mdx; doc `25fd1903aa70`, corpo `978fc7a120a1`). Os três fatos somam 900; a projeção parte de 1000 com dois fatos faltantes, e o rollback SQLite fica separado do replay. Não é ledger de produção, checkpoint durável ou recuperação PostgreSQL. Fonte: financial:[(343, 361)].

**diagram-32 — PASS_BOUNDED** (content/explicacoes/casos/order-boundaries/index.mdx; doc `4d5dc484c87c`, corpo `2feb7f35a909`). AUTHORISED e 10000 centavos viram accepted e 100; a validação impede a escrita negativa e a estratégia altera a taxa. A função contém probes separadas; a seta é uma composição didática, sem provar uma única transação executável que encadeia todos os mecanismos. Fonte: financial:[(24, 45), (61, 63)].

**diagram-35 — PASS_BOUNDED** (content/explicacoes/casos/queue-workflow/index.mdx; doc `2a254250d96b`, corpo `963c37124fbf`). A conta de admissão é 120 menos 20 igual a 100 recusas; poison esgota três tentativas e fica fora da fila normal. A composição liga probes de memória. Não é um broker, uma DAG real nem um replay durável; a espera de retry é modelo. Fonte: financial:[(186, 237), (274, 277)].

**diagram-38 — PASS_BOUNDED** (content/explicacoes/casos/safe-release/index.mdx; doc `b2a27050fe08`, corpo `f98b4e1c8537`). A expansão conserva os dois campos, cinco de cem requisições formam 5%, e funções puras detectam a diferença 10 contra 1000 preservando o primário. Os probes não executam uma pipeline de deployment nem uma promoção real; a rota e o shadow são mecanismos compostos para estudo. Fonte: financial:[(410, 422)].

**diagram-40 — PASS_BOUNDED** (content/explicacoes/casos/storage-partitions/index.mdx; doc `84e5fd9b484a`, corpo `1efd1c0d8568`). A chave 7 seleciona uma partição por módulo; o contraexemplo de JOIN soma 100 vezes 2 mais 200 vezes 3 igual a 800, frente a 300 no grão correto. O índice e o plano são SQLite e a junção é aritmética de fixture; não representam topologia ou EXPLAIN PostgreSQL. Fonte: financial:[(378, 398)].

**diagram-42 — PASS_BOUNDED** (content/explicacoes/code-boundaries/index.mdx; doc `7bb6ae7dec9a`, corpo `a5fa86bee2af`). Os três módulos expõem APIs públicas e mantêm os detalhes internos; o texto declara que essa fronteira ainda é proposta. A seta direta Qualificação para internos é uma relação estrutural. Como fluxo de autorização ela é ambígua e pode parecer contornar Pedido permitido; melhoria MEDIUM no backlog. Fonte: modelo hipotético explicitado no JSON.

**diagram-44 — PASS_BOUNDED** (content/explicacoes/code-boundaries/index.mdx; doc `7bb6ae7dec9a`, corpo `20cfd79a50bd`). Cada entrada conduz ao seu handler; a intenção D1 só persiste pelo ramo validado e as três entradas recebem o contrato compartilhado de autorização. Não comprova que esses handlers ou essa organização já existam no checkout. Fonte: modelo hipotético explicitado no JSON.

**diagram-46 — PASS_BOUNDED** (content/explicacoes/code-boundaries/index.mdx; doc `7bb6ae7dec9a`, corpo `b4a03e2ac642`). A view passiva envia selectMode ao Presenter; o Model confirma ou recusa e o Presenter renderiza a escolha ou conserva o modo anterior. Não descreve a sincronização atual entre as janelas React nem classifica o aplicativo inteiro como MVP. Fonte: modelo hipotético explicitado no JSON.

**diagram-48 — PASS_BOUNDED** (content/explicacoes/code-patterns/index.mdx; doc `b2c3b29b4df5`, corpo `95525fce59f7`). ReadOperation depende de ProviderPort; os provedores PostgreSQL e Salesforce implementam o mesmo fetch, com direção coerente de implementação. O gráfico oferece uma estrutura candidata. Não prova classes locais nem duas dimensões concretas de variação já exercitadas. Fonte: modelo hipotético explicitado no JSON.

**diagram-50 — PASS_BOUNDED** (content/explicacoes/code-patterns/index.mdx; doc `b2c3b29b4df5`, corpo `3891fba22d6b`). O comando reconhecido atualiza o modelo e notifica a apresentação; o comando inválido retorna ao coordenador sem mudar o estado. Não certifica Observer/Mediator GoF ou compartilhamento de uma instância de hook entre janelas. Fonte: modelo hipotético explicitado no JSON.

**diagram-52 — PASS_BOUNDED** (content/explicacoes/concurrency/index.mdx; doc `a83595be0daa`, corpo `fb5f1178a444`). A e B leem versão 7; A avança para 8 e B recebe conflito antes de reler e revalidar, preservando o crédito de A. Aceitação exige comparação e escrita atômicas no recurso; a hipótese não comprova esse contrato em uma API implantada. Fonte: modelo hipotético explicitado no JSON.

**diagram-54 — PASS_BOUNDED** (content/explicacoes/data-distribution/index.mdx; doc `34abbabc12cf`, corpo `7e714f328df4`). O texto distingue lookup de uma conta em sua shard da consolidação que reúne ambas; o ramo indisponível permite parcial identificado ou falha. As duas setas do roteador representam destinos alternativos conforme a chave, e não broadcast obrigatório de todo lookup. Não é topologia implantada. Fonte: modelo hipotético explicitado no JSON.

**diagram-56 — PASS_BOUNDED** (content/explicacoes/data-distribution/index.mdx; doc `34abbabc12cf`, corpo `5b2d10f6ff9c`). W={A,B,C} e R={C,D,E} compartilham C; comparar versão e conflito é obrigatório antes de qualquer promessa de frescor. A interseção não prova linearizabilidade; membership fixo e seleção correta da versão são premissas. Fonte: modelo hipotético explicitado no JSON.

**diagram-58 — PASS_BOUNDED** (content/explicacoes/data-durability/index.mdx; doc `f2a147286150`, corpo `cb1b30c4548c`). A restauração usa backup-base e WAL contínuo até o alvo; um segmento necessário ausente deixa esse alvo sem demonstração. Não prova backup, arquivamento, restore ou PITR habilitado no servidor .137. Fonte: modelo hipotético explicitado no JSON.

**diagram-60 — PASS_BOUNDED** (content/explicacoes/data-durability/index.mdx; doc `f2a147286150`, corpo `2c763d5a4610`). Tanto o líder novo como o antigo chegam ao mesmo destino, que aceita somente a autoridade válida e rejeita a antiga. A eleição sozinha não implementa esse guard; nenhum destino com fencing na Faz é certificado. Fonte: modelo hipotético explicitado no JSON.

**diagram-62 — PASS_BOUNDED** (content/explicacoes/distributed-work/index.mdx; doc `c96345ff2180`, corpo `b669163987f7`). A rejeição principal libera a reserva; uma operação válida conserva o efeito e registra o aviso acessório pendente para retomada. Concluir refere-se à operação principal; não certifica que o aviso pendente já foi entregue, nem que existe uma Saga implantada. Fonte: modelo hipotético explicitado no JSON.

**diagram-64 — PASS_BOUNDED** (content/explicacoes/messages/index.mdx; doc `6490d79817eb`, corpo `27f20e66fab0`). Auditoria e KPI são assinaturas independentes; os dois workers KPI pertencem ao mesmo grupo, e a pendência é condicional à durabilidade do transporte. As duas arestas do grupo não significam que cada worker execute cada mensagem; o texto define divisão. Não prova Redis Pub/Sub durável. Fonte: modelo hipotético explicitado no JSON.

**diagram-66 — PASS_BOUNDED** (content/explicacoes/messages/index.mdx; doc `6490d79817eb`, corpo `73d07b030190`). A CTE escolhe PENDING sob limite e SKIP LOCKED e o UPDATE muda para BOT_PROCESSING na mesma instrução; a necessidade de recuperar abandono permanece explícita. O gráfico é uma intercalação possível enquanto há locks; depois de commit, o estado também exclui o item. Não prova workers ativos ou recuperação completa. Fonte: claim:[(485, 515)].

**diagram-68 — PASS_BOUNDED** (content/explicacoes/observability/index.mdx; doc `f496432e43af`, corpo `c79c4d1ef425`). O span filho da consulta e o contexto propagado à chamada externa permitem relacionar os ramos de sucesso e erro; exportação depende da política. Não comprova instrumentação/exporter/collector existente nem causa de incidente. Fonte: modelo hipotético explicitado no JSON.

**diagram-70 — PASS_BOUNDED** (content/explicacoes/read-models/index.mdx; doc `b6b5bb503268`, corpo `d54ad98b8f48`). persist_report adquire política/lock quando configurado e decide commit ou rollback; read chama o port/repository que monta total, linhas e resumo. A separação é local, não um transporte assíncrono. O gráfico resume o fluxo e omite o registro posterior da tentativa falha. Fonte: report_write:[(127, 168)]; report_read:[(24, 60)]; report_repository:[(191, 281)].

**diagram-72 — HIGH** (content/explicacoes/read-models/index.mdx; doc `b6b5bb503268`, corpo `731e16024424`). A aresta Model para Ranking não corresponde à cadeia retornada pelo mesmo snapshot: ranking recebe de fct_advisor_dashboard. A correção é somente da topologia gráfica. Nenhum runtime ou frescor atual de ranking foi inferido. Os valores datados de 14/10 permanecem históricos. Fonte: graph_primary:[].

**diagram-74 — PASS_BOUNDED** (content/explicacoes/reliable-integration/index.mdx; doc `fa192b82b3ba`, corpo `ec4c2e3c6ce9`). O responsável e pending mudam na mesma instrução, condicionados ao responsável anterior; rowcount zero retorna False antes de histórico e efeitos atribuídos à troca. A instrução não é um commit autônomo nem certifica entrega Salesforce; a transação externa ainda possui seu contrato. Fonte: apply:[(337, 415)].

**diagram-76 — PASS_BOUNDED** (content/explicacoes/reliable-integration/index.mdx; doc `fa192b82b3ba`, corpo `7344d47817b3`). O estado e a outbox entram numa transação, a decodificação lógica alimenta o consumidor e atraso exige retenção/progresso. Não afirma CDC habilitado no banco datado com wal_level=minimal; identidade e deduplicação continuam necessárias. Fonte: modelo hipotético explicitado no JSON.

**diagram-78 — PASS_BOUNDED** (content/explicacoes/safe-change/index.mdx; doc `ae62d79a2abf`, corpo `e8ab9ec65ea7`). A versão atual continua dona da resposta e da única escrita; a candidata não executa efeitos e só passa a escritora após critério aceito. Copiar entrada exige autorização e supressão de todos os efeitos; o desenho não prova migração ativa. Fonte: modelo hipotético explicitado no JSON.

**diagram-80 — PASS_BOUNDED** (content/explicacoes/safe-change/index.mdx; doc `ae62d79a2abf`, corpo `ce4f6b7658f1`). O Service ativo atende pela azul enquanto o preview verifica a verde; promoção depende de compatibilidade/saúde e exige observação posterior. Voltar tráfego não desfaz alterações de dados; não comprova Argo instalado nem ensaio de rollback. Fonte: modelo hipotético explicitado no JSON.

**diagram-82 — PASS_BOUNDED** (content/explicacoes/safe-change/index.mdx; doc `ae62d79a2abf`, corpo `43ee92414d72`). A autorização vem antes da elegibilidade da flag; desligar a função muda a rota de comportamento e conserva efeitos já aceitos. A flag não concede direitos e não compensa registros anteriores. Não é uma política de produção observada. Fonte: modelo hipotético explicitado no JSON.

**diagram-84 — PASS_BOUNDED** (content/explicacoes/security/index.mdx; doc `ddc600a30732`, corpo `2986a9d27b2a`). O pedido deve ter identidade e autorização, transporte protegido, privilégios delimitados e consulta restrita; a recusa impede leitura. As setas organizam responsabilidades, não a cronologia do handshake TLS; as camadas não estão todas comprovadas no runtime Airflow. Fonte: modelo hipotético explicitado no JSON.

**diagram-86 — PASS_BOUNDED** (content/explicacoes/workflow/index.mdx; doc `3a39fdb9c077`, corpo `a2a1a717ef99`). O processor usa o arquivo local para arquivar bytes e transformar; o proxy só publica o Asset após o teste e o consumer encadeia cálculo, sync e validação. As chamadas do processor são sequenciais; os ramos representam origem dos dados. O objeto não alimenta a transformação. O consumer foi lido em objeto Git, sem nova medição de deploy ou execução .70. Fonte: xp_processor:[(510, 574), (1173, 1247)]; xp_proxy:[(22, 22), (29, 150), (175, 184)]; xp_consumer:[(27, 49), (57, 64), (104, 116), (132, 182)]; xp_loop:[(41, 99)]; s3_capture:[(27, 35), (69, 76)].

**diagram-88 — PASS_BOUNDED** (content/guias/investigar-impacto.mdx; doc `6a936ddbbe4b`, corpo `51d9fea56681`). A investigação parte da alteração, orienta-se por pipeline, calcula alcance e só depois consulta dados em leitura; as lacunas impedem fechamento indevido. O procedimento não prova sozinho contratos de consumidores nem transforma contagens históricas em estado atual. Fonte: modelo hipotético explicitado no JSON.

**diagram-90 — PASS_BOUNDED** (content/tutoriais/optimistic-concurrency.mdx; doc `f8de20c0e324`, corpo `ccc28cffb489`). As duas cópias leem 7; a primeira grava 8; a segunda comparação esperada 7 falha, conservando approved na versão 8. A sequência não demonstra concorrência de threads ou transação em banco; o texto exige comparação/gravação atômicas ao portar. Fonte: modelo hipotético explicitado no JSON.

**diagram-92 — PASS_BOUNDED** (content/tutoriais/read-projection.mdx; doc `5821c113f9b8`, corpo `b0855d1abad1`). O gráfico relaciona as fotografias10 e15 ao avanço de cursor, coerentes com o resultado esperado do programa. A primeira atualização ocorre quando somente evt-01 existe; evt-02 entra depois. A caixa agregada com os dois eventos é resumo do conjunto final, não uma chamada que processe parcialmente ambos. Fonte: modelo hipotético explicitado no JSON.

**diagram-94 — PASS_BOUNDED** (content/tutoriais/state-machine.mdx; doc `2b174b3488d0`, corpo `92e517362098`). UNKNOWN, operador e especialista sem motivo preservam IN_CONTACT; somente o especialista com motivo chega a PENDING, como o código. Os rótulos dos laços se sobrepõem no PNG original. A semântica do corpo corresponde, mas a legibilidade visual não fica aprovada; achado MEDIUM no backlog. Fonte: modelo hipotético explicitado no JSON.

## Backlog delimitado

No diagrama42, a mesma convenção gráfica representa dependência de módulo e sequência de autorização; diferenciar essas setas removeria a ambiguidade. No diagrama94, os rótulos de recusa dos laços de IN_CONTACT se sobrepõem no PNG original. Esses dois itens são MEDIUM de comunicação, sem mudança comprovada de comportamento de produto.

PLACAR:1 achado HIGH real; 2 MEDIUM no backlog; 0 PENDING. PROXIMO PASSO: corrigir a aresta do diagrama72 e retornar somente esse recorte ao mesmo revisor.
