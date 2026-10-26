import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { requestJson, describeError } from '../src/api/client.ts'
const fetchOriginal = globalThis.fetch
afterEach(() => { globalThis.fetch = fetchOriginal })
const campaign = { id: 'c1', workspace_id: 'w1', name: 'Launch', publication_date: '2026-11-12', caption: '', content_revision: 1, source_revision: 0, created_at: '2026-10-26T00:00:00Z' }
function session() { return { workspace_id: 'w1', mode: 'synthetic_demo', notice: 'Synthetic demo', expires_at: '2099-01-01T00:00:00Z', actors: Object.fromEntries(['owner','creator','reviewer'].map(role => [role, {role,access_token: `test-${role}`}])) } }
test('bodyless session uses creator bearer; exact campaign payload and full revisions preserved', async () => {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push(url)
    if (url.endsWith('demo-sessions')) { assert.equal(options.method, 'POST'); assert.equal(options.body, undefined); assert.equal(options.headers.get('Authorization'), null); return Response.json(session()) }
    assert.equal(options.headers.get('Authorization'), 'Bearer test-creator')
    if (options.method === 'POST') assert.deepEqual(JSON.parse(options.body), { name: 'Launch', publication_date: '2026-11-12' })
    return Response.json(url.endsWith('/campaigns') && !options.method ? [] : campaign)
  }
  const client = createBackendClient('http://test/api/v1')
  await client.connect()
  const saved = await client.create({ title: 'Launch', publicationDate: '2026-11-12', brand: 'not sent', brief: 'not sent' })
  assert.deepEqual(saved.data.reviews[0].backendCampaign, campaign)
  assert.equal((await client.get('c1')).data.reviews[0].id, 'c1')
  assert.equal(calls.filter(url => url.endsWith('demo-sessions')).length, 1)
  // A new JS client has no restored session and cannot read the old workspace.
  await assert.rejects(createBackendClient('http://test/api/v1').list(), error => error.status === 401)
})
test('runtime envelope preserves safe details and actionable status errors', async () => {
  for (const status of [401,403,404,409,422]) {
    globalThis.fetch = async () => Response.json({ error: { code: 'test_error', message: 'Backend message', details: [{ location: ['body','publication_date'], message: 'Invalid date' }] } }, { status })
    await assert.rejects(requestJson('http://test'), error => {
      assert.equal(error.status, status); assert.equal(error.code, 'test_error')
      assert.match(describeError(error), /Backend message/)
      assert.match(describeError(error), /publication_date: Invalid date/)
      return true
    })
  }
})
test('connected write failure is not retried or turned into local success', async () => {
  let writes = 0
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('demo-sessions')) return Response.json(session())
    if (!options.method) return Response.json([])
    writes++; throw new TypeError('Offline')
  }
  const client = createBackendClient('http://test/api/v1')
  await client.connect()
  await assert.rejects(client.create({ title: 'Launch', publicationDate: '2026-11-12', brand: '', brief: '' }), error => error.status === 0)
  assert.equal(writes, 1)
})
