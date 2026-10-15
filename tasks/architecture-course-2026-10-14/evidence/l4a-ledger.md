# S4 — Ledger curto de consistência

Este registro usa os 17 itens do `prepared-council/packet.json`, capturados em `2026-10-14T17:03:36Z`, e os recibos descritos em `s4-consistency.md`. Os trechos do MakersHub pertencem ao checkout `main@e233fb046ec333982cd1547171b0f0bd8d8d92ee`, lido em 14/10/2026; não afirmam o estado atual do serviço. Os links OSS são referências de implementação para comparação, não prova de dependência ou implantação local.

O agregado PostgreSQL medido às 16:08 UTC registrou 4.771 linhas `done` em `_idempotency_key` e 2.574 linhas no recorte D1. Essas contagens descrevem linhas e estados locais; não provam que cada efeito ocorreu no Salesforce, que ocorreu uma só vez, ou que todas as sincronizações terminaram.

## 1. Claim, replay e `request_hash` — Idempotency

**Antes.** Se o navegador repetir a mesma solicitação depois de perder a resposta, a API pode executar o pedido outra vez. A mesma chave também pode chegar com outro corpo e devolver um resultado que não pertence à nova solicitação.

**Depois.** O código tenta inserir uma chave composta por escopo, usuário e chave idempotente, guardando `request_hash`. Em uma repetição, o serviço compara a solicitação registrada e pode recuperar o estado e a resposta persistidos. Isso dá à aplicação uma identidade local para reconhecer uma repetição. O pacote não fixa o status HTTP de uma chave que chega com outro hash.

**Custo.** O serviço precisa gravar a chave, o hash, o estado, a resposta e o prazo de retenção; também precisa definir o que responde quando a mesma chave chega com outro hash.

**Limite.** A chave coordena a API e o PostgreSQL. Ela não controla sozinha o Salesforce. Se o Salesforce concluir a atualização e o processo cair antes de persistir `finish`, uma tentativa posterior ainda pode repetir o efeito externo; veja o segundo quadro.

```mermaid
sequenceDiagram
    participant Client as Navegador
    participant API as API
    participant DB as PostgreSQL
    participant SF as Salesforce
    Client->>API: Envia chave K e pedido P
    API->>DB: Tenta inserir K e request_hash(P)
    DB-->>API: Novo claim ou registro existente
    alt Mesmo K e mesmo hash, com resposta pronta
        API->>DB: Lê estado e resposta persistidos
        DB-->>API: Retorna a resposta anterior
        API-->>Client: Reproduz o resultado
    else Mesmo K com hash diferente
        API-->>Client: Trata a chave como incompatível; resposta conforme contrato
    else Novo claim
        API->>SF: Aplica a atualização externa
        SF-->>API: Atualização concluída
        Note over API,DB: Uma queda antes de finish deixa a conclusão local incerta
    end
```

