# Rechecagem do reparo DSEM2-H1

O reparo está aceito como **PASS_BOUNDED**. O diagrama 39 agora diz que o laboratório inicia cinco leitores e cancela um deles. Essa entrada corresponde a `run.py:26–29`, e a legenda identifica o cancelamento como condição injetada antes de comparar os corpos históricos.

O documento atual tem SHA-256 `e5c161c698269c733a11ef7740f36abbf2dd3abbf418e94652572cb0155b2bcd`. O corpo Mermaid tem SHA-256 `497912ccad79ccd0acace839ca7845c837aa830986ad86a283282b0969252d19`. O gerador canônico conserva o mesmo corpo, e somente a chave `single-flight-cancel` foi alterada. O recibo de parsing e renderização aponta para esses hashes; o PNG novo foi inspecionado.

O escudo da tarefa, a liberação pelo callback e os quatro leitores sobreviventes continuam sustentados pelos mesmos três arquivos fonte, cujos hashes permanecem iguais. Esta conclusão não estabelece nem nega cancelamento automático de uma requisição FastAPI quando alguém fecha uma tela. O fluxo continua sendo uma demonstração local controlada.

As outras 44 decisões permanecem aceitas. Seus corpos Mermaid coincidem com os da primeira revisão. Os diagramas 71 e 73 receberam somente o novo hash do documento compartilhado de read models, `8f29603bce6224121926258212263058d4e83b48234a4c5a8477ffae1ca4a42c`; o único hunk daquele documento modifica a seta do diagrama 72, que pertence à outra lane. Seus corpos e seus contextos de explicação permaneceram iguais.

- [2026-10-15T18:39:39.301757+00:00] worktree FBI-4991 — leitura de documento, gerador e fontes mais comparação SHA-256 → `diagram-39=PASS_BOUNDED`, `retained_bodies=44`, `document_rebindings=2`, `unresolved_high=0`.
- [2026-10-15T18:39:39.301757+00:00] mesmo worktree — leitura de `mermaid-semantic-repairs.json` e conferência do PNG → `syntax=PASS`, `render=PASS`, `png_sha256=438d78629860b4ce7bdb05062c2e8b0622e146ccdb80dfefa917fef95eec495a`.

A lane contém 45 aprovações com limites, zero HIGH e zero PENDING após incorporar este reparo. O revisor fica estacionado, sem solicitar outra rodada.
