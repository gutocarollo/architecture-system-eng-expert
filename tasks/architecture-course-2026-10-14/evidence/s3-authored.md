# Autoria S3 — capítulos, referência e guia

## Entrega e contrato

A autoria ocorreu no worktree `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. Foram usados o contrato de autoria, o mapa de cobertura, os deltas L3A/L3B/L3C, a reconciliação S6 e a pesquisa da fase S3. A rota warm manteve o especialista Sol 6.1/xhigh. Nenhum auxiliar foi despachado nesta autoria.

A referência confirma o caminho do mapa `content/referencia/catalogo/16-workflow-e-processamento.mdx`. As quatro páginas usam frontmatter Diátaxis. A autoria entrega conteúdo e hashes; compilação, links, renderização Mermaid e veredito pertencem aos gates independentes da raiz. Não houve execução dos exercícios, de DAGs ou dos comandos operacionais publicados no guia.

## Arquivos e SHA-256

Medição feita em 2026-10-14 às 17:24:29 UTC por `shasum -a 256` contra os quatro caminhos abaixo.

| Arquivo | SHA-256 |
|---|---|
| `content/explicacoes/distributed-work/index.mdx` | `960e40d9205f9565f582d5922c316ca69d8272cc32e87013d0a308491b6e4666` |
| `content/explicacoes/workflow/index.mdx` | `ebbd3a808359730709aa9837804dc3c6b142dcd49ca8573dfbe602cd272effde` |
| `content/referencia/catalogo/16-workflow-e-processamento.mdx` | `9bc134994ce187247009fd7691a9851f70cc40d04520362c6c7eedf00dffe6a8` |
| `content/guias/recuperar-pipeline.mdx` | `a41cd270542e85640f72550ff4529d905a1d58bab211d87d29c7897f52f0e916` |

## Cobertura

A referência tem seções identificáveis para State Machine, Finite State Machine, Workflow Engine, DAG, Pipeline, Orchestrator, Choreography, Job Queue, Worker Pool, Batch Processing, Stream Processing, Lambda Architecture, Kappa Architecture, MapReduce, Scatter/Gather e Fork/Join. Cada seção define o mecanismo, aplica um caso, apresenta seu limite e vincula skill, base e aplicação OSS com classificação REF/PROD. Lambda/Kappa registram explicitamente a lacuna de uma aplicação completa verificada; Beam serve à comparação dos mecanismos, sem capacidade atribuída pelo nome.

`distributed-work` desenvolve State Machine, o prioritário core 40, com identidade, confirmação perdida, transição e concorrência. Também trata Saga, Orchestration Saga, Choreography Saga, Reservation Pattern, TCC e Compensating Transaction, usando uma reserva financeira fictícia e links para S4. O exemplo de aviso acessório que falha preserva a reserva válida; a decisão principal que rejeita o pedido permite compensar. O capítulo não representa a Saga Eventuate ou Temporal como infraestrutura implantada.

`workflow` liga as definições aos três mapas concretos Salesforce, XP e áudio. Desenvolve Pipe and Filter, Task, Producer/Consumer, Fan-in, Aggregator e Competing Consumers como apoios, com links para os capítulos dos outros owners. A transformação XP parte do arquivo local e bifurca para arquivamento e transformação; ler o objeto para replay não foi apresentado como implementado. Scatter/Gather, Fork/Join e MapReduce mostram critérios de junção, partição lenta e custo de agrupamento. Batch/Stream/Lambda/Kappa permanecem distintos de gatilho por Asset.

O guia prepara uma decisão de recuperação com comandos somente de leitura: contexto Kubernetes, configuração do scheduler, fonte `.70` com mtime, runs/estados e agregado PostgreSQL em transação read-only com tempo máximo. Ele define o resultado exigido e os limites do agregado; não manda disparar runs, limpar estados ou apagar objetos.

## Fronteiras preservadas

- A igualdade de cinco arquivos entre `.70` e pod é fonte estática, sem prova de execução recente. O helper `SalesforcePipeline`, a DAG/modelo dbt, `loop_engine.run_cycle` e o consumer XP permanecem fontes `.70` sem paridade demonstrada.
- Os valores de paralelismo 32 no Kubernetes e 5 no Docker `.70` são snapshots de configuração, não workers ativos ou capacidade útil provada.
- As 746.779 Tasks e 723.247 calls medidos em PostgreSQL possuem grãos diferentes e não viraram taxa de conversão.
- Os dois workflows n8n tinham configuração PostgreSQL lida; as buscas com zero hits não provaram ausência global de objetos ou Airflow. Destinos de HTTP Request permanecem não examinados.
- SeaweedFS aparece como implementação OSS de interface S3 e backend candidato. O endpoint efetivo das DAGs XP/áudio permanece desconhecido.
- Os desenhos de falha, estados persistidos adicionais, reserva financeira e retomadas são cenários propostos. O código observado de áudio tem upload/metadados sem transação distribuída.

## Fonte pontual adicionada durante autoria

A [referência oficial CLI do Airflow 3.2.2](https://airflow.apache.org/docs/apache-airflow/3.2.2/cli-and-env-variables-ref.html), consultada em 2026-10-14 às 17:22 UTC, define `airflow dags list-runs` com `dag_id` posicional e `--start-date`/`--end-date`, e `airflow tasks states-for-dag-run` com `dag_id` e `logical_date_or_run_id`. O guia usa esses contratos e manda conferir a ajuda da instalação. Não foi executada uma consulta CLI no runtime nesta autoria.
