# Correção da entrega de early-refresh

O dono corrigiu a entrega: “mas que porra eh essa. nao está na mesma pagina. é a unica coisa que eu pedi...”. A versão c0230de8 entregou navegação entre páginas; esse comportamento não atende à experiência agora explicitada.

A correção reúne explicação, tutorial, guia e referência completos em `/jornadas/early-refresh/`. O sumário usa fragmentos da própria página. Os textos têm uma única fonte em quatro corpos MDX compartilhados; os endereços antigos continuam mostrando esses mesmos corpos e preservam os fragmentos publicados.

- [x] Confirmar HEAD e remoto em c0230de87e0a392169ccfdfe141ffc6c6dd72ae6, checkout limpo e checkpoint restaurável pelo commit.
- [x] Reproduzir a ausência das quatro facetas com testes do conteúdo da jornada.
- [x] Extrair os corpos compartilhados, compor as quatro seções e ajustar títulos, sumário, links e indexação.
- [x] Validar build, URLs antigas, teclado, celular, busca e navegação sem mudar de página.
- [ ] Revisar a correção, commitar, enviar ao GitHub e atualizar a imagem do serviço existente.
- [ ] Conferir a página publicada e a identidade commit/imagem/export.

## Critério que decide a entrega

O HTML e o navegador da jornada devem conter as quatro facetas completas. Um link para outra página não conta como faceta presente. Ao selecionar Entender, Praticar, Aplicar ou Consultar, somente o fragmento da URL pode mudar.

## Fonte e reversão

Pasta autorizada: `courses/makershub-architecture/`. Restaurar apenas os arquivos desta correção a partir de c0230de8 reverte a mudança editorial. A imagem anterior é `sha256:f2e9aaad1960f405569691003a45bad986bf64fc9bd0db77ce39e0dbefa5ce0b`; a leitura do serviço será refeita antes da troca.

## Rotas

WARM_REUSE `/root/nextra_contract`, default, gpt-6.1-sol/high, exploração somente leitura do mesmo compilador. Resultado: imports MDX diretos fora de content agregam o sumário; usar H2 por faceta e H3 por subtítulo. O principal escreve a correção. A revisão final avaliará o pedido corrigido, não herdará o aceite da entrega anterior.

## Aprendizagem desta correção

O erro foi transformar o objetivo de acompanhar todo o conteúdo numa preferência arquitetural por páginas separadas. Os testes anteriores provaram a navegação escolhida e não provaram a presença das quatro facetas no documento. O guard novo falha quando uma faceta vira apenas um link ou quando a navegação sai da jornada. Este registro fica no escopo autorizado do curso; não é apresentado como ingestão no catálogo central de lições.

## Evidência anterior à publicação

Sete testes novos falharam contra o HTML anterior. A correção passou em 22 testes, conservou 184 HTML e indexou 177 páginas, quatro a menos porque as entradas de compatibilidade não repetem o índice da jornada. A revisão independente confirmou que nenhum texto, comando, tabela ou Mermaid das quatro facetas foi perdido. Retirar a referência inteira matou três testes; apontar o controle Consultar para outra página matou um teste. A prévia confirmou o mesmo pathname nos quatro cliques, o celular, o teclado e os resultados da busca na jornada.
