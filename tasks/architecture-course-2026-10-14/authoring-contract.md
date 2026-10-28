# Autoria da trilha

Ao redigir, leia o mapa `evidence/coverage.json`, o pacote do seu domínio e os três auxiliares atribuídos. Reutilize os caminhos de capítulos do mapa. Cada arquivo pertence a um autor; a raiz escreve índices e navegação. Preserve mudanças de outros autores.

## Conteúdo e fontes

Escreva em `content/explicacoes/<chapter_id>/index.mdx`. Use frontmatter com `title`, `description` e `diataxis: explanation`, seguido de uma abertura que conte uma dor concreta e explique o benefício de aprender. O corpo desenvolve todos os conceitos atribuídos ao capítulo, com contexto, mecanismo, exemplos, custos e limites. Os 40 prioritários recebem seções próprias e exemplos desenvolvidos; uma lista de nomes não constitui explicação.

Identifique o escopo de cada caso: código lido no SHA, configuração medida no runtime, mudança histórica em outro commit ou proposta. Os caminhos e símbolos precisam vir da evidência. Dê ao leitor uma pequena história com quem age, o que ocorre, a consequência e a lição. Use dados agregados medidos e faça a conta; preserve a unidade, o sinal, o período e o grão. Casos financeiros sem código existente são hipotéticos e não descrevem uma operação interna da XP.

Use Mermaid nativo em fences. Prefira um fluxo para decisões, uma sequência para chamadas e uma máquina de estados para transições. Nomeie fronteiras e funções quando ajudarem. Represente o ramo de falha e a recuperação. Em um desenho proposto, diga isso antes do diagrama; uma seta contínua em um fluxo observado exige fonte da conexão. Todos os fences serão extraídos com hash, analisados, renderizados e revistos.

## Referência completa

Escreva os grupos sob sua responsabilidade em `content/referencia/catalogo/<NN>-<slug>.mdx`, usando os nomes do mapa. Cada conceito tem seção identificável, definição, problema aplicado, limite e vínculos verificáveis a skill, framework ou biblioteca e aplicação OSS. Identifique quando a aplicação é didática, histórica ou um produto. Um único sistema pode servir a vários conceitos quando a fonte mostra a relação. Para um conceito sem referência adequada verificada, registre a lacuna exata; não atribua uma capacidade a uma biblioteca pelo nome.

Uma estrela é um valor medido em uma data. Tendência exige comparação temporal ou presença comprovada num ranking datado. Preserve a diferença entre popularidade, manutenção, licença, adequação e prova de implementação. Use fontes primárias e links diretos.

## Exercícios e guias

O tutorial usa dados fictícios em uma experiência local segura: pré-requisitos, passos numerados, código completo, saídas esperadas, comparação e próximo passo. O guia resolve uma tarefa concreta para quem já conhece a ferramenta, com pré-condição, procedimento e critério de conclusão. Links levam à explicação e à referência; não repita a mesma aula em quatro tipos.

## Ownership por especialista

S1 integra a experiência de aprendizagem e os seis laboratórios. S2 possui `business-rules`, `code-boundaries`, `code-patterns` e os grupos 1, 10 e 17. S3 possui `distributed-work`, `workflow` e o grupo 16. S4 possui `reliable-integration`, `messages`, `read-models`, `data-durability`, `data-distribution` e os grupos 2–5. S5 possui `cache`, `concurrency`, `capacity`, `api-integration`, `observability` e os grupos 6–9 e 15. S6 possui `availability`, `safe-change`, `security` e os grupos 11–14. A raiz integra o grupo 18, os índices, a navegação e os recibos.

O revisor independente confere os hashes finais. O autor entrega sua lista de arquivos, conceitos cobertos e limites. Autoria concluída não autoriza anunciar aceite.

Para o site, um caminho local de SKILL.md é texto e localizador do workspace. Use uma URL pública verificada ou link para `/referencia/skills-e-projetos`; não crie href de filesystem `/Users/` no Nextra.
