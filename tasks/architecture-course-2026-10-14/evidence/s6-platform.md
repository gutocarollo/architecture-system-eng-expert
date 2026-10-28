# S6 — Plataforma, disponibilidade, segurança e mudanças

## Veredito e fronteira

A fonte Kubernetes foi medida diretamente. O cluster Rancher `local` tinha três nós RKE2, e o scheduler Airflow executava `LocalExecutor` com paralelismo 32. A leitura S3 de Docker `.70`, com paralelismo 5, continua válida somente para aquele container. Cinco arquivos dos casos Salesforce, XP e áudio têm hashes iguais no disco `.70` e no disco do scheduler Kubernetes. Isso permite reutilizar seus conteúdos como fonte estática do cluster; não prova uma execução recente dessas DAGs.

O checkout de autoria é `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. A escrita desta frente ficou exclusivamente neste arquivo. Não houve restart, deploy, alteração de configuração, segredo exposto ou execução de DAG. Este pacote é planejamento e medição; o council independente pertence à raiz.

## Composição antes de colisão

Reutilizar os três casos de S3: a ligação entre Salesforce e dbt, a prontidão dos relatórios XP e a gravação de áudio com metadados. Reutilizar `docs/aplicado/aplicacao-makershub-40-patterns.md` como proposta didática, `docs/referencias/catalogo-40-patterns-skills-frameworks.md` como ponto inicial de referências e `evidence/coverage.json` como inventário. O arquivo aplicado já distingue flag de autorização e rollback de efeitos realizados; essa explicação deve permanecer.

A colisão é de identidade da fonte: o registro `live-sources.json` e a skill `airflow-live-source` descrevem o checkout `.70`; as skills `airflow-rke2-api` e `rancher-api` descrevem o cluster. O pod consome `main` via git-sync e resolve uma árvore de SHA `8f06738d7d3bc735c48c5c5450d5297b4dedc398`. Ele não consome o checkout `airflow-prod` `.70` como bind mount. Portanto, nenhuma frase sobre executor, volume, metadata ou deployment deve transportar automaticamente a identidade `.70` para Kubernetes.

As skills Rancher, Airflow RKE2, observabilidade Kubernetes, fonte viva e docs-autoagents foram lidas. O perfil docs-autoagents da raiz usa `metadata` e aceita as capturas pelo source `workflow-evidence`. Recomenda-se identificar nesta captura duas fontes distintas, `airflow-70-disk` e `airflow-rke2-runtime`. O registro global não foi editado. A preparação, os locks e o gate final continuam sob o condutor único.

## Topologia medida e suas consequências

Em 14/10, entre 16:10 e 16:16 UTC, Rancher respondeu `v2.15.2`, RKE2 `v1.36.5+rke2r1` e três nós Ready: `rke2-55`, `rke2-60`, `rke2-75`. API, dag-processor e triggerer tinham duas réplicas Ready; o scheduler tinha uma. O Service da API tinha dois endpoints Ready. As réplicas de API estavam em nós diferentes, com anti-affinity obrigatória por hostname.

O scheduler usa estratégia `Recreate`. API, dag-processor, triggerer e PgBouncer DW usam `RollingUpdate`, com `maxSurge=0` e `maxUnavailable=1`. Uma troca da API pode preservar uma de suas duas réplicas, mas isso depende da prontidão e dos componentes compartilhados. Uma troca do scheduler não tem outra réplica medida para continuar o agendamento durante o intervalo. Nenhum ensaio de failover foi executado.

A imagem Airflow do scheduler é `crg.apkg.io/fazcapital/airflow-prod:r2-calamine-gitsync`, com imageID `sha256:ca38e8350d98ee3f96a510ce2de875682208c820bffef7027518a9f725f85965`. O git-sync `v4.4.2` busca `https://bitbucket.org/fazcapital/airflow.git`, ref `main`, para um volume `emptyDir`; o container Airflow monta DAGs somente para leitura. O diretório configurado é `/opt/airflow/airflow-dags/dags`, que resolve a árvore git-sync. Os logs usam `s3://airflow-task-logs/prod`. A imagem por digest é um conteúdo identificável, mas o conjunto da release inclui a revisão mutável das DAGs. Git-sync isoladamente não prova GitOps nem imutabilidade de toda a release.

