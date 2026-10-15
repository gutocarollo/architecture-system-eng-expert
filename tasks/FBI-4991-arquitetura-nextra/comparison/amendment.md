# Complemento solicitado pelo proprietário: aprender arquitetura pelos nossos problemas reais

O estudante deve conseguir reconhecer uma dor que a equipe viveu, entender qual conceito explica o problema e executar uma prática que mostre o que muda com a correção. A comparação com o Nextra do MakersHub deve conferir esse caminho nos arquivos e na navegação. As conclusões precisam identificar a versão examinada e distinguir fonte local de interface renderizada e de produção.

## R14 — Uma jornada por problema, com as quatro necessidades do Diátaxis

Organizar os conceitos em famílias e casos de uso com uma entrada compreensível para o estudante. Cada família deve reunir ou ligar claramente quatro destinos: a explicação mostra por que o problema acontece e o que o desenho oferece; o tutorial conduz uma experiência prática e previsível; o guia ajuda quem já conhece o assunto a resolver uma tarefa no sistema; a referência reúne os contratos, funções, caminhos, dados e parâmetros necessários à consulta. A organização pode reutilizar o padrão de páginas por assunto do MakersHub. Os tipos mantêm suas finalidades e recebem links contextualizados, sem se tornarem um único texto que mistura teoria, operação e consulta.

O mesmo caso deve continuar reconhecível ao mudar de página. O estudante precisa saber qual problema está estudando, o que já conseguiu fazer e qual é o próximo passo. Pré-requisitos, passos, resultados e links devem estar próximos da atividade a que pertencem. A matriz relaciona a totalidade dos conceitos do pedido às famílias, aos casos e aos destinos disponíveis. Um exercício pode ensinar vários conceitos relacionados, mas essa relação precisa estar declarada; contar pastas ou páginas não comprova a jornada.

## R15 — Hands-on de antes e depois, derivado de uma mudança real

Cada caso de aprendizado deve conter uma prática reproduzível, com objetivo, ambiente isolado, dependências, preparação, entradas conhecidas, comandos ou ações, resultados esperados e modo de reiniciar. Quando houver um bug documentado, a prática deve reproduzir a condição anterior, permitir observar o sintoma e o impacto na tarefa da pessoa, aplicar ou estudar a correção identificada e repetir a mesma condição para observar o resultado posterior. Os resultados precisam indicar qual garantia foi adquirida e o que continua fora dessa garantia.

Vincular as versões anterior e corrigida aos SHAs, ao diff e aos caminhos reais, incluindo funções, páginas, endpoints, DAGs ou modelos quando forem pertinentes. Usar trechos reais do código ou uma reprodução mínima rastreável a esses trechos. Uma reprodução em ambiente de aprendizado deve ser identificada como tal, com dados anonimizados ou sintéticos declarados e limites em relação ao sistema original. Um exemplo genérico de biblioteca ou a leitura passiva de um diff não satisfazem sozinhos esse requisito. Se a implementação histórica era uma evolução de funcionalidade, apresentá-la como evolução; o roteiro não pode inventar um incidente para torná-la mais dramática.

Os fluxos Mermaid devem mostrar a entrada, a decisão, os sistemas envolvidos, a falha e a recuperação antes e depois, quando esses elementos fizerem parte do caso. A versão histórica corrigida precisa ser distinguida de uma arquitetura adicional proposta pelo material. A prática acontece em ambiente isolado; escritas em produção não integram este aceite.

## R16 — Linhagem verificável da dor, da decisão e da correção

Construir as histórias a partir da leitura efetiva das descrições dos PRs, dos cards e comentários Jira pertinentes, dos commits anteriores e corretivos e dos diffs. O registro deve ligar o conceito ao caso, à tarefa de negócio afetada, à manifestação documentada do problema, à decisão, à alteração e à evidência posterior. Quando houve regressão, outra correção ou uma sequência de implementação, preservar a cronologia e as relações comprovadas. Commits e PRs de infraestrutura ou desenvolvimento podem ser casos úteis sem constituírem incidentes de produção.

Uma chave Jira no título ou um assunto de commit pode orientar a descoberta, mas não prova sozinho a causa. Distinguir o que o card ou PR relata, o que o código permite reproduzir, o que foi observado no ambiente identificado e o que é uma interpretação pedagógica. Registrar links, SHAs, trechos, datas de leitura e a fronteira do efeito. Não atribuir uma falha à ausência de um padrão arquitetural sem demonstrar o mecanismo e avaliar outras causas.

