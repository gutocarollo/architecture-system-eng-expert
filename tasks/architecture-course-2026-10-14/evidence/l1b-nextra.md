# L1B — Compatibilidade Nextra, MDX e Mermaid

## O que reutilizei

A matriz `evidence/coverage.json` já define 18 grupos, 374 ocorrências, 310 IDs canônicos, 40 prioridades e os caminhos planejados de cada item. Reusei esses IDs e caminhos como contrato do verificador. Também usei o parser MDX que a instalação Nextra já traz (`@mdx-js/mdx`), com `remark-frontmatter`, `remark-gfm` e `github-slugger`; não acrescentei dependências. A integração Mermaid documentada pelo Nextra já usa `@theguild/remark-mermaid`, então o verificador só inventaria os fences existentes e não cria outro renderer.

## Compatibilidade observada

A documentação oficial do Nextra mostra a rota `app/[[...mdxPath]]/page.jsx` com `generateStaticParamsFor` e `importPage`, o layout com `Layout`, `Navbar`, `Footer`, `Head` e `getPageMap`, e o `mdx-components` que importa `useMDXComponents` do tema. O scaffold local usa esses mesmos imports e contratos. As versões instaladas são Nextra e tema `4.6.1`, Next `16.4.0` e React `19.3.0`; os peer ranges locais do tema são Next `>=14`, React/React DOM `>=18` e Nextra `4.6.1`.

O Nextra aceita fences `mermaid` pela integração existente. Sua documentação permite arquivos `_meta.js` colocados junto às páginas e proíbe misturá-los com `_meta.global`. Na leitura de 16:29 UTC havia dois `_meta.js` locais e nenhum `_meta.global`, portanto essa convenção não colidia. A confirmação de compilação do site não foi feita.

## Verificador e limite da medição

`scripts/verify-course.mjs` usa `createProcessor` do MDX e percorre a AST para registrar páginas, links Markdown e `href` JSX literal, IDs de heading, fences Mermaid e suas posições. O manifesto atribui índice global, índice por página e SHA-256 do fence original. Links JSX dinâmicos falham como não verificáveis; a checagem de links cobre páginas `.md`/`.mdx`, não valores de `_meta.js`.

O script compara os 310 IDs e as 40 prioridades aos caminhos da matriz. Ele só marca `EXPLANATORY_SECTION_CANDIDATE` quando encontra um heading canônico e parágrafos de prosa fora de listas, tabelas e citações. A prioridade exige dois parágrafos, 60 palavras e headings com prosa para cada parte requerida. Esses critérios separam título/menção/lista de uma seção com explicação estrutural; não substituem revisão humana de semântica ou qualidade didática. O relatório final fica em `tasks/architecture-course-2026-10-14/artifacts/course-verification.json` quando o curso estiver completo.

## Colisão e estado de execução

Na medição inicial de 16:28 UTC ainda não havia diretório `content/`. Às 16:30 UTC o checkout tinha dois MDX (`content/index.mdx` e `content/explicacoes/index.mdx`) e dois `_meta.js`; a matriz ainda registra 310 conceitos, 40 prioridades e `written_pages=0`. Por isso não executei a verificação final nem gerei um artefato parcial. O verificador devolve `NOT_RUN` e código de saída 1 se não houver MDX; a análise completa deve rodar ao fim da autoria.

## Recibos locais

- [2026-10-14 16:28 UTC] Worktree — `pwd -P; git branch --show-current; git rev-parse HEAD` → `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`; `perfect-citizen-a30f5998`; `23d5d158d3a964dceba296296368ec14bcd8970b`.
- [2026-10-14 16:29 UTC] Worktree — `find content -type f | sort; find content -type f -name '*.mdx' | wc -l` → `content/_meta.js`; `content/explicacoes/_meta.js`; `content/explicacoes/index.mdx`; `content/index.mdx`; `2`.
- [2026-10-14 16:29 UTC] Node instalado — `node -e` lendo `node_modules/*/package.json` → `next 16.4.0; nextra 4.6.1; nextra-theme-docs 4.6.1; react/react-dom 19.3.0; @mdx-js/mdx 3.1.1; remark-gfm 4.0.1; remark-frontmatter 5.0.0; github-slugger 2.0.0; @theguild/remark-mermaid 0.3.0; mermaid-cli 11.12.0`.
- [2026-10-14 16:30 UTC] `coverage.json` — `node -e` selecionando `summary` e caminhos prioritários → `18 grupos; 374 ocorrências; 310 conceitos; 40 prioridades; written_pages=0; 40 caminhos prioritários distintos`.
- [2026-10-14 16:30 UTC] `scripts/verify-course.mjs` — `node --check scripts/verify-course.mjs` → saída vazia, código `0`. Não executei testes unitários nem o relatório de cobertura.
- [2026-10-14 16:30 UTC] `package.json`, `package-lock.json`, `next.config.mjs`, `mdx-components.jsx`, `app/layout.jsx`, `app/[[...mdxPath]]/page.jsx`, `coverage.json`, `s1-design.md` — `shasum -a 256` → respectivamente `7902bda6e87f71952a12b7670cd7115d75603153ae1364948274d48681740b56`, `eed847ee8f9c5edebc040d6f19532a25aff4834f6a744419fff75a80d5a30f09`, `47bc6e3f4b4139320d3bfb878b379a70ec81119677e21d2e3287a8ece03df4ed`, `ef9e47075361b51a667027501174d110041c5692929100b49244db71aaa0a2d0`, `03e3379a4209d7762d8f9d647b3517b5e84712bdce5cb3738bf71d25c096f361`, `b394674281e4e1d2b31693ff3467d4b6ed2250b4a980a36ab414e2f2de2c0aed`, `8f53d09722820fd9e5962ba225b01ca8e7c4f66b32a434c579e17defded8b914`, `f94147fe2ae1ba450e1c042d4eb86db8dde1cee69d4e952bca0e4bfc50caca56`.

## Fontes primárias consultadas

- [Nextra: Docs Theme e layout](https://nextra.site/docs/docs-theme/start)
- [Nextra: content directory e rota App Router](https://nextra.site/docs/file-conventions/content-directory)
- [Nextra: mdx-components.js](https://nextra.site/docs/file-conventions/mdx-components-file)
- [Nextra: metadados e exclusividade de `_meta.global`](https://nextra.site/docs/file-conventions/meta-file)
- [Nextra: integração Mermaid](https://nextra.site/docs/advanced/mermaid)
- [MDX: pacote e árvore MDAST/remark](https://mdxjs.com/packages/mdx/)
- [MDX: sintaxe de JSX, expressões e comentários](https://mdxjs.com/docs/what-is-mdx/)
