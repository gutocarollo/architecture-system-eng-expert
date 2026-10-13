# Aplicação dos 40 padrões ao dia a dia (MakersHub)

> Os exemplos abaixo partem da arquitetura **MakersHub**: Next.js/React, FastAPI, PostgreSQL,
> Redis, Airflow, VMs self-hosted e integrações Bitbucket/Jira/Salesforce.
> São **aplicações propostas** a dores descritas — não uma afirmação de que o código atual já
> implementa cada padrão.
>
> **Ponto central:** você não precisa instalar 40 ferramentas. Vários padrões podem coexistir
> dentro do mesmo FastAPI e PostgreSQL.

## Índice

- [A. Organização do código e das regras de negócio](#a-organização-do-código-e-das-regras-de-negócio)
- [B. Eventos, consistência e organização dos dados](#b-eventos-consistência-e-organização-dos-dados)
- [C. Cache, capacidade e tolerância a falhas](#c-cache-capacidade-e-tolerância-a-falhas)
- [D. APIs, mudanças de arquitetura e releases](#d-apis-mudanças-de-arquitetura-e-releases)
- [E. Coordenação, disponibilidade e infraestrutura](#e-coordenação-disponibilidade-e-infraestrutura)
- [F. Integrações, processamento e controle dos fluxos](#f-integrações-processamento-e-controle-dos-fluxos)
- [Priorização por dor concreta](#priorização-por-dor-concreta)

---

## A. Organização do código e das regras de negócio

### 1. Modular Monolith — separar responsabilidades sem criar microsserviços

**O que é:** aplicação implantada como unidade, mas dividida em módulos com interfaces e
dependências controladas. Separar arquivos, sozinho, não garante modularidade.

**No MakersHub:** módulos como Agendamento, Distribuição de Leads, Carteira, Telefonia e KPIs.
Agendamento não altera diretamente as tabelas internas de Distribuição: chama uma operação
pública daquele módulo.

**Dor resolvida:** uma alteração no Super R1 deixa de exigir entender o backend inteiro. Reduz
conflitos entre devs e agentes trabalhando em funcionalidades diferentes.

### 2. Hexagonal — separar regras de negócio de HTTP, banco e integrações

**O que é:** a regra central conversa com interfaces; adaptadores implementam PostgreSQL,
Salesforce, HTTP ou testes. O domínio não depende diretamente dessas tecnologias.

**No MakersHub:** `SelecionarAssessorElegivel` recebe data da reunião, critérios e disponibilidade.
Pode ser chamada por FastAPI, uma rotina Airflow ou um teste sem iniciar navegador e Salesforce.

**Dor resolvida:** testar "suspenso hoje, disponível semana que vem" sem montar toda a
infraestrutura. Trocar uma integração não exige reescrever a regra de distribuição.

**Limite:** não significa criar uma interface para cada função; concentre a separação nas regras
relevantes e dependências externas.

### 3. Vertical Slice — organizar por funcionalidade completa

**O que é:** reunir o que muda junto para executar um caso de uso, em vez de organizar tudo
exclusivamente em camadas genéricas (controllers, services, repositories).

**No MakersHub:** a funcionalidade "Reagendar reunião" tem entrada, validações, operação,
contrato de resposta e testes claramente associados. Outra fatia: "Suspender assessor por período".

**Dor resolvida:** um PR deixa de espalhar alterações por dezenas de arquivos compartilhados. O
agente carrega o contexto da funcionalidade, não o backend inteiro.

**Diferença para o item 1:** o módulo organiza uma área; a slice organiza uma ação dentro dela.

### 4. DDD / Bounded Context — dar significado preciso aos conceitos

**O que é:** organizar modelos e regras conforme o negócio, delimitando onde cada conceito tem
determinado significado.

**No MakersHub:** "assessor ativo", "habilitado para determinada faixa" e "disponível no horário
solicitado" não deveriam ser o mesmo booleano. Para a suspensão, modelar **intervalo de
indisponibilidade** e uma **política de elegibilidade avaliada na data da reunião**, não apenas no
momento atual.

**Dor resolvida:** ambiguidades que viram bugs recorrentes. O pattern ajuda a expressar a regra
correta; **não substitui a validação dessa regra com o negócio**.

---

## B. Eventos, consistência e organização dos dados

### 5. Event-Driven Architecture — reagir a fatos sem acoplar tudo

**O que é:** componentes publicam acontecimentos e outros reagem, sem que o produtor execute
diretamente todas as consequências.

**No MakersHub:** uma gravação ficou disponível. O evento `GravacaoDisponivel` inicia transcrição,
atualização do histórico do cliente e geração de insights, sem que o componente que recebeu a
gravação aguarde tudo.

**Dor resolvida:** requisições demoradas e cadeias em que uma falha na IA interrompe o registro da
atividade.

**Cuidado:** o evento precisa ser **entregue de maneira recuperável** quando não pode ser perdido.

### 6. Pub/Sub — distribuir o mesmo acontecimento para interessados diferentes

**O que é:** um produtor publica e cada assinatura interessada recebe o evento. Não é a mesma coisa
que dividir uma tarefa entre workers.

**No MakersHub:** `LeadConvertido` interessa simultaneamente ao módulo de carteira, ao cálculo de
indicadores e às notificações.

**Dor resolvida:** acrescentar um novo consumidor sem modificar a rotina de conversão.

**Cuidado concreto:** **Redis Pub/Sub não guarda mensagens** para consumidores desconectados. Para
eventos críticos, precisa de persistência e confirmação (Redis Streams, broker durável), não
apenas `PUBLISH`.

### 7. Transactional Outbox — não perder a integração depois de salvar

**O que é:** salvar a mudança de negócio e a intenção de publicar um evento **na mesma transação**.

**No MakersHub:**

```
Transação PostgreSQL:
  registrar agendamento
  registrar evento na outbox
COMMIT
Depois:
  publicar/sincronizar com o sistema externo
```

**Dor resolvida:** o agendamento foi salvo, mas a aplicação caiu antes de atualizar o Salesforce.

**Importante:** não exige Kafka nem CDC. Um worker pode consultar a outbox. Ainda é necessário
tratar duplicação e ordenação quando ela importa.

### 8. CDC — perceber alterações independentemente de quem escreveu

**O que é:** capturar mudanças do banco, frequentemente a partir do log de transações (Debezium
usa decodificação lógica no PostgreSQL).

**No MakersHub:** tanto Airflow quanto FastAPI atualizam dados que alimentam indicadores. O CDC
detecta essas alterações sem depender de cada escritor lembrar de invalidar o cache.

**Dor resolvida:** atualizações fora da aplicação deixam de passar despercebidas.

**Limite:** detectar uma linha alterada **não** revela quais JOINs ou chaves Redis ficaram
inválidos. E um consumidor parado pode causar retenção de WAL e consumir disco.

### 9. Saga — coordenar uma operação que atravessa sistemas

**O que é:** sequência de transações locais com ações de compensação quando uma etapa necessária
falha. Não existe rollback global.

**No MakersHub:** reservar horário no MakersHub + confirmar reserva em sistema externo; uma falha
definitiva externa pode exigir liberar a reserva local.

**Critério importante:** falha no aviso do Teams **não** deveria cancelar uma reunião válida. Uma
etapa acessória pode ser apenas retentada. Defina o que é **obrigatório, compensável ou
irreversível**.

### 10. Idempotency — repetir uma operação sem repetir seu efeito

**O que é:** reconhecer tentativas repetidas da mesma operação e impedir efeitos adicionais. Uma
chave identifica a intenção original, permitindo recuperar seu resultado.

**No MakersHub:** o webhook de encerramento de ligação chega duas vezes — usar o identificador do
evento do provedor para não cadastrar duas atividades. O navegador repete "Agendar" porque a
resposta se perdeu — o servidor devolve o agendamento já criado.

**Dor resolvida:** duplicidades por retries, webhooks repetidos e cliques duplicados.

**Distinção para KPIs:** se uma R1 aparece duas vezes porque um **JOIN multiplicou linhas**,
idempotência não resolve — corrija a granularidade e as relações da consulta.

### 11. CQRS — separar o modelo de alteração do modelo de consulta

**O que é:** modelos e operações diferentes para comandos e consultas. **Pode continuar tudo no
mesmo PostgreSQL**; outro banco e mensageria não são obrigatórios.

**No MakersHub:** `AgendarReuniao` valida e grava. "Carregar agenda do assessor" consulta uma
representação preparada para a tela. Nos KPIs, a escrita mantém fatos detalhados; a leitura usa
agregados por assessor, período e segmento.

**Dor resolvida:** tentar fazer uma única estrutura servir para transações complexas e dashboards
rápidos.

**Cuidado:** uma projeção atrasada pode servir para indicadores, mas **não deve decidir sozinha se
um horário está disponível**.

### 12. Event Sourcing — reconstruir o estado pelo histórico

**O que é:** os eventos são a fonte de verdade; o estado atual é derivado deles. **Não** é
simplesmente acrescentar logs ou manter tabela de auditoria.

**Aplicação possível:** `LeadDistribuido → ReatribuicaoManual → AssessorSubstituido`, permitindo
reconstruir quem era responsável em determinado momento.

**Dor resolvida:** investigação histórica e reconstrução de estado.

**Avaliação:** aplicar apenas onde a reconstrução é requisito central. Suas dimensões SCD2 **não**
tornam o sistema automaticamente event-sourced.

### 13. Materialized Views / Projections — calcular uma vez, consultar muitas

**O que é:** persistir resultados derivados para não repetir o cálculo completo a cada leitura.

**No MakersHub:** métricas diárias por assessor, captação por período ou segmentação de contas, em
vez de rodar os mesmos JOINs pesados a cada abertura do dashboard.

**Dor resolvida:** latência e pressão repetitiva sobre PostgreSQL.

**Limite:** `REFRESH MATERIALIZED VIEW CONCURRENTLY` mantém consultas disponíveis durante a
atualização, mas exige índice `UNIQUE` compatível. **Não** transforma o refresh em atualização
incremental nem elimina seu custo de processamento.

---

## C. Cache, capacidade e tolerância a falhas

### 14. Cache Aside — consultar o cache antes do banco

**O que é:** a aplicação procura no cache; se não encontrar, consulta a fonte e armazena.

**No MakersHub:** KPIs de um assessor em determinado período. A chave precisa representar filtros
e o **escopo de acesso** que alteram o resultado.

**Dor resolvida:** usuários repetindo a mesma consulta cara.

**Limites:** chave incompleta devolve dados de outro filtro/contexto. E cache-aside **não** garante
funcionamento durante queda do PostgreSQL — se faltar a chave, a página ainda falha.

### 15. Refresh Ahead — renovar antes que o usuário encontre o cache vencido

**O que é:** atualizar antecipadamente entradas relevantes, evitando que a próxima leitura pague o
custo completo.

**No MakersHub:** um job renova os recortes mais acessados de KPIs/carteira antes de expirarem,
chamando a função de leitura diretamente.

**Dor resolvida:** "o primeiro usuário espera muito; os seguintes carregam rápido".

**Cuidado:** preservar a última versão válida quando a renovação falhar, numa política explícita de
desatualização. Registrar a **data dos dados de origem**, não só a hora do Redis. Não pré-calcular
todas as combinações de filtros.

### 16. Circuit Breaker — parar de insistir numa dependência quebrada

**O que é:** após um padrão de falhas, bloquear novas tentativas por um período e permitir testes
controlados de recuperação.

**No MakersHub:** Salesforce indisponível — em vez de cada requisição esperar um timeout longo, a
integração é interrompida temporariamente e as operações pendentes ficam identificadas.

**Dor resolvida:** dependência externa consumindo conexões e tempo até prejudicar funções que
poderiam continuar.

**Diferença por operação:** leitura de indicadores pode aceitar dados antigos; uma verificação
obrigatória no merge gate **deve continuar bloqueando**. Circuit breaker não é autorização para
ignorar validação.

### 17. Retry + Backoff + Jitter — repetir sem tempestade

**O que é:** repetir falhas transitórias com esperas crescentes, aleatoriedade e limites.

**No MakersHub:** agente recebe indisponibilidade temporária do Jira; task Airflow perde conexão;
integração recebe rate limit.

**Dor resolvida:** falhas ocasionais deixam de exigir intervenção manual.

**Cuidado:** retries no proxy, cliente HTTP e Airflow **multiplicam** as tentativas. Defina qual
camada é responsável. Repetir escrita exige idempotência. Em Python, **Tenacity**.

### 18. Bulkhead — impedir que carga pesada afete todo o sistema

**O que é:** separar recursos para limitar o alcance de falha/sobrecarga (processos, containers,
filas, pools de conexão).

**No MakersHub:** a rota pesada capaz de elevar muito a memória não deveria competir sem limites
com agendamento e operações interativas. Workers e limites próprios para exportações, processamento
analítico e Chrome.

**Dor resolvida:** um relatório pesado derrubar páginas e agendamentos.

**No Airflow:** pools limitam concorrência, mas **não substituem** isolamento de memória entre
processos/containers.

### 19. Backpressure — produzir no ritmo que o sistema absorve

**O que é:** a capacidade do consumidor controla quanto trabalho recebe. Consumidores por pull e
lotes limitados são mecanismos comuns.

**Nos agentes:** muitos PRs para revisar — os workers retiram trabalho conforme liberam capacidade,
em vez de abrir uma execução de IA por PR imediatamente.

**Dor resolvida:** crescimento descontrolado de memória, processos, chamadas de modelo e conexões.

**Diferença de "colocar uma fila":** a fila precisa de política de capacidade, atraso e admissão.
Guardar trabalho indefinidamente só adia a saturação.

### 20. Rate Limiting — controlar volume por intervalo

**O que é:** limitar a taxa por usuário, credencial, integração, etc. Em Python, **`limits`**.

**No MakersHub:** limitar chamadas de todos os agentes ao Jira/Bitbucket e impedir que um lote de
enriquecimento consuma a capacidade reservada para operações interativas.

**Dor resolvida:** esgotamento de quotas e uso desproporcional.

**Diferença de backpressure:** rate limiting controla a **taxa**; backpressure controla o **fluxo
conforme capacidade**. Em várias VMs, um limite global não pode viver só na memória de cada processo.

---

## D. APIs, mudanças de arquitetura e releases

### 21. API Gateway — centralizar entrada e políticas transversais

**No MakersHub:** usar a camada de entrada para organizar acesso ao Next.js, FastAPI e endpoints de
integrações, evitando expor cada serviço.

**Dor resolvida:** configuração de acesso, roteamento e proteção repetida inconsistentemente.

**Limite:** o gateway valida identidade geral; a FastAPI ainda decide se aquele usuário pode
acessar determinada conta ou executar uma distribuição. **Regra de negócio não migra para o proxy.**

### 22. BFF — entregar à interface exatamente o que ela precisa

**No MakersHub / Call Sprint:** a resposta reúne dados do lead, histórico recente e info da tela, em
vez de o React coordenar várias chamadas independentes.

**Dor resolvida:** telas com excesso de requisições, carregamentos desencontrados e transformação de
dados espalhada pelos componentes.

**Regra:** manter elegibilidade e gravação na FastAPI. O BFF **compõe e adapta**; não cria segunda
implementação das regras.

### 23. Strangler Fig — substituir o legado por partes

**No MakersHub:** refatorar o agendamento sem reescrever tudo — primeiro a consulta de
disponibilidade; depois a seleção do assessor; por último outras operações.

**Dor resolvida:** refatorações que ficam meses sem entregar e exigem troca arriscada.

**Cuidado:** comparar resultados antigo/novo em **modo somente leitura** é útil. Executar os dois
caminhos de **escrita** e criar duas reservas **não é**. Cada operação precisa de um responsável
inequívoco pela gravação.

### 24. Expand / Contract — mudar contratos sem quebrar consumidores

**No MakersHub:** substituir um campo de responsável por uma modelagem com closer e banker:
`adicionar estrutura → publicar código compatível → preencher histórico em lotes → migrar APIs/DAGs
→ validar → remover campo antigo`.

**Dor resolvida:** backend, frontend e Airflow precisarem entrar no ar no mesmo instante.

**Aplicação a Bitbucket/Jira:** dependências de PR passam a representar fases de compatibilidade
verificáveis, não só uma ordem informal de merges.

### 25. Blue/Green — manter a versão anterior pronta durante a troca

**No MakersHub:** subir nova versão de Next.js/FastAPI, verificar autenticação e fluxos críticos,
então trocar o tráfego.

**Dor resolvida:** deploy com interrupção e rollback que exige reconstruir a versão anterior.

**Limites:** custo de capacidade simultânea; sessões/contratos compatíveis. Voltar o tráfego **não
desfaz** migração destrutiva de banco.

### 26. Canary — expor uma mudança a uma parcela controlada

**No MakersHub:** liberar mudança no fluxo de distribuição para um grupo controlado e acompanhar
erros, latência, conflitos de agenda e sucesso efetivo.

**Cuidado específico:** medir só HTTP 200 é insuficiente — o algoritmo pode responder 200 e escolher
o **assessor errado**. As métricas de aprovação precisam incluir **resultados de negócio**.

### 27. Feature Flags — separar deploy de ativação

**No MakersHub:** publicar uma nova regra de pulling desligada e ativá-la para uma equipe específica.
Se houver problema, interromper novas utilizações sem outro deploy.

**Dor resolvida:** depender de deploy emergencial para desativar uma funcionalidade.

**Limites:** desligar a flag **não desfaz** distribuições já efetuadas. Não substitui autorização.

---

## E. Coordenação, disponibilidade e infraestrutura

### 28. Leader Election — escolher quem exerce determinada função

**No MakersHub:** definir qual PostgreSQL está autorizado a atuar como primário em HA.

**Distinção importante:** o Airflow permite **múltiplos schedulers** coordenados por locks no banco
de metadados. Não é preciso adicionar eleição própria via etcd.

### 29. Distributed Lock + Lease + Fencing — impedir ações concorrentes e atrasadas

**O que é:** o lock dá exclusividade; a lease limita sua validade; o fencing rejeita um executor
antigo. **O recurso protegido precisa validar o token.**

**Nos agentes:** o agente A assume um PR e trava durante uma chamada de modelo; sua autorização
expira; B assume e conclui; depois A retorna tentando publicar uma decisão antiga.

**Dor resolvida:** dois agentes se considerarem responsáveis pelo mesmo trabalho.

**Cuidado:** expiração no Redis, sozinha, **não impede** a ação atrasada. O caminho de escrita
precisa rejeitar a versão antiga; decisões de review precisam estar vinculadas ao SHA analisado.

### 30. Replication — manter outra cópia operacional

**No MakersHub:** proteger o banco de negócio **e** o banco de metadados do Airflow. Workers
redundantes não resolvem indisponibilidade do metadata DB.

**Limites:** replicação **não é backup**; exclusões incorretas também replicam. Leituras críticas de
disponibilidade de agenda não deveriam depender de réplica atrasada. Duas VMs no mesmo host não
protegem contra a perda do host.

### 31. Sharding — repartir os dados entre bancos

**Para você:** o tamanho de banco não justifica sharding — ele complicaria justamente os JOINs e
indicadores consolidados. Investigue **consultas, índices, agregados, particionamento e réplicas**
antes. Particionar tabelas no mesmo PostgreSQL **não é** sharding.

### 32. Consistent Hashing — distribuir sem remapear tudo

**Para você:** aproveitar dentro de ferramenta madura (ex.: anéis do Loki), **não** desenvolver um
algoritmo próprio para o MakersHub agora.

### 33. Optimistic Concurrency — impedir sobrescrita silenciosa

**O que é:** atualizar somente se a versão do registro ainda for aquela que o cliente leu.

**No MakersHub:** dois gestores abrem o mesmo lead na versão 7. Um altera (v8). A tentativa do
segundo com v7 é rejeitada.

**Cuidado para agendamentos:** versionar o **lead** não impede dois leads diferentes de ocuparem o
mesmo horário. Essa exclusividade precisa estar protegida no **recurso compartilhado** (constraints
no PostgreSQL).

### 34. WAL — registrar alterações para recuperação

**O que é:** o PostgreSQL registra alterações no log **antes** de gravar as páginas de dados.

**No MakersHub:** recuperar o banco após queda e, com backup-base + arquivamento de WAL, restaurar
para um momento anterior a uma operação destrutiva.

**Importante:** WAL já faz parte do PostgreSQL — não é camada nova da aplicação. **Recuperação para
um instante específico** exige cadeia válida de backups + WAL, não apenas "ter WAL habilitado".

### 35. Sidecar — acompanhar a aplicação com processo auxiliar

**No Airflow:** o Helm Chart oferece integração com `git-sync` para disponibilizar DAGs — o
sincronizador cuida do Git enquanto os componentes do Airflow fazem suas funções.

**Limite:** um sidecar por réplica também consome recursos. Para coleta de logs, um coletor por nó
pode ser mais adequado.

### 36. Service Mesh — padronizar a comunicação entre serviços

**Para você:** **não** adotaria apenas por usar Kubernetes. Mesh não corrige queries, não torna
PostgreSQL HA e não substitui idempotência. Precisa resolver uma dificuldade operacional concreta
(identidade entre serviços, mTLS, políticas de rede).

---

## F. Integrações, processamento e controle dos fluxos

### 37. Anti-Corruption Layer — traduzir sistemas externos para seu modelo

**O que é:** uma camada que impede que conceitos/contratos de um sistema externo determinem o modelo
interno. A tradução é **semântica**, não só troca de nomes.

**No MakersHub:** converter campos e estados do Salesforce para conceitos canônicos. Um `OwnerId`
externo não deveria ser tratado automaticamente como a identidade interna de um assessor. No Jira,
o adaptador resolve campos diferentes por tipo de issue, entregando um contrato consistente.

**Dor resolvida:** mudanças/peculiaridades externas se espalharem por dezenas de módulos.

### 38. Competing Consumers — vários workers dividindo uma fila

**O que é:** workers compartilham o trabalho; cada mensagem é atribuída a um consumidor por
tentativa. Pode haver reentrega → **não elimina** a necessidade de idempotência.

**No Airflow:** `CeleryExecutor` distribui tasks entre workers prontos, que podem consumir filas
específicas (uma para curtas, outra para tarefas com Chrome/dependências pesadas).

**Para suas tasks de 15–40s:** workers prontos merecem avaliação; não há obrigação de migrar tudo
para KubernetesExecutor.

### 39. Dead Letter Queue — separar falhas que precisam de tratamento

**No MakersHub:** um webhook de lead chega com formato inválido. Em vez de ser perdido ou retentado
infinitamente, fica preservado com payload, identificação, erro e tentativas.

**Dor resolvida:** "alguns leads sumiram e ninguém sabe quais", ou mensagens problemáticas
consumindo processamento.

**Distinção:** uma task Airflow marcada como `failed` **não** constitui automaticamente uma DLQ com
capacidade de recuperação.

### 40. State Machine — tornar explícitas as transições permitidas

**O que é:** definir estados, eventos e condições que permitem uma transição.

**Nos agentes/PRs:** `Em análise → Bloqueado por dependência → Revisado → Aguardando aprovação →
Apto para merge`. Um novo commit pode invalidar "Revisado" (aprovação estava vinculada ao SHA
anterior). Não basta `approved=true`.

**Dor resolvida:** flags contraditórias, etapas puladas e decisões antigas tratadas como atuais.

**No MakersHub:** também serve para agendamento e tutoriais guiados. Porém, a máquina no React
**não substitui** validação no backend nem persistência durável do processo.

---

## Priorização por dor concreta

Ordem de investigação baseada nas dores relatadas — **não** uma recomendação de adotar todos os
padrões simultaneamente:

| Dor concreta | Padrões relacionados | Primeiro resultado a buscar |
|---|---|---|
| Agendamento e distribuição incorretos | 4, 10, 33, 40 | Regras por data, transições válidas e proteção contra concorrência |
| KPIs lentos ou inconsistentes | 11, 13, 14, 15 | Granularidade correta, consultas preparadas e cache com atualização controlada |
| Integração fica incompleta após salvar | 7, 10, 17, 39 | Nenhuma intenção de integração perdida; recuperação rastreável |
| Tasks e agentes saturam as VMs | 18, 19, 20, 38 | Concorrência limitada e isolamento de cargas pesadas |
| PRs dependentes e alterações que quebram DAGs | 3, 24, 27, 29, 40 | Compatibilidade entre versões e decisões vinculadas ao código realmente analisado |
| PostgreSQL indisponível interrompe tudo | 28, 30, 34 (+ 14–16) | Recuperação do banco e continuidade parcial testada |

> **A distinção mais importante:** se o algoritmo verifica apenas o primeiro assessor, falta
> corrigir a **regra e a busca**; se duas requisições reservam o mesmo horário, falta **proteção de
> concorrência**; se a reunião foi salva mas não sincronizada, falta **confiabilidade de
> integração**. São três problemas diferentes — não se resolvem instalando o mesmo framework.
