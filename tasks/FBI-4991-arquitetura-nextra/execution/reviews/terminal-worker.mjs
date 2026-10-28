import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { createServer } from 'node:http'
import { Readable } from 'node:stream'
import puppeteer from 'puppeteer-core'

const root = process.cwd()
const site = path.join(root, 'sites/architecture-course')
const { build } = await import(pathToFileURL(path.join(site, 'server-build/node_modules/esbuild/lib/main.js')))
const source = await readFile(path.join(site, 'worker/index.js'), 'utf8')
const temp = await mkdtemp(path.join(tmpdir(), 'terminal-fbi4991-worker-'))
const report = { startedAt: new Date().toISOString(), sourceSha256: createHash('sha256').update(source).digest('hex'),
  scope: 'Independent local adversarial inputs; fake private R2 and real headless Chrome. Synthetic credentials only; no live service mutation.', checks: [], mutations: [], browser: {} }
const synthetic = { COURSE_PASSWORD: 'terminal-fixture-course-only', COURSE_SESSION_SECRET: 'terminal-session-signing-fixture-'.repeat(3),
  COURSE_UPLOAD_SECRET: 'terminal-upload-bearer-fixture-'.repeat(3), COURSE_RELEASE_ID: 'b'.repeat(64) }
let reads = [], writes = [], failRead = false, failWrite = false
const html = '<!doctype html><html><title>Terminal private course</title><h1>Terminal private course</h1><script src="/_next/terminal.js"></script><form method="post" action="/logout"><button>Leave course</button></form></html>'
const env = { ...synthetic, COURSE_ASSETS: {
  async get(key) { reads.push(key); if (failRead) throw new Error('synthetic transient read failure'); return { body: new Blob([key.endsWith('.js') ? 'window.terminalAssetLoaded=true' : html]).stream(), httpMetadata: { contentType: key.endsWith('.js') ? 'text/javascript' : 'text/html' } } },
  async put(key, stream, options) { if (failWrite) throw new Error('synthetic transient write failure'); const bytes = await new Response(stream).arrayBuffer(); writes.push({ key, bytes: bytes.byteLength, options }); return {} }
} }
globalThis.FixedLengthStream = class extends TransformStream { constructor(expected) { let count = 0; super({ transform(value, controller) { count += value.byteLength; if (count > expected) throw new Error('oversized'); controller.enqueue(value) }, flush() { if (count !== expected) throw new Error('short') } }) } }
const origin = 'https://terminal.example'
async function bundle(contents, label) { const outfile = path.join(temp, label + '.mjs'); await build({ stdin: { contents, resolveDir: path.join(site, 'worker'), sourcefile: 'index.js' }, outfile, bundle: true, platform: 'browser', target: 'es2022', format: 'esm', nodePaths: [path.join(site, 'server-build/node_modules')] }); return (await import(pathToFileURL(outfile))).default }
let worker = await bundle(source, 'original')
function request(url, options = {}, settings = env) { return worker.fetch(new Request(origin + url, options), settings) }
function login(options = {}, settings = env) { const { password = synthetic.COURSE_PASSWORD, returnTo = '/', originHeader = origin, contentType = 'application/x-www-form-urlencoded', body, ...extra } = options; return request('/login', { method: 'POST', headers: { ...(originHeader === null ? {} : { Origin: originHeader }), 'Content-Type': contentType }, body: body ?? new URLSearchParams({ password, returnTo }).toString(), ...extra }, settings) }
function cookie(response) { return response.headers.get('set-cookie')?.split(';')[0] }
async function check(name, operation) { reads = []; writes = []; await operation(); report.checks.push({ name, passed: true, r2Reads: reads.length, r2Writes: writes.length }) }

