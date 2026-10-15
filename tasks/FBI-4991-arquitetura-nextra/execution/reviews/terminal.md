# Auditoria terminal da FBI-4991

**PASS_FOR_PROTECTED_SITE_AND_DRAFT.** A auditoria não encontrou um HIGH novo no recorte congelado do curso, do download e do worker. O pacote permanece **PARTIAL**, e a Story deve permanecer **In Progress**. O parecer permite avançar para a publicação protegida já autorizada e para a verificação pública pelo principal; ele não encerra os critérios de histórico, catálogo ou council documental completo.

O revisor foi `/root/terminal_delivery`, com runtime nativo `default`, modelo explícito `gpt-6.1-sol`, esforço `xhigh` e contrato `adversarial-review`. A fonte auditada foi `623ae1d3d34143df53c571327a508de47ab58951`; o checkout independente de Sites estava em `1677c81236d3588736e88597e9589d942b655a25`. Os arquivos rastreados estavam sem alteração. Artefatos locais não rastreados preexistentes foram preservados. O mandato inline e o perfil da execução delimitaram a auditoria porque este checkout não contém um arquivo original de pedido em `.harness/requests` nem o scanner da harness.

| Recorte | Contrato e evidência conferidos | Resultado |
| --- | --- | --- |
| Senha e arquivos privados | O worker verifica o cookie assinado antes do único `COURSE_ASSETS.get`. HTML, Next, Pagefind, RSC e ZIP usam esse caminho. O manifesto omite `static`, e `dist` contém somente o manifesto e o servidor. | 13 grupos de sondas passaram. A retirada do gate anônimo e a retirada do gate de origem foram detectadas. |
| Sessão e uploads | Cookie `__Host`, `Secure`, `HttpOnly`, `SameSite=Lax`; expiração de oito horas, invalidação por troca da senha ou segredo, origem de POST e bearer administrativo separado. | Cookies adulterados, sessões vencidas ou futuras, destinos inválidos, corpos excedentes e falhas de R2 foram recusados. Repetição após falha e logout funcionaram. |
| Download | O ZIP foi extraído em pasta nova sem Git. Os 98 arquivos do manifesto coincidem com o checkout, e os locks foram instalados nessa extração. | Os 16 runners passaram. O recibo marcou `base_sha=null` e `UNVERSIONED_SOURCE_SNAPSHOT`. |
| Jornada e conteúdo | Os hashes dos 181 MDX e a projeção de `content/` para Sites foram reconciliados. As 18 jornadas têm 90 destinos com os quatro vínculos de navegação entre páginas. As 15 mudanças de tutorial alteram somente a frase de instalação do TypeScript. | O verificador encontrou 7.894 links e zero links locais inválidos. Ele preserva `REVIEW_REQUIRED`; sintaxe e links não equivalem a aprovação pedagógica. |
| Curadoria | A matriz `ee53aae70c2edf9256dc0b56660993b05283b0b1db028b6f738343764aa3313b` foi ligada aos julgamentos reais. As 51 rechecagens preservam as outras 259 decisões; as 12 correções de licença preservam os 310 fingerprints de mecanismo. | 375 controles passaram, com zero HIGH e zero julgamento independente pendente na curadoria. A auditoria não refez a pesquisa semântica já aprovada. |
| Histórico e aceite | Os exports foram descomprimidos e verificados novamente pela allowlist. | Permanecem 12.697 commits e 595 classificações: 7 causas sustentadas por código, 290 somente relatadas, 35 sem evidência causal e 263 não aplicáveis. Esses números não encerram o histórico integral. |

O Chrome real, em uma fixture local com credenciais sintéticas e R2 substituído, abriu o formulário, recusou a senha errada, aceitou a tentativa seguinte, carregou JavaScript privado e encerrou a sessão. O recibo está em [terminal-worker.json](terminal-worker.json). As sondas cobrem os consumidores do gate comum, retiram duas proteções para conferir a detecção e simulam falhas de leitura e escrita para conferir a recuperação. Nenhuma afirmação sobre valores atuais do banco de produção depende desses dados sintéticos.

Os recibos hospedados foram reconciliados como capturas do principal. O arquivo original `private-fixed-verification.json` conserva **FAIL** por duas mensagens genéricas de console, com `failures=[]` e `pageErrors=[]`. Ele contém 1.397 recusas anônimas, 1.397 corpos autenticados cujo SHA corresponde ao export atual e mais 1.397 recusas após aquecer o cache. O diagnóstico seguinte identificou somente `POST /login 401` para a senha errada, `GET /favicon.ico 401` antes da sessão e `GET /favicon.ico 404` após autenticar. Login correto, busca, abertura do caso do Airflow e logout passaram. Isso sustenta o gate funcional privado; a verificação posterior à mudança de audiência ainda pertence ao principal.

