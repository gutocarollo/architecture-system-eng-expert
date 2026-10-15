# S1 — Desenho pedagógico e cobertura do curso

Este desenho propõe uma trilha para entender decisões de arquitetura a partir de problemas que uma pessoa consegue reconhecer. O estudante acompanha um agendamento, uma consulta de indicadores e um processamento de tarefas. Primeiro percebe o que pode dar errado. Depois aprende o mecanismo que protege aquela parte do trabalho e o preço que essa proteção cobra.

O mapa foi produzido no worktree `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`, branch `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. A escrita de S1 pertence somente a este arquivo e a `coverage.json`. As páginas MDX ainda estão planejadas. Este inventário não demonstra implementação nem deploy de qualquer padrão no MakersHub ou no Airflow.

## O que podemos reutilizar

O catálogo original oferece uma taxonomia por nível arquitetural. Preservaremos cada label, grupo e posição, inclusive quando o mesmo conceito aparece em mais de um lugar. Seu grupo 18 é uma seleção dos outros grupos, acrescida do nome geral DDD; ele funciona como prioridade transversal e não como uma nova família de mecanismos.

O documento `docs/aplicado/aplicacao-makershub-40-patterns.md` oferece os problemas que abrem o curso: agendar na data correta, preservar uma integração após salvar, reduzir o custo de indicadores, limitar tarefas pesadas e invalidar uma revisão quando o código muda. O próprio documento apresenta esses casos como aplicações propostas. Eles podem motivar a aprendizagem; a descrição do que já acontece exige a evidência atual dos especialistas S2–S6.

Os textos de Outbox, Saga e consistência oferecem material de mecanismo, SQL, falhas e comparação. Eles devem ser repartidos por necessidade: a discussão de garantias vai para explicações; os contratos e campos vão para referência; a recuperação de uma operação vai para um guia; uma experiência controlada e repetível vai para um tutorial. Reproduzir esses arquivos inteiros em MDX conservaria a mistura atual de propósitos.

As onze pastas em `references/repos/` e o handbook oferecem código e documentação de terceiros. O manifesto registra seus READMEs com hash e mtime, além de menções textuais dos conceitos. Isso permite encontrar exemplos para leitura. Uma menção não comprova que a aplicação implementa o padrão da forma sugerida, e o inventário dos READMEs não é uma auditoria de todo o código vendorizado. Os frameworks e aplicações associados aos 40 padrões são declarações do catálogo; os auxiliares devem conferir versões, finalidade e relação concreta nas fontes oficiais.

O scaffolding Nextra atual pode ser reutilizado. `package.json` declara Nextra e seu tema em `4.6.1`, Next em `16.4.0` e React em `19.3.0`. A rota `app/[[...mdxPath]]/page.jsx` já chama `importPage`, `generateStaticParamsFor` e o wrapper de MDX. Esses números descrevem arquivos locais; instalação e compilação ainda exigem recibos próprios.

## Cobertura e limite do inventário

A matriz conserva 374 ocorrências: 334 nos grupos 1–17 e 40 na lista prioritária. Após reunir aliases explícitos, há 310 conceitos canônicos do catálogo. A matriz liga os 40 prioritários aos 40 itens do documento aplicado e às 40 linhas de frameworks e aplicações OSS. Quatro prioritários são combinações: DDD com Bounded Context, Materialized Views com Projections, Retry com Backoff e Jitter, e Distributed Lock com Lease e Fencing. Cada combinação aponta para seus mecanismos sem transformar todos eles em sinônimos.

O arquivo também registra 42 conceitos auxiliares. Alguns vêm de fontes do corpus, como isolamento, recuperação em um instante anterior, lock semântico e execução durável. Object Storage, dbt, scraping, n8n e Azure estão ligados ao pedido do usuário e aguardam provas dos seus especialistas. Esses itens adicionais não entram na conta dos 310 conceitos do catálogo.

Todos os estados de páginas neste mapa são `PLANNED`. As contagens `written_pages`, `reviewed_pages` e `rendered_pages` valem zero para o entregável de S1. O autor deve atualizar uma etapa somente quando houver um artefato daquela etapa, com caminho e hash. Cobertura de catálogo, existência de páginas, qualidade pedagógica e confirmação técnica são medições distintas.

## Mapa de capítulos proposto

Os capítulos seguem decisões que o estudante precisa entender. A sequência abaixo funciona como percurso recomendado; alguém que já está trabalhando pode entrar pelo guia ou pela referência de sua necessidade.

| Capítulo | Problema que motiva o estudo | Owner proposto | Slug |
|---|---|---|---|
| 01 | Quando uma reserva correta no papel sai errada no sistema | S2 | `business-rules` |
| 02 | Mudar uma função sem precisar entender o backend inteiro | S2 | `code-boundaries` |
| 03 | Salvar uma reunião sem perder nem duplicar sua integração | S4 | `reliable-integration` |
| 04 | Concluir uma operação quando uma etapa externa falha | S3 | `distributed-work` |
| 05 | Entregar um fato aos interessados certos e recuperar falhas | S4 | `messages` |
| 06 | Mostrar indicadores que têm o mesmo significado que os fatos | S4 | `read-models` |
| 07 | Carregar indicadores rápido sem mostrar outro recorte ou outro usuário | S5 | `cache` |
| 08 | Impedir que dois pedidos ocupem o mesmo horário | S5 | `concurrency` |
| 09 | Continuar atendendo quando uma dependência ou a carga piora | S5 | `capacity` |
| 10 | Integrar Salesforce sem espalhar seu contrato pelo produto | S5 | `api-integration` |
| 11 | Recuperar os dados depois de uma queda ou uma exclusão indevida | S4 | `data-durability` |
| 12 | Manter o serviço disponível sem criar dois líderes conflitantes | S6 | `availability` |
| 13 | Distribuir dados quando uma máquina deixa de ser suficiente | S4 | `data-distribution` |
| 14 | Trocar uma versão sem quebrar quem ainda usa a anterior | S6 | `safe-change` |
| 15 | Permitir a operação certa para a pessoa ou serviço certo | S6 | `security` |
| 16 | Descobrir em qual etapa uma operação ficou lenta ou incompleta | S5 | `observability` |
| 17 | Processar tarefas e dados com estados e recuperação explícitos | S3 | `workflow` |
| 18 | Mudar o comportamento do código sem multiplicar condicionais | S2 | `code-patterns` |

Os 18 capítulos ficam agrupados em quatro entradas de navegação: dar significado e organizar o código; concluir o trabalho com segurança; entregar dados e respostas no ritmo certo; manter o sistema operável enquanto ele muda. Cada entrada reúne três ou cinco capítulos. A página inicial explica os percursos antes de mostrar links. O catálogo completo permanece disponível por seus grupos originais, enquanto os 40 prioritários recebem aprofundamento.

Os caminhos recomendados são `content/explicacoes`, `content/tutoriais`, `content/guias` e `content/referencia`. Cada tipo tem uma página de entrada que descreve a necessidade que atende. Dentro das explicações, o capítulo recebe `index.mdx` e os prioritários recebem páginas próprias. Para conceitos fora dos 40, a referência cobre definição, nível arquitetural, garantias, limites, relações e link ao capítulo. Quando um conceito exige reflexão extensa, seu capítulo pode ganhar uma página específica. Não criaremos diretórios vazios apenas para preencher quatro quadrantes em cada assunto.

## Quatro conteúdos realmente diferentes

**A explicação ajuda a pensar.** A página sobre repetição segura começa com o cenário proposto do corpus: o navegador envia o pedido de agendamento e perde a resposta. O leitor acompanha as possibilidades e entende por que repetir pode criar uma segunda reserva. A página compara benefício, custo, limite e alternativas, mostra o mecanismo em Mermaid e liga fontes. Ela não conduz uma sequência de instalação.

**O tutorial dá uma primeira experiência bem-sucedida.** Em um laboratório local proposto, a pessoa envia três vezes a mesma operação fictícia e observa um único resultado de negócio. Três tentativas com um resultado significam duas repetições sem efeito adicional. A lição escolhe versões, fixtures e comandos; mostra a saída esperada em cada etapa; admite repetição e termina com o estado útil que a pessoa produziu. O laboratório não chama Salesforce nem altera dados de cliente. Até que seus comandos sejam executados em ambiente limpo, ele é um desenho de tutorial.

**O guia ajuda quem tem uma tarefa concreta.** Um operador que já conhece a ferramenta precisa recuperar um evento de integração que falhou. O guia parte da identidade da operação, identifica a condição para reprocessar, orienta a recuperação segura e mostra como confirmar o resultado. Os ramos dependem dos estados realmente implementados e medidos. A explicação conceitual e todos os campos possíveis ficam nos links de apoio.

**A referência permite consultar fatos.** A referência descreve os campos, estados, erros e garantias do laboratório ou do contrato comprovado, com unidades e versões explícitas. Seus verbos descrevem o comportamento. Ela não recomenda a arquitetura inteira nem conta a história de sua escolha. Um glossário consultável liga `Pub/Sub` a `Publish/Subscribe`, mas mantém Outbox, Saga, CQRS e Event Sourcing como conceitos diferentes.

As mesmas quatro necessidades podem reaparecer nos outros capítulos. Não exigimos quatro cópias de cada padrão. Exigimos que cada página tenha uma necessidade central e que os links atendam às demais.

## Critério de aprofundamento dos 40 padrões

Cada página prioritária deve explicar o que o padrão faz, contar um caso concreto com seu escopo de evidência, mostrar benefício, custo e limite, apresentar um diagrama legível e ligar um framework base, uma aplicação OSS e uma skill pertinente. A escolha do framework precisa resolver o problema na stack do exemplo. Um framework Java ou .NET pode ser um bom objeto de estudo; isso não o torna uma recomendação de instalação no FastAPI.

Uma história apresenta quem tentou fazer algo, qual entrada ou dado importou, onde o resultado se perdeu ou mudou e qual decisão altera o desfecho. Os números devem mostrar a conta. Se cada camada puder tentar três vezes, duas camadas podem produzir até nove chamadas; com três camadas, até 27. Esse é um cálculo didático, e a página precisa identificar os limites configurados antes de afirmá-lo sobre um runtime real.

Diagramas de chamadas usam `sequenceDiagram`; decisões usam `flowchart`; transições usam `stateDiagram-v2`; chaves persistidas podem usar `erDiagram`. Os diagramas de casos propostos recebem esse rótulo. Relações sem prova não ganham aparência de caminho executado.

## Compatibilidade Nextra e riscos MDX

A convenção `content/` com a rota de entrada do App Router está descrita na [documentação oficial do Nextra](https://nextra.site/docs/file-conventions/content-directory). Sua navegação pode usar `_meta.js` em cada pasta; o projeto deve escolher essa convenção ou `_meta.global`, pois a [documentação dos metadados](https://nextra.site/docs/file-conventions/meta-file) proíbe combinar as duas.

O Nextra aceita blocos de código `mermaid` e os transforma no componente correspondente com sua integração existente. Não é preciso inventar um componente próprio antes de experimentar essa capacidade. A fonte é a [documentação oficial de Mermaid no Nextra](https://nextra.site/docs/advanced/mermaid). Compilar MDX, aceitar sintaxe Mermaid, renderizar a página e conferir a semântica do diagrama são quatro resultados distintos.

MDX combina Markdown, JSX e expressões JavaScript, conforme a [documentação oficial do MDX](https://mdxjs.com/docs/what-is-mdx/). Portanto, contratos com chaves e sinais de menor que devem aparecer como código; copiar HTML ou comentários Markdown sem considerar essa gramática pode exigir adaptação. As páginas devem manter exemplos dentro de fences, nomes de componentes importados explicitamente, um título principal, headings estáveis e links de site em vez de caminhos de disco do Mac. Mermaid precisa de texto equivalente para o estudante que não consegue consultar o desenho.

Não há recibo de compilação ou renderização neste planejamento. A raiz mantém ownership do scaffolding; S1 consome seus contratos e escreve conteúdo somente quando receber caminhos de autoria. O renderer usado no gate precisa corresponder ao renderer de destino, pois validar em uma versão diferente não prova compatibilidade.

## Colisões que exigem tratamento

O documento aplicado declara propostas; alguns outros documentos usam linguagem de produção. A autoria deve manter a indicação original de escopo e exigir prova para promovê-la. O catálogo de referências contém estrelas aproximadas sem data de medição. O curso pode preservar o nome e papel das ferramentas, mas uma comparação de popularidade exige consulta atual com fonte e horário.

Há frases do texto de Saga que devem ser revalidadas tecnicamente antes do reuso: a classificação geral como AP, a expressão “perda total de isolamento” e a afirmação de que qualquer Saga moderna usa Outbox. S1 identificou os trechos; o especialista de consistência deve adjudicar suas condições e escrever a formulação correta. O número de etapas também não deve se tornar um limiar universal para escolher coreografia ou orquestração. Fontes existentes ajudam a criar a explicação, mas não transferem automaticamente suas conclusões.

## Skill de orquestração encontrada e gates da raiz

A skill existe em `/Users/augustocarollo/skills/docs-autoagents/skills/orchestrating-docs-autoagents/SKILL.md`. Foram lidos seu texto e os quatro contratos de perfil, mapeamento, autoria/council e Mermaid/ADRs. A CLI oferece `init`, `check-profile`, `prepare`, `lock`, `check-lock`, `check-packet`, `review-context` e `gate`.

A raiz deve preparar o perfil e o lock no output autorizado, fixar a pergunta e o SHA, consumir os mapas dos especialistas e manter um owner por arquivo. O council precisa de identidade independente e do hash realmente revisado. Uma entrega pedagógica de arquitetura baseada em casos de domínio deve obter o recibo de preparação de domínio pertinente; a lane S1 inventaria metadados do corpus e não escolhe regras de negócio. O protocolo local aponta para os artefatos dessa execução. S1 não criou arquivos de perfil, protocolos ou recibos fora de sua ownership.

## Três tarefas específicas para os auxiliares de S1

**Auxiliar de evidência e cobertura.** Consuma `coverage.json` e os arquivos originais. Primeiro identifique o que pode ser reutilizado dos mapas de S2–S6. Confira os 18 grupos, aliases, combinações prioritárias e links de fonte. Devolva apenas lacunas e correções com path, linha, hash e escopo. A ocorrência textual de um padrão não pode virar prova de implementação. Não redistribua owner nem escreva MDX.

**Auxiliar de referências e compatibilidade.** Consuma o scaffolding atual e a documentação oficial por Context7 e fontes primárias. Confira MDX, Mermaid, `_meta.js`, rotas e imports contra as versões do projeto. Proponha um contrato de autoria mínimo e exemplos de sintaxe que a raiz possa compilar. Para frameworks e aplicações dos 40, reutilize as verificações dos especialistas; investigue somente associações sem prova. Não conte estrelas do catálogo como observação atual nem altere dependências.

**Auxiliar de experiência de aprendizagem.** Proponha seis experiências locais: repetição segura, falha após o commit, disputa de versão, projeção atrasada, tempestade de renovação do cache e transição de estado inválida. Para cada uma, descreva entrada fictícia, ação escolhida, resultado observável, repetição e saída segura. Escreva uma amostra curta de cada tipo Diátaxis para o mesmo problema, com frases completas e contas explícitas. Reutilize os casos e as evidências dos especialistas; preserve a indicação de hipótese ou proposta. Não crie chamadas a sistemas vivos nem publique dados pessoais.

Essas são tarefas propostas para despacho pela raiz. S1 não abriu auxiliares. A configuração de modelo vem da autorização corrente e do registro real de roteamento, não do nome “auxiliar”.

## Recibos das verificações de S1

- [2026-10-14 16:05 UTC] worktree autorizado — `pwd -P && git branch --show-current && git rev-parse HEAD` → `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`; `perfect-citizen-a30f5998`; `23d5d158d3a964dceba296296368ec14bcd8970b`.
- [2026-10-14 16:05 UTC] `coverage.json`, catálogo e tabelas locais — inventário dos grupos e ligações por número → `catalog_groups=18; catalog_entry_occurrences=374; canonical_catalog_concepts=310; priority_entries=40; framework_mappings=40; applied_entries=40`.
- [2026-10-14 15:58 UTC] `package.json`, arquivo local — `cat package.json` → `"nextra": "4.6.1"`; `"nextra-theme-docs": "4.6.1"`; `"next": "16.4.0"`; `"react": "19.3.0"`.
- [2026-10-14 16:05 UTC] skill de docs, arquivo local — `Path('/Users/augustocarollo/skills/docs-autoagents/skills/orchestrating-docs-autoagents/SKILL.md').exists()` → `True`.
- [2026-10-14 16:05 UTC] `docs/saga/README.md`, arquivo local — leitura das linhas 190, 203 e 225 → `A Saga prioriza **Disponibilidade e Tolerância a Partições (AP)**`; `**Perda total de isolamento:**`; `Em qualquer arquitetura distribuída moderna, uma Saga **usa o Transactional Outbox`.

Os hashes e mtimes dos arquivos do corpus estão em `source_snapshots` no JSON. As verificações não observaram MakersHub, Airflow, PostgreSQL ou FazGraph vivos. Esses ambientes dependem das lanes dos especialistas responsáveis.

## Nota de aliases com contexto

A sigla `ACL` significa Anti-Corruption Layer no recorte de DDD e integração; ela pode significar Access Control List no recorte de segurança. A sigla `EDA` descreve a arquitetura orientada a eventos neste curso; em referências de engenharia de dados, pode significar análise exploratória. O lookup precisa conservar esse contexto. A dupla original Layered / N-Tier também exige explicar a diferença entre camadas lógicas e níveis implantados. A matriz preserva o label do catálogo e registra essa cautela, sem afirmar equivalência universal.
