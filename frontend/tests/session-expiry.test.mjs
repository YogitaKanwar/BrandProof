import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
const original=globalThis.fetch
afterEach(()=>{globalThis.fetch=original})
test('expired demo access is reported without silently rotating workspace or retrying writes',async()=>{
  let sessionRequests=0,protectedRequests=0
  globalThis.fetch=async url=>{
    if(url.endsWith('demo-sessions')){sessionRequests++;return Response.json({workspace_id:'expired-test',mode:'synthetic_demo',notice:'Test only',expires_at:'2020-01-01T00:00:00Z',actors:Object.fromEntries(['owner','creator','reviewer'].map(role=>[role,{role,access_token:`test-${role}`}]))})}
    protectedRequests++;return Response.json([])
  }
  const client=createBackendClient('http://test/api/v1')
  await assert.rejects(client.connect(),error=>error.status===401)
  await assert.rejects(client.create({title:'Cannot save expired session',publicationDate:'2026-11-12',brand:'',brief:''}),error=>error.status===401)
  assert.equal(sessionRequests,1);assert.equal(protectedRequests,0)
})