Evidência: `backend/app/services/idempotency_store.py:70-120` no pacote preparado; resumo S4, linhas 27 e 55, delimita o hash, o reclaim e o `finish`. Implementação comparativa: [Temporal](https://github.com/temporalio/temporal), para estudar execução durável e identidade de workflow; não tratar isso como garantia de idempotência do Salesforce.

## 2. Lease, UUID do owner e `finish` — Inbox como comparação

**Antes.** Um worker pode ficar parado além da lease. Outro worker assume a linha e termina o trabalho; o primeiro pode voltar depois e tentar gravar uma conclusão antiga.

**Depois.** O reclaim troca `owner_token`, e `finish` só atualiza enquanto o token recebido ainda for o owner e o estado continuar `in_progress`. Assim, o worker antigo não consegue finalizar a linha local depois que outro assumiu.

**Custo.** O serviço precisa de expiração, caminho de reclaim, geração e conferência de ownership em cada atualização final. Mensagens repetidas também pedem deduplicação no consumidor, como uma Inbox que grava o ID recebido junto com o efeito local.

**Limite.** O UUID prova ownership nesta linha do PostgreSQL. O Salesforce não recebe nem confere um contador monotônico; portanto, o UUID não é fencing global e não oferece Exactly Once entre os dois sistemas.

```mermaid
sequenceDiagram
    participant A as Worker A
    participant B as Worker B
    participant DB as PostgreSQL
    participant SF as Salesforce
    A->>DB: Claim com UUID-A e lease
    A->>SF: Atualiza owner
    SF-->>A: Sucesso
    Note over A,SF: A cai antes de gravar finish
    B->>DB: Lease expirada; reclaim com UUID-B
    B->>SF: Repete a atualização
    SF-->>B: Resultado externo
    B->>DB: finish condicionado a UUID-B
    A->>DB: Retorna e tenta finish com UUID-A
    DB-->>A: Nenhuma linha atualizada
    Note over DB,SF: A guarda é local; não cerca o efeito já aceito pelo Salesforce
```

Evidência: `backend/app/services/idempotency_store.py:70-120, 127-214`, conforme o resumo S4. Implementação comparativa de Inbox e detecção de duplicatas: [Eventuate Tram Core](https://github.com/eventuate-tram/eventuate-tram-core). A referência ajuda a estudar deduplicação do consumidor; não transforma a lease local em fencing remoto.

## 3. Mudança de responsável e `sf_owner_sync_pending` — Outbox

**Antes.** Se o serviço grava o novo responsável no PostgreSQL e chama o Salesforce na mesma sequência síncrona, uma falha de rede pode deixar os dois sistemas com responsáveis diferentes ou apenas parte dos quatro objetos atualizada.

**Depois.** `_apply` grava o novo responsável e `sf_owner_sync_pending=TRUE` no mesmo `UPDATE`, condicionado ao responsável anterior esperado. A tarefa de lote `sync_absence_reassignments` usa essa intenção para sincronizar Opportunity, Account, Contact e Event na ordem conhecida pelo serviço.

**Custo.** O Salesforce pode ficar temporariamente atrasado. A operação precisa de tentativas, visibilidade de falha e reconciliação para que o trabalho pendente não desapareça.

**Limite.** A flag funciona como sinal durável de trabalho a sincronizar. Ela não é um histórico imutável e completo de eventos: não guarda necessariamente cada mudança, versão e dado para reconstruir o estado. O trecho mostra a gravação da flag e a tarefa que a consome; não prova o resultado de cada atualização remota.

```mermaid
sequenceDiagram
    participant App as Serviço de reatribuição
    participant DB as PostgreSQL
    participant Job as Lote de sincronização
    participant SF as Salesforce
    App->>DB: UPDATE owner para B e pending=TRUE se owner ainda é A
    DB-->>App: Uma linha alterada ou corrida perdida
    DB-->>App: Owner e intenção ficam registrados no mesmo UPDATE
    Job->>DB: Busca sincronizações pendentes
    Job->>SF: Atualiza Opportunity e Account
    SF-->>Job: Atualizações aceitas
    Job->>SF: Atualiza Contact e Event
    SF--xJob: Falha de rede antes de concluir o lote
    Note over DB,Job: A intenção precisa continuar recuperável; limpeza e retry exigem verificação própria
```

Evidência: `backend/app/services/absence_reassignment_service.py:337-418`, hash `4d6cab0034db33fcdbc908f9fdb048a01e17adc1eb31020f65cba967d479d370`, conforme `pending-intent-code`. Implementação comparativa de Outbox: [EventSourcing.NetCore](https://github.com/oskardudycz/EventSourcing.NetCore). O link é material de estudo, não sinal de que esta aplicação use um event store.

## 4. `FOR UPDATE SKIP LOCKED` — Competing Consumers

**Antes.** Dois workers podem ler as mesmas linhas `PENDING` quase ao mesmo tempo e gastar esforço no mesmo lead.

**Depois.** A consulta seleciona linhas com `FOR UPDATE SKIP LOCKED` e, na mesma instrução, muda o estado para `BOT_PROCESSING` e devolve os IDs claimados. Enquanto um worker mantém as linhas travadas, o outro pula essas linhas e pode pegar trabalho diferente.

**Custo.** O banco coordena os workers por meio de locks e transações. Lotes longos mantêm locks por mais tempo e deixam menos trabalho disponível a outros workers.

**Limite.** O trecho prova a consulta de claim e a transição de estado; não informa quantos workers rodam, nem prova recuperação de linhas que ficam `BOT_PROCESSING` após uma queda. Uma fila durável ou política de recuperação exige evidência separada.

```mermaid
sequenceDiagram
    participant W1 as Worker 1
    participant DB as PostgreSQL
    participant W2 as Worker 2
    W1->>DB: Claim até N linhas PENDING
    DB-->>W1: IDs A e B; linhas ficam BOT_PROCESSING
    W2->>DB: Claim até N linhas PENDING com SKIP LOCKED
    DB-->>W2: Pula A e B; devolve IDs C e D
    W1->>W1: Processa A e B
    W2->>W2: Processa C e D
    Note over W1,DB: Queda depois do claim pode deixar estado sem recuperação demonstrada
```

Evidência: `backend/app/repositories/lead_pipeline_repository.py:485-515`, hash `6f3bd65cf9a401ddae83b8a4c78d7a8196a0f1e3a6207d3a9847b574d04cdaa3`, conforme `competing-claims-code`. Implementação comparativa de roteamento e consumidores concorrentes: [Watermill](https://github.com/ThreeDotsLabs/watermill). A ligação é conceitual; não afirma que o MakersHub usa Watermill.
