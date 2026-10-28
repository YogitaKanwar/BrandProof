import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { loadInitialWorkspace } from '../src/workspaceStartup.ts'

const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })
const actorRoles = ['owner', 'creator', 'reviewer']
const session = {
  workspace_id: 'same-workspace', mode: 'synthetic_demo', notice: 'Fictional data only', expires_at: '2099-01-01T00:00:00Z',
  actors: Object.fromEntries(actorRoles.map(role => [role, { role, access_token: `test-${role}` }])),
}
const campaign = { id: 'saved-campaign', workspace_id: session.workspace_id, name: 'Saved review', publication_date: '2026-11-12', caption: 'Saved content', content_revision: 3, source_revision: 2, created_at: '2026-10-26T00:00:00Z' }
const localData = { mode: 'local', notice: 'Local only', data: { campaigns: [], reviews: [{ id: 'local-draft', title: 'Local draft' }] } }
const backendData = { mode: 'backend', notice: 'Resumed', data: { campaigns: [], reviews: [{ id: 'server-draft', title: 'Saved review' }] } }

test('fresh JS client restores saved campaigns using a cookie request and keeps bearer credentials in memory', async () => {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push(url)
    if (url.endsWith('/resume')) {
      assert.equal(options.method, 'POST')
      assert.equal(options.credentials, 'include')
      assert.equal(options.cache, 'no-store')
      assert.equal(options.headers.get('X-BrandProof-Session'), 'resume')
      assert.equal(options.headers.get('Authorization'), null)
      assert.equal(options.body, undefined)
      return Response.json(session)
    }
    assert.equal(options.headers.get('Authorization'), 'Bearer test-creator')
    return Response.json([campaign])
  }
  const first = await createBackendClient('http://test/api/v1').resume()
  const refreshed = await createBackendClient('http://test/api/v1').resume()
  assert.deepEqual(refreshed, first)
  assert.equal(refreshed.data.reviews[0].backendCampaign.caption, 'Saved content')
  assert.equal(calls.filter(url => url.endsWith('/demo-sessions')).length, 0)
})

test('missing session clears client access without creating another workspace or making protected calls', async () => {
  let requests = 0
  globalThis.fetch = async url => {
    requests++
    assert.ok(url.endsWith('/resume'))
    return Response.json({ error: { code: 'unauthenticated', message: 'Expired' } }, { status: 401 })
  }
  const client = createBackendClient('http://test/api/v1')
  assert.equal(await client.resume(), null)
  await assert.rejects(client.list(), error => error.status === 401)
  assert.equal(requests, 1)
})

for (const status of [403, 404, 500, 503]) {
  test(`resume ${status} is an error rather than an empty or new workspace`, async () => {
    let requests = 0
    globalThis.fetch = async () => { requests++; return Response.json({ error: { message: 'Unavailable' } }, { status }) }
    await assert.rejects(createBackendClient('http://test/api/v1').resume(), error => error.status === status)
    assert.equal(requests, 1)
  })
}

test('invalid resume envelope and inaccessible campaign list fail without replacing stored data', async () => {
  globalThis.fetch = async () => Response.json({ ...session, actors: {} })
  await assert.rejects(createBackendClient('http://test/api/v1').resume(), error => error.code === 'invalid_response')
  globalThis.fetch = async url => url.endsWith('/resume') ? Response.json(session) : Response.json([{ ...campaign, workspace_id: 'other-workspace' }])
  await assert.rejects(createBackendClient('http://test/api/v1').resume(), error => error.code === 'invalid_response')
})

test('startup restores a saved server workspace without combining browser-local drafts', async () => {
  const result = await loadInitialWorkspace({ resume: async () => backendData }, { list: async () => localData }, { page: 'draft', id: 'server-draft' })
  assert.deepEqual(result, backendData)
  assert.equal(result.data.reviews.some(review => review.id === 'local-draft'), false)
})

test('explicit local routes and local draft deep links stay local even with an existing demo', async () => {
  let restores = 0
  const backend = { resume: async () => { restores++; return backendData } }
  const local = { list: async () => localData }
  assert.equal(await loadInitialWorkspace(backend, local, { page: 'new', id: '', local: true }), localData)
  assert.equal(await loadInitialWorkspace(backend, local, { page: 'draft', id: 'local-draft' }), localData)
  assert.equal(restores, 0)
})

test('no saved browser session opens local drafts but a failed restore remains an error', async () => {
  assert.equal(await loadInitialWorkspace({ resume: async () => null }, { list: async () => localData }, { page: 'home', id: '' }), localData)
  await assert.rejects(loadInitialWorkspace({ resume: async () => { throw new Error('Server unavailable') } }, { list: async () => localData }, { page: 'home', id: '' }), /Server unavailable/)
})

test('unreadable local storage does not prevent restoring a genuine server workspace or clear it', async () => {
  const local = { list: async () => { throw new Error('Stored data unreadable') } }
  assert.equal(await loadInitialWorkspace({ resume: async () => backendData }, local, { page: 'home', id: '' }), backendData)
  await assert.rejects(loadInitialWorkspace({ resume: async () => null }, local, { page: 'home', id: '' }), /Stored data unreadable/)
})
