# Publicar o curso no EasyPanel

O usuário autorizou hospedar o curso no projeto do MakersHub, usando a senha informada no chat. O serviço exclusivo é hub/makershub-architecture-course. O conteúdo é o export Nextra já publicado; a implementação reutiliza o controle de acesso existente, com leitura local dos arquivos no container.

A execução deve configurar o serviço e disparar o deploy pelo MCP EasyPanel. O transporte de artefatos pode usar o acesso SSH existente ao manager. A senha e a chave de sessão ficam somente no ambiente de execução. O acesso sem sessão deve continuar bloqueado em HTML, RSC, arquivos estáticos, busca e download.

A conferência deve medir o clique em /tutoriais/state-machine/, confirmar o conteúdo visível, a busca e a saída, comparar o comportamento com o endereço anterior e registrar os limites da medição. Não declarar que a troca resolve a latência sem medir. Os serviços existentes do MakersHub ficam fora da alteração de configuração.
