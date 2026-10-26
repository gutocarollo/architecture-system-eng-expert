import { useMDXComponents as getThemeComponents } from 'nextra-theme-docs'

const theme = getThemeComponents()
const aliases = { 'guide-before-start': ['antes-de-começar'] }

function withLegacyAnchors(Heading) {
  return function LegacyHeading(props) {
    return <>{(aliases[props.id] || []).map(id => <span key={id} id={id} className="case-legacy-anchor" />)}<Heading {...props} /></>
  }
}

export const legacyCaseHeadings = {
  h3: withLegacyAnchors(theme.h3),
  h4: withLegacyAnchors(theme.h4)
}
