# S3 — Airflow, workflows, integrações e objetos

## Veredito e escopo

Há três histórias concretas para ensinar a partir do código lido no servidor: ingestão incremental Salesforce com transformação dbt; relatórios XP com arquivo original, transformação e prontidão; gravações com objeto binário e metadados no PostgreSQL. Estas leituras provam o conteúdo dos arquivos no momento indicado. Elas não demonstram que cada fluxo está executando hoje no cluster informado pelo usuário.

O worktree autorizado é `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. A fonte Airflow lida por SSH foi `/home/fazcapital/airflow/airflow-dags`, branch `airflow-prod`, SHA `9ae34ee347cb4212515e3b26aeb87e02b167fb8d`. A skill `airflow-live-source` e o registro `~/.claude/sources/live-sources.json` foram lidos integralmente. CodeGraph foi consultado primeiro e devolveu o código atual em disco. As leituras posteriores ficaram nas áreas que ele não trouxe.

O scheduler Docker observado no host `.70` respondeu Airflow `3.2.2`, `LocalExecutor` e `parallelism=5`. Isto descreve somente esse container. A frente S6 precisa reconciliar estes componentes com Rancher/Kubernetes em produção antes da autoria sobre implantação, disponibilidade ou consumidores concorrentes. A presença de credenciais permanece desconhecida: o lookup SDK fora de uma task não forneceu uma medição válida, e não foi repetido.

## Composição antes de colisão

Reutilizar `docs/catalogos/catalogo-patterns.md`, que já enumera os conceitos de mensageria e do grupo 16; `docs/referencias/stack-makershub-airflow-postgres-salesforce.md`, para links e vocabulário; e `docs/aplicado/aplicacao-makershub-40-patterns.md`, para as dores iniciais e distinções entre task com falha e DLQ. `references/repos/temporal` serve à comparação entre workflow durável e DAG analítica; o corpus `awesome-software-architecture` oferece referências de mensageria. Estes repositórios são referências locais, sem prova de implantação.

As afirmações sobre CeleryExecutor e Helm/git-sync no corpus devem ser apresentadas como capacidades ou alternativas enquanto S6 fecha o runtime. No container medido, o executor é LocalExecutor. A mesma palavra MinIO no nome de uma classe identifica o SDK/contrato usado pelo código e, sozinha, não identifica o servidor que atende: pode existir um endpoint S3 compatível. O read-back de endpoint/cluster não foi fechado nesta frente.

## Caso 1 — Salesforce, PostgreSQL e dbt

`dags/crm__salesforce__api_to_stg__task.py` instancia `SalesforceDagFactory` com `postgres_prod`, `salesforce_prod` e o prefixo `stg_salesforce__`. Em `toolkit/salesforce/factory.py:88`, a cadeia é `extract`, `transform`, `validate_columns`, `load`; `extract_deleted`, `process_deleted` formam outra cadeia. `SalesforcePipeline.extract` busca campos descritos pela API e usa uma marca de modificação (`SystemModstamp`) para o incremental. O helper salva/carrega dados temporários; `load` usa COPY na primeira carga e upsert por `Id`, com comparação da marca de modificação. Existe também `run_inline`, que reutiliza a lógica em um processo; sua existência não prova qual DAG o aciona hoje.

`dags/fct_salesforce_calls__salesforce__stg_to_fct.py` usa Cosmos `DbtDag`, `ExecutionMode.LOCAL`, `LoadMode.DBT_LS`, `TestBehavior.AFTER_EACH` e seleciona `fct_salesforce__calls`. O modelo `dbt/models/facts/fct_salesforce__calls.sql` é incremental por `call_id`, lê `salesforce_prod.stg_salesforce__task`, filtra `TaskSubtype='Call'` e usa janela retrospectiva de duas horas sobre `source_updated_at`. A ingestão e a transformação são etapas distintas; o arquivo de transformação não define sozinho o agendamento da ingestão.

O PostgreSQL medido tinha 746.779 tasks e 723.247 calls. Esses números pertencem a tabelas com grãos diferentes e não devem virar uma taxa de conversão. O máximo de `SystemModstamp` era `2026-10-14 12:54:02-03:00`.

No capítulo, uma operadora espera que a ligação já modificada no CRM apareça na análise. A janela retrospectiva explica por que reler parte do passado protege registros tardios; a chave estável explica como evitar duas linhas para a mesma ligação. O custo é leitura repetida e dependência de regras de atualização corretas. A lição liga pipeline, idempotência, transformação e água alta do incremental sem prometer exatamente uma execução.

## Caso 2 — XP, arquivo original e prontidão

No código lido em `toolkit/faz_consulting_scraping_portfolio_positions_headless/processor.py`, `upload_files_to_minio` arquiva os bytes originais com SDK MinIO em `holdings_reports/{report_type}/{date}/{file_name}`. `process_downloaded_files_scoped` faz isso por arquivo, chama `process_single_file` e `upload_file_scoped`, com troca escopada e preservação de parcelas anteriores. `loop_engine.run_cycle` confirma downloads no ledger. Os parâmetros e nomes foram lidos; nenhum arquivo de cliente foi aberto.

A transformação usa o arquivo local baixado. Portanto, o diagrama deve mostrar o arquivo se dividindo em arquivamento e transformação. A leitura de volta do objeto para reprocessar seria um exercício/proposta até existir prova do consumidor; desenhar objeto seguido de transformação como caminho efetivo seria uma inferência não verificada.

`dags/stg_xp__diversification__proxy.py` verifica `logs.log_table_updates` e `public.get_available_dates_with_match()`; quando encontra match, `check_match` precede `produce_dataset`, que publica o Asset `dataset://xp_consolidated_positions_ready`. O consumidor `dags/fct_xp_consolidated_position__build.py` encadeia `calculate_fct_and_rpt`, `sync_makershub`, `validate_sync`, executando a procedure de posições e a sincronização MakersHub. A publicação de um Asset fornece prontidão a uma DAG e não prova a existência de um log contínuo de eventos.

