# Evidências da central Nextra do MakersHub para FBI-4991

## EVIDENCE_PACKET

**Veredito.** A fonte de ajuda examinada reúne o assunto e as quatro necessidades do leitor em um mesmo núcleo por tela. Ela oferece um padrão reaproveitável de proximidade entre conceito e prática. A presença de Nextra e dos quatro tipos, sozinha, não comprova uma jornada de aprendizagem: o que faz diferença nesta amostra são as páginas de entrada, os passos com resultados observáveis e os links específicos entre páginas. A comparação com o curso deve ser feita sobre esses comportamentos.

**Escopo.** Leitura em 2026-10-15, entre 00:15 e 00:16 UTC. O checkout principal `/Users/augustocarollo/Developer/makershub` resolve para `/Users/augustocarollo/Developer.noindex/makershub`, branch `main`, SHA `e233fb046ec333982cd1547171b0f0bd8d8d92ee`. Ele não contém `help-center`. A fonte comparável está em `/Users/augustocarollo/.superset/worktrees/makershub/paint-bistro`, branch `docs/FBI-4371-help-selector-guards`, SHA `b010c697a31eaeea43d8919c2a50c6ff7514d9fd`. Nas referências abaixo, `H` significa esse diretório seguido de `/help-center`. Há WIP em outras telas, preservado. Os três temas examinados não apareceram na saída de `git status --short -- help-center`. Não houve consulta à produção, build, teste ou alteração do MakersHub.

**Composição: o que reutilizar primeiro.**

- A estrutura mantém o contexto da tela. `H/content/screens/call-sprint/_meta.js:2-6` ordena “Visão geral”, “Primeiros passos”, “Guias práticos”, “Referência” e “Entenda a tela”. O tutorial, os guias e as explicações não exigem que o leitor saia do tema para procurar uma grande pasta global de cada tipo.
- A entrada explica a tarefa e oferece percursos com propósito. `H/content/screens/super-r1/index.mdx:20-44` apresenta uma primeira volta de quinze minutos e separa onze guias em agendamento, preparação da qualificação e acompanhamento. A página de Call Sprint agrupa os guias em montar a lista, ligar e preparar/registrar a conversa (`index.mdx:26-45`). Seguros agrupa produção, propostas e carteira (`index.mdx:28-43`). São introduções com links, não cards locais: os cards constatados estão na entrada geral (`H/content/index.mdx:16-18`).
- A prática fornece ação e sinal de sucesso. Na Call Sprint, o tutorial manda clicar em **Clientes** e descreve as colunas e o alternador que aparecem (`getting-started.mdx:28-32`). O guia de chamada termina a fila e explicita o resultado no Salesforce (`guides/call-list-in-sequence.mdx:18-36`).
- A ponte entre tipos chega a uma seção. O guia da Super R1 aponta para **Campo Valor**, **Faixas e destinos**, **A faixa de patrimônio escolhe o time** e **O lote das 21h** (`guides/schedule-lead-r1.mdx:48-49`). Seguros liga a busca da apólice à referência do painel e à explicação dos dois filtros (`guides/find-proposal-or-policy.mdx:31-32`).

**Três casos comparáveis.**

| Tema | Forma encontrada | Exemplo que dá contexto |
|---|---|---|
| Super R1 | 15 MDX: entrada, primeiros passos, referência, explicação e 11 guias. | O guia qualifica, confirma e verifica a oportunidade com **Agendado** (`guides/schedule-lead-r1.mdx:18-26`). A explicação usa leads explicitamente fictícios de R$ 120 mil e R$ 300 mil para mostrar a mudança de destino (`explanation.mdx:24`). |
| Call Sprint | 16 MDX com a mesma estrutura e 12 guias. | A primeira volta ensina a montar e observar a fila sem ligar (`getting-started.mdx:10-16`). O guia faz a chamada real, acompanha as fases e encerra a sprint (`guides/call-list-in-sequence.mdx:18-24`). |
| Seguros | 12 MDX com a mesma estrutura e 8 guias. | O tutorial altera **Emissão**, observa os números e restaura o mês atual (`getting-started.mdx:36-40,94-98`). A explicação conta uma venda criada em julho e emitida em setembro, com personagens declaradamente fictícios (`explanation.mdx:20`). |

**Onde o padrão é insuficiente.** Os primeiros passos usam dados da conta. Call Sprint exige clientes com telefone e admite que a volta não funciona para alguns usuários (`getting-started.mdx:16`). Super R1 orienta a interromper parte da lição quando faltam leads (`getting-started.mdx:18`). Portanto, não constituem por si um ambiente reproduzível de curso. Também não foi verificado um wizard com estado ou progresso salvo. A amostra mostra sequências em MDX com `<Steps>`.

O branch irmão `/Users/augustocarollo/Developer/makershub-workspaces/docs-help-videos`, SHA `bf496e99c7617fef6f2223bad1313f4f1548d0b7`, acrescenta `<Video>` à entrada de Super R1 e Call Sprint (`help-center/content/screens/{super-r1,call-sprint}/index.mdx:15`). A busca de marcação direta não encontrou imagem ou vídeo em Seguros nessa amostra. Isso comprova referências no código, não reprodução de mídia. Os blocos de fontes e revisões históricas presentes nessas páginas também não devem virar texto de aprendizagem: a skill Diátaxis, `references/end-user-help.md:8`, mantém o registro de investigação em evidência interna.

**Critérios sugeridos ao responsável por FBI-4991.** Cada unidade deve oferecer uma entrada pelo assunto, uma primeira experiência completa com pré-requisitos reproduzíveis, ações e resultados verificáveis; a prática deve manter o mesmo caso ou artefato até o resultado final; cada conceito deve apontar à prática correspondente e esta deve voltar à seção conceitual pertinente; o leitor deve conhecer o próximo passo ao terminar; exemplos fictícios devem ser identificados; dependências de conta, dados e ambiente devem ser explícitas. A validação deve acompanhar uma jornada real de ponta a ponta, além de contar arquivos ou conferir categorias. Progresso salvo exige decisão própria: a amostra do MakersHub não o prova.

**Recibos.**

- [2026-10-15 00:17 UTC] MakersHub principal — `git rev-parse HEAD; if [ -d help-center ]; then printf 'help-center=present\n'; else printf 'help-center=absent\n'; fi` → `e233fb046ec333982cd1547171b0f0bd8d8d92ee` e `help-center=absent`.
- [2026-10-15 00:16 UTC] MakersHub paint-bistro — `git rev-parse HEAD` → `b010c697a31eaeea43d8919c2a50c6ff7514d9fd`.
- [2026-10-15 00:16 UTC] `H/content/screens` — contagem Python de `rglob('*.mdx')` e `guides.glob('*.mdx')` → `super-r1 MDX 15 guides 11`; `call-sprint MDX 16 guides 12`; `insurance MDX 12 guides 8`.

**Referência de método.** A skill Diátaxis foi aplicada. `references/complex-hierarchies.md:170-193` apresenta contexto antes dos tipos como uma possibilidade e alerta que os quatro tipos não impõem quatro pastas globais. Isso sustenta a organização por assunto; não exige copiar os nomes, a árvore ou os textos do MakersHub. CodeGraph foi consultado primeiro no principal, mas não localizou esta central; o worktree comparável não tem `.codegraph`. `docs/documentation-protocol.md` não foi encontrado na fonte principal nem no registro de arquivos do worktree comparável.
