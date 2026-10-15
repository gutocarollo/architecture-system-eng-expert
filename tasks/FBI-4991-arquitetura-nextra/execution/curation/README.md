# Evidência da curadoria por conceito

Esta pasta conserva a matriz dos 310 conceitos e as fontes públicas que permitem conferir cada correspondência. O material de consulta do estudante está em `content/referencia/curadoria/`, com uma entrada pesquisável por conceito, e em `content/referencia/casos/`, com os contratos dos casos aplicados. O site usa essas páginas MDX e não precisa carregar a matriz JSON durante o build.

## Abra a matriz publicada

A publicação usa `matrix.json.gz` e `sources.json.gz` para respeitar o limite de tamanho do repositório. `matrix.publication.json` informa os tamanhos e os hashes do arquivo comprimido e do conteúdo original. Para restaurar a cópia de trabalho, execute na raiz do curso:

```sh
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/unpack_matrix.py
```

O programa consulta `publication-index.json` e confere os hashes antes de restaurar `matrix.json` e `sources.json`. Se já existir uma cópia diferente, ele pede que você a preserve ou use `--force` para restaurar explicitamente a versão publicada. Esses JSONs integrais são artefatos gerados locais; eles não devem ser publicados sem compressão.

## Confira o alcance de cada prova

A situação `AUTHOR_SOURCE_MATCH` registra uma correspondência proposta pelo autor, vinculada a código e licença. Ela não é uma aprovação independente. `PENDING` conserva uma lacuna e sua razão. Nenhum conceito recebe uma dispensa como não aplicável. A contagem de linhas, um HTTP 200 ou a presença de um nome no código não provam sozinhos a correspondência semântica.

`sources.json` conserva as revisões, os caminhos, os horários, os hashes e os trechos consultados. `revision-licenses.json` liga a licença à revisão do código. Quando o projeto declara a licença no cabeçalho do arquivo ou no manifesto do pacote, o recibo informa essa origem. Um rótulo ausente ou indefinido da API não é substituído por uma licença inventada.

`github-metadata.json` registra as estrelas dos repositórios nos horários indicados. `trending-monthly.json` conserva o universo de 22 cards da página mensal. O crescimento informado pela própria página e a diferença entre snapshots de 14 e 15 de outubro são medições distintas. Os recibos não tratam a diferença de algumas horas como crescimento de trinta dias.

## Reproduza a preparação

Os scripts abaixo leem fontes públicas e materializam os artefatos da curadoria. As consultas REST usam uma sessão já autenticada do GitHub CLI e não imprimem credenciais.

```sh
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/select_sources.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/harvest.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/license_revisions.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/normalize_license_proofs.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/sanitize_captures.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/build_matrix.py
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/reconcile_references.py
node tasks/FBI-4991-arquitetura-nextra/execution/curation/verify_reference_mdx.mjs
python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/verify_curation.py --require-complete
```

A coleta reutiliza os recibos de revisões já lidas. Uma atualização deliberada de popularidade ou de branch precisa gerar uma nova medição; o horário anterior não passa a representar o presente. `case_contracts.py` publica as referências dos casos a partir do registro e das saídas dos laboratórios, sem escrever nos programas ou nas fontes do MakersHub.

## Capturas sanitizadas e arquivos locais

A captura HTML da página mensal conserva somente o texto visível dos cards. Scripts, atributos de sessão, dados ocultos e valores de CSRF não integram a publicação. Duas linhas de comandos de autorização da documentação pública APISIX também foram sanitizadas. `sanitization-receipts.json` conserva a classificação, os hashes originais e os hashes dos arquivos sanitizados. Os valores de autorização não são repetidos no relatório.

Os hashes originais continuam permitindo confrontar a fonte remota na revisão indicada. Quando o arquivo publicado é sanitizado, `sha256` e `artifact_sha256` conferem os bytes publicados; `remote_sha256` e `original_artifact_sha256` conservam a proveniência do original. O arquivo sanitizado não é apresentado como cópia byte a byte da resposta remota.

Os arquivos `*-tree.json` e `*-tree.json.gz` são caches locais de descoberta e não precisam ser publicados. Os arquivos completos de código em `raw/` sustentam os recibos selecionados; os seus avisos de autoria e licença são preservados. O pacote `rare-support/` conserva as investigações delimitadas e suas incertezas, inclusive a distinção entre uma demonstração e uma aplicação real.

`verify_reference_mdx.mjs` compila os MDX de referência e confere seus links e âncoras contra a árvore atual de conteúdo. `verify_curation.py` confere os 310 IDs, os 40 prioritários, as revisões, os arquivos, os hashes, as licenças lidas e a restauração dos arquivos gzip. A opção `--require-complete` exige que não haja lacuna autoral aberta; `--require-independent` exige uma aprovação independente por conceito e permanece um gate separado. Um resultado estrutural positivo não substitui essa revisão.