No capítulo, o relatório de renda fixa chega antes do relatório de diversificação. Publicar o resultado combinado cedo pode entregar uma visão incompleta; esperar prontidão dá consistência ao lote, com custo de atraso. O objeto original permite explicar preservação e reprocessamento, mas a garantia do replay depende de uma rotina de leitura e de metadados que identifiquem a versão.

## Caso 3 — Áudio e metadados

`dags/recordings__nextbilling__api_to_stg__audio.py` encadeia `extract_recordings`, `enrich_with_salesforce_data`, `download_and_upload`, `load_metadata`. `create_minio_client` lê variáveis `minio_endpoint`, `minio_access_key`, `minio_secret_key`, `minio_secure`; isto é o contrato de configuração do código, sem confirmação dos valores efetivos. A etapa de upload verifica `stat_object`, preserva o objeto existente ou executa `put_object` de áudio. A carga usa `ON CONFLICT(nextbilling_call_id)` em `public.fct_minio__call`.

A história mostra uma gravação que precisa ficar disponível e ser encontrada por uma consulta. O binário vive no objeto e a consulta procura os metadados. Uma queda entre upload e inserção explica o risco entre dois sistemas: verificar existência e usar chave estável ajudam a recuperar, mas não constituem uma transação distribuída. O código passa caminhos temporários locais entre tasks; a disponibilidade desses caminhos precisa ser revisitada ao explicar workers em máquinas diferentes. O curso deve usar um identificador sintético nos exemplos de paths.

## Três papéis dos objetos

`AirflowMinIOHelper` usa `airflow-temp/{dag_id}/{execution_date}/{file_key}.pkl` como transporte; a extensão vem do builder mesmo quando a serialização passada é JSON. `RawParquetS3Sink` usa boto3, Parquet e chave `raw/{source}/{dataset}/dt={UTC}/{dag_id}__{run_id}__t{try}.parquet`, antes da transformação. `RAW_LANDING_STRICT` decide se falha de landing interrompe o fluxo. O terceiro papel é o produto binário, como o áudio. Explicar transporte, preservação original e produto ajuda o estudante a escolher retenção, custo, replay e acesso; um bucket por si só não estabelece essa política.

## Plano didático e referências

As páginas abaixo são propostas; S1 define os caminhos Nextra finais antes de qualquer MDX.

