# Navegação consistente em todos os casos

O dono apontou quatro falhas na entrega: o breadcrumb “Siga um caso completo / <caso>” desapareceu no piloto; os controles e a tabela perderam a aparência azul de link; a mudança alcançou somente um caso; o rodapé oferecia “Conceitos e prática” dos dois lados em vez da sequência Explicação → Tutorial → Guia → Referência. A imagem fornecida mostra a jornada opportunity-entry.

O escopo autorizado agora abrange os 18 casos e suas 72 facetas, além dos mapas opcionais de conceitos. A exigência anterior permanece: cada jornada contém os quatro textos completos na mesma página, a partir de corpos MDX únicos. Uma entrada direta por uma faceta deve identificar o caso e dar acesso às outras etapas.

## Contrato de aceitação

- Todas as jornadas contêm explicação, tutorial, guia e referência completos, com sumário local.
- Toda entrada de caso exibe o breadcrumb Siga um caso completo / nome do caso; facetas identificam também sua etapa.
- Barra, tabela, breadcrumb e rodapé usam links azuis e sublinhados antes do hover, com foco visível.
- A sequência é Explicação → Tutorial → Guia → Referência. O pager anterior/próximo conhece a etapa do caso; a paginação global não aparece nos casos ou mapas.
- Os 90 endereços das jornadas/facetas e os mapas existentes preservam seus fragmentos anteriores.
- Nenhum texto, código, tabela, diagrama ou ressalva histórica é perdido na extração. As três famílias especiais PostgreSQL/Airflow conservam seu conteúdo.
- GitHub e Easypanel recebem a mudança; a verificação final confere versão e comportamento publicados.

## Execução

- [x] Confirmar HEAD/remoto ef5bd78bd0224571ccfde49873ac1b16489b59c1 e checkout limpo; o commit é o checkpoint de reversão.
- [x] Inventariar 18 jornadas e 72/72 fontes de facetas; localizar os estilos e a paginação que causam a inconsistência.
- [x] Capturar os fragmentos publicados e reproduzir os problemas com testes do conjunto.
- [x] Generalizar componentes, breadcrumb, links do tema e sequência; compor os 18 casos com fontes únicas.
- [x] Validar corpus, browser desktop/celular/teclado e entradas diretas; executar mutações.
- [ ] Obter revisão independente, commitar e publicar no GitHub e no Easypanel.
- [ ] Conferir o conteúdo e a versão publicados.

## Rotas e limites

O principal é o único escritor. As explorações reutilizam `/root/case_sources` e `/root/nextra_contract`, default, gpt-6.1-sol/high, somente leitura; os resultados confirmaram os 18 casos, os três templates especiais e os contratos do tema/MDX. A revisão será independente da autoria.

Os corpos mantêm seus identificadores de subtítulos. Quando “Antes de começar” colide com a introdução da jornada, o guia recebe ID próprio e a rota antiga injeta o alias imediatamente antes do subtítulo. Essa adaptação mantém o sumário compilado e evita aliases duplicados na jornada.

## Rechecagem material R1

Na verificação em navegador, o principal encontrou parágrafos antigos de navegação dentro dos corpos: eles ainda ofereciam links para as páginas separadas. O detector inicial exigia quatro links de facetas, mas o template comum possui a jornada e três outras facetas. O critério foi corrigido para o conjunto de destinos do mesmo caso. Foram retirados 112 parágrafos de chrome, e 45 links contextuais dos mapas passaram a apontar para as seções da jornada. Um teste do corpus agora rejeita links de facetas antigas dentro da jornada completa.

ROUND_GATE: missão 100 pontos; itens afetados = contexto (15) e completude do caso (40), união 55. Notas decisão/risco/evidência/blast/reuso = 5/2/4/1/4; fator 71%; ganho bruto 39,05%; custo de oportunidade 5% do grupo de publicação; ganho líquido 34,05%. Decisão: uma rechecagem aquecida limitada a R1. Nenhum novo council ou revisão integral.

Não alterar sistemas de produção do MakersHub/Airflow nem executar laboratórios externos. A mudança é documental e de navegação dentro da pasta do curso. A aprendizagem desta correção é tornar a aceitação transversal: um piloto funcional não prova consistência do corpus, e href válido não prova aparência ou sequência de navegação.

## Verificação anterior à publicação

A suíte passou em 77 testes. A revisão independente conferiu os 72 corpos contra o commit de base, incluindo 129 blocos de código e 65 tabelas. A rechecagem R1 também passou. No navegador, a pauta opportunity-entry mostrou breadcrumb, barra, tabela e rodapé com links do tema; a leitura dos estilos computados retornou rgb(0, 107, 230), underline e pointer nos quatro grupos. A entrada direta em Explicação de date-only ofereceu Tutorial como próximo passo e chegou à jornada completa. A largura CSS 390 não produziu overflow na barra; Tab e Enter conservaram o caso.
