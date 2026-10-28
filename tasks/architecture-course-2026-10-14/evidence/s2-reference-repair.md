# S2 — delta de referências para TH1

Status: `REPAIR_SUBMITTED_FOR_WARM_RECHECK`. Esta nota entrega o delta ao mesmo reviewer; não emite aprovação.

A escrita foi limitada às duas referências atribuídas e a este relatório. Foram lidos os achados de `reviews/teaching-findings.md`. A composição começou pelo corpus e pelos clones existentes: MyMeetings e Wild Workouts foram reaproveitados como fontes de contexto, porém seus documentos não declaravam os cinco padrões em falta. Os novos fontes foram lidos em referências públicas fixadas; nenhum clone, sistema de produção, índice, explicação ou coverage foi alterado.

## Oito entradas reparadas

| ID | Conceito | Prova acrescentada | Limite preservado |
|---|---|---|---|
| g01-e006 | Microkernel / Plugin Architecture | Eclipse Equinox/OSGi como base; plugin.xml do JDT registra org.eclipse.ui.views e a classe PackageExplorerPart implementa ViewPart/createPartControl. | Prova de código de plugin consumidor, sem execução de IDE nesta lane. |
| g01-e020 | Blackboard Architecture | Play Framework 2.5.10 e Neo4j 3.2.1 declarados; BlackboardSystem.runKS, KnowledgeSource.runKS, KSource.execute e ChemblKSource compartilham KGraph e acrescentam nós/arestas. | NCATS é LEGADO; o controle visto é solicitado por HTTP, sem atribuição de scheduler autônomo. |
| g01-e021 | Pipe and Filter | NiFi Generate_and_Update.json registra três processadores e duas conexões; LookupAttribute e UpdateAttribute mostram leitura, transformação e transferência. | Flow de bundle de teste é REF; não foi executado nem tratado como pipeline financeiro de produção. |
| g10-e016 | Shared Kernel | Modelo do próprio Context Mapper: LanguageCore e ArchitecturalRefactorings têm SK; o comentário nomeia o modelo semântico compartilhado. | Modelo declarado: cinco contextos, quatro relações, uma SK; não comprova rotina de negociação de equipes. |
| g10-e017 | Customer/Supplier | Insurance-Example-Stage-2.cml declara D,C e U,S para CustomerSelfServiceContext/CustomerManagementContext. | Modelo REF fictício TO_BE; seis contextos, sete relações, uma C/S. |
| g10-e018 | Conformist | O mesmo CML declara PolicyManagementContext D,CF perante CustomerManagementContext U,OHS,PL. | Uma relação CF no modelo; não atribui conformidade ao MakersHub. |
| g10-e019 | Open Host Service | PrintingContext publica U,OHS,PL para CustomerManagementContext, PolicyManagementContext e DebtCollection. | Três consumidores declarados; não finge execução de APIs no modelo TO_BE. |
| g10-e021 | Separate Ways | DcaShop product/domain.md nomeia Portal e Backoffice; BackofficeContext.cs declara Separate Ways explicitamente. Base DomainCentric.BuildingBlocks/ArchRules e teste gerador do mapa foram lidos. | Oito contextos no mapa e dois casos nomeados no documento; alcance é relação de modelo, com infraestrutura compartilhada. Teste não executado. |

O caso Separate Ways não foi deduzido apenas pela ausência de imports. Sua classificação e seu alcance estão declarados pelo autor do sample. O exemplo mantém dependências técnicas de infraestrutura e leitura operacional; a página explica essa diferença. O arquivo CML de seguros não foi usado para afirmar Separate Ways, pois não apresentou essa declaração.

## Recibos das fontes primárias

Os fontes abaixo foram recuperados por `urllib.request.urlopen(url)` nas URLs brutas fixadas. Todos retornaram HTTP 200. O hash é do corpo integral recuperado; esta tabela evita depender de snippets de busca ou de uma etiqueta pelo nome.

