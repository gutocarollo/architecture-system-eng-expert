import nextra from 'nextra'

const withNextra = nextra({})

export default withNextra({
  poweredByHeader: false,
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true }
})
