# Revisão independente da navegação e das contagens

**PASS_BOUNDED.** Não foi encontrado achado alto ou bloqueante no código e nos textos deste recorte. A aprovação cobre a implementação por fonte e a inspeção estática. A renderização, o build e a publicação continuam sendo os gates do orquestrador.

O revisor atuou como `default`, configurado com `gpt-6.1-sol`, esforço `xhigh` e contexto novo. O worktree é `wt-FBI-4991`, no branch `docs/FBI-4991-arquitetura-aplicada`, com base `83150a31c0d27f655b1160570aedd6c3e32e5d63` e diff atual. Os hashes dos doze arquivos principais estão no recibo JSON deste parecer.

## Aderência ao pedido

| Pedido | Evidência examinada | Resultado e limite |
| --- | --- | --- |
| Clicar no grupo da reserva deve abrir o caso. | Nextra 4.6.1 em `normalize.js:27`, `sidebar.js:68` e `sidebar.js:97`; frontmatter e `_meta` atuais da reserva; documentação oficial. | O índice vira a âncora do grupo e a seta continua controlando a expansão. O clique real cabe ao navegador. |
| A navegação deve aproveitar o comportamento do Nextra do MakersHub. | Fonte local `help-center/src/app/brand.css` no SHA `c1cf3e760473d2932d319c4b395af1bb73f5a497`; `app/course.css`. | O curso reaproveita largura de 100rem, TOC de 13rem, padding de 2rem, sidebar de 300ms, links de 250ms, rolagem nativa e redução de movimento. Isso não comprova paridade com a produção. |
| O título público deve ser exato. | Logo, metadata, título e H1 dos prioritários, label da referência; contrato `title.absolute` do Next.js. | O texto é “Arquitetura na prática: Makershub”; a página prioritária evita o sufixo repetido. O documento renderizado cabe ao navegador. |
| A tabela deve ganhar espaço sem corte. | CSS do curso, wrapper/Table nativos do Nextra e ausência de alteração em `mdx-components`. | A largura é maior e o scroll horizontal nativo permanece. A ausência de corte exige a medição renderizada. |
| Explicar 40, 310 e os casos com precisão. | Seis arquivos de dados com hashes conferidos, recomputação dos IDs e três textos públicos. | Há 40 temas ligados a 46 conceitos, 310 conceitos distintos, 15 casos principais, 17 famílias e 18 jornadas. O texto distingue observação, implementação e produção. |
| Evitar reabrir os outros documentos. | Comparação mecânica dos índices e objetos `_meta`. | Dos 119 índices alterados, 116 só recebem frontmatter; três têm os textos examinados. Os 26 `_meta` só removem `index`, além do título solicitado em referência. |

## Limites preservados

O mapa de aprendizado mantém 310 valores `independent_review: PENDING` e 238 valores `specific_pattern_implementation_gap: true`. Esses estados não foram convertidos em afirmação de implementação completa. O parecer não reabre as 310 correspondências com fontes OSS e não certifica execução dos exercícios ou comportamento em produção.

Não existem neste root os arquivos de request/scanner ou as pastas canônicas de arquitetura e design system procuradas pela skill. O objetivo foi reconstruído apenas do recorte original fornecido pelo orquestrador e do plano citado. A consulta de Nextra no Context7 funcionou; a consulta posterior de Next.js encontrou quota mensal e foi complementada pela documentação oficial. O código instalado fixa as versões exatas.

## Pendências baixas

A substituição do título deixou duas frases com concordância ruim: `Os [Arquitetura na prática: Makershub] ajudam` em `content/explicacoes/index.mdx` e `Consulte os [Arquitetura na prática: Makershub]` em `content/referencia/index.mdx`. A redação pode usar “A seleção ... ajuda” e “Consulte a seleção ...”. Isso não impede navegação nem altera contagens.

O README do recibo diz que o título da seção “Os quarenta prioritários” foi preservado, mas o texto atual usa o título solicitado. A busca restrita não encontrou referências à âncora antiga. Cabe corrigir a descrição do recibo quando ele for atualizado.

Três `_meta` de topo apresentavam `casos` antes de `index`. O mecanismo nativo promove o índice existente; este parecer não declara que todos os grupos preservam a primeira chave anterior do `_meta`.

## Recibos desta revisão

- [2026-10-17 03:32 UTC] `wt-FBI-4991` — inspeção Python registrada em `mechanical-inspection.json` → `"changed_index_files": 119`, `"index_metadata_only": 116`, `"missing_as_index": []`, `"mdx_components_changed": false`.
- [2026-10-17 03:32 UTC] `wt-FBI-4991` — inspeção Node registrada em `meta-inspection.json` → `"count": 26`, `"unexpected": []`, `"removed_index_count": 26`.
- [2026-10-17 03:33 UTC] `wt-FBI-4991`, arquivos JSON de cobertura/aprendizado/curadoria — recomputação de `priority_entries`, `concept_ids`, `concepts` e `case_id` → `"priority_themes": 40`, `"priority_unique_concepts": 46`, `"canonical_unique_concepts": 310`, `"learning_unique_concepts": 310`.
- [2026-10-17 03:32 UTC] `wt-FBI-4991`, `execution/learning/concept-matrix.json` — contagem de `independent_review` e `specific_pattern_implementation_gap` → `{'PENDING': 310}` e `{'True': 238, 'False': 72}`.
- [2026-10-17 03:33 UTC] `wt-FBI-5049` — `git rev-parse HEAD` e leitura de `help-center/src/app/brand.css:71-113,135-148` → `c1cf3e760473d2932d319c4b395af1bb73f5a497`; valores de largura/movimento citados acima.

Fontes oficiais: [Nextra, pasta com índice](https://nextra.site/docs/file-conventions/meta-file#with-index-page) e [Next.js, título absoluto](https://nextjs.org/docs/app/api-reference/functions/generate-metadata#absolute). A documentação pública de Next.js está na série 16.4 e a dependência local está em 16.4.0.

PLACAR: 0 altos ou bloqueantes; 2 ajustes baixos de texto/recibo; renderização pendente no orquestrador. Próximo passo: concluir build e navegador no mesmo diff antes de afirmar ausência de corte ou publicação.
