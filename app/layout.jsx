import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'

export const metadata = {
  title: {
    default: 'Arquitetura na prática — Faz Capital',
    template: '%s — Arquitetura na prática'
  },
  description: 'Aprenda arquitetura com problemas, código e dados do MakersHub e do Airflow.'
}

export default async function RootLayout({ children }) {
  return (
    <html lang="pt-BR" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={<Navbar logo={<b>Arquitetura na prática</b>} />}
          footer={<Footer>Material de estudo da Faz Capital.</Footer>}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/gutocarollo/architecture-system-eng-expert/tree/main"
          editLink={null}
          feedback={{ content: null }}
          toc={{ title: 'Nesta página' }}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