O scheduler aponta para `airflow-pg-rw.airflow.svc:5432/airflow`. CloudNativePG tinha três instâncias saudáveis, primário `airflow-pg-2` e dois standbys. A consulta no primário retornou dois streams em `quorum`, com atraso de replay de zero bytes naquele instante. A configuração efetiva era `synchronous_commit=on`, `ANY 1` e `dataDurability=required`. Isso ensina a diferença entre aguardar um standby e aguardar todos. Zero bytes agora não define RPO sob toda falha. O CronJob de backup tinha sucesso às `07:14:42Z`; não houve leitura do objeto nem restore, portanto a recuperação permanece sem prova nesta frente.

Etcd `3.6.14` respondeu nos três membros `.55/.60/.75`, termo Raft 8, com `.75` como líder. Para três membros votantes, a maioria é `floor(3/2)+1=2`; uma perda deixa dois votos, enquanto duas perdas deixam um. Essa conta pressupõe que os sobreviventes se comuniquem. Não foram medidos discos, latência de consenso ou falha de energia conjunta. Os nós não tinham labels de zona/região, o que não permite afirmar Multi-AZ ou Multi-Region.

Há Leases de Kubernetes, incluindo `kube-scheduler`, `kube-controller-manager` e `plndr-cp-lock`. Lease escolhe quem deve agir por um período; o recurso que recebe a escrita ainda precisa rejeitar um agente antigo para haver fencing. O próprio client-go declara que sua eleição não garante fencing. O curso deve manter separadas a eleição do controle Kubernetes, a coordenação do scheduler Airflow pelo metadata e a proteção de efeitos externos. A documentação Airflow `stable` consultada era 3.3.2; ela explica coordenação por locks de linha no metadata. A página 3.2.2 do scheduler não foi obtida, portanto essa consulta não certifica os detalhes internos da versão instalada.

Há RoleBindings do namespace, identidades ServiceAccount e scheduler com `runAsUser=50000`, `allowPrivilegeEscalation=false`, `capabilities.drop=[ALL]`. Isso fornece um exemplo concreto de camadas de defesa, sem provar menor privilégio de todos os papéis. Os Ingresses lidos não tinham `spec.tls`; nenhuma NetworkPolicy foi encontrada no namespace `airflow`. Esses são escopos de configuração, não um ensaio de tráfego: TLS em outro salto, ACL de rede externa e políticas de outro mecanismo não foram medidos. O auth manager efetivo é FAB; OAuth2/OIDC do ambiente não foram confirmados.

## Reconciliação dos cinco arquivos

Os paths abaixo são relativos às raízes `.70` `/home/fazcapital/airflow/airflow-dags` e pod `/opt/airflow/dags/.worktrees/8f06738d7d3bc735c48c5c5450d5297b4dedc398`. Os hashes de cada linha são iguais nos dois discos. O mtime do pod é de materialização da árvore e não a data da mudança lógica.

| Arquivo | SHA-256 | Mtime `.70`, UTC | Mtime pod, UTC |
|---|---|---|---|
| `dags/crm__salesforce__api_to_stg__task.py` | `63d2b11a4eb36cb637504cacb0f96808351109799f8e2aad2c8ac89805b4403d` | 2026-06-26 20:29:48 | 2026-10-13 17:57:00 |
| `dags/stg_xp__diversification__proxy.py` | `ea489597682d480f9345e9c8c931566ac78db0dc70c14337065668e2adfff059` | 2026-09-29 17:33:43 | 2026-10-13 17:57:00 |
| `dags/recordings__nextbilling__api_to_stg__audio.py` | `0f07f024b88303ed2f07f1343eb45e879591291222706d68916f65f4aeac50ad` | 2026-08-20 04:02:42 | 2026-10-13 17:57:00 |
| `toolkit/salesforce/factory.py` | `e20a6b8996a672bbd0d514e1ef1b83f9deb7459bd50bd773f0aabd610cfbeb1b` | 2026-10-08 19:09:44 | 2026-10-13 17:57:01 |
| `toolkit/faz_consulting_scraping_portfolio_positions_headless/processor.py` | `dbb158f6a35fddb5135a23affd11e3baaea71adccd43542749d3f839ab357b16` | 2026-06-09 20:32:17 | 2026-10-13 17:57:00 |