try {
  await check('anonymous HTML, Next, Pagefind, RSC, download and HEAD deny before R2', async () => {
    for (const url of ['/', '/jornadas/security', '/index.html', '/_next/static/app.js', '/_pagefind/pagefind.js', '/jornadas/security.txt', '/jornadas/security?_rsc=terminal', '/downloads/architecture-labs.zip', '/404.html']) {
      for (const method of ['GET', 'HEAD']) { const response = await request(url, { method }); assert.ok([401, 303].includes(response.status), url); assert.equal(response.headers.get('cache-control'), 'private, no-store'); assert.equal(response.headers.get('vary'), 'Cookie') }
    }
    assert.equal(reads.length, 0)
  })
  await check('fail closed for missing config and R2 bindings', async () => {
    for (const key of Object.keys(synthetic).concat('COURSE_ASSETS')) { assert.equal((await request('/', {}, { ...env, [key]: undefined })).status, 503) }
    assert.equal(reads.length, 0)
  })
  await check('same-origin POST gate rejects missing null and foreign origins', async () => {
    for (const value of [null, 'null', 'https://foreign.example']) { assert.equal((await login({ originHeader: value })).status, 403); assert.equal((await request('/logout', { method: 'POST', headers: value === null ? {} : { Origin: value } })).status, 403) }
    assert.equal(reads.length, 0)
  })
  await check('invalid, duplicate, oversized and wrong-type logins cannot issue sessions', async () => {
    for (const [options, status] of [[{ password: 'wrong-fixture' }, 401], [{ body: 'password=a&password=b' }, 401], [{ body: 'x'.repeat(4097) }, 413], [{ contentType: 'application/json', body: '{}' }, 415]]) { const r = await login(options); assert.equal(r.status, status); assert.equal(r.headers.get('set-cookie'), null) }
  })
  let validCookie
  await check('valid signed host session unlocks all resource classes and HEAD has no body', async () => {
    const r = await login(); assert.equal(r.status, 303); validCookie = cookie(r); const attr = r.headers.get('set-cookie'); for (const expected of ['__Host-course_session=', 'Secure', 'HttpOnly', 'SameSite=Lax', 'Path=/', 'Max-Age=28800']) assert.ok(attr.includes(expected), expected)
    for (const url of ['/', '/_next/terminal.js', '/_pagefind/pagefind.js', '/downloads/architecture-labs.zip', '/jornadas/security.txt', '/jornadas/security?_rsc=terminal']) assert.equal((await request(url, { headers: { Cookie: validCookie } })).status, 200)
    const h = await request('/_next/terminal.js', { method: 'HEAD', headers: { Cookie: validCookie } }); assert.equal(h.status, 200); assert.equal(await h.text(), ''); assert.ok(reads.every(x => x.startsWith('releases/' + synthetic.COURSE_RELEASE_ID + '/')))
  })
  await check('tampered, unsigned and unprefixed sessions cannot read R2', async () => {
    for (const value of [validCookie + 'x', '__Host-course_session=unsigned', validCookie.replace('__Host-', ''), validCookie.slice(0, -6) + 'AAAAAA']) assert.equal((await request('/_next/terminal.js', { headers: { Cookie: value } })).status, 401)
    assert.equal(reads.length, 0)
  })
  await check('password and signing-secret rotation invalidate existing session', async () => {
    for (const settings of [{ ...env, COURSE_PASSWORD: 'rotated-synthetic-password' }, { ...env, COURSE_SESSION_SECRET: 'rotated-signing-secret-'.repeat(4) }]) assert.equal((await request('/_next/terminal.js', { headers: { Cookie: validCookie } }, settings)).status, 401)
    assert.equal(reads.length, 0)
  })
  await check('expired and future-issued signed sessions are rejected server-side', async () => {
    const originalNow = Date.now; const now = originalNow()
    try { Date.now = () => now + 28801 * 1000; assert.equal((await request('/_next/terminal.js', { headers: { Cookie: validCookie } })).status, 401); const futureCookie = cookie(await login()); Date.now = () => now; assert.equal((await request('/_next/terminal.js', { headers: { Cookie: futureCookie } })).status, 401) } finally { Date.now = originalNow }
    assert.equal(reads.length, 0)
  })
  await check('open redirect and encoded path attacks cannot select foreign objects', async () => {
    for (const value of ['//foreign.example/path', '/%2f%2fforeign.example', '/_admin/assets', '/login', '/%255fadmin/assets']) { const r = await login({ returnTo: value }); assert.equal(r.headers.get('location'), '/') }
    for (const value of ['/%2Fsecret', '/%5csecret', '/%252e%252e/secret', '/bad%00name', '/double//slash', '/bad%zz']) assert.equal((await request(value, { headers: { Cookie: validCookie } })).status, 400)
    assert.equal(reads.length, 0)
  })
  const uploadPath = '/_admin/assets?release=' + synthetic.COURSE_RELEASE_ID + '&path=terminal.txt'
  const uploadHeaders = { Authorization: 'Bearer ' + synthetic.COURSE_UPLOAD_SECRET, 'Content-Length': '4', 'X-Asset-Content-Type': 'text/plain', 'X-Asset-Sha256': createHash('sha256').update('test').digest('hex') }
  await check('session and course password do not authorize admin uploads', async () => {
    for (const headers of [{ Cookie: validCookie }, { Authorization: 'Bearer ' + synthetic.COURSE_PASSWORD }, {}]) assert.equal((await request(uploadPath, { method: 'PUT', headers, body: 'test' })).status, 401)
    assert.equal(writes.length, 0)
  })
  await check('bounded admin upload validates method destination checksum and size', async () => {
    assert.equal((await request(uploadPath, { method: 'GET', headers: uploadHeaders })).status, 405)
    for (const url of [uploadPath.replace('terminal.txt', '../leak'), uploadPath + '&path=second', uploadPath.replace('terminal.txt', '%2fsecret')]) assert.equal((await request(url, { method: 'PUT', headers: uploadHeaders, body: 'test' })).status, 400)
    assert.equal((await request(uploadPath, { method: 'PUT', headers: { ...uploadHeaders, 'Content-Length': String(25 * 1024 * 1024 + 1) }, body: 'test' })).status, 413)
    const r = await request(uploadPath, { method: 'PUT', headers: uploadHeaders, body: 'test' }); assert.equal(r.status, 204); assert.equal(writes.length, 1); assert.equal(writes[0].options.sha256, uploadHeaders['X-Asset-Sha256'])
    assert.equal((await request(uploadPath, { method: 'PUT', headers: { ...uploadHeaders, 'Content-Length': '2' }, body: 'test' })).status, 400)
  })
  await check('read and write failures fail closed then recover on next request', async () => {
    failRead = true; assert.equal((await request('/', { headers: { Cookie: validCookie } })).status, 503); failRead = false; assert.equal((await request('/', { headers: { Cookie: validCookie } })).status, 200)
    failWrite = true; assert.equal((await request(uploadPath, { method: 'PUT', headers: uploadHeaders, body: 'test' })).status, 400); failWrite = false; assert.equal((await request(uploadPath, { method: 'PUT', headers: uploadHeaders, body: 'test' })).status, 204)
  })
  await check('logout expires host cookie and subsequent anonymous access is denied', async () => { const r = await request('/logout', { method: 'POST', headers: { Origin: origin, Cookie: validCookie } }); assert.equal(r.status, 303); assert.ok(r.headers.get('set-cookie').startsWith('__Host-course_session=')); assert.ok(r.headers.get('set-cookie').includes('Max-Age=0')); assert.equal((await request('/_pagefind/pagefind.js')).status, 401); assert.equal(reads.length, 0) })

  for (const [name, before, after, url, options, expected] of [
    ['anonymous-gate-removal', 'if (!await authenticated(c)) {', 'if (false) {', '/_next/terminal.js', {}, 401],
    ['origin-gate-removal', 'if (!sameOrigin(c.req.raw))', 'if (false)', '/login', { method: 'POST', headers: { Origin: 'https://foreign.example', 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ password: synthetic.COURSE_PASSWORD }).toString() }, 403]
  ]) { assert.ok(source.includes(before)); worker = await bundle(source.replace(before, after), name); let killed = false; try { assert.equal((await request(url, options)).status, expected) } catch { killed = true } assert.ok(killed); report.mutations.push({ name, killed }) }
  worker = await bundle(source, 'browser-original')
  reads = []
  const events = []
  const server = createServer(async (incoming, outgoing) => {
    const incomingUrl = new URL(incoming.url, 'http://' + incoming.headers.host)
    const req = new Request(incomingUrl, { method: incoming.method, headers: incoming.headers, ...(incoming.method === 'POST' ? { body: Readable.toWeb(incoming), duplex: 'half' } : {}) })
    let response = await worker.fetch(req, env)
    if (incomingUrl.pathname === '/login' && incoming.method === 'GET') response = new Response((await response.text()).replace('</body>', '<script>window.terminalPlatformScript=true</script></body>'), response)
    events.push({ method: incoming.method, path: incomingUrl.pathname, origin: incoming.headers.origin ?? null, status: response.status, reads: reads.length })
    outgoing.writeHead(response.status, Object.fromEntries(response.headers)); if (response.body) Readable.fromWeb(response.body).pipe(outgoing); else outgoing.end()
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  let browser
  try {
    const browserOrigin = 'http://localhost:' + server.address().port
    browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--no-default-browser-check'] })
    const page = await browser.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message))
    await page.goto(browserOrigin + '/jornadas/terminal', { waitUntil: 'networkidle0' }); assert.equal(new URL(page.url()).pathname, '/login'); assert.equal(await page.evaluate(() => window.terminalPlatformScript), true); assert.equal(reads.length, 0)
    await page.type('#password', 'wrong-synthetic'); await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('button')]); assert.ok((await page.$eval('[role="alert"]', e => e.textContent)).includes('inválida'))
    await page.type('#password', synthetic.COURSE_PASSWORD); await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('button')]); assert.equal(new URL(page.url()).pathname, '/jornadas/terminal'); assert.equal(await page.title(), 'Terminal private course'); assert.equal(await page.evaluate(() => window.terminalAssetLoaded), true)
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('button')]); assert.equal(new URL(page.url()).pathname, '/login'); const denied = await page.evaluate(async () => (await fetch('/_pagefind/pagefind.js')).status); assert.equal(denied, 401); assert.deepEqual(errors, [])
    report.browser = { passed: true, browserOrigin, browserVersion: await browser.version(), events, pageErrors: errors, logoutSearchStatus: denied, scope: 'Real Chromium form POST origin, cookie acceptance, wrong-password recovery, private JS and logout; local synthetic R2 only.' }
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)) }
  report.verdict = 'PASS'
} catch (error) { report.verdict = 'FAIL'; report.failure = String(error.stack); throw error }
finally { report.finishedAt = new Date().toISOString(); await writeFile(path.join(root, 'tasks/FBI-4991-arquitetura-nextra/execution/reviews/terminal-worker.json'), JSON.stringify(report, null, 2) + '\n'); await rm(temp, { recursive: true, force: true }); console.log(JSON.stringify({ verdict: report.verdict, checks: report.checks.length, mutations: report.mutations.length, browser: report.browser.passed ?? false, sourceSha256: report.sourceSha256 })) }
