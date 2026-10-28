# Real-Time Trading Operations Platform

> Intraday position keeping, two-way trade reconciliation and a rules-driven exception engine on one Apache Ignite cluster, with a conflated live dashboard.

Three subsystems sharing one cluster, one Kafka broker and one dashboard:

| Subsystem | Question it answers | Computation | Storage decision |
|---|---|---|---|
| **Position Monitor** | *What do we hold?* | A **fold** — trades collapse into running per-`(account, security)` state | Store trade-derived state; value lazily |
| **Reconciliation** | *Does our book agree with the broker's?* | A **join** across two unbounded streams, with a timeout | Store raw records; **derive outcomes at read time** |
| **Exception Engine** | *Is anything wrong, and who is fixing it?* | A **filter + enrich** against reference data and rules | **Store the verdicts; discard the evaluations** |

The three storage decisions are genuinely different, and each is forced by the workload rather than chosen for consistency — see [Exception Engine](#exception-engine--how-it-works) for why the reconciliation approach is impossible there.

## Overview

Trading desks need to know their exposure *now*, not after an end-of-day batch. This service consumes a stream of trade executions from Kafka, folds each one into a running per-`(account, security)` position using weighted-average-cost accounting, revalues those positions against a live price feed, and pushes the result to a React dashboard several times a second.

It is built as a runnable demo with production-shaped architecture: the Ignite patterns that matter for this workload — affinity colocation, `EntryProcessor`-based atomic updates, and continuous queries — are used for real against a genuine two-node cluster, without the auth, persistence, and HA that would obscure them.

## Features

- **Atomic position updates** via Ignite `EntryProcessor`, executed on the node owning the key — no read-modify-write race under concurrent fills
- **Weighted-average-cost accounting** with signed quantities: long, short, and crossing through zero in a single code path
- **Lazy valuation** — a price tick costs one cache write regardless of how many positions hold the security
- **Conflated WebSocket feed** — outbound message rate is bounded by the clock, not by market activity
- **Exactly-once trade application** despite Kafka's at-least-once delivery
- **Affinity colocation by account**, so account-level rollups are local scans rather than cluster-wide scatter-gather
- **Manual controls** — inject arbitrary trades and force marks to drive the engine by hand
- **Node-failure resilience** — positions are backed up; a data node can be killed while the dashboard keeps updating

## Architecture

```
TradeSimulator ─┐
                ├─→ Kafka topic "trades" ─→ TradeKafkaConsumer
POST /api/trades┘         (keyed by account)        │
                                                    │ cache.invoke(key, PositionUpdateProcessor)
                                                    ▼
                                    positions cache — PARTITIONED, affinity = account
                                                    │
PriceSimulator ─┐                                   │ ContinuousQuery
                ├─→ prices cache — REPLICATED       ▼
POST /api/prices┘         │                   dirty PositionKeys
                          └──→ dirty symbols        │
                                     │              │
                                     └──────┬───────┘
                                            ▼
                            PositionPublisher — @Scheduled 250ms
                            expand symbols → keys, value, merge
                                            │
                                            ▼
                          STOMP /topic/positions/{account}, /topic/summary
                                            │
                                            ▼
                                    React dashboard
```

### Two design decisions worth knowing

**Fan-out asymmetry.** A trade touches one position; a price tick touches every position holding that security. The two are handled differently: trades go through an `EntryProcessor` on the owning node, while price ticks only mark a *symbol* dirty, deferring expansion into position keys to publish time. `Position` deliberately has no `marketValue` or `unrealizedPnl` field — those are computed on read by `PositionValuer`, so there is nowhere for a stale derived value to live.

**Conflation.** Ten securities ticking twice a second across fifty positions each produces ~1,000 cache events per second. Publishing each one would saturate the browser. `DirtyTracker` accumulates changes and `PositionPublisher` flushes a merged batch every 250ms, so a position touched fifty times in one window is sent once. The observed collapse ratio is exposed at `GET /api/stats`.

## Tech Stack

| Layer | Technology |
|---|---|
| Distributed cache | Apache Ignite 2.18.0 on JDK 17 (2 server nodes + 1 client node) |
| Backend | Spring Boot 3.5.3, Java 17 |
| Messaging | Apache Kafka 4.3.1 (KRaft mode — no ZooKeeper) |
| Push transport | STOMP over native WebSocket |
| Frontend | React 18, TypeScript 5.6, Vite 6, Zustand 5 |
| Build & runtime | Maven 3.9 and Docker Compose |

### Version constraints (these are not arbitrary)

| Constraint | Reason |
|---|---|
| **Ignite 2.18, not 3.x** | This design depends on `EntryProcessor`, `ContinuousQuery`, and `@AffinityKeyMapped`. Ignite 3 reshapes or drops these APIs. |
| **Java 17, in containers only** | Ignite 2.x cannot start on Java 22 — it relies on JDK internals sealed off after 17. The backend builds and runs entirely in JDK 17 containers so the host toolchain is never involved. |
| **`--add-opens` flags required** | Even on Java 17, Ignite fails at startup with opaque `InaccessibleObjectException` traces without them. Defined once as a YAML anchor in `docker-compose.yml` and shared by every JVM service. |
| **Never add `ignite-spring`** | It transitively pulls Spring Framework 5, which collides with Spring Boot 3's Spring 6 / `jakarta.*` namespace. Ignite is configured programmatically in `IgniteConfig.java`; `ignite-core` itself has no Spring dependency. |
| **Never add `ignite-indexing`** | It pins H2 1.4.197, which the Spring Boot BOM would silently upgrade to H2 2.x and break at runtime. This project uses no Ignite SQL — `PositionIndex` serves symbol lookups from an in-memory reverse index instead. |
| **Vite 6, not 7+** | Vite 7 requires Node ≥ 20.19. Vite 6 is the newest line declaring `^18.0.0` support. |
| **Ignite servers run a custom JDK 17 image** | `apacheignite/ignite:2.18.0` ships JDK 11. Peer class loading delivers this app's Java 17 bytecode (class file 61) to the data nodes, which a Java 11 JVM (max 55) cannot load — every trade fails with `UnsupportedClassVersionError` while the cluster looks healthy. `ignite/Dockerfile` lifts the Ignite distribution onto `eclipse-temurin:17-jre`. |

### Ignite gotchas this project hit (all fixed, all non-obvious)

| Symptom | Cause | Fix |
|---|---|---|
| `OutOfMemoryError` under a 1000/sec feed | A scan materialised the **whole cache** into a `List` before callers applied their `limit` — invisible at 50 groups, fatal at 24,000. An Ignite cursor is lazy; wrapping it in a list throws that away. | Stream the cursor with a visitor that can stop early, so `limit` bounds memory rather than only the response |
| `Failed to load peer class ... NoClassDefFoundError` on data nodes | Peer class loading covers **code** classes, not the **data** classes a cache holds | `withKeepBinary()` + named `BinaryObject` filters |
| Matching cost growing quadratically | The match key has no time component, so a narrow universe funnels a whole day's fills into a few groups, and the matcher scores a cross product per group (measured: 59 × 55 and climbing) | Widen the key space (`accounts-per-desk`, `synthetic-securities`), shorten the group TTL to 5 min, and add a `MAX_CROSS_PRODUCT` fallback |
| `No qualifying bean of type KafkaTemplate<String, Trade>` | Boot's `@ConditionalOnMissingBean(KafkaTemplate.class)` checks the **raw** type, so declaring a second template for another payload suppresses the default one | Keep the recon producer/consumer factories as private methods, and declare the trade template explicitly |
| `Work directory does not exist and cannot be created: /app/ignite/work` | `WORKDIR` creates the directory as **root**, but the image drops to a non-root user. Ignite needs a writable work dir. | `mkdir` + `chown` before the `USER` switch; work dir set via `RTPM_IGNITE_WORK_DIR` |
| Opaque Tomcat `400` on every acknowledge/resolve | The exception id travels in a **URL path** and used `\|` as its separator — not an allowed path character, so Tomcat rejects the request before Spring sees it | Separator changed to `~`, unreserved in RFC 3986 and needing no encoding |
| A rule that never fires, indistinguishable from a clean book | The price-deviation rule looked prices up by **CUSIP** while the price cache is keyed by **symbol**. Its null-guard then correctly skipped every trade — silently | Resolve the symbol via the security master first. Found by comparing injected counts against detected counts |
| `UnsupportedClassVersionError` on the data node, every trade failing | Server JVM older than the compiling JVM. Bytecode crosses the JVM boundary whenever an `EntryProcessor` is shipped. | Rebase the Ignite image on JDK 17 |
| `Failed to execute query ... filter=...$$Lambda$2561/0x00007f...` | **Lambdas cannot be peer-class-loaded.** `LambdaMetafactory` synthesizes them at runtime, so there is no class file to ship. | Use a *named* class for anything executed remotely — `AccountPositionFilter` |
| `ClassNotFoundException: com.rtpm.domain.PositionKey` on a scan query | Peer class loading covers **code** classes, not the **data** classes a cache holds. A filter taking deserialized types forces the server to load them. | Query via `withKeepBinary()` and filter on `BinaryObject.field(...)` |
| Symbol count silently 9 instead of 10 | A YAML map key containing a dot (`BRK.B`) is read by Spring's relaxed binding as a nesting separator, and the entry vanishes with no error. | Bracket notation: `"[BRK.B]": 445.20` |

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | Any recent | Must be **running** — the backend and infrastructure are containerised |
| Node.js | 18+ | The frontend runs on the host for fast HMR |
| Java / Maven | *not required* | Only needed to run the backend outside Docker |

Roughly 4 GB of free RAM for the container stack.

## Getting Started

### 1. Start the backend stack

```bash
docker compose up --build
```

This starts four services: two Ignite server nodes, a single-node Kafka cluster in KRaft mode, and the Spring Boot backend (which joins Ignite as a client node).

Wait for the cluster to form. In the Ignite logs you should see:

```
Topology snapshot [ver=3, locNode=..., servers=2, clients=1, ...]
```

`servers=2, clients=1` means both data nodes are up and the backend has joined.

### 2. Start the dashboard

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` and `/ws` to `localhost:8080`, so browser traffic is same-origin and no CORS configuration is needed.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `RTPM_IGNITE_ADDRESSES` | `127.0.0.1:47500..47509` | Comma-separated Ignite discovery addresses |
| `RTPM_KAFKA_BOOTSTRAP` | `localhost:9092` | Kafka bootstrap servers |
| `JAVA_TOOL_OPTIONS` | *(set by compose)* | Carries the Ignite `--add-opens` flags |
| `SPRING_PROFILES_ACTIVE` | — | Set to `docker` by compose |

Application settings live in `backend/src/main/resources/application.yml`:

| Key | Default | Description |
|---|---|---|
| `rtpm.publish.flush-interval-ms` | `250` | Conflation window. Raise for less bandwidth, lower for less latency. |
| `rtpm.simulator.trades-enabled` | `true` | Toggle synthetic trade flow |
| `rtpm.simulator.trades-per-tick` | `4` | Trades generated per interval |
| `rtpm.simulator.prices-enabled` | `true` | Toggle the simulated price feed |
| `rtpm.simulator.volatility` | `0.0015` | Per-tick standard deviation as a fraction of price |
| `rtpm.universe.accounts` | 5 accounts | The account universe |
| `rtpm.universe.symbols` | 10 securities | Symbol to seed price |

## Usage

### Inject a trade

```bash
curl -X POST http://localhost:8080/api/trades \
  -H 'Content-Type: application/json' \
  -d '{"account":"ACC-MACRO-01","symbol":"AAPL","side":"BUY","quantity":100,"price":50}'
```

### Watch a position cross through zero

The scenario the accounting is easiest to get wrong. Buy 100, then sell 150:

```bash
curl -X POST http://localhost:8080/api/trades -H 'Content-Type: application/json' \
  -d '{"account":"ACC-MACRO-01","symbol":"AAPL","side":"BUY","quantity":100,"price":50}'

curl -X POST http://localhost:8080/api/trades -H 'Content-Type: application/json' \
  -d '{"account":"ACC-MACRO-01","symbol":"AAPL","side":"SELL","quantity":150,"price":60}'
```

The position must end at **-50** (short), average cost **60**, realised P&L **+1,000** — booked on the 100 closing shares only. A result of +1,500 means P&L was booked on the full trade quantity, which is the classic bug.

The dashboard's **Scenarios** panel runs this for you, along with a duplicate-trade replay.

### Force a mark

```bash
curl -X POST http://localhost:8080/api/prices/AAPL \
  -H 'Content-Type: application/json' -d '{"price":55}'
```

Every position holding `AAPL` revalues within one publish window — without a single position being written.

## API Reference

### REST

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/positions?account=` | Valued positions; omit `account` for the firm-wide view |
| `GET` | `/api/summary` | Account-level P&L rollups |
| `GET` | `/api/universe` | Configured accounts and symbols |
| `GET` | `/api/stats` | Engine counters, including the conflation ratio |
| `POST` | `/api/trades` | Submit a trade → `202 Accepted` |
| `GET` | `/api/prices` | All known prices |
| `GET` | `/api/prices/{symbol}` | One price |
| `POST` | `/api/prices/{symbol}` | Force a mark |

`POST /api/trades` accepts an optional `tradeId`. Supplying the same id twice applies the trade once — the de-duplication guard that makes Kafka's at-least-once delivery safe.

### REST — reconciliation

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/recon/groups?account=&status=&limit=` | Evaluated groups with field-level breaks |
| `GET` | `/api/recon/summary` | Match rate and outcome counts |
| `GET` | `/api/recon/stats` | Engine counters plus what the generators deliberately injected |
| `GET` | `/api/recon/rules` | The active matching rule set |
| `PUT` | `/api/recon/rules` | Replace the rules — reclassifies everything, writes nothing |
| `GET` | `/api/recon/rules/options` | Available fields and comparison types |
| `POST` | `/api/recon/records` | Inject one record by hand → `202 Accepted` |
| `GET\|POST` | `/api/recon/generator` | Read or change feed rate and running state |

### WebSocket

Connect to `ws://localhost:5173/ws` (proxied) and subscribe:

| Destination | Payload |
|---|---|
| `/topic/positions` | All accounts |
| `/topic/positions/{account}` | One book only |
| `/topic/summary` | Account rollups; ticks every window, so it doubles as the heartbeat |
| `/topic/recon` | Conflated reconciliation groups |
| `/topic/recon/summary` | Match rate and counts; also the reconciliation heartbeat |

Frames carry a monotonic `sequence`, so a client can detect a missed frame and re-fetch the snapshot.

## Project Structure

```
RealTimePositionEngine/
├── docker-compose.yml            # 4 services + the shared --add-opens anchor
├── ignite/ignite-server.xml      # Ignite server node config (XML is fine here)
├── backend/
│   ├── Dockerfile                # multi-stage, JDK 17, non-root
│   └── src/main/java/com/rtpm/
│       ├── config/               # IgniteConfig, WebSocketConfig, KafkaConfig, properties
│       ├── domain/               # Position, PositionKey, Trade, Price, views, Decimals
│       ├── ingest/               # Kafka consumer, simulator, TradeController
│       ├── position/             # PositionUpdateProcessor ⭐, Valuer, Service, Index
│       ├── marketdata/           # PriceService, PriceSimulator, PriceController
│       └── publish/              # DirtyTracker, PositionChangeListener, PositionPublisher
└── frontend/src/
    ├── api/                      # REST client and STOMP feed
    ├── store/positionStore.ts    # Zustand, with per-row reference stability
    └── components/               # Grid, summary tiles, control panel
```

### Files worth reading first

| File | Why |
|---|---|
| `position/PositionUpdateProcessor.java` | The accounting engine — the core of the product |
| `publish/PositionPublisher.java` | Conflation, and the drain-before-read ordering |
| `config/IgniteConfig.java` | Cache topology and the partitioned/replicated trade-off |
| `store/positionStore.ts` | How unchanged rows avoid re-rendering |

## Testing

```bash
cd backend
mvn test
```

To run tests outside a container on a machine whose default JDK is not 17:

```bash
JAVA_HOME="/path/to/jdk-17" mvn test
```

The suite is split by what each layer can actually catch:

| Suite | Scope | Needs Docker |
|---|---|---|
| `PositionUpdateProcessorTest` | 17 cases of pure accounting arithmetic — opening, increasing, reducing, crossing zero both ways, multi-trade sequences. Millisecond feedback, no cluster. | No |
| `PositionValuerTest` | 7 cases covering valuation and P&L sign conventions for longs and shorts. | No |
| `PositionEngineIntegrationTest` | Real embedded Ignite node: `EntryProcessor` serialization, create-on-absent-key, trade de-duplication, snapshot valuation, and `@AffinityKeyMapped` colocation. | No |

The integration suite exists because the unit tests structurally cannot fail on the things that break in a cluster — they call `applyTrade` as a static method, so they would still pass if `PositionUpdateProcessor` were not serializable or if the affinity annotation were misspelled. Those defects only surface when a real cache is involved.

Its tests use JUnit *assumptions* rather than failures for the unimplemented position math, so the affinity and topology coverage keeps reporting instead of the whole class erroring out.

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
```

## Reconciliation — how it works

Two feeds are correlated in Ignite, compared under configurable rules, and classified as **Match**, **Break**, or **Missing**.

### The constraint that dictates the design

**You cannot hash on a tolerance-matched field.** If quantity matches within ±1 then 100 and 101 must pair, but they hash to different buckets — no key lookup could ever bring them together. So:

| | Fields | Role |
|---|---|---|
| **Match key** | `account`, `cusip`, `tradeDate`, `side` | Exact only. Forms the Ignite cache key |
| **Compared** | `quantity`, `price`, `settlementDate`, `currency`, `counterparty`, `tradeId` | Evaluated *after* pairing |

Tolerances never widen *what pairs up* — only whether a pair is a Match or a Break. Currency and counterparty are compared rather than keyed on purpose: keying them would turn a currency mismatch into two separate *Missing* records instead of one clearly-labelled *Currency Break*.

### Pairing is a search, not a lookup

With no trade ID in the key, the key is **not unique** — two same-day fills of one security share it. So each cache entry holds *lists* on both sides and matching becomes a small assignment problem, solved by **greedy best-fit**. Getting it wrong is not cosmetic: pairing a 100-share fill against a 500-share fill would fabricate two enormous breaks out of a clean match.

The scoring function deliberately **ignores the configured tolerances**. If widening a tolerance could change which records pair, a rule edit would silently reshuffle assignments and surface breaks on entirely different rows.

### Outcomes are derived, never stored

`ReconGroup` holds only raw records. Everything else — status, breaks, missing — is computed at publish time from the *current* rules. This is the same call as lazy valuation in the position engine, and it is why **changing a tolerance reclassifies every group in the cluster with zero cache writes**. It also means the sweeper needs no state: *Missing* is simply `unpaired && age > window`.

### Missing is a timeout, not an event

An unpaired record is initially just *early* — the feeds are asynchronous by design. It becomes `PENDING`, then `MISSING` once the window elapses, and reclassifies to `MATCHED` or `BREAK` if the counterpart arrives late. Crossing the window produces no cache event (nothing was written, time merely passed), which is the sole reason `ReconSweeper` exists.

### The broker feed's rate is not configured

Only `internal-per-second` is a setting. The broker rate *emerges* from the drop and phantom percentages — at 1000/sec with a 3% drop it lands near 970/sec. Configuring both independently would let the stated ratio drift from the discrepancy profile actually producing it.

## Exception Engine — how it works

Trades on `internal-trades` are enriched with reference data, evaluated against configurable rules, and — where a rule fires — raise a persisted exception with a severity, an owner queue and an SLA clock.

### Why this inverts the reconciliation design

Reconciliation stores nothing derived, which is what lets a tolerance edit reclassify the whole cluster with zero writes. **That is impossible here.** An exception acquires state no rule can regenerate — who owns it, whether it was acknowledged, when its SLA started. Recompute it and you erase the analyst's work.

Two consequences follow:

1. **Evaluation is synchronous on ingest.** The SLA clock starts at detection, so detection needs a definite instant.
2. **A rule change does not retroactively clear open exceptions.** An exception someone is working is a historical fact, not a stale projection — the opposite of the reconciliation behaviour, and correct for an ops workflow.

### The volume asymmetry

1000 trades/sec × 15 rules = **15,000 evaluations/sec**. Persisting each would write tens of millions of rows an hour, almost all PASS results nobody reads. Exceptions are written only when a rule *fires*; passes increment in-memory counters. **Write volume tracks problems, not traffic — so adding a rule costs nothing at steady state.**

### The SpEL evaluation context is a security boundary

Rules are editable over REST, so an expression is untrusted input. SpEL's default `StandardEvaluationContext` permits type references and arbitrary method calls, making `T(java.lang.Runtime).getRuntime().exec(…)` a working RCE payload. The engine uses `SimpleEvaluationContext.forReadOnlyDataBinding()`, which registers only a read-only property accessor.

That restriction has a direct design consequence: it also bans method invocation, so `quantity.multiply(price)` will not evaluate. Derived values are therefore **precomputed** onto `TradeContext` and read as plain properties:

```
#ctx.accountLimit != null and #ctx.notional > #ctx.accountLimit
```

The security constraint and the API ergonomics are the same decision. Expressions are validated by *executing* them against a probe trade at save time — parsing alone accepts `T(java.lang.Runtime)`.

### One exception per (trade, rule)

A trade breaching a counterparty rule and a limit rule raises **two** exceptions, routed to two queues and resolved independently. Collapsing them per trade would give one owner and one SLA clock to problems belonging to different teams — the credit desk closing their issue would close the risk desk's with it.

### Workflow transitions are atomic

`OPEN → ACKNOWLEDGED → RESOLVED`, enforced inside an Ignite `EntryProcessor`. Two analysts working the same queue and claiming the same exception is ordinary, not exotic: under a read-modify-write both would read `OPEN`, both would write `ACKNOWLEDGED`, and the second would silently overwrite the first. The processor makes exactly one win; the loser gets a `409`.

### SLA is durable, not derived

`slaBreached` is written once by `SlaMonitor` rather than computed from `now > slaDueAt`. Acknowledgement stops the clock, so a computed flag would silently *un-breach* an exception that genuinely did breach — quietly improving the SLA statistics by deleting the evidence.

## Status

Complete and verified running end-to-end. All 32 tests pass, and the full stack has been exercised against a live two-node Ignite cluster.

## Verification

Every step below has been run against the deployed stack, with the observed result recorded.

| # | Check | Observed |
|---|---|---|
| 1 | `docker compose up --build` | `Topology snapshot [ver=3, servers=2, clients=1, state=ACTIVE]` |
| 2 | `cd frontend && npm run dev` | Vite 6.4.3 on `localhost:5173`; `/api` proxy returns live data |
| 3 | Cross through zero — buy 100 @ 50, sell 150 @ 60 | `quantity -50`, `avgPrice 60`, `realizedPnl 1000.00` — booked on the closing portion only |
| 4 | Force a mark below a short's cost (60 → 55) | `unrealizedPnl +250.00`; at 70 it becomes `-500.00` |
| 5 | Lazy valuation | `lastUpdated` unchanged across both marks — the position was never written |
| 6 | `docker compose stop ignite-node-2` | Position intact from backup; `tradesApplied` kept climbing 702 → 966 through the node loss |
| 7 | `docker compose start ignite-node-2` | Rejoined: `ver=5, servers=2, clients=1` |
| 8 | `GET /api/stats` under full simulator load | `conflationRatio` ≈ **9.1** — about nine raw cache events collapsed per published frame |
| 9 | `mvn test` | **76/76 pass, 0 skipped** |

### Reconciliation

| # | Check | Observed |
|---|---|---|
| 1 | Tolerance boundary — qty 100 vs **101** (exactly ±1) | `MATCHED` |
| 2 | One past tolerance — qty 100 vs **102** | `BREAK`, reported as `QUANTITY 100vs102 dev=+2 tol=±1` |
| 3 | Multi-fill — 100/500 internal vs 500/100 external, reversed | Both `MATCHED`, **zero breaks** |
| 4 | Internal only | `PENDING`, then `MISSING_EXTERNAL` at 42s (window 30s) |
| 5 | **Live rule edit** — widen quantity ±1 → ±5 | `BREAK` → `MATCHED`, and `lastUpdatedAt` **byte-identical**: reclassified with zero cache writes |
| 6 | Restore rules ±5 → ±1 | Back to `BREAK` — reclassification works in both directions |
| 7 | **Throughput at target** | internal **1002/sec**, broker **973/sec**, frames **4.0/sec** — conflation holding, 0 publish failures |
| 8 | Broker/internal ratio | **96.5%** — *emerged* from the 3% drop + 1.5% phantom rates, never configured |
| 9 | All five break types firing | `QUANTITY 4084 · PRICE 4246 · SETTLEMENT_DATE 1881 · CURRENCY 985 · COUNTERPARTY 1496` |
| 10 | `docker compose stop ignite-node-2` at 1000/sec | Backend healthy, summary `HTTP 200`, ingestion climbed 74,904 → 105,075 straight through the node loss |
| 11 | Group size after the key-space fix | 3 × 3, down from 59 × 55 |

### Exception engine

| # | Check | Observed |
|---|---|---|
| 1 | Rules evaluate cleanly on live traffic | 34,425 evaluations, **0 errors**, 0.88% fire rate |
| 2 | Detected counts match deliberately injected counts | Unknown Security **30 vs 30**; settlement 48 vs 49; order-size 34 vs 39 |
| 3 | One exception per (trade, rule) | An oversize trade raises **two** — notional + order size — routed to one queue each |
| 4 | Queue routing by category | `ops-static-data` / `risk-desk` / `ops-settlements` |
| 5 | **Live reference data** — suspend GOLDMAN | `Inactive Counterparty` **0 → 249 in 25s**; already-raised exceptions untouched |
| 6 | Workflow | acknowledge `200` → second acknowledge `409` → resolve `200` → re-acknowledge `409` |
| 7 | **Concurrent claims** (integration test) | 8 simultaneous acknowledgements → **exactly 1 winner** |
| 8 | **SLA breach** with a 1-minute rule | 53 breached, `slaBreachesDetected` **exactly 53** — marked once each |
| 9 | **SpEL RCE rejected at save time** | `T(java.lang.Runtime)…` → `400 INVALID_RULE`, not stored |
| 10 | Rule edit is not retroactive | Widened threshold changes what fires next; open exceptions keep their frozen facts |
| 11 | All three subsystems coexist | positions 9.0× conflation · recon 84.4% match rate · exceptions live |
| 12 | `mvn test` | **121/121 pass, 0 skipped** |

## Known Limitations

- **No persistence.** Ignite runs in pure in-memory mode; positions are lost on full cluster restart. Enabling native persistence would be a `DataRegionConfiguration` change.
- **No authentication.** Every endpoint is open.
- **Single Kafka broker**, replication factor 1 — not durable against broker loss.
- **Exhausted Kafka records are logged, not dead-lettered.**
- **`PositionIndex` is per-instance.** Correct for the current design, but a second backend replica builds its own copy from its own continuous query.
- **Average-cost accounting only.** FIFO lot tracking would require positions to hold a lot collection.
- **Reconciliation group size is bounded by configuration, not by the algorithm.** The match key has no time component, so the number of distinct keys is exactly `accounts × securities × 2 sides`, and the matcher scores a cross product within each group. Two settings therefore govern matching cost quadratically: the generator's key space (`accounts-per-desk`, `synthetic-securities`) and the group cache TTL. A narrow universe or a long TTL turns matching quadratic — measured with 5 accounts, 10 securities and a 30-minute TTL, groups reached 59 × 55 records within minutes. A `MAX_CROSS_PRODUCT` ceiling in `ReconMatcher` degrades to linear sorted pairing rather than stalling, but it is a safety net, not the fix. A production system would add a time bucket to the key.
- **The reconciliation summary is recomputed rather than maintained.** It evaluates every group, memoised for one second. Correct by construction and immune to drift after a rule change, but O(all groups); the first thing to denormalise if the working set grows.
- **No Kafka end-to-end test.** A Testcontainers-backed test covering produce → consume → position would need a running Docker daemon; the Kafka path is currently exercised only by running the stack. `PositionEngineIntegrationTest` covers everything downstream of the consumer.
- **Exceptions are never archived.** Open exceptions are entities and deliberately have no TTL — expiring one would discard an analyst's work and quietly improve the SLA statistics by deleting the evidence. Resolved exceptions accumulate indefinitely; a production system would archive them out.
- **`CURRENT_USER` in the UI is hardcoded.** Acknowledgements are attributed to `ops.analyst`; a real deployment would take the owner from authentication.
- **Custom rules are not runtime-editable.** They are Java beans discovered at startup, so adding one requires a deployment — the honest trade for having the full power an expression cannot reach.
- **Price-deviation coverage is partial.** Only the ten named securities carry marks; the forty synthetic ones never tick, so the rule correctly skips them rather than guessing.

## License

Unlicensed demo project.
