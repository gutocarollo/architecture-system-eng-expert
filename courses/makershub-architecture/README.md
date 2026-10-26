# Arquitetura na prática: Makershub

Esta pasta contém a fonte editorial, a aplicação Nextra e os laboratórios do curso publicado em https://hub-makershub-architecture-course.6bv96u.easypanel.host. A pasta do Git não aparece nas URLs do site.

Os 18 casos apresentam explicação, tutorial, guia e referência completos na página de sua jornada, com sumário local. Cada texto tem uma única fonte em `case-content/<caso>/`. Os 72 endereços de facetas conservam o acesso aos mesmos corpos e aos fragmentos antigos. Todas as entradas mostram o caso, links do tema e o percurso Explicação → Tutorial → Guia → Referência.

Para construir o curso, use Node compatível com o lock e Python 3.11 ou posterior:

```sh
cd courses/makershub-architecture
npm ci
npm run build
npm test
```

O build gera o download de early-refresh a partir de `labs/architecture/early-refresh`, produz o export em `out/` e cria o índice Pagefind dentro desse export. `out/`, dependências e contextos Docker são gerados; não são outra fonte de edição.

Para praticar somente early-refresh, o Python usa a biblioteca padrão:

```sh
python3 labs/architecture/early-refresh/run.py
```

O download específico disponível no tutorial mantém essa mesma estrutura de diretórios. Ele não exige TypeScript, OpenTelemetry, OpenSSL ou acesso ao MakersHub. Os demais laboratórios conservam seus próprios pré-requisitos. Os scripts históricos de autoria e extração não fazem parte do build; eles podem reescrever páginas e precisam de uma mudança específica antes de serem reutilizados.

A navegação está em `components/CaseNavigation.jsx`, e o catálogo dos casos fica em `case-content/cases.js`. Os fatos repetidos de early-refresh ficam em `case-content/early-refresh.js`, e seus snapshots são identificados pelo manifesto do laboratório. O protocolo e os critérios de entrega estão em `docs/documentation-protocol.md` e `tasks/FBI-4991-case-navigation-all/`.

`scripts/compose-all-case-pages.mjs` registra a migração inicial e recusa uma segunda execução. Ele não faz parte do build. Depois da migração, edite os corpos canônicos; as páginas antigas são wrappers de compatibilidade. Os testes inventariam todos os casos, verificam suas etapas e preservam os fragmentos capturados antes da mudança.

Para congelar um contexto Docker depois dos testes:

```sh
python3 deploy/easypanel/package-export.py --path-only
```

O comando imprime uma pasta temporária com runtime, manifesto e export. Use essa pasta como contexto de build do Dockerfile incluído. Publique a imagem e selecione seu digest no serviço `hub/makershub-architecture-course`. A senha e o segredo de sessão continuam exclusivamente na configuração do serviço; nunca entram no código ou na imagem.
