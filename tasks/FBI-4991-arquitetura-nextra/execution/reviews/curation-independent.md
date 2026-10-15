# Revisão independente da curadoria

O veredito é **REPAIR** para os 183 conceitos desta lane. O julgamento individual está em `curation-independent.assignment-one.json`: 153 correspondências estão sustentadas no recorte declarado, 10 têm ajustes médios e 20 têm lacuna material de fonte. Os 127 conceitos da outra lane não receberam aprovação por este relatório.

O alvo foi a matriz congelada `a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e`. Esta revisão não alterou a matriz, os MDX, os laboratórios, o Jira ou as capturas do autor. O detalhamento verificável dos achados está em `curation-independent.findings.json`.

## Os reparos materiais

- WebSocket usa handlers HTTP e webhook. At Least Once usa deduplicação do broker. Scatter/Gather espera o encerramento de scrapes, sem reunir respostas de uma mesma operação.
- A ACL usa separação entre repositório e serviço, sem tradução de significado externo. Context Map usa uma lista de namespaces, sem relações. Domain Service usa a própria entidade Loan.
- Distributed Cache mostra uma abstração sem backend compartilhado. Refresh Ahead usa aquecimento periódico sem renovar antes da expiração. Single Flight mostra um Group.Do que o caminho de cache selecionado não chama.
- Consistent Hashing mostra a montagem e os tokens do ring, sem o lookup de chave para dono. Range Sharding mostra hash e lookup; o range vazio citado serve ao broadcast. Thread Pool mostra tarefas do event loop. Circuit Breaker usa orçamento de capacidade como aplicação de uma política de falha e recuperação.
- Denormalization, Materialized View e Precomputation usam um agregador Druid que calcula a consulta corrente e retorna uma Sequence. A base PostgreSQL já capturada pode ser reutilizada se seu papel e o mecanismo forem explicitados.
- MVC aponta para uma API JAX-RS sem view e renderização selecionadas. Saga, Orchestration Saga e Compensating Transaction mostram a capacidade opcional do SDK e o fluxo de criação de pedido, mas falta o callback concreto que compensa o efeito desse fluxo. As reservas Medusa já capturadas fornecem outra cadeia concreta, caso o recorte seja ajustado.

Esses achados não afirmam que os produtos OSS careçam desses mecanismos. Eles demonstram que o recorte selecionado ainda não sustenta a correspondência publicada. A correção deve ligar o conceito ao mecanismo primário adequado e manter como pendente qualquer item ainda sem prova.

## O que recebeu suporte direto

PAC no WengoPhone contém hierarquia de controles e passagem de eventos do modelo à apresentação. O OpenDaylight executa votação, pré-commit e commit com aborto. O Medusa tem módulos carregados no mesmo backend, containers próprios e serviços públicos. Geode combina regiões particionadas em memória com processamento local aos dados. Nova/Neutron conserva o pedido do consumidor, o plano do fornecedor e a implementação de port bindings. Nova conserva o ciclo de reservas de migração; Mastodon conserva Follow/Accept/Reject/Undo com compensações; Grafana conserva a ponte de painéis Angular/React. Os limites históricos e de atomicidade desses casos foram mantidos.

A integridade passou no recibo `curation-independent.final-receipt.json`: 799 registros históricos HTTP 200, 737 artefatos únicos, 545 localizadores ativos e 176 revisões de licença não tiveram divergências de hash. As duas publicações compactadas reproduzem os JSONs locais. A sonda que corrompeu apenas o hash esperado em memória foi rejeitada. Os 59 MDX de referência compilaram com zero erros de vínculo; as 335 ocorrências do catálogo e os 46 links das 40 prioridades foram reconciliados.

O ranking público está limitado aos packs candidatos e às consultas datadas. A captura mensal preserva 22 cards, incluindo o Addy Osmani na posição 15 com 12.981 estrelas no mês. Isso não mede a qualidade individual de uma skill nem estabelece um vencedor universal. As licenças foram conferidas por revisão e integridade; esta revisão não é uma decisão jurídica de compatibilidade.

A próxima ação é reparar os 20 conceitos altos. A única rechecagem desta lane deve se limitar a esses achados e aos hashes alterados. Os dez ajustes médios ficam registrados para o principal, sem reabrir semânticas já aprovadas.
