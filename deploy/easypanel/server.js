import { serve } from '@hono/node-server'
import { fileURLToPath } from 'node:url'
import app from './app.js'

const configuredPort = process.env.PORT ?? '8080'
if (!/^\d+$/.test(configuredPort) || Number(configuredPort) < 1 || Number(configuredPort) > 65535) {
  throw new Error('PORT must be an integer between 1 and 65535')
}
const runtime = Object.freeze({
  COURSE_PASSWORD: process.env.COURSE_PASSWORD,
  COURSE_SESSION_SECRET: process.env.COURSE_SESSION_SECRET,
  COURSE_PUBLIC_ORIGIN: process.env.COURSE_PUBLIC_ORIGIN,
  COURSE_ASSETS_DIR: process.env.COURSE_ASSETS_DIR ?? fileURLToPath(new URL('./public/', import.meta.url))
})
const server = serve({
  hostname: '0.0.0.0',
  port: Number(configuredPort),
  fetch: (request, bindings) => app.fetch(request, { ...bindings, ...runtime })
}, info => console.info(`Course runtime listening on port ${info.port}`))

server.requestTimeout = 30_000
server.headersTimeout = 15_000
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, () => {
    server.close(error => process.exit(error ? 1 : 0))
    server.closeIdleConnections()
    setTimeout(() => process.exit(1), 10_000).unref()
  })
}
