# Ajustar a navegação e esclarecer a estrutura do curso

O usuário pediu que clicar em um grupo abra seu primeiro conteúdo, que a navegação use as transições de rolagem do Nextra do MakersHub e que o nome público seja Arquitetura na prática: Makershub. Também pediu para explicar a relação entre os quarenta padrões destacados, os 310 conceitos e a tabela de casos, além de ampliar o espaço disponível para as tabelas.

A implementação compara primeiro o Nextra instalado e o código atual do Help Center do MakersHub, sem escrever nesse repositório. O curso permanece no worktree da FBI-4991 e será publicado no serviço exclusivo hub/makershub-architecture-course pelo MCP EasyPanel. A senha existente é preservada. As regras de acesso, a navegação e a largura são verificadas no navegador.

A explicação deve distinguir conceitos referenciados, observações de laboratório, mecanismos efetivamente implementados e evidência de produção. A contagem não pode ser apresentada como prova de implementação ou de revisão completa. As mudanças devem permanecer reproduzíveis nos geradores que forem responsáveis pelos textos editados.

## Rechecagem do pacote publicado

A verificação hospedada confirmou o título, a largura, a navegação e o controle de acesso, mas encontrou a seta presa no grupo atual. O patch normaliza a barra final do foco. A primeira recompilação conservou o código anterior no JavaScript exportado. O gate de publicação agora exige conferir também o trecho compilado e repetir o clique no novo bundle. Os recibos das duas tentativas permanecem preservados; não são tratados como aprovação.
