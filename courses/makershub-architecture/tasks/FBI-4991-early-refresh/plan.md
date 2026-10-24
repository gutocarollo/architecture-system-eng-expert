# Caso early-refresh autocontido — plano de implementação

> Execução autorizada pelo proprietário nesta conversa: implementar o piloto, commitar no GitHub numa pasta nova e atualizar a imagem do serviço Easypanel existente.

**Objetivo:** permitir entender, praticar, aplicar e consultar early-refresh pela navegação do próprio caso, preservando as cinco URLs e seus fragmentos.

**Arquitetura:** o curso existente passa a morar em `courses/makershub-architecture/`, com uma única árvore editorial e build estático. Um componente compartilhado apresenta a identidade e os destinos do caso. Os fatos repetidos vêm de dados e trechos compartilhados. Os demais casos conservam o conteúdo importado.

**Tecnologias:** Nextra/theme 4.6.1, Next 16.4.3 (patch de segurança da linha 16.4), React 19.3.0, Pagefind 1.5.2; runtime Hono existente.

**Especificação:** análise e recomendação aprovadas na conversa, seguidas da ordem literal: “execute a mudança, commite no github nesse repositorio em uma pasta nova https://github.com/gutocarollo/architecture-system-eng-expert e depois faça push no easypanel da imagem atualizada”.

## Restrições

- Escrever apenas na nova pasta do curso. A fonte anterior permanece somente leitura.
- Conservar as cinco rotas, os fragmentos publicados, as finalidades Diátaxis e a autenticação existente.
- Não reorganizar outros casos, não trocar bibliotecas e não versionar credenciais, caches ou builds.
- Uma fonte editorial por conteúdo; pacotes de download são gerados a partir do laboratório versionado.
- Revisão independente antes do push e deploy; ler de volta o commit remoto, o digest e as páginas publicadas.

## Foco da revisão

- Entrada direta na referência com fragmento, sem passar pela jornada.
- Navegação local em tela estreita e por teclado, sem cobrir o título ou foco.
- Herança de `_meta.js` e manutenção da navegação dos demais casos.
- Arquivos portáveis, inclusive laboratório e dependências MDX, dentro da nova pasta.
- Índice Pagefind e artefato Docker correspondentes ao código commitado.

## Tarefas

- [ ] Importar a fonte correspondente ao export publicado e registrar um checkpoint restaurável.
- [ ] Criar verificações de HTML que falhem na versão anterior pela ausência da navegação local.
- [ ] Implementar identidade, navegação persistente, fatos compartilhados e preparação específica do laboratório.
- [ ] Gerar o download diretamente do laboratório, construir o curso e conferir rotas, âncoras, busca e comportamento no navegador.
- [ ] Demonstrar que os testes detectam a remoção da navegação e a quebra de um link compartilhado.
- [ ] Obter revisão independente e resolver achados materiais.
- [ ] Commitar e enviar ao GitHub, construir e enviar a imagem e atualizar o serviço existente por digest.
- [ ] Conferir commit remoto, container, HTML e percurso publicado; registrar reversão.

## Decisões

- A pasta Git não cria um prefixo de URL: o serviço continua servindo o curso em `/`.
- A configuração de exportação passa a ser a configuração única desta pasta; não haverá outro checkout editorial em `sites/`.
- O modo de execução é local, com o principal como único escritor e um revisor independente ao final.
- A captura de iniciativa Hindsight falhou no servidor com erro de índice HNSW; não bloqueia o código e não autoriza alterar o serviço de memória.
