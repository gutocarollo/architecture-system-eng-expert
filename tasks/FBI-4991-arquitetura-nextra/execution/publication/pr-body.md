## Entrega

Este PR entrega o curso de arquitetura em Nextra/MDX vinculado à [Story FBI-4991](https://fazcapital.atlassian.net/browse/FBI-4991). As 18 jornadas conectam o problema, a explicação, o tutorial, o guia e a referência do mesmo caso. O curso tem 181 páginas e cobre os 310 conceitos dos 18 grupos, incluindo os 40 prioritários.

Sete casos partem de código histórico do MakersHub e do Airflow. Onze usam hipóteses financeiras declaradas. Os exercícios mostram o comportamento anterior, a correção e o contrato que evita repetir o problema. O ZIP de laboratórios inclui 98 arquivos de fonte e 16 executores; a extração fora do Git foi conferida independentemente. Os casos PostgreSQL usam servidor real isolado e dados sintéticos. A função histórica do Airflow usa dependências controladas.

O site está em https://fazcapital-arquitetura-na-pratica.navy-teal-7786.chatgpt.site. A opção B aprovada usa senha compartilhada validada pelo servidor e dispensa conta ChatGPT. O código de autenticação e a fonte hospedada são versionados pelo provedor Sites em um checkout separado; a senha e as chaves ficam no Keychain e nos segredos de execução. Os recibos de publicação e de leitura autenticada estão na pasta hosting desta frente.

## Revisão e evidência

A curadoria tem 310 julgamentos independentes vinculados às fontes. Os 51 achados HIGH foram corrigidos e aceitos pelos revisores que os emitiram. Os 94 diagramas têm parsing, render e parecer semântico delimitado à fonte histórica, ao laboratório ou à proposta declarada. As duas últimas correções identificam o cancelamento injetado pelo laboratório e recolocam o dashboard entre captação e ranking.

A auditoria terminal aprovou o escopo de site protegido e PR em rascunho. O recibo final-source-delta registra que o Worker e os executores permanecem com os mesmos bytes examinados; as correções de conteúdo têm rechecagens próprias. O veredito bruto do navegador permanece preservado quando acusa respostas 401 esperadas e o favicon ausente. Não há alegação de verificação integral sem ressalvas.

## Pendências que mantêm o PR em rascunho

A autoridade para registrar este repositório GitHub no catálogo global não foi localizada no escopo auditado. A proposta de Document foi preservada, sem alteração do contrato global. A análise histórica classifica 12.697 commits e 595 cards FBI, mas não confirma a causalidade de todo o histórico: 290 casos são relatos e 35 carecem de evidência causal. O método também ainda exige recibos formais por documento para o aceite integral do pacote; as aprovações por fonte e diagrama não foram promovidas em aprovações fictícias de todos os documentos.

Os apontamentos médios e baixos seguem no backlog. A Story continua em andamento. Este PR não modifica nem comprova deploy de MakersHub, Airflow ou banco de produção.