| Página de explicação | Conceitos e caso | Diagrama e exercício vinculado |
|---|---|---|
| Por que uma tarefa espera outra | DAG, Pipeline, Pipe and Filter, Workflow Engine, Orchestrator; Salesforce | Grafo de dependências; transformar três registros sintéticos com uma falha de validação |
| Como o processamento lembra onde parou | State Machine, Finite State Machine, marca incremental, retry, timeout; Salesforce/áudio | Estados de uma tentativa; queda sintética depois do upload e recuperação por chave |
| Quando o lote está pronto | Batch, Producer/Consumer, Fan-in, Aggregator; XP | Arquivo dividido em arquivo preservado/carga; dois relatórios que chegam em horários diferentes |
| Quem executa e quem limita a carga | Worker Pool, Job Queue, Competing Consumers, Bulkhead, Backpressure; runtime reconciliado com S6 | Capacidade do executor e pool separados; exemplo hipotético de 12 tarefas, 3 vagas, 4 ondas sem prometer duração |
| Transformar e repartir trabalho | Message Translator, Enricher, Filter, Router, Splitter, Aggregator, Resequencer, Scatter/Gather, Fork/Join, MapReduce | Distribuir arquivos sintéticos por partição, agrupar totais e lidar com partição lenta; dividir trabalho não basta para afirmar MapReduce completo |
| Lote, fluxo e reconstrução | Stream Processing, Lambda, Kappa, Choreography | Comparar atraso, janela, watermark, replay e custo de manter duas lógicas; estes estilos ficam como alternativas, sem afirmar que o ambiente os implementa |
| O arquivo e sua referência | Object Storage, metadados, S3, MinIO/SeaweedFS, checksum, versão, retenção; áudio/XP | Sequência upload/metadados e queda entre etapas; download público e identidade real ficam fora do exercício |

Recomendação: aproveitar Airflow, Cosmos e dbt já presentes para as histórias analíticas; usar Temporal como comparação do corpus para processos duráveis que esperam interação externa. MapReduce e Beam entram para comparação e exercício, sem proposta de instalar infraestrutura no ambiente.

