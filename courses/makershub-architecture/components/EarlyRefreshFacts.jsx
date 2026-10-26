import { earlyRefresh } from '../case-content/early-refresh.js'
import manifest from '../labs/architecture/early-refresh/manifest.json'
import { useMDXComponents as getThemeComponents } from 'nextra-theme-docs'

const CourseLink = getThemeComponents().a

export function EarlyRefreshFact({ name }) {
  if (!['inputs', 'before', 'mechanism', 'outcome', 'limits'].includes(name)) {
    throw new Error(`Unknown early-refresh fact: ${name}`)
  }
  return <p data-case-fact={name}>{earlyRefresh[name]}</p>
}

export function EarlyRefreshOutput() {
  return <pre className="case-output" data-case-output="early-refresh"><code>{earlyRefresh.expectedOutput}</code></pre>
}

export function EarlyRefreshCommand() {
  return <pre className="case-output"><code>{earlyRefresh.command}</code></pre>
}

export function EarlyRefreshCommandInline() {
  return <code>{earlyRefresh.command}</code>
}

export function EarlyRefreshSources() {
  return (
    <div className="case-table">
      <table>
        <thead><tr><th>Fase</th><th>Fonte histórica</th><th>SHA</th><th>Cópia do laboratório</th></tr></thead>
        <tbody>
          {manifest.snapshots.map(snapshot => (
            <tr key={snapshot.phase}>
              <td>{snapshot.phase === 'before' ? 'Anterior' : 'Posterior'}</td>
              <td><CourseLink href={snapshot.phase === 'before' ? earlyRefresh.beforeUrl : earlyRefresh.afterUrl}>{snapshot.source_path}</CourseLink></td>
              <td><code>{snapshot.sha}</code></td>
              <td><code>{snapshot.local_path}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>O diff preservado é <code>labs/architecture/early-refresh/source.diff</code>; seu SHA-256 é{' '}
        <code>{manifest.diff_sha256}</code>. O manifesto na mesma pasta identifica os hashes dos snapshots.
        Esses localizadores descrevem o recorte histórico; não certificam outro checkout ou deploy.
      </p>
    </div>
  )
}

export function EarlyRefreshProvenance() {
  return (
    <p data-case-fact="provenance">
      Este caso vem do <CourseLink href={earlyRefresh.issueUrl}>card FBI-2331</CourseLink> e do{' '}
      <CourseLink href={earlyRefresh.pullRequestUrl}>PR 51</CourseLink>. A investigação leu o conteúdo visível do card,
      a descrição e os comentários pertinentes do PR. Você pode comparar a{' '}
      <CourseLink href={earlyRefresh.beforeUrl}>versão anterior</CourseLink> com a{' '}
      <CourseLink href={earlyRefresh.afterUrl}>versão alterada</CourseLink>. A prática executa esse recorte em isolamento;
      o estado de produção não foi medido por ela.
    </p>
  )
}
