# S1 — Páginas redigidas para revisão

S1 concluiu a autoria de seis tutoriais e de um guia. O estado é `AUTHORED_FOR_REVIEW`; não há aceite independente neste recibo. A raiz conserva ownership de índices, `_meta.js`, `coverage.json`, `packet.json` e da compilação integrada.

A escrita ocorreu no worktree `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`, branch `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. Foram reutilizados `authoring-contract.md` e os deltas `l1a-coverage.md`, `l1b-nextra.md` e `l1c-labs.md`. A rota foi warm reuse do especialista S1; nenhum subagente foi despachado por S1 nesta fase.

## Páginas

- `content/tutoriais/idempotency.mdx`. SHA-256: `210373c740ca4f7cfab7101c695e29439e63ce37038e33f7dc5d59bd3119938b`.
- `content/tutoriais/outbox.mdx`. SHA-256: `dbdd3a555486f0f957b893192d5d40d38667fe3ae68771866f3259e18969df09`.
- `content/tutoriais/optimistic-concurrency.mdx`. SHA-256: `f8de20c0e3249b2bcf075f4cc4765581f810feff6e3a94f4430d1e5ae3f580ec`.
- `content/tutoriais/read-projection.mdx`. SHA-256: `5821c113f9b8fa07790b34a8efa0748742d024b4e6ce5ec49bc4a194aea63fd7`.
- `content/tutoriais/single-flight.mdx`. SHA-256: `11cabe78ebcfe33c953413f7b56b2ead6bf090f42fd781b666dabe0be5dcadcc`.
- `content/tutoriais/state-machine.mdx`. SHA-256: `2b174b3488d04994be136f1d4652dae9baff8c964c4bfc508bce6695a62db985`.
- `content/guias/investigar-impacto.mdx`. SHA-256: `6a936ddbbe4b3fe330ddc1654b3c8520f103d61bd18144b769e9507b8a70324c`.

Os tutoriais oferecem uma experiência local com pré-requisitos, cinco passos, código completo, saída esperada, observação do resultado, Mermaid didático e links aos capítulos do mapa. Os seis assuntos são idempotência, retomada de envio com deduplicação, conflito de versão, atualidade de uma projeção, busca compartilhada com cancelamento isolado e transição de estado condicionada. O sexto script usa o papel inglês `specialist`; seu resultado mantém os mesmos quatro casos do auxiliar.

O guia começa pelo termo de negócio no FazGraph, consulta o impacto de um nó identificado, orienta a consulta agregada PostgreSQL em leitura e termina com a verificação de chave, grão e cardinalidade. Ele usa os recibos de 14/10/2026: `557731` linhas e chaves distintas; `43` tabelas, `424` cards e `27` endpoints no snapshot do grafo de 13/10. Preserva também período, sinais e limites da soma. Foram consumidos `evidence/bootstrap.md`, `evidence/postgres-inflow.json` e o pacote S4; o caminho citado no despacho como bootstrap/postgres-inflow.json resolve, neste worktree, para evidence/postgres-inflow.json.

## Verificação sintética

- [2026-10-14 17:01:47 UTC] seis MDX locais — extração dos fences Python, execução por `exec(compile(code, str(path), "exec"), {})` com stdout em memória e comparação literal → `6/6 OUTPUT_MATCH True`; cinco headings numerados e um fence Mermaid em cada tutorial.
- [2026-10-14 17:01:47 UTC] interpretador local — `sys.version.split()[0]` → `3.14.8`.

A execução leu somente os arquivos das seis páginas e usou a biblioteca padrão. Ela não acessou banco, rede, Redis, Salesforce, Airflow ou arquivos de cliente e não criou scripts auxiliares no checkout. Todos os registros dos laboratórios são fictícios. As saídas conferidas são:

### `content/tutoriais/idempotency.mdx`

```text
first=OWN created=reservation-01
repeat=HIT replay=reservation-01
changed=MISMATCH 422: key reused with another payload
business_effects=1
```

### `content/tutoriais/outbox.mdx`

```text
commit order-01=confirmed outbox=event-01
delivery attempt=1 event=event-01
consumer=applied event=event-01
publisher=crashed before marking outbox sent
delivery attempt=2 event=event-01
consumer=duplicate-ignored event=event-01
outbox=sent event=event-01
delivery_attempts=2 applied_effects=1
```

### `content/tutoriais/optimistic-concurrency.mdx`

```text
editor-a-read=version:7
editor-b-read=version:7
editor-a-save=saved version=8
editor-b-save=conflict expected=7 actual=8
stored=version:8 text:approved
```

### `content/tutoriais/read-projection.mdx`

```text
source-commit=evt-01 amount=10
projected-through=evt-01 total=10
source-commit=evt-02 amount=5
dashboard=10 source=15 cursor=evt-01
projected-through=evt-02 total=15
dashboard=15 source=15 cursor=evt-02
```

### `content/tutoriais/single-flight.mdx`

```text
producer-started=1
cancelled-reader=CancelledError
surviving-readers=4 value=rows-1
producer-started=2
early-refresh-read=rows-1
refreshed-read=rows-2
producer-calls=2
```

### `content/tutoriais/state-machine.mdx`

```text
unsupported-target=invalid-edge state=IN_CONTACT
operator-result=blocked-specialist-only state=IN_CONTACT
specialist-without-reason=needs-reason state=IN_CONTACT
specialist-with-reason=accepted state=PENDING
```

## Limites e próximo gate

Os dados de banco e de linhagem são evidências históricas dos pacotes da raiz. S1 não repetiu consultas de produção nem transformou o snapshot em uma afirmação sobre consumidores ativos hoje. As fontes de código MakersHub são de checkout; os mecanismos simulados não são certificados como garantias universais do produto.

A conferência sintética não prova transação SQL, durabilidade real após encerramento de processo, coordenação entre workers, autorização no servidor ou ausência de atraso no relatório de produção. Os limites aparecem nas páginas correspondentes. A compilação MDX integrada, os links no site final, a sintaxe e renderização Mermaid e a revisão independente ficam para os gates da raiz. Autoria e execução sintética não constituem self-approval.