Referências oficiais consultadas em 2026-10-14: [Airflow 3.2.2: arquitetura](https://airflow.apache.org/docs/apache-airflow/3.2.2/core-concepts/overview.html), [pools](https://airflow.apache.org/docs/apache-airflow/3.2.2/administration-and-deployment/pools.html), [dbt incremental](https://docs.getdbt.com/docs/build/incremental-models), [S3 API do SeaweedFS](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API), [MapReduce](https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html) e [Beam](https://beam.apache.org/documentation/programming-guide/). Context7 resolveu `/apache/airflow`; a consulta sobre pools trouxe `pool_slots` e limites de concorrência. O material retornado de `main` é conceitual; detalhes do ambiente usam a documentação fixada em 3.2.2. A URL `stable` respondeu 3.3.2 e não foi tomada como versão instalada.

## Recibos vivos

Os mtimes abaixo foram coletados com `TZ=UTC ls -l --time-style=long-iso`; os paths são relativos a `/home/fazcapital/airflow/airflow-dags` no host `airflow-70`.

- [2026-10-14 16:03 UTC] worktree arquitetura — `pwd -P; git branch --show-current; git rev-parse HEAD` → `perfect-citizen-a30f5998`, `23d5d158d3a964dceba296296368ec14bcd8970b`.
- [2026-10-14 15:55 UTC] airflow-70 — `pwd -P; git branch --show-current; git rev-parse HEAD` → `/home/fazcapital/airflow/airflow-dags`, `airflow-prod`, `9ae34ee347cb4212515e3b26aeb87e02b167fb8d`.
- [2026-10-14 15:56 UTC] FazGraph — `status()` → `source_mode=built`, `graph_mtime_utc=2026-10-13T03:08:04+00:00`, `data_dir=/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4/data`; `realpath /Users/augustocarollo/Developer/fazgraph-canonical-v4` → `/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4`. `pipeline("salesforce__task")` orientou a ligação staging/dbt; as regras vieram marcadas inferidas e os snapshots de runtime vieram stale.
- [2026-10-14 15:56 UTC] PostgreSQL MCP — `SELECT current_timestamp AT TIME ZONE 'UTC', inet_server_addr(), inet_server_port(), current_database(), (SELECT count(*) FROM salesforce_prod.stg_salesforce__task), (SELECT max("SystemModstamp") FROM salesforce_prod.stg_salesforce__task), (SELECT count(*) FROM public.fct_salesforce__calls)` → `2026-10-14 15:56:22.865167`, `192.168.254.137`, `5432`, `faz_capital`, `746779`, `2026-10-14 12:54:02-03:00`, `723247`.
- [2026-10-14 15:57 UTC] scheduler Docker `.70` — `airflow version; airflow config get-value core executor; airflow config get-value core parallelism` → `3.2.2`, `LocalExecutor`, `5`.
- [2026-10-14 15:57 UTC] arquivos Salesforce — leitura em disco mais `TZ=UTC ls -l --time-style=long-iso` → `toolkit/salesforce/factory.py: 2026-10-08 19:09`; `toolkit/salesforce/pipeline.py: 2026-10-08 19:35`; `dags/fct_salesforce_calls__salesforce__stg_to_fct.py: 2026-10-06 21:38`; `dbt/models/facts/fct_salesforce__calls.sql: 2026-08-20 04:02`.
- [2026-10-14 15:58 UTC] metadata acessado pelo scheduler Docker `.70` — `SELECT dag_id,state,count(*),max(start_date),max(end_date) FROM dag_run WHERE dag_id=ANY(:ids) AND start_date >= now()-interval '7 days' GROUP BY dag_id,state` para as cinco DAGs acima → somente `fct_salesforce_calls__salesforce__stg_to_fct, success, 2, latest_end=2026-10-08 19:06:37.553619+00:00`. `SELECT DISTINCT dag_id,task_id FROM task_instance` com mesmo filtro → `fct_salesforce__calls_run`. A medição não cobre o metadata do cluster.
- [2026-10-14 16:00 UTC] arquivos XP/áudio — leituras em disco mais `TZ=UTC ls -l --time-style=long-iso` → `processor.py: 2026-06-09 20:32`; `loop_engine.py: 2026-06-09 20:36`; `dags/stg_xp__diversification__proxy.py: 2026-09-29 17:33`; `dags/fct_xp_consolidated_position__build.py: 2026-09-29 17:33`; `dags/recordings__nextbilling__api_to_stg__audio.py: 2026-08-20 04:02`.

## Histórico limitado

`git log -2 --format='%h %cI %s' -- toolkit/salesforce/pipeline.py dbt/models/facts/fct_salesforce__calls.sql`, lido no host em 15:57 UTC, devolveu `33b52a83`, de 2026-10-06, sobre levar main revisada à árvore viva (FBI-4646), e `f77e50d3`, de 2026-09-29, sobre mover limpeza temporária para `cleanup_temp`. A leitura atual de `pipeline.load` ainda mostra limpeza dentro de `load`; o histórico não substitui o conteúdo vivo. Isto é uma divergência observada útil à pedagogia de proveniência, sem diagnóstico de incidente.

O log de dois commits para as DAGs XP/áudio trouxe `7d32ec21`, de 2026-09-29, sobre naming, e `f0099d5c`, de 2026-08-20, sobre congelar ondas de naming. Os commits são marcos históricos; os mtimes e o conteúdo foram medidos separadamente.

## Três tarefas delimitadas para auxiliares Luna

Nenhum auxiliar foi despachado por S3. Modelo e esforço efetivos são responsabilidade da raiz.

1. **Evidência:** receber o pacote S6 e reconciliar namespace, executor, metadata e origem das DAGs. Confirmar somente agregados e task IDs dos três casos, com UTC, arquivo e mtime. Gate: nenhuma frase transforma a observação Docker `.70` em topologia global; nenhum segredo ou dado pessoal é lido.
2. **Referências:** vincular cada conceito das sete páginas às fontes oficiais de Airflow, Cosmos/dbt, S3/SeaweedFS, Temporal, Beam e MapReduce. Confirmar API/versão pelo Context7 e URL oficial, identificar exemplos OSS reutilizáveis e manter padrões conceituais separados de implantação. Gate: links verificados e nenhuma contagem de estrelas herdada como atual.
3. **Apoio didático:** preparar três histórias, seus diagramas Mermaid e exercícios com registros/arquivos sintéticos. Explicar benefício, custo, limite e falha concreta em português completo. Gate: toda seta tem fonte ou marca de proposta; o exercício não aciona Airflow, Salesforce, bucket real ou deploy.
