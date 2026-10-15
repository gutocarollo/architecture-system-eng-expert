# L6A — Quatro elos da plataforma

Esta captura descreve quatro relações medidas no runtime Kubernetes em 14/10/2026, entre 16:10 e 16:16 UTC. Ela reaproveita os recibos de [S6](s6-platform.md), a amostra de DAG registrada em [S3](s3-airflow.md) e a distinção entre bancos registrada em [S4](s4-consistency.md). Não fiz novas consultas de produção nem ensaios de falha ou implantação. As páginas upstream marcadas como referência foram lidas em 14/10/2026; seus branches mutáveis não identificam a versão instalada.

## 1 — O código da DAG chega ao scheduler

**Antes:** identifique a fonte que o pod realmente usa. O checkout lido no host .70 estava em **airflow-prod**; o pod do scheduler buscava a branch **main**. **Depois:** o **git-sync v4.4.2** deixava a árvore resolvida no volume **emptyDir**, e o Airflow lia o diretório de DAGs montado somente para leitura. Na medição, esse diretório apontava para o SHA **8f06738d7d3bc735c48c5c5450d5297b4dedc398**; o scheduler também estava configurado com **LocalExecutor** e paralelismo **32**. A DAG Salesforce de S3 é uma amostra real da árvore, não prova de uma execução recente.

**Risco:** main pode avançar sem a imagem do scheduler mudar; o digest da imagem sozinho não identifica o código completo da release. **Limite:** o SHA é um retrato daquele instante. Os hashes iguais de cinco arquivos entre .70 e o pod provam igualdade desses arquivos, não do repositório inteiro. O git-sync também não prova GitOps.

**Base e amostra:** Kubernetes e [git-sync](https://github.com/kubernetes/git-sync), já referenciados em S6; o arquivo OSS [Apache Airflow scheduler-deployment.yaml](https://github.com/apache/airflow/blob/main/chart/templates/scheduler/scheduler-deployment.yaml) mostra a composição condicional do container git-sync e do volume. Esse template em main é exemplo didático, não a configuração renderizada do cluster medido.

~~~mermaid
flowchart LR
  ref["Bitbucket: main"]
  sync["git-sync v4.4.2"]
  volume["emptyDir com árvore<br/>SHA 8f06738d"]
  scheduler["Airflow scheduler<br/>DAGs em leitura"]
  ref --> sync --> volume --> scheduler
~~~

## 2 — O controle do cluster usa consenso

**Antes:** uma proposta do plano de controle depende de membros que consigam concordar. **Depois:** às 16:15 UTC, os três membros votantes .55, .60 e .75 respondiam; o status mostrava o líder .75 e termo Raft 8. Para três votos, a maioria é 2: se um membro sair e os outros dois ainda se comunicarem, a maioria permanece; se dois saírem, resta um e não há maioria.

**Risco:** a minoria não pode avançar o consenso; uma partição de rede também pode impedir que os dois sobreviventes se comuniquem. **Limite:** não houve teste de falha e os nós sem labels de zona não provam domínios físicos independentes. O termo 8 identifica o termo observado, não oito nós ou oito gravações. Também são mecanismos distintos o líder Raft do etcd e as Leases Kubernetes: na mesma captura, .75 liderava o etcd e rke2-55 mantinha plndr-cp-lock. O arquivo OSS do [kube-controller-manager](https://github.com/kubernetes/kubernetes/blob/master/cmd/kube-controller-manager/app/controllermanager.go) mostra a eleição de controladores por client-go; essa eleição não garante fencing. A [implementação client-go](https://raw.githubusercontent.com/kubernetes/client-go/master/tools/leaderelection/leaderelection.go), já verificada em S6, exige que o recurso de destino também rejeite um líder antigo.

~~~mermaid
flowchart LR
  n55["etcd .55<br/>votante"]
  n60["etcd .60<br/>votante"]
  leader["etcd .75<br/>líder, termo 8"]
  quorum["Maioria necessária<br/>2 de 3"]
  n55 --> quorum
  n60 --> quorum
  leader --> quorum
~~~

## 3 — O metadata do Airflow espera um standby

**Antes:** a aplicação envia uma transação ao primário do cluster CNPG. **Depois:** a configuração lida às 16:14 UTC tinha synchronous_commit=on e ANY 1; a confirmação de um dos dois standbys satisfaz a espera síncrona. Às 16:12 UTC, ambos apareciam como streams em estado quorum, com atraso de replay medido em zero bytes.

**Risco:** se o standby exigido não puder confirmar, a escrita pode esperar; replicar não substitui backup. O CronJob teve sucesso às 07:14:42Z, mas nenhum objeto foi lido nem restaurado. **Limite:** este é o banco de metadata airflow-pg, com primário airflow-pg-2; não é 192.168.254.137:5432/faz_capital. O wal_level=minimal registrado em S4 pertence a esse outro servidor e não descreve o CNPG. A documentação de [replicação do CloudNativePG](https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/replication.md), verificada em S6, traz exemplos da configuração síncrona; a configuração observada também tinha failoverQuorum=false. A captura não prova RPO sob falha nem recuperação por restore.

~~~mermaid
flowchart LR
  app["Airflow"]
  primary["CNPG primary<br/>airflow-pg-2"]
  standby1["Standby airflow-pg-1"]
  standby2["Standby airflow-pg-3"]
  ack["ANY 1: um ACK<br/>satisfaz a espera"]
  app --> primary
  primary --> standby1
  primary --> standby2
  standby1 -. ACK .-> ack
  standby2 -. ACK alternativo .-> ack
  ack --> app
~~~

## 4 — A troca da aplicação tem duas estratégias

**Antes:** a captura encontrou duas réplicas Ready da API e uma do scheduler. **Depois:** a API usava RollingUpdate, maxSurge=0 e maxUnavailable=1; com duas réplicas saudáveis, a regra permite uma indisponível durante a troca e pode deixar uma atendendo. O scheduler usava Recreate; o Kubernetes encerra os Pods antigos antes de criar os novos, então uma troca pode deixar o agendamento sem Pod até o novo ficar pronto.

**Risco:** uma atualização do scheduler pode interromper temporariamente o início de novas tarefas; a API ainda depende de metadata e serviços compartilhados. **Limite:** estratégia e réplicas foram lidas, mas nenhum rollout foi ensaiado, então duração e impacto real não foram medidos. A semântica de Recreate e dos limites de RollingUpdate está na [documentação de Deployments do Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), lida em 14/10/2026. O template OSS do Airflow citado no quadro 1 é uma amostra de configuração, não prova do rollout local.

~~~mermaid
flowchart LR
  api["API<br/>2 réplicas Ready"]
  rolling["RollingUpdate<br/>máx. indisponível 1<br/>sem Pod extra"]
  apiReady["Pode restar 1 API<br/>se estiver saudável"]
  scheduler["Scheduler<br/>1 réplica Ready"]
  recreate["Recreate<br/>encerra antigos<br/>antes dos novos"]
  gap["Janela sem scheduler<br/>até o novo ficar pronto"]
  api --> rolling --> apiReady
  scheduler --> recreate --> gap
~~~
