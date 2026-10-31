import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
const original=globalThis.fetch
afterEach(()=>{globalThis.fetch=original})
test('profile writes use the owner and exact revisions; conflicts are not retried',async()=>{
  let writes=0
  const profile={jurisdiction:'IN',sector:'general',language:'en'}
  const snapshot={expected_content_revision:3,expected_source_revision:5}
  globalThis.fetch=async(url,options)=>{
    if(url.endsWith('/demo-sessions'))return Response.json({workspace_id:'w',mode:'synthetic_demo',notice:'QA',expires_at:'2099-01-01T00:00:00Z',actors:Object.fromEntries(['owner','creator','reviewer'].map(role=>[role,{role,access_token:`qa-${role}`}]))})
    if(url.endsWith('/campaigns'))return Response.json([])
    assert.ok(url.endsWith('/campaigns/c/advertising-profile'))
    if(options.method==='PUT'){
      writes++;assert.equal(options.headers.get('Authorization'),'Bearer qa-owner')
      assert.deepEqual(JSON.parse(options.body),{...snapshot,...profile})
      return Response.json({error:{code:'version_conflict',message:'Reload first'}},{status:409})
    }
    assert.equal(options.headers.get('Authorization'),'Bearer qa-creator')
    return Response.json({profile:null,source_revision:5,pack:{version:'frozen'}})
  }
  const api=createBackendClient('http://test/api/v1');await api.connect()
  assert.equal((await api.advertisingProfile('c')).profile,null)
  await assert.rejects(api.saveAdvertisingProfile('c',profile,snapshot),e=>e.status===409)
  assert.equal(writes,1)
})