| UTC | Repositório e caminho | HTTP | SHA-256 |
|---|---|---:|---|
| 2026-10-14 19:40:30 UTC | [ContextMapper/context-mapper-examples/src/main/cml/insurance-example/Insurance-Example-Stage-2.cml](https://github.com/ContextMapper/context-mapper-examples/blob/3c28b419e965e74aa3bfe616467cf5ebfff261a8/src/main/cml/insurance-example/Insurance-Example-Stage-2.cml) | 200 | `e104ba774c0684267dfc8345343119dcee9db19b2945fb45253dc43bc06e1c8d` |
| 2026-10-14 19:40:30 UTC | [ContextMapper/context-mapper-examples/src/main/cml/context-mapper-example/ContextMapper-Example-Stage-2.cml](https://github.com/ContextMapper/context-mapper-examples/blob/3c28b419e965e74aa3bfe616467cf5ebfff261a8/src/main/cml/context-mapper-example/ContextMapper-Example-Stage-2.cml) | 200 | `0100c23b4d50126afdb5dac952ae63187d2a0dd6648636d1673e5b0e8e69f928` |
| 2026-10-14 19:40:31 UTC | [eclipse-jdt/eclipse.jdt.ui/org.eclipse.jdt.ui/plugin.xml](https://github.com/eclipse-jdt/eclipse.jdt.ui/blob/c11bc906124cb07c1e5abbf29b4805164754d37c/org.eclipse.jdt.ui/plugin.xml) | 200 | `32106ab61d215359ec49ea39e68943d900066bb36e6d22c45920685cf964a60e` |
| 2026-10-14 19:40:30 UTC | [eclipse-jdt/eclipse.jdt.ui/org.eclipse.jdt.ui/ui/org/eclipse/jdt/internal/ui/packageview/PackageExplorerPart.java](https://github.com/eclipse-jdt/eclipse.jdt.ui/blob/c11bc906124cb07c1e5abbf29b4805164754d37c/org.eclipse.jdt.ui/ui/org/eclipse/jdt/internal/ui/packageview/PackageExplorerPart.java) | 200 | `126b876f55002406b55f42b4408abf192bd7f8feb9ff362e86cba328caa75766` |
| 2026-10-14 19:40:30 UTC | [ncats/blackboard/project/plugins.sbt](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/project/plugins.sbt) | 200 | `84ea109dcb4141b468172ae720c0fd57fe5c27459c9d32caa0f37fcdc9675059` |
| 2026-10-14 19:40:30 UTC | [ncats/blackboard/build.sbt](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/build.sbt) | 200 | `27775b71202a25b71a8bdcb80102fbee31c3c4b4945a7d388d2d14f2f8f3ee52` |
| 2026-10-14 19:40:31 UTC | [ncats/blackboard/app/controllers/api/kg/BlackboardSystem.java](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/app/controllers/api/kg/BlackboardSystem.java) | 200 | `3c897a6537366771c45eb4940856177aec26fbe3e3b5bb81c76ba3a0aeb7535b` |
| 2026-10-14 19:40:31 UTC | [ncats/blackboard/app/controllers/ks/KnowledgeSource.java](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/app/controllers/ks/KnowledgeSource.java) | 200 | `c2c779c3c2ab47134073413524fa63361e52de43860a2ed20b85c03a48d829e6` |
| 2026-10-14 19:40:31 UTC | [ncats/blackboard/modules/core/app/blackboard/KSource.java](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/modules/core/app/blackboard/KSource.java) | 200 | `8b29c373e2216bc59195b02d701503ef07602dd5caeb1c911320a47f25484a0d` |
| 2026-10-14 19:40:31 UTC | [ncats/blackboard/modules/chembl/src/main/java/blackboard/chembl/ChemblKSource.java](https://github.com/ncats/blackboard/blob/b06a98b26e807e9ea3eab9a107ec24d2393f5040/modules/chembl/src/main/java/blackboard/chembl/ChemblKSource.java) | 200 | `2dfba2275f3b36adb39de1bf6f7b0ca26d5ddfe39eb3f7f9e27aad5439b210e5` |
| 2026-10-14 19:40:31 UTC | [apache/nifi/nifi-connector-mock-bundle/nifi-connector-mock-test-bundle/nifi-connector-mock-test-connectors/src/main/resources/flows/Generate_and_Update.json](https://github.com/apache/nifi/blob/9e6c18893f1b1df713dac55d98c2b2944d235844/nifi-connector-mock-bundle/nifi-connector-mock-test-bundle/nifi-connector-mock-test-connectors/src/main/resources/flows/Generate_and_Update.json) | 200 | `3d57875e975c2f2becf22b9ca9a48a94e291fe8085ed27986778829d15e848cb` |
| 2026-10-14 19:40:31 UTC | [apache/nifi/nifi-extension-bundles/nifi-standard-bundle/nifi-standard-processors/src/main/java/org/apache/nifi/processors/standard/LookupAttribute.java](https://github.com/apache/nifi/blob/9e6c18893f1b1df713dac55d98c2b2944d235844/nifi-extension-bundles/nifi-standard-bundle/nifi-standard-processors/src/main/java/org/apache/nifi/processors/standard/LookupAttribute.java) | 200 | `6aea2985111023edefa3cbfa699af5797710c5fec5329434f7320291117c93e1` |
| 2026-10-14 19:40:31 UTC | [apache/nifi/nifi-extension-bundles/nifi-update-attribute-bundle/nifi-update-attribute-processor/src/main/java/org/apache/nifi/processors/attributes/UpdateAttribute.java](https://github.com/apache/nifi/blob/9e6c18893f1b1df713dac55d98c2b2944d235844/nifi-extension-bundles/nifi-update-attribute-bundle/nifi-update-attribute-processor/src/main/java/org/apache/nifi/processors/attributes/UpdateAttribute.java) | 200 | `c5fbffc1ded6bfdabd40e8da904fb01114bc8660d0ec3598f02ff4e65ca57844` |
| 2026-10-14 19:40:31 UTC | [domain-centric-development/dca-ecommerce-sample-dotnet/product/domain.md](https://github.com/domain-centric-development/dca-ecommerce-sample-dotnet/blob/640268e41f34a045554de4a134d3b850d9a0ba21/product/domain.md) | 200 | `4e520eb88bc59c1f95581aebec2b0765d44ceb5361517732aa3d8b9bc73f410f` |
| 2026-10-14 19:40:31 UTC | [domain-centric-development/dca-ecommerce-sample-dotnet/src/DcaShop.Backoffice/BackofficeContext.cs](https://github.com/domain-centric-development/dca-ecommerce-sample-dotnet/blob/640268e41f34a045554de4a134d3b850d9a0ba21/src/DcaShop.Backoffice/BackofficeContext.cs) | 200 | `006ea513744594beb67ddee40391d6a1e12f153e4d99d847fa477744a4363b4a` |
| 2026-10-14 19:40:31 UTC | [domain-centric-development/dca-ecommerce-sample-dotnet/tests/DcaShop.ArchitectureTests/DcaShop.ArchitectureTests.csproj](https://github.com/domain-centric-development/dca-ecommerce-sample-dotnet/blob/640268e41f34a045554de4a134d3b850d9a0ba21/tests/DcaShop.ArchitectureTests/DcaShop.ArchitectureTests.csproj) | 200 | `75e0b9d2c03bdcb1a0125e4f9a382dff4663b7493230b5586986917c8896f364` |
| 2026-10-14 19:40:31 UTC | [domain-centric-development/dca-ecommerce-sample-dotnet/tests/DcaShop.ArchitectureTests/ContextMapDocumentationTest.cs](https://github.com/domain-centric-development/dca-ecommerce-sample-dotnet/blob/640268e41f34a045554de4a134d3b850d9a0ba21/tests/DcaShop.ArchitectureTests/ContextMapDocumentationTest.cs) | 200 | `66a2d201990d978bc756bc3ba3ea240841ce57e09e52e3c59ea172a6f9d82f27` |
| 2026-10-14 19:40:31 UTC | [domain-centric-development/dca-ecommerce-sample-dotnet/docs/architecture/context-map.md](https://github.com/domain-centric-development/dca-ecommerce-sample-dotnet/blob/640268e41f34a045554de4a134d3b850d9a0ba21/docs/architecture/context-map.md) | 200 | `d77c7a9e371d333a0974707996c6db067037d09ec38c70072c65d3a8bf5d09ff` |

- [2026-10-14 19:40:32 UTC] GitHub público NCATS — `GET https://api.github.com/repos/ncats/blackboard` → `archived=true`.

A documentação primária [Context Mapper/CML](https://contextmapper.org/docs/context-map/) foi lida para interpretar SK, C/S, CF, OHS e o estado TO_BE. A documentação [Equinox](https://equinox.eclipseprojects.io/) identifica a base OSGi. Os caminhos de aplicação acima sustentam os exemplos; a documentação de framework não foi usada sozinha como prova de aplicação.

## Escopo do reparo e limites

Os títulos e a ordem das entradas permanecem nos mesmos caminhos do catálogo. Space-Based conserva o sample Apache Ignite e o rótulo REF; ele não foi tratado como lacuna. As explicações, o H1 visível integrado pela raiz, o anchor DDD e outros owners não foram reescritos.

Não resta ausência de fonte concreta nos oito itens reparados no nível solicitado de código ou modelo REF. O council ainda precisa decidir se o enquadramento e seus limites satisfazem TH1. Não foi comprovado uso desses acordos por equipes de produção, não foram executados os samples e não foi emitido aceite.

O limite original do histórico permanece: o censo de 12.697 commits é de metadados locais observados, com três diffs aprofundados. Não houve leitura semântica de todos os diffs nem uma nova passada ampla nesta rodada.

## Hashes finais locais

| Arquivo | SHA-256 |
|---|---|
| `content/referencia/catalogo/01-arquiteturas-de-aplicacao.mdx` | `94fbb6133740e753c78c8e48fe0a463fc59d6de767529c2410a3ce0566b0e44a` |
| `content/referencia/catalogo/10-ddd-domain-driven-design.mdx` | `c0a23012114f5d9169959853498fb2148b5116c5d928e4d1e635c2f190932633` |
