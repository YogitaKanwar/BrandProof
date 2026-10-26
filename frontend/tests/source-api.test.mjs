import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { sourceValidity, isSource } from '../src/api/sources.ts'
const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })
const source = { id:'s1', version_id:'sv1', version:1, title:'Price', rule:{kind:'price',amount:'499',currency:'INR'}, status:'pending',text:'The approved campaign price is INR 499.',valid_from:null,valid_until:null,confirmed_by:null,created_at:'2026-10-26T00:00:00Z' }
function session() { return {workspace_id:'w1',mode:'synthetic_demo',notice:'Demo',expires_at:'2099-01-01',actors:Object.fromEntries(['owner','creator','reviewer'].map(role=>[role,{role,access_token:`test-${role}`}]))} }
test('source mutations use owner token and exact expected version; reads use creator', async () => {
  const calls = []
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('demo-sessions')) return Response.json(session())
    if (url.endsWith('/campaigns')) return Response.json([])
    calls.push([url, options.method || 'GET', options.body ? JSON.parse(options.body) : null])
    assert.equal(options.headers.get('Authorization'), `Bearer test-${options.method ? 'owner' : 'creator'}`)
    if (url.endsWith('/confirm')) return Response.json({...source,status:'approved',version:2,confirmed_by:'owner-id'})
    return Response.json(!options.method ? [source] : source)
  }
  const client = createBackendClient('http://test/api/v1')
  await client.connect()
  const payload = {title:'Price',rule:source.rule,valid_from:null,valid_until:null}
  await client.createSource('c1',payload)
  await client.listSources('c1')
  await client.confirmSource('c1','s1',1)
  await client.updateSource('c1','s1',2,payload)
  await client.sourceVersions('c1','s1')
  assert.deepEqual(calls[0][2],payload)
  assert.deepEqual(calls[2][2],{expected_version:1})
  assert.deepEqual(calls[3][2],{...payload,expected_version:2})
})
test('stale-source error is surfaced once without retrying or replacing expected version', async () => {
  let attempts=0
  globalThis.fetch=async(url)=> {
    if(url.endsWith('demo-sessions'))return Response.json(session())
    if(url.endsWith('/campaigns'))return Response.json([])
    attempts++
    return Response.json({error:{code:'version_conflict',message:'Source changed; reload before continuing'}},{status:409})
  }
  const client=createBackendClient('http://test/api/v1');await client.connect()
  await assert.rejects(client.confirmSource('c','s',1),error=>error.status===409&&error.code==='version_conflict')
  assert.equal(attempts,1)
})
test('validity uses publication date and validates confirmation response provenance',()=> {
  const bounded={...source,valid_from:'2026-11-01',valid_until:'2026-11-30'}
  assert.equal(sourceValidity(bounded,'2026-10-31'),'Not yet valid')
  assert.equal(sourceValidity(bounded,'2026-11-01'),'Valid for publication')
  assert.equal(sourceValidity(bounded,'2026-12-01'),'Expired for publication')
  assert.equal(isSource({...source,status:'approved'}),false)
  assert.equal(isSource(source),true)
})