Para relações de dados, usar o FazGraph para orientar a linhagem e o blast radius e o MCP PostgreSQL para confirmar valores e resultados relevantes, com consulta, horário e identidade da fonte. A matriz deve marcar separadamente a disponibilidade de Jira, PR, versão anterior, versão corrigida, dados e prova de execução. Evidência ausente permanece uma lacuna; não é substituída por uma narrativa confiante. Esta frente não encerra a análise causal integral do histórico enquanto esse alcance maior não estiver demonstrado.

## R17 — Caso financeiro aplicado quando faltar um caso da nossa stack

Procurar primeiro um caso pertinente em MakersHub, Airflow, Salesforce, PostgreSQL, dbt, n8n e nas integrações documentadas da nossa stack. Quando a busca delimitada não localizar uma implementação adequada, registrar onde se procurou e apresentar um problema aplicado a uma corretora de maior porte, como o tipo de operação que uma empresa do setor da XP poderia enfrentar.

O caso alternativo deve conter participantes, tarefa, entradas, condição de falha, consequências, desenho anterior, solução, prática e resultados observáveis. Deve conservar a mesma conexão entre explicação, tutorial, guia e referência. Quando for hipotético, identificar esse fato explicitamente. A XP pode contextualizar o setor; atribuir um incidente ou uma arquitetura interna real à empresa exige fonte pública primária. A ausência de exemplo interno não pode ser declarada a partir de uma única busca ou de uma falha de acesso.

## Critérios de aceite adicionais

12. Existe uma comparação documentada entre o Nextra do curso e o Nextra do MakersHub, com repositório ou worktree, SHA, caminhos e exemplos que permitam reproduzir a leitura. Ela identifica o que será reutilizado e quais diferenças afetam o aprendizado. Fonte local, navegação renderizada e produção estão distinguidas; uma fonte indisponível fica como pendência explícita.
13. A matriz da totalidade dos conceitos relaciona famílias e casos aos quatro destinos Diátaxis. As jornadas oferecem links diretos e contextualizados de ida e retorno, pré-requisitos, objetivo, resultado e próximo passo. Destinos inexistentes ou sem conteúdo pertinente são lacunas de cobertura. A presença de quatro diretórios não satisfaz este aceite.
14. Os casos apresentados como históricos têm linhagem conferida em Jira, PR e código, com SHA anterior, SHA corrigido e diff. Quando faltar uma fonte necessária, o caso permanece pendente e não conta como aceite cumprido; a matriz identifica a fonte ausente. A história explica quem enfrentou a dor, qual tarefa foi afetada, qual mecanismo produziu o problema e como a mudança o tratou. Fato relatado, fato reproduzido, execução observada e hipótese permanecem distinguíveis.
15. Cada caso de aprendizado oferece um hands-on executável, com as condições anteriores e posteriores delimitadas, preparação completa, entradas, passos, falha esperada, correção, resultado e reinício. Um aluno consegue repetir a mesma condição e comparar a saída. Os casos compartilham exercícios apenas quando a matriz identifica os conceitos ensinados e a garantia demonstrada.
16. Os diagramas e trechos de código preservam o caminho real e os limites do efeito. Há verificação da sintaxe, renderização e correspondência com as fontes; comandos, resultados e SHAs da prática são registrados. Dados e ações de aprendizado são isolados dos sistemas de produção.
17. Cada conceito sem caso interno adequado possui uma busca delimitada registrada e um caso financeiro aplicado com prática e resultados esperados. O roteiro identifica se é hipotético, reprodução de fonte pública ou caso observado. Uma suposição sobre a XP não pode aparecer como fato sobre a empresa.
18. Um revisor independente percorre as jornadas e executa os hands-ons com as instruções entregues, confrontando as versões e as saídas. O recibo vincula o resultado à versão examinada e registra lacunas por caso e por conceito. Aprovar a redação destes critérios não significa que o conteúdo ou a prática já os atendam.

## Estado deste complemento

Este complemento acrescenta entregáveis e critérios a verificar. O registro na Story não certifica a execução dos novos hands-ons, não converte os exercícios atuais em reproduções históricas e não declara encerrada a cobertura pedagógica do curso.
