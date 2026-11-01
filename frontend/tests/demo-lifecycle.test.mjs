import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
const original=globalThis.fetch
afterEach(()=>{globalThis.fetch=original})
const session=(id='first')=>({workspace_id:id,mode:'synthetic_demo',notice:'Synthetic guest',expires_at:'2099-01-01T00:00:00Z',actors:Object.fromEntries(['owner','creator','reviewer'].map(role=>[role,{role,access_token:`test-${id}-${role}`}]))})
test('logout sends cookie and CSRF header, clears memory only after acknowledgement',async()=>{
  let fail=true
  globalThis.fetch=async(url,options)=>{
    if(url.endsWith('/demo-sessions'))return Response.json(session())
    if(url.endsWith('/logout')){
      assert.equal(options.credentials,'include');assert.equal(options.headers.get('X-BrandProof-Session'),'resume');assert.equal(options.headers.get('Authorization'),'Bearer test-first-creator')
      return fail?Response.json({error:{message:'Unavailable'}},{status:503}):Response.json({logged_out:true})
    }
    return Response.json([])
  }
  const api=createBackendClient();await api.connect()
  await assert.rejects(api.logout(),error=>error.status===503)
  await api.list()
  fail=false;await api.logout()
  assert.equal(api.expiresAt,null)
  await assert.rejects(api.list(),error=>error.status===401)
})
test('reset adopts the acknowledged new sandbox and does not replay failed writes',async()=>{
  let calls=0
  globalThis.fetch=async(url,options)=>{
    if(url.endsWith('/demo-sessions'))return Response.json(session())
    if(url.endsWith('/reset')){
      calls++;assert.equal(options.headers.get('X-BrandProof-Session'),'resume');assert.equal(options.credentials,'include')
      return Response.json(session('second'))
    }
    assert.equal(options.headers.get('Authorization'),calls?'Bearer test-second-creator':'Bearer test-first-creator')
    return Response.json([])
  }
  const api=createBackendClient();await api.connect();assert.equal((await api.reset()).mode,'backend');assert.equal(calls,1)
})
test('revoked protected requests signal session recovery without silently creating a demo',async()=>{
  let protectedCalls=0,expired=0
  globalThis.fetch=async url=>{
    if(url.endsWith('/health'))return Response.json({status:'ok',database:'ok'})
    if(url.endsWith('/demo-sessions'))return Response.json(session())
    protectedCalls++
    return protectedCalls===1?Response.json([]):Response.json({error:{message:'Revoked'}},{status:401})
  }
  const api=createBackendClient('/api/v1',{onSessionExpired:()=>expired++});await api.connect()
  await assert.rejects(api.list(),error=>error.status===401);assert.equal(expired,1);assert.equal(protectedCalls,2)
})
