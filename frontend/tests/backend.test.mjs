import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { requestJson, describeError } from '../src/api/client.ts'
const fetchOriginal = globalThis.fetch
afterEach(() => { globalThis.fetch = fetchOriginal })
const campaign = { id: 'c1', workspace_id: 'w1', name: 'Launch', publication_date: '2026-11-12', caption: '', content_revision: 1, source_revision: 0, created_at: '2026-10-26T00:00:00Z' }

test('connected deletion uses owner, exact revisions and acknowledged removal; failed requests preserve cached review',async()=>{
  let conflict=false,removals=0
  globalThis.fetch=async(url,options)=>{
    if(url.endsWith('demo-sessions'))return Response.json(session())
    if(options.method==='DELETE'){
      removals++;assert.equal(options.headers.get('Authorization'),'Bearer test-owner')
      assert.deepEqual(JSON.parse(options.body),{expected_content_revision:1,expected_source_revision:0})
      if(conflict)return Response.json({error:{code:'version_conflict',message:'Changed'}},{status:409})
      return Response.json({campaign_id:'c1',deletion_id:'deletion-1',deleted:true,retained_history:true})
    }
    if(url.endsWith('/restore')){
      assert.equal(options.headers.get('Authorization'),'Bearer test-owner')
      assert.deepEqual(JSON.parse(options.body),{expected_content_revision:1,expected_source_revision:0,expected_deletion_id:'deletion-1'})
      return Response.json(campaign)
    }
    return Response.json([campaign])
  }
  const api=createBackendClient('http://test/api/v1');await api.connect()
  const removed=await api.removeReview('c1',{expected_content_revision:1,expected_source_revision:0})
  assert.equal(removed.data.reviews.length,0)
  assert.equal((await api.restoreReview(campaign,'deletion-1')).data.reviews.length,1)
  conflict=true
  await assert.rejects(api.removeReview('c1',{expected_content_revision:1,expected_source_revision:0}),error=>error.status===409)
  assert.equal(removals,2)
  assert.equal((await api.list()).data.reviews.length,1)
})
test('caption removal uses an explicit creator write with the expected revision and never retries a conflict', async () => {
  let removals = 0
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('demo-sessions')) return Response.json(session())
    if (url.endsWith('/caption/clear')) {
      removals++
      assert.equal(options.method, 'POST')
      assert.equal(options.headers.get('Authorization'), 'Bearer test-creator')
      assert.deepEqual(JSON.parse(options.body), {expected_revision: 4})
      if (removals > 1) return Response.json({error:{code:'version_conflict',message:'Caption changed'}},{status:409})
      return Response.json({...campaign, content_revision:5})
    }
    return Response.json([])
  }
  const client = createBackendClient('http://test/api/v1')
  await client.connect()
  const cleared = await client.clearCaption('c1',4)
  assert.equal(cleared.data.reviews[0].backendCampaign.caption,'')
  assert.equal(cleared.data.reviews[0].backendCampaign.content_revision,5)
  await assert.rejects(client.clearCaption('c1',4), error=>error.status===409)
  assert.equal(removals,2)
})
function session() { return { workspace_id: 'w1', mode: 'synthetic_demo', notice: 'Synthetic demo', expires_at: '2099-01-01T00:00:00Z', actors: Object.fromEntries(['owner','creator','reviewer'].map(role => [role, {role,access_token: `test-${role}`}])) } }

test('a delayed opening read cannot replace a newer acknowledged caption save', async () => {
  let releaseRead
  let current = campaign
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('demo-sessions')) return Response.json(session())
    if (url.endsWith('/campaigns')) return Response.json([current])
    if (url.endsWith('/caption')) {
      current = {...current, caption: JSON.parse(options.body).text, content_revision: 2}
      return Response.json(current)
    }
    return new Promise(resolve => { releaseRead = () => resolve(Response.json(campaign)) })
  }
  const api = createBackendClient('http://test/api/v1')
  await api.connect()
  const delayed = api.get('c1')
  await new Promise(resolve => setImmediate(resolve))
  await api.saveCaption('c1', 'Explicit newer edit.', 1)
  releaseRead()
  const record = (await delayed).data.reviews[0].backendCampaign
  assert.equal(record.caption, 'Explicit newer edit.')
  assert.equal(record.content_revision, 2)
})

test('a delayed read cannot roll back source-only revisions; a newer opening read still hydrates empty cached content', async () => {
  let releaseRead, reads = 0
  const saved = {...campaign, caption: 'Saved example caption.', content_revision: 3, source_revision: 9}
  globalThis.fetch = async url => {
    if (url.endsWith('demo-sessions')) return Response.json(session())
    if (url.endsWith('/campaigns')) return Response.json([campaign])
    reads++
    if (reads === 1) return new Promise(resolve => { releaseRead = () => resolve(Response.json(saved)) })
    return Response.json({...saved, source_revision: 10})
  }
  const api = createBackendClient('http://test/api/v1')
  await api.connect()
  const delayed = api.get('c1')
  await new Promise(resolve => setImmediate(resolve))
  const newest = await api.get('c1')
  assert.equal(newest.data.reviews[0].backendCampaign.caption, saved.caption)
  releaseRead()
  assert.equal((await delayed).data.reviews[0].backendCampaign.source_revision, 10)
})
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