No pod, a DAG Salesforce importa `SalesforceDagFactory` nas linhas 3/7 e configura `postgres_prod`/`salesforce_prod` nas linhas 8/9. XP declara o Asset nas linhas 22 e encadeia `check_match`/`produce_dataset`. Áudio define tasks de extração, enriquecimento, download/upload e metadata nas linhas 914–933, com `ON CONFLICT(nextbilling_call_id)` na linha 760. A factory e o processor confirmam as pontas reutilizadas por S3. A igualdade dos cinco arquivos não afirma igualdade do repositório inteiro.

## Cobertura dos grupos 11–14

O inventário tem 59 entradas nestes quatro grupos: 13+12+17+17. A palavra “proposta” abaixo significa que o curso explica o mecanismo e apresenta um exercício; a frente não confirmou sua implantação. Não significa ausência no sistema inteiro.

| Grupo | Presença sustentada nesta frente | Conceitos que ficam como proposta ou comparação |
|---|---|---|
| 11 — decomposição | Os casos S3 fornecem fronteiras concretas para exercitar migração. Nenhuma migração ativa foi medida. | Strangler Fig; Branch by Abstraction; Parallel Run; Shadow Traffic; Dark Launch; Feature Toggle; Expand/Contract; Transitional Architecture; Modularization; Service Extraction; Database Decomposition; CDC Migration; Dual Write Migration. |
| 12 — releases | Rolling Deployment e Recreate Deployment são estratégias declaradas nos Deployments medidos. Imagem e revisão git são duas entradas identificáveis. | Blue/Green Deployment; Canary Release; Shadow Deployment; Dark Launch; Feature Flags; Progressive Delivery; A/B Deployment; Immutable Infrastructure do conjunto; Infrastructure as Code com procedência; GitOps. |
| 13 — disponibilidade | Duas APIs no Service permitem ensinar Active/Active de réplicas de aplicação. Primário/standbys e streams sustentam Leader/Follower, Replication e Hot Standby. Etcd e Leases sustentam exemplos de Quorum, Heartbeat e Leader Election. A configuração CNPG sustenta discussão de failover, sem ensaio nesta frente. | Active/Passive de um serviço completo; Warm Standby; Cold Standby; Multi-AZ; Multi-Region; Failover e Automatic Failover exercitados; Split-Brain Prevention sob falha; Fencing; Stateless Services como contrato completo de estado externo. |
| 14 — segurança | RoleBindings e ServiceAccounts sustentam RBAC e identidade de serviço no Kubernetes. O contexto do scheduler sustenta Defense in Depth parcial. | Zero Trust; Least Privilege validado; ABAC; ReBAC; Policy-Based Access Control; OAuth2; OIDC; Token Exchange; Short-Lived Credentials com ciclo de vida medido; Secrets Rotation; mTLS verificado em cada ligação; API Gateway Security; Bastion Host; Network Segmentation. |

## Prioritários, base reutilizável e aplicação OSS

Todos os links foram consultados em 2026-10-14. “REF” identifica uma aplicação de referência, sem implantação presumida no ambiente. Não foram usados números de estrelas como prova de qualidade. Context7 resolveu `/argoproj/argo-rollouts` e retornou exemplos reais de `prePromotionAnalysis`, `postPromotionAnalysis`, Blue/Green e Canary.

