# Taxonomia de problemas em sistemas distribuídos

> O Dual Write é apenas um sintoma do problema clássico de **Atomic Broadcast** e **Falhas
> Parciais**. Os problemas fundamentais dividem-se em 7 categorias estruturais.

```
                               SISTEMAS DISTRIBUÍDOS
                                          │
 ┌───────────────┬────────────────┬───────┴────────┬────────────────┬──────────────┐
 │               │                │                │                │              │
Tempo &         Consenso &       Consistência &   Rede &           Concorrência   Mensageria &
Ordem           Coordenação      Replicação       Falhas           Distribuída    Entrega
```

---

## 1. Tempo e ordem dos acontecimentos

- **Ausência de tempo global unificado:** não existe relógio físico perfeito compartilhado. O NTP
  sofre com *clock drift*, *clock skew*, pausas de GC e virtualização.
- **Incapacidade de determinar ordem causal:** dois nós gerando timestamps locais produzem
  inconsistências ou sobrescritas indevidas (*Last-Write-Wins* destrutivo).
- **Soluções:** Relógios Lógicos de Lamport, Relógios Vetoriais, Relógios Lógicos Híbridos (HLCs,
  usados em CockroachDB e Spanner).

## 2. Consenso e coordenação

- **Teorema FLP** (Fischer-Lynch-Paterson): impossível alcançar consenso determinístico em sistema
  assíncrono se ao menos um nó puder falhar por parada (*crash*).
- **Teoremas CAP e PACELC:** sob partição (**P**), escolhe-se Consistência (**C**) ou
  Disponibilidade (**A**). Sem partição (**E**), equilibra-se Latência (**L**) ou Consistência (**C**).
- **Split-Brain:** nós perdem comunicação e ambos acreditam ser o líder, aceitando escritas
  conflitantes.
- **Falhas Bizantinas (BFT):** nós que não apenas caem, mas enviam dados corrompidos/maliciosos.

## 3. Consistência e replicação de dados

- **Linearizabilidade vs Serializabilidade:** a primeira lida com tempo real de leituras/escritas
  de um único registro; a segunda com transacionalidade multi-registros. Alcançar ambos (*Strict
  Serializability*) custa latência alta.
- **Anomalias de consistência eventual:**
  - **Violação de Read-Your-Writes:** usuário salva e o refresh bate numa réplica com *replication
    lag* — não vê a própria alteração.
  - **Violação de Monotonic Reads:** leituras sucessivas batem em nós com atrasos diferentes,
    fazendo o tempo "voltar".

## 4. Falhas de rede e falhas parciais

- **Indeterminação de estado (o Triângulo da Morte):** ao sofrer timeout, o chamador não sabe se
  (a) a requisição nunca chegou; (b) o servidor caiu processando; (c) teve sucesso mas a resposta
  se perdeu.
- **Falhas Cinzentas (*Grey Failures*):** o nó não morreu (healthcheck passa), mas a latência
  subiu para 10s ou há 1% de perda de pacotes, degradando o cluster silenciosamente.
- **Quedas em Cascata (*Cascading Failures*):** um nó falha, o tráfego migra para os sobreviventes,
  que sobrecarregam e caem em sequência.

## 5. Concorrência distribuída e perda de isolamento

- **Perda de isolamento em Sagas e workflows:** alterações parciais visíveis (Dirty Reads
  distribuídos) → exige Semantic Locks e atualizações comutativas.
- **Lost Updates distribuídos:** dois nós leem X=5 e gravam X+1 → resulta 6 em vez de 7.
- **Deadlocks distribuídos:** Nó A reserva recurso local e espera lock no Nó B, e vice-versa.

## 6. Integridade de mensagens e fluxo de dados

- **Impossibilidade do Exactly-Once físico na rede:** toda comunicação opera em At-Least-Once (com
  retries) ou At-Most-Once (sem retries). O "exatamente uma vez" é **abstração lógica** dependente
  de deduplicação e idempotência.
- **Poison Pill Messages:** mensagens malformadas que quebram o consumidor em loop e travam o
  pipeline.
- **Esgotamento de memória por falta de Backpressure:** produtores rápidos afogam consumidores
  lentos → saturação de filas e OOM.

## 7. Degradação operacional e desvio de schema

- **Dual Writes de Schema (Contract Drift):** migrações com campos renomeados quebram consumidores
  em versões antigas durante deploys contínuos.
- **Thundering Herd:** milhares de instâncias acordam simultaneamente para invalidar/preencher a
  mesma chave de cache quando ela expira → derrubam o banco de suporte.

---

## Mapa: problema → padrão de resolução

| Categoria do problema | Desafio técnico central | Padrão/Arquitetura de resolução |
|---|---|---|
| Integração Banco ↔ Broker | Dual Write, perda de mensagens | Transactional Outbox, CDC, Event Sourcing, Listen-to-Yourself |
| Transações multi-serviços | Falta de transação ACID global | Saga (orquestrada/coreografada), TCC |
| Ordenação sem relógio global | Drift de NTP, sobrescrita destrutiva | HLC, Version Vectors, Lamport Timestamps |
| Consenso e eleição de líder | Split-brain, partição de rede | Raft, Multi-Paxos; quóruns (R+W>N) |
| Timeout indeterminado | Retries gerando duplicidades | Idempotency Keys, Transactional Inbox, Dedup Table |
| Falta de isolamento global | Dirty Reads e Lost Updates em Sagas | Semantic Lock, Commutative Updates, OCC |
| Sobrecarga em cascata | Falha de uma dependência derruba tudo | Circuit Breaker, Bulkhead, Backpressure, Rate Limiting |
| Replication lag na leitura | Usuário não vê a própria escrita | Read-Your-Writes (roteamento ao primário) |
| Consumo concorrente seguro | Workers paralelos na mesma fila | Competing Consumers + leasing + fencing tokens |
| Falha de mensagem permanente | Poison pills travando partições | Dead Letter Queue, Exponential Backoff com Jitter |

---

Ver também:
- [Dual Write e alternativas](../consistencia/dual-write-e-alternativas.md)
- [Catálogo de padrões](../catalogos/catalogo-patterns.md)
