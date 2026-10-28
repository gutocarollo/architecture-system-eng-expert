// Adapted from sites/architecture-course/worker/index.js.
// Original SHA-256: 3afee5efd34af4dbc9e8b6b50f031b6f6b09b325e4a1b9ee0b8e2010414cf825
// Keeps the password/session gate; replaces R2 with a contained local-file adapter.
import { Hono } from 'hono'
import { open, realpath } from 'node:fs/promises'
import { resolve, sep } from 'node:path'
import { Readable } from 'node:stream'
import { getMimeType } from 'hono/utils/mime'
import { deleteCookie, getSignedCookie, setSignedCookie } from 'hono/cookie'
import { timingSafeEqual } from 'hono/utils/buffer'

const app = new Hono()
const sessionName = 'course_session'
const sessionSeconds = 8 * 60 * 60
const maxLoginBytes = 4096
const releasePattern = /^[a-f0-9]{64}$/
const cookieOptions = { prefix: 'host', secure: true, httpOnly: true, sameSite: 'Lax', path: '/' }
const encoder = new TextEncoder()

function publicOrigin(env) {
  try {
    const url = new URL(env.COURSE_PUBLIC_ORIGIN)
    if (url.protocol !== 'https:' || url.origin !== env.COURSE_PUBLIC_ORIGIN) return null
    return url.origin
  } catch {
    return null
  }
}

function configured(env) {
  return typeof env.COURSE_PASSWORD === 'string' && env.COURSE_PASSWORD.length > 0 &&
    typeof env.COURSE_SESSION_SECRET === 'string' && env.COURSE_SESSION_SECRET.length >= 32 &&
    publicOrigin(env) !== null && typeof env.COURSE_ASSETS_DIR === 'string'
}

function decodedPath(value) {
  if (!value.startsWith('/') || /%2f|%5c|%25|\\/i.test(value)) return null
  try {
    const decoded = decodeURIComponent(value)
    if (/[\x00-\x1f\x7f\\]/.test(decoded) || decoded.includes('//')) return null
    if (decoded.split('/').some(part => part === '.' || part === '..')) return null
    return decoded
  } catch {
    return null
  }
}