| Core | Base e aplicação | Skill e finalidade didática |
|---|---|---|
| 23 — Strangler Fig | Envoy/Traefik; [sandbox front proxy Envoy](https://www.envoyproxy.io/docs/envoy/latest/start/sandboxes/front_proxy), REF. [Azure Strangler Fig](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig) fornece o mecanismo; o sandbox fornece roteamento, não uma migração completa. | `deprecation-and-migration`: transferir uma rota do caminho antigo para o novo, com dono de escrita explícito. |
| 24 — Expand/Contract | Flyway/Liquibase; [GitLab migrations](https://docs.gitlab.com/development/database/avoiding_downtime_in_migrations/), aplicação OSS com orientação de compatibilidade. | `framework-migration:database-migration`: adicionar contrato compatível, migrar consumidores e retirar contrato antigo somente após evidência. |
| 25/26 — Blue/Green e Canary | Argo Rollouts/Flagger; [rollouts-demo](https://github.com/argoproj/rollouts-demo), REF, e [Blue/Green oficial](https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/). | `devops-progressive-delivery`: comparar troca de Service com exposição gradual e gates de análise. |
| 27 — Feature Flags | Unleash; [GitLab feature flags](https://docs.gitlab.com/operations/feature_flags/) demonstra a API compatível com Unleash; [conceito Unleash](https://docs.getunleash.io/concepts/feature-flags). | `backend-feature-flags`: controlar elegibilidade da nova regra de pulling sem tratar a flag como autorização ou reversão de efeitos anteriores. |
| 28 — Leader Election | etcd/client-go; Kubernetes observado e [Leases](https://kubernetes.io/docs/concepts/architecture/leases/). [client-go](https://raw.githubusercontent.com/kubernetes/client-go/master/tools/leaderelection/leaderelection.go) limita a garantia sobre fencing. | `backend-distributed-locking`: exercício com líder antigo que volta depois de perder a lease; o recurso rejeita uma geração antiga. |
| 30 — Replication | PostgreSQL/CNPG; operador OSS [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg), aplicado ao metadata real, e [documentação de replicação](https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/replication.md). | `cloud-infrastructure:multi-cloud-architecture`, quando comparar regiões; `rancher-api`/`k8s-observability-api` para leitura operacional. Comparar replicação, backup e restore. |
| 35 — Sidecar | [Kubernetes git-sync](https://github.com/kubernetes/git-sync), aplicado no pod real. Envoy/Dapr ficam como comparação. | `cloud-infrastructure:service-mesh-observability`: mostrar volume compartilhado e responsabilidade do auxiliar, sem prometer um mesh. |
| 36 — Service Mesh | Istio/Linkerd; [Istio Bookinfo](https://istio.io/latest/docs/examples/bookinfo/), REF. | `cloud-infrastructure:istio-traffic-management` e `cloud-infrastructure:mtls-configuration`: ensinar identidade, política, telemetria e custo operacional; instalação no ambiente não foi medida. |
| 37 — Anti-Corruption Layer | Camel/adaptadores de domínio; [Wild Workouts](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example), REF de fronteiras, sujeito a localizar o adaptador exato com S5. | `api-and-interface-design`/DDD: traduzir vocabulário externo em contrato interno. Esta ACL não é uma Access Control List. S5 mantém a autoria principal. |

## Plano de ensino

`safe-change` deve partir de uma mudança proposta na regra de pulling. Uma liberação para 10 de 100 usuários sintéticos expõe 10% das pessoas, mas desligar a flag não desfaz os leads já distribuídos. O exercício exige uma única autoridade de escrita, comparação de resultados e condição explícita para avanço. Shadow Traffic só pode comparar efeitos se a sombra não executar efeitos reais. Blue/Green precisa de compatibilidade do banco para permitir rollback; voltar a imagem não retira dados já escritos.

`availability` deve partir da operadora que abre a API enquanto um pod é trocado. Duas réplicas de API ajudam nesse trecho; o scheduler único, o metadata e o armazenamento continuam sendo dependências. Um Mermaid de topologia mostrará API, scheduler/LocalExecutor, git-sync/volume, PostgreSQL e logs remotos. Um Mermaid de sequência mostrará renovação da lease, pausa do antigo líder e rejeição de uma escrita com geração antiga. O exercício ocorre em simulação local, sem matar pods reais.

`data-durability/replication` deve partir de um histórico de execução que precisa sobreviver à perda de um banco e também a uma exclusão acidental. Uma réplica pode receber a exclusão; o backup preserva uma versão anterior; só o restore demonstra que ela pode ser usada. O guia de operação exige medir RPO/RTO e testar integridade em ambiente separado. Segurança deve partir de “quem pode ler o log” e seguir identidade, autorização, transporte e retenção em camadas; siglas entram depois da necessidade humana.

Recomendação: ensinar a plataforma já medida e usar Argo Rollouts, Unleash, GitOps e mesh como blueprint de exercício. Não propor implantação desses produtos como consequência automática de documentá-los.

## Recibos

Os comandos `kubectl` usaram `/Users/augustocarollo/airflow-ha/bin/kubectl` e o kubeconfig canônico, sem imprimir seu conteúdo. Rancher usou a CA canônica com verificação TLS. As linhas seguintes contêm as projeções literais relevantes dos resultados.

- [2026-10-14 16:16 UTC] worktree arquitetura — `pwd -P; git branch --show-current; git rev-parse HEAD` → `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`, `perfect-citizen-a30f5998`, `23d5d158d3a964dceba296296368ec14bcd8970b`.
- [2026-10-14 16:10 UTC] Rancher HTTPS — `GET /v3/clusters/local; GET /v3/settings/server-version; GET /k8s/clusters/local/api/v1/nodes` → `state=active`, `nodeCount=3`, `gitVersion=v1.36.5+rke2r1`, `v2.15.2`, `rke2-55/rke2-60/rke2-75 Ready=True`.
- [2026-10-14 16:10 UTC] namespace airflow — `GET /apis/apps/v1/namespaces/airflow/deployments` pelo Rancher → `api-server replicas=2 ready=2`, `dag-processor=2/2`, `scheduler=1/1`, `triggerer=2/2`, `pgbouncer-dw=2/2`.
- [2026-10-14 16:11 UTC] scheduler `airflow-scheduler-748ddbb5b8-d8kxh` — `kubectl exec ... -c scheduler -- python -c 'from airflow.configuration import conf; ... conf.get(...)'` → `core.executor=LocalExecutor`, `core.parallelism=32`, `core.dags_folder=/opt/airflow/airflow-dags/dags`, `logging.remote_logging=True`, `logging.remote_base_log_folder=s3://airflow-task-logs/prod`.
- [2026-10-14 16:12 UTC] mesmo scheduler — `git -c safe.directory=<resolved-root> -C <resolved-root> rev-parse HEAD; import airflow; airflow.__version__` → `8f06738d7d3bc735c48c5c5450d5297b4dedc398`, `3.2.2`. A opção `-c` foi por comando; não houve escrita em config Git.
- [2026-10-14 16:11–16:12 UTC] pod e `.70` — `Path.read_bytes(); hashlib.sha256(...); Path.stat().st_mtime` para os cinco paths da tabela → hashes literais da tabela em ambos os discos. A leitura `.70` ocorreu por `ssh airflow-70`, sem BatchMode.
- [2026-10-14 16:11 UTC] namespace airflow — `kubectl get deployments -o json` → scheduler `strategy.type=Recreate`; API, dag-processor, triggerer e PgBouncer DW `RollingUpdate, maxSurge=0, maxUnavailable=1`.
- [2026-10-14 16:16 UTC] Service API — `kubectl get endpointslices -l kubernetes.io/service-name=airflow-api-server -o json` → `airflow-api-server-68c74c6b7c-jcdnd ready=True`, `airflow-api-server-68c74c6b7c-nqh4m ready=True`.
- [2026-10-14 16:12 UTC] `airflow-pg-2`, container postgres — `SELECT current_timestamp AT TIME ZONE 'UTC',pg_is_in_recovery(); SELECT application_name,state,sync_state,pg_wal_lsn_diff(pg_current_wal_lsn(),replay_lsn) FROM pg_stat_replication ORDER BY application_name` → `2026-10-14 16:12:47.836059|f`, `airflow-pg-1|streaming|quorum|0`, `airflow-pg-3|streaming|quorum|0`.
- [2026-10-14 16:14 UTC] mesmo primário — `SHOW synchronous_commit; SHOW synchronous_standby_names` → `on`, `ANY 1 ("airflow-pg-1","airflow-pg-3","airflow-pg-2")`; `kubectl get cluster.postgresql.cnpg.io airflow-pg -o json` → `postgresql.synchronous={dataDurability:required,failoverQuorum:false,method:any,number:1}`.
- [2026-10-14 16:10 UTC] backup airflow — `GET /apis/batch/v1/namespaces/airflow/cronjobs` → `airflow-metadata-backup schedule=10 4 * * *, lastSuccessfulTime=2026-10-14T07:14:42Z`.
- [2026-10-14 16:15 UTC] etcd `etcd-rke2-55` — `etcdctl --cacert=<server-ca.crt> --cert=<server-client.crt> --key=<server-client.key> endpoint status --cluster -w table` → `.55/.60/.75 version=3.6.14, learner=false, raft_term=8`; `.55/.60 leader=false`, `.75 leader=true`, `ERRORS` vazio. A primeira tentativa com `client.crt` falhou por arquivo ausente; a segunda usou o certificado existente, sem alterar arquivos.
- [2026-10-14 16:11 UTC] coordenação Kubernetes — `kubectl -n kube-system get leases -o json` → `kube-scheduler leaseDurationSeconds=15`, `kube-controller-manager=15`, `plndr-cp-lock holder=rke2-55 leaseDurationSeconds=15`, com `renewTime` em `16:11:56/57Z`.
- [2026-10-14 16:10–16:14 UTC] segurança namespace airflow — `kubectl get rolebindings -o json; kubectl get ingresses -o json; GET networkpolicies` → RoleBindings `airflow-pg`, `airflow-pod-log-reader-rolebinding`, `cnpg-certificados-le-clusters`, `deploy-agent`; ingress `tls=None`; NetworkPolicies `[]`. `kubectl get pod airflow-scheduler-748ddbb5b8-d8kxh -o json` → `serviceAccountName=airflow-scheduler`, `runAsUser=50000`, scheduler `allowPrivilegeEscalation=false`, `capabilities.drop=[ALL]`.
- [2026-10-14 16:15 UTC] configuração metadata/auth do scheduler — `make_url(conf.get("database","sql_alchemy_conn")); conf.get("core","auth_manager")`, projetando somente host/porta/database → `airflow-pg-rw.airflow.svc 5432 airflow`, `airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager`.

## Três missões delimitadas para os auxiliares Luna

1. **Topologia e evidência.** Transformar somente os recibos desta frente em inventário de produtores, consumidores e pontes. Conferir relações git-sync→volume→scheduler, scheduler→metadata e primário→standbys. Entregar Mermaid proposto, ledger de presença/proposta e lacunas de restore/failover, sem consultar segredos nem executar falhas reais.
2. **Skills e referências OSS.** Conferir a correspondência dos onze prioritários da tabela com as skills instaladas e os projetos oficiais. Fixar URL, revisão/data e trecho que prova cada mecanismo, com atenção à limitação de fencing do client-go e ao adaptador exato do Wild Workouts para S5. Não inferir adoção por stars ou nome de pasta.
3. **Ensino e Diátaxis.** Produzir histórias, benefícios, custos, limites e exercícios sintéticos para `safe-change`, `availability` e `data-durability/replication`. Calcular maioria de 3 e exposição 10/100, distinguir replicação de restore e flag de autorização, e devolver esboços para a raiz adjudicar antes de MDX.

Estas missões foram planejadas; nenhum auxiliar foi despachado por S6.
