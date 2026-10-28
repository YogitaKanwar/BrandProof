import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createReadinessCheck } from '../src/api/readiness.ts'
import { createBackendClient } from '../src/api/backend.ts'
const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })
const healthy = () => Response.json({status:'ok',database:'ok'})
const session = () => ({workspace_id:'w1',mode:'synthetic_demo',notice:'Synthetic demo',expires_at:'2099-01-01T00:00:00Z',actors:Object.fromEntries(['owner','creator','reviewer'].map(role=>[role,{role,access_token:`test-${role}`}]))})

test('cold-start health retries are credential-free, shared, validated and briefly cached', async () => {
  let calls=0
  const messages=[]
  globalThis.fetch=async(url,options)=>{
    assert.equal(url,'/api/v1/health')
    assert.equal(options.method,'GET');assert.equal(options.credentials,'omit');assert.equal(options.cache,'no-store')
    assert.equal(options.headers.Authorization,undefined)
    calls++
    if(calls===1)return new Response('Proxy unavailable',{status:502})
    if(calls===2)return new Response('<html>Starting</html>')
    if(calls===3)return Response.json({status:'ok',database:'unavailable'})
    return healthy()
  }
  const wait=createReadinessCheck('/api/v1',{timeoutMs:1000,retryMs:1,onStatus:message=>messages.push(message)})
  await Promise.all([wait(),wait()]);await wait()
  assert.equal(calls,4)
  assert.ok(messages.some(message=>message.includes('Starting the review service')))
  assert.equal(messages.at(-1),'')
})

test('unavailable health blocks session creation and resume without replacing a workspace', async () => {
  let writes=0
  globalThis.fetch=async(url,options)=>{
    if(options.method!=='GET')writes++
    return new Response('Unavailable',{status:502})
  }
  const client=createBackendClient('/api/v1',{timeoutMs:15,retryMs:1})
  await assert.rejects(client.connect(),error=>error.code==='service_starting')
  await assert.rejects(client.resume(),error=>error.code==='service_starting')
  assert.equal(writes,0)
})

test('health readiness precedes writes; an ambiguous campaign 502 is never retried', async () => {
  let healthCalls=0,sessionWrites=0,campaignWrites=0
  globalThis.fetch=async(url,options)=>{
    if(url.endsWith('/health')){healthCalls++;return healthy()}
    assert.ok(healthCalls>0)
    if(url.endsWith('/demo-sessions')){sessionWrites++;return Response.json(session())}
    if(options.method==='POST'){campaignWrites++;return new Response('Proxy unavailable',{status:502})}
    return Response.json([])
  }
  const client=createBackendClient('/api/v1',{})
  await client.connect()
  await assert.rejects(client.create({title:'Preserved draft',publicationDate:'2026-11-12',brand:'',brief:''}),error=>error.status===502)
  assert.equal(healthCalls,1);assert.equal(sessionWrites,1);assert.equal(campaignWrites,1)
})