function safeReturnTo(value, origin) {
  if (typeof value !== 'string' || value.length > 2048 || !decodedPath(value.split(/[?#]/)[0])) return '/'
  const target = new URL(value, origin)
  if (target.origin !== origin || /^\/(?:login|logout|_admin)(?:\/|$)/.test(target.pathname)) return '/'
  return target.pathname + target.search + target.hash
}

function sameOrigin(request, env) {
  return request.headers.get('Origin') === publicOrigin(env)
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character])
}

function loginPage(returnTo, failed = false) {
  return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Acesso ao curso</title></head><body><main><h1>Acesso ao curso</h1><p>Informe a senha compartilhada para abrir o curso.</p>${failed ? '<p role="alert">Senha inválida. Tente novamente.</p>' : ''}<form action="/login" method="post"><input type="hidden" name="returnTo" value="${escapeHtml(returnTo)}"><label for="password">Senha</label><input id="password" name="password" type="password" autocomplete="current-password" required maxlength="1024"><button type="submit">Entrar</button></form></main></body></html>`
}

async function passwordFingerprint(env) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(env.COURSE_SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(`course-password:${env.COURSE_PASSWORD}`))
  return Array.from(new Uint8Array(signature), byte => byte.toString(16).padStart(2, '0')).join('')
}

async function authenticated(c) {
  if ((c.req.header('Cookie')?.length ?? 0) > 8192) return false
  const value = await getSignedCookie(c, c.env.COURSE_SESSION_SECRET, sessionName, 'host')
  if (!value) return false
  try {
    const session = JSON.parse(value)
    const now = Math.floor(Date.now() / 1000)
    if (session.version !== 1 || !Number.isSafeInteger(session.issuedAt) || !Number.isSafeInteger(session.expiresAt)) return false
    if (session.issuedAt > now || session.expiresAt <= now || session.expiresAt - session.issuedAt !== sessionSeconds) return false
    if (typeof session.passwordHash !== 'string' || !releasePattern.test(session.passwordHash)) return false
    return await timingSafeEqual(session.passwordHash, await passwordFingerprint(c.env))
  } catch {
    return false
  }
}

async function boundedLoginBody(request) {
  const declaredLength = request.headers.get('Content-Length')
  if (declaredLength !== null && (!/^\d+$/.test(declaredLength) || Number(declaredLength) > maxLoginBytes)) return null
  if (!request.body) return ''
  const reader = request.body.getReader()
  const chunks = []
  let size = 0
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      size += value.byteLength
      if (size > maxLoginBytes) {
        await reader.cancel()
        return null
      }
      chunks.push(value)
    }
  } finally {
    reader.releaseLock()
  }
  const bytes = new Uint8Array(size)
  let offset = 0
  for (const chunk of chunks) {
    bytes.set(chunk, offset)
    offset += chunk.byteLength
  }
  return new TextDecoder().decode(bytes)
}

app.use('*', async (c, next) => {
  c.header('Cache-Control', 'private, no-store')
  c.header('Vary', 'Cookie')
  c.header('X-Content-Type-Options', 'nosniff')
  c.header('Referrer-Policy', 'same-origin')
  if (!configured(c.env)) return c.text('Acesso temporariamente indisponível.', 503)
  const rawPath = c.env.incoming?.url?.split(/[?#]/)[0] ?? c.req.url.match(/^https?:\/\/[^/]+([^?#]*)/)?.[1] ?? '/'
  const path = decodedPath(rawPath)
  if (!path) return c.text('Caminho inválido.', 400)
  c.set('assetPath', path)
  await next()
})

app.get('/login', c => {
  c.header('Content-Security-Policy', "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
  return c.html(loginPage(safeReturnTo(c.req.query('returnTo'), publicOrigin(c.env))))
})

app.post('/login', async c => {
  if (!sameOrigin(c.req.raw, c.env)) return c.text('Origem inválida.', 403)
  if (c.req.header('Content-Type')?.split(';')[0].trim().toLowerCase() !== 'application/x-www-form-urlencoded') return c.text('Formato inválido.', 415)
  const body = await boundedLoginBody(c.req.raw)
  if (body === null) return c.text('Solicitação muito grande.', 413)
  const form = new URLSearchParams(body)
  const password = form.get('password') ?? ''
  const returnTo = safeReturnTo(form.get('returnTo'), publicOrigin(c.env))
  if (form.getAll('password').length !== 1 || password.length > 1024 || !await timingSafeEqual(password, c.env.COURSE_PASSWORD)) {
    c.header('Content-Security-Policy', "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
    return c.html(loginPage(returnTo, true), 401)
  }
  const issuedAt = Math.floor(Date.now() / 1000)
  const expiresAt = issuedAt + sessionSeconds
  await setSignedCookie(c, sessionName, JSON.stringify({ version: 1, issuedAt, expiresAt, passwordHash: await passwordFingerprint(c.env) }), c.env.COURSE_SESSION_SECRET, {
    ...cookieOptions, maxAge: sessionSeconds, expires: new Date(expiresAt * 1000)
  })
  return c.redirect(returnTo, 303)
})

app.post('/logout', c => {
  if (!sameOrigin(c.req.raw, c.env)) return c.text('Origem inválida.', 403)
  deleteCookie(c, sessionName, cookieOptions)
  return c.redirect('/login', 303)
})

async function localAsset(root, key, head) {
  const base = await realpath(root)
  const candidate = resolve(base, key)
  if (!candidate.startsWith(base + sep)) return null
  let handle
  try {
    const canonical = await realpath(candidate)
    if (!canonical.startsWith(base + sep)) return null
    handle = await open(canonical, 'r')
    const metadata = await handle.stat()
    if (!metadata.isFile()) {
      await handle.close()
      return null
    }
    if (head) {
      await handle.close()
      return { size: metadata.size, body: null }
    }
    return { size: metadata.size, body: Readable.toWeb(handle.createReadStream()) }
  } catch (error) {
    await handle?.close()
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR' || error.code === 'EACCES') return null
    throw error
  }
}

app.all('*', async c => {
  const path = c.get('assetPath')
  if (path === '/login' || path === '/logout' || path === '/_admin' || path.startsWith('/_admin/')) return c.text('Método não permitido.', 405)
  if (c.req.method !== 'GET' && c.req.method !== 'HEAD') return c.text('Método não permitido.', 405, { Allow: 'GET, HEAD' })
  if (!await authenticated(c)) {
    const asset = path.startsWith('/_next/') || path.startsWith('/_pagefind/') || /\.[^/]+$/.test(path) && !path.endsWith('.html')
    if (asset) return c.text('Acesso negado.', 401)
    const returnTo = safeReturnTo(new URL(c.req.url).pathname + new URL(c.req.url).search, publicOrigin(c.env))
    return c.redirect('/login?returnTo=' + encodeURIComponent(returnTo), 303)
  }
  if (path.split('/').some(segment => segment.startsWith('.'))) return c.text('Página não encontrada.', 404)
  const relative = path.slice(1)
  const key = !relative || path.endsWith('/') ? relative + 'index.html' : /\.[^/]+$/.test(path) ? relative : relative + '/index.html'
  const object = await localAsset(c.env.COURSE_ASSETS_DIR, key, c.req.method === 'HEAD')
  if (!object) return c.text('Página não encontrada.', 404)
  c.header('Content-Type', getMimeType(key) ?? 'application/octet-stream')
  c.header('Content-Length', String(object.size))
  return c.body(object.body, 200)
})

app.onError(() => new Response('Acesso temporariamente indisponível.', { status: 503, headers: {
  'Cache-Control': 'private, no-store', Vary: 'Cookie', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin'
} }))

export default app
