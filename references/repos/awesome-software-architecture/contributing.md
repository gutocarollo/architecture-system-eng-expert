# Contribution Guidelines

Awesome Architecture is a Markdown-first catalog. Content lives in [`docs/`](docs/), and the web experience indexes those documents into collections, subcollections, and topic pages.

## Add a Resource

1. Choose the most specific existing topic file under [`docs/`](docs/). Prefer an existing subcollection over creating a new one.
2. Add the resource using this format:

   ```text
   [Name](URL) | Library, project, article, or book | GitHub-UserName/GitHub-RepositoryName - Short description
   ```

3. Keep descriptions concise, factual, and useful. Explain what the resource provides.
4. Preserve the surrounding file's ordering and Markdown style.
5. Use the `**[Research]**` tag for research or academic projects.

Resources must be educational, technical, or genuinely useful to architecture practitioners. Promotional, advertorial, sponsored, or sales-focused resources are not accepted.

## Add a Topic

Create a new Markdown file when no existing topic is a good fit. Place it in the relevant collection or nested subcollection. The web catalog discovers Markdown files automatically.

Use lowercase kebab-case for new filenames, for example `distributed-tracing.md`. Keep the topic focused and avoid duplicating links from another topic.

Create a new collection or subcollection only when the content represents a meaningful group of topics. Use one of these collections:

- `ai`
- `foundations`
- `distributed-systems`
- `data`
- `cloud-platforms`
- `devops`
- `software-architecture` (with `architecture-patterns/` and `anti-patterns/` subcollections)

The web catalog derives collection and topic navigation from this folder structure. Do not add a separate navigation file or landing document unless it contains useful content.

## Validate Changes

Before opening a pull request:

- Check every new URL and make sure it points to the intended resource.
- Confirm local links use paths relative to the edited Markdown file.
- Keep descriptions concise and free of promotional claims.
- Run repository checks:

  ```bash
  cd web
  npm ci
  npm run lint
  npm run build
  ```

- Review the generated web route and README collection map when adding or moving a topic.

## Pull Requests

- Keep each pull request focused on one collection or closely related topic.
- Use a meaningful title and describe what changed and why.
- Include screenshots for user-facing web changes when useful.
- Do not modify unrelated collections or reformat large files.

## Documentation Structure

- [`docs/`](docs/) is the source catalog.
- [`web/`](web/) contains the searchable static web experience.
- [`README.md`](README.md) provides the repository overview and collection map.
- [`assets/home.png`](assets/home.png) is the README web preview.

Thanks to all [contributors](https://github.com/mehdihadeli/awesome-software-architecture/graphs/contributors) for improving the collection.
