# EVIDENCE_PACKET — workflows e processamento

SHA `23d5d158d3a964dceba296296368ec14bcd8970b`; grupo 16=16; seis apoios S3=22.

S3: `.70:/home/fazcapital/airflow/airflow-dags`, `airflow-prod` @ `9ae34ee347cb4212515e3b26aeb87e02b167fb8d`; S6: Kubernetes git-sync `main` @ `8f06738d7d3bc735c48c5c5450d5297b4dedc398`. Hash parity cobre cinco arquivos (14/10 16:11–16:12 UTC). Airflow 3.2.2/LocalExecutor: K8s 32, `.70` 5 (15:57 UTC). Snapshots; sem requery ou execução provada.

## 22 conceitos

| # | Conceito | Definição; caso; limite | Skill / base / código |
|---:|---|---|---|
| 1 | State Machine | Estados/transições; áudio upload→SQL; sem atomicidade entre stores. | O / Temporal / T |
| 2 | Finite State Machine | Estados finitos; estados de task; espera longa pede engine. | D / Airflow / A3 |
| 3 | Workflow Engine | Executa passos; Salesforce/dbt; efeitos não são atômicos. | O / Airflow+Temporal / A1,T |
| 4 | DAG | Dependências acíclicas; CRM; ciclos não cabem. | D / Airflow / A1 |
| 5 | Pipeline | Transformações em ordem; CRM extract→load; replay pede idempotência. | D / Cosmos+dbt / A1 |
| 6 | Orchestrator | Coordenador; scheduler Airflow; falha pausa agendamentos. | O / Airflow / A1 |
| 7 | Choreography | Reações a eventos; Watermill; XP Asset segue scheduler central. | O / Watermill / W |
| 8 | Job Queue | Trabalho espera worker; Temporal WorkflowTask; ordem depende do contrato. | J / Temporal / TQ |
| 9 | Worker Pool | Limita concorrência; K8s parallelism=32; não conta workers ativos. | C / Airflow / A1 |
| 10 | Batch Processing | Lote finito; XP espera relatórios pareados; aumenta latência. | D / Airflow+dbt / A2 |
| 11 | Stream Processing | Eventos contínuos/janelas; Beam; exige política para atraso. | S / Beam / B |
| 12 | Lambda Architecture | Batch e stream separados; exercício; duplica lógica. | S / Beam comparação / B |
| 13 | Kappa Architecture | Um stream com replay; exercício; precisa de log retido. | S / Beam comparação / B |
| 14 | MapReduce | Reduz por chave; Hadoop WordCount; shuffle custa rede. | S / Hadoop / H |
| 15 | Scatter/Gather | Divide chamadas e coleta respostas; partições sintéticas; lenta segura o grupo. | P / Beam / B |
| 16 | Fork/Join | Ramos e junção; XP arquiva/processa; paralelismo não provado. | P / Airflow / A2 |
| 17 | Orchestration | Coordenador rege sequência; XP Asset; segue scheduler-led. | O / Eventuate / E |
| 18 | Producer/Consumer | Produtor enfileira, consumidor processa; excesso cria backlog. | J / Temporal+Watermill / TQ,W |
| 19 | Fan-in | Aguarda pré-requisitos; XP `check_match`; ausência atrasa lote. | D / Airflow Assets / A2 |
| 20 | Aggregator | Combina partes; somas XP sintéticas; prontidão não agrega. | S / Beam+Hadoop / B,H |
| 21 | Pipe and Filter | Etapas transformam dados; factory CRM; esquema muda a jusante. | D / Airflow / A1 |
| 22 | Task | Unidade executável; áudio upload; retry pode repetir efeito. | J / Airflow / A3 |

Skills: D=`data-engineering:airflow-dag-patterns`; O=`backend-workflow-orchestration-patterns`; J=`backend-background-jobs`; C=`backend-concurrency-mechanics`; S=`data-streaming`; P=`async-python-patterns`. Distinções: Machine=estado; DAG=dependências; engine=execução. Orchestration=coordenador; choreography=reações. MapReduce=chaves; Scatter/Gather=respostas; Fork/Join=ramos. Batch=finito; Stream=contínuo; Lambda=dois caminhos; Kappa=replay de um log.

## Três mapas produtor → ponte → consumidor

| Fluxo / ambiente | Código e evidência |
|---|---|
| **Salesforce → dbt.** | Salesforce API → `dags/crm__salesforce__api_to_stg__task.py:3,7–9`, SHA-256 `63d2b11a4eb36cb637504cacb0f96808351109799f8e2aad2c8ac89805b4403d` → `toolkit/salesforce/factory.py:88`, SHA-256 `e20a6b8996a672bbd0d514e1ef1b83f9deb7459bd50bd773f0aabd610cfbeb1b` → PostgreSQL staging → `.70`-only `dags/fct_salesforce_calls__salesforce__stg_to_fct.py` + `dbt/models/facts/fct_salesforce__calls.sql` (linhas/hashes não registrados). `SystemModstamp`; não afirmar exactly-once. |
| **XP → arquivo + prontidão.** | Download (`toolkit/faz_consulting_scraping_portfolio_positions_headless/loop_engine.py::run_cycle`, linha não capturada) → `toolkit/faz_consulting_scraping_portfolio_positions_headless/processor.py::process_downloaded_files_scoped`, SHA-256 `dbb158f6a35fddb5135a23affd11e3baaea71adccd43542749d3f839ab357b16` → **arquivo local** divide-se em arquivamento (`upload_files_to_minio`) e transformação local → `dags/stg_xp__diversification__proxy.py:22`, SHA-256 `ea489597682d480f9345e9c8c931566ac78db0dc70c14337065668e2adfff059`, Asset após `check_match` → `.70`-only `dags/fct_xp_consolidated_position__build.py`. Replay lendo MinIO não provado. |
| **Áudio → objeto + metadado.** Endpoint MinIO real desconhecido. | NextBilling `extract_recordings` → `dags/recordings__nextbilling__api_to_stg__audio.py:914–933`, SHA-256 `0f07f024b88303ed2f07f1343eb45e879591291222706d68916f65f4aeac50ad` → enriquecer Salesforce/baixar/enviar → MinIO SDK + PostgreSQL `public.fct_minio__call`, `ON CONFLICT(nextbilling_call_id):760`. Falha separa stores; chave ajuda recuperar, sem atomicidade. |

Código corpus RO: T=Temporal `workflow_rebuilder.go:67–105`; TQ=`transfer_queue_task_executor_base.go:147–168`; W=Watermill `message/router.go:23–40`; E=Eventuate `CreateOrderSaga.java:24–31`. Nenhum implica implantação. Fontes: [Airflow 3.2.2 DAG Runs](https://airflow.apache.org/docs/apache-airflow/3.2.2/core-concepts/dag-run.html), [Assets](https://airflow.apache.org/docs/apache-airflow/3.2.2/authoring-and-scheduling/assets.html), [Temporal](https://docs.temporal.io/temporal), [Hadoop MapReduce](https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html), [Beam](https://beam.apache.org/documentation/programming-guide/). H/B não provam Lambda/Kappa nem paralelismo XP.