Os 94 diagramas conservaram os hashes de fonte e de PNG. Eu também li os kernels e inspecionei os PNGs de três explicações: a comissão duplicada por granularidade, a revisão obsoleta com `xmin` e o retry histórico de `55P03`. Esses três desenhos correspondem ao recorte explicado, com seus limites preservados. O recibo [terminal-diagrams.json](terminal-diagrams.json) registra os três julgamentos. Os outros 91 receberam conferência de integridade, sem novo parecer semântico terminal. O pacote continua com `reviews=[]`; não foram criadas aprovações por documento a partir de contagem ou hash.

O contrato dos cookies foi conferido na [documentação oficial do Hono](https://hono.dev/docs/helpers/cookie) e na implementação instalada de Hono 4.13.13. O limite de stream e o checksum do upload foram comparados com os contratos oficiais de [FixedLengthStream](https://developers.cloudflare.com/workers/runtime-apis/streams/transformstream/) e [R2PutOptions](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/). O Context7 foi chamado e respondeu que a cota mensal terminou. O build mantém esbuild 0.28.2 em dependências isoladas.

## Recibos desta execução

- [2026-10-15 18:00:39 UTC] checkout principal da tarefa — `git rev-parse HEAD` → `623ae1d3d34143df53c571327a508de47ab58951`.
- [2026-10-15 18:03:53 UTC] fixture local do worker — `node tasks/FBI-4991-arquitetura-nextra/execution/reviews/terminal-worker.mjs` → `{"verdict":"PASS","checks":13,"mutations":2,"browser":true,"sourceSha256":"3afee5efd34af4dbc9e8b6b50f031b6f6b09b325e4a1b9ee0b8e2010414cf825"}`.
- [2026-10-15 18:06:43 UTC] ZIP extraído em diretório temporário sem Git — `python3 tasks/FBI-4991-arquitetura-nextra/execution/reviews/terminal-download.py` → `"files_verified": 98`, `"verdict": "PASS"`, `"runners": 16`, `"base_sha": null`.
- [2026-10-15 18:11:26 UTC] fontes congeladas e recibos locais — `python3 tasks/FBI-4991-arquitetura-nextra/execution/reviews/terminal-integrity.py` → `{"verdict": "PASS_WITH_DECLARED_DELIVERY_GAPS", "curation_concepts": 310, "guard_checks": 375, "documents": 181, "diagrams": 94, "journeys": 18, "history_commits": 12697, "fbi_issues": 595, "packet_status": "PARTIAL"}`.
- [2026-10-15 18:12:20 UTC] checkout principal da tarefa — `git status --porcelain --untracked-files=no` → saída vazia.
- [2026-10-15 18:13:29 UTC] read-back dos arquivos de captura privada e dos 1.397 arquivos locais de `out/` — reconciliação registrada em `terminal.json` → `"private_export_sha_matches": 1397`, `"overall_packet": "PARTIAL"`.

O verificador do curso foi executado a partir de uma cópia terminal que adapta somente a raiz do repositório e a pasta permitida para o relatório. Os validadores de curadoria e histórico tiveram apenas o destino de escrita dos recibos redirecionado. Os hashes e comandos estão em [terminal.json](terminal.json) e [terminal-integrity.json](terminal-integrity.json).

## Backlog sem nova rodada

**B1 — MEDIA, REAL.** O export não contém `favicon.ico`, e a captura hospedada registra 404 depois do login. Falta o ícone da aba; leitura e navegação funcionam. Acrescentar o ícone no próximo ajuste visual autorizado.

**B2 — MEDIA, REAL.** O empacotador em `hosting/build_lab_bundle.py:12` percorre todos os arquivos de `labs/` e exclui `.venv` e `__pycache__`, mas não exclui `node_modules`. A instalação recém-executada confirma que o lock dos labs cria esse diretório. Uma futura regeneração depois de `npm ci --prefix labs/architecture` pode incluir dependências no download. O ZIP congelado atual contém os 98 arquivos de fonte verificados. Excluir `node_modules` na próxima manutenção do empacotador.

O catálogo continua como lacuna declarada no pacote, com a proposta fora do escopo autorizado de escrita. A cobertura causal integral e o council completo dos documentos também permanecem abertos. Este parecer não estabelece merge ou implantação do MakersHub ou do Airflow.

ADVERSARIAL-VERIFICATION: SATISFEITO

GAPS-CRITICOS-DO-RECORTE-TERMINAL: 0

PLACAR: 2 reais não bloqueantes | 0 HIGH novo | limites de entrega preservados

PROXIMO PASSO: O principal pode publicar o site protegido conforme a opção B aprovada e conferir o acesso público, mantendo a Story em andamento e o pacote PARTIAL.
