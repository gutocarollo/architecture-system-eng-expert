# Segunda partição da curadoria — FBI-4991

ADVERSARIAL-VERIFICATION: CORRIGIR
GAPS-CRITICOS: 31
PROXIMA-ACAO: corrigir as correspondências semânticas indicadas no JSON; depois devolver apenas os reparos altos a esta revisão aquecida.

A revisão julgou os 127 conceitos atribuídos, na matriz congelada `a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e`. O resultado é de 92 aprovações, 31 reparos de alta prioridade e 4 observações para backlog. Não restou conceito sem julgamento. A cada lote foi consultado o recibo da primeira partição; nenhum destes IDs tinha avaliação concluída para reaproveitar. A rota registrada é `native_type=default`, contrato independente REVIEW, `gpt-6.1-sol`, esforço `xhigh`.

## Reparos que mudam o aceite

O problema mais repetido está na base escolhida. `JpaRepository` implementa persistência por identidade; ele não implementa CDC, seleção entre armazenamentos, feature flags ou comparação de duas execuções. Isso afeta Aggregate, Aggregate Root, Branch by Abstraction, CDC Migration, Dark Launch, Dual Write Migration, Factory, Feature Flags, Parallel Run, Service Extraction e Transitional Architecture. Em vários desses itens a aplicação GitLab já demonstra o mecanismo e pode ser conservada; falta substituir a base. Database Decomposition e Expand Contract também têm aplicações úteis, mas sua única base Rails é um link de diretório sem captura da implementação.

Outras correspondências trocam o mecanismo solicitado por um vizinho. Centralized Logging aponta ao logger local do próprio Loki. Composite aponta apenas ao Visitor. Choreography aponta apenas ao publicador local de eventos. Distributed Tracing mostra spans sem a fronteira de propagação entre processos. Pipeline mostra uma etapa NiFi sem o encadeamento da aplicação. Domain Policy repete a entidade inteira sem identificar a regra. GraphQL Federation ainda não mostra planejamento e execução entre subgraphs. REST precisa do contrato dos recursos e métodos, além dos handlers HTTP.

O rebuilder Temporal restaura o histórico, mas os arquivos selecionados não mostram as transições de Finite State Machine e State Machine. O conceito GoF State também precisa demonstrar a delegação de comportamento ao estado. Recreate Deployment permite configurar uma estratégia e entrega RollingUpdate por padrão; falta a seleção real de Recreate e sua sequência de parada e início. Service Mesh precisa do caminho de controle que gera a configuração do proxy. Service-to-Service Identity precisa da identidade do workload e sua verificação. Zero Trust precisa da política por identidade e recurso. Template Method precisa de uma base que implemente o algoritmo e seus hooks. Token Exchange precisa de uma base de troca de subject token; o cliente selecionado demonstra o grant comum de authorization code.

Os 31 conceitos têm fonte, linhas, motivo e correção objetiva em `curation-second.concepts.json`. Os quatro itens de backlog são Batch Processing, Immutable Infrastructure, Modularization e Request ID. Eles têm um recorte demonstrável, mas precisam de localizadores ou limites mais precisos.

## Recibos desta leitura

- [2026-10-15 03:41 UTC] worktree `/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991` — `pwd && git branch --show-current` → `/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991` e `docs/FBI-4991-arquitetura-aplicada`.
- [2026-10-15 03:40 UTC] `execution/reviews/curation-second.close.py` — `python3 tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-second.close.py` → `127` julgamentos, `223` capturas próprias, `source_hash_errors: []`, `127` seções de referência e `reference_errors: []`.
- [2026-10-15 03:40 UTC] `curation-second.concepts.json` — SHA-256 → `1b767d48cfa0d4e6b0e664480fbd596ae0c4e07045a3b6c0608b1ae3579ac074`.

As 127 seções MDX preservam os mecanismos, os limites, os links de base/aplicação/skill e os destinos de aprendizagem da matriz. A comparação decodifica entidades HTML, como `Specification&lt;Client&gt;`, para não confundir escape MDX com divergência. Os recibos globais de licenças, metadados, arquivos gzip e vínculos prioritários da primeira revisão foram reutilizados. Esta partição não repete esses gates nem aprova execução, implantação ou produção.

PLACAR: 31 lacunas altas reais, 4 observações de backlog, 92 aprovações delimitadas.
