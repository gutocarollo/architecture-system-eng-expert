# Comparação da jornada de aprendizagem

## Conclusão e alcance

A percepção de distância entre conceito e prática tem suporte nos recortes examinados. O curso já oferece casos de código e seis exercícios executáveis. A lacuna demonstrada é a continuidade do mesmo caso entre explicação, tutorial, guia e referência, junto da reprodução histórica de antes e depois. Esta comparação não afirma que o curso inteiro careça de exemplos reais nem que cada conceito precise de quatro páginas próprias.

As fontes são arquivos locais. No curso, foi examinado o conteúdo do worktree perfect-citizen-a30f5998, com HEAD 23d5d158d3a964dceba296296368ec14bcd8970b e arquivos da entrega ainda locais. No MakersHub, a fonte de ajuda examinada foi paint-bistro, branch docs/FBI-4371-help-selector-guards, SHA b010c697a31eaeea43d8919c2a50c6ff7514d9fd. O main e233fb046ec333982cd1547171b0f0bd8d8d92ee não contém essa central. O exame não certifica que o branch da ajuda seja a versão implantada que o usuário vê.

## Diferenças que afetam o leitor

| Aspecto | MakersHub, na amostra | Curso, na amostra | Consequência e reuso |
|---|---|---|---|
| Entrada pelo assunto | Cada tela reúne visão geral, primeiros passos, guias, referência e explicação. Super R1 tem 15 MDX/11 guias, Call Sprint 16/12, Seguros 12/8. | A entrada organiza quatro necessidades e apresenta três percursos, com explicações agrupadas. | Reutilizar a entrada contextual por família de problemas, preservando os quatro tipos. |
| Passos observáveis | As instruções usam ações da tela, resultados e links para seções de referência e explicação. | Os seis tutoriais têm arquivo completo, Python 3.11+, comando, saída esperada e repetição. | O curso já tem prática útil; a mudança deve aproximá-la do caso real que deu origem à explicação. |
| Continuidade entre tipos | Guias de Super R1 e Seguros apontam para seções específicas da referência e da explicação. | Em integração, modelos de leitura e cache, as explicações não apontam a um guia; nenhum dos seis tutoriais aponta a guia de trabalho. | Acrescentar ligações diretas e contextualizadas de ida e retorno, com o mesmo caso e próximo passo. |
| Falha histórica antes/depois | A central de ajuda ensina operação das telas; não foi demonstrado um laboratório de arquitetura ou de commits. | Os seis tutoriais fornecem o programa já protegido. Eles não executam primeiro a implementação anterior defeituosa e depois a correção histórica. | Criar laboratórios rastreáveis à versão anterior, ao diff corretivo, ao PR e ao Jira. |
| Limites de reprodução | Alguns primeiros passos dependem de clientes ou leads existentes na conta e podem não completar a volta. | Os programas locais têm entradas controladas e limites explícitos; o Outbox não usa transação SQL. | Preservar a previsibilidade dos exercícios locais e acrescentar o vínculo ao código real; não copiar a dependência de dados imprevisíveis da conta. |

## Casos do curso que esclarecem a diferença

Em integração, a explicação identifica uma gravação real de responsável e flag de sincronização. O exercício Outbox demonstra deduplicação após uma queda simulada. Entretanto, o caminho da explicação não leva diretamente ao tutorial ou ao guia. A própria explicação identifica a disputa desenhada como hipótese, sem tratá-la como incidente registrado de um cliente.

Em cache, o capítulo contém dois SHAs históricos e descreve mecanismos de cancelamento e refresh. O tutorial single-flight cancela um leitor e mantém quatro consumidores. Essa é uma boa base de composição. Nos materiais examinados, a cadeia publicada de versão anterior, correção, descrição de PR, card Jira verificado e exercício antes/depois não está fechada.

Em modelos de leitura, existe o vínculo ao PR 362, mas o capítulo informa que ele não comprovou a introdução do CQRS. Portanto, esse PR não pode ser apresentado como a origem demonstrada de CQRS só porque foi citado no pedido.

## Evidências e limites

O pacote makershub-packet.md registra paths, linhas, SHAs e as três telas. O review do curso examinou a navegação, os seis tutoriais, os dois guias e as três famílias identificadas, sem executar os exercícios. Os resultados a seguir são saídas e ligações descritas nos arquivos, não novas execuções dos programas:

- [2026-10-15 00:16 UTC] course content/tutoriais/outbox.mdx:84–91, leitura numerada: publisher=crashed before marking outbox sent; delivery_attempts=2 applied_effects=1.
- [2026-10-15 00:16 UTC] course content/tutoriais/single-flight.mdx:125–131, leitura numerada: surviving-readers=4 value=rows-1; producer-calls=2.
- [2026-10-15 00:16 UTC] extração de hrefs dos três capítulos: integração e modelos de leitura têm direct_tutorial_hrefs []; cache tem ['/tutoriais/']; os três têm direct_guide_hrefs [].
- [2026-10-15 00:16 UTC] extração dos hrefs dos seis tutoriais: direct_guide_hrefs [] em cada um.
- [2026-10-15 00:16 UTC] MakersHub help-center/content/screens, contagem de MDX e guias: super-r1 MDX 15 guides 11; call-sprint MDX 16 guides 12; insurance MDX 12 guides 8.

Não foram comprovados produção, reprodução de mídia ou progresso salvo na central MakersHub. O complemento amendment.md registra R14–R17 e os critérios 12–18 como trabalho a realizar e verificar; sua aprovação de redação não aceita automaticamente o conteúdo existente.
