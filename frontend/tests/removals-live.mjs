import {apiBase,verifyBackend} from './live-config.mjs'
import {requestJson} from '../src/api/client.ts'
import assert from 'node:assert/strict'
await verifyBackend()
// Fictional isolated workspace only; bearer credentials stay in this process.
const demo=await requestJson(`${apiBase}/demo-sessions`,{method:'POST'})
const call=(method,path,body,role='owner',actors=demo.actors)=>requestJson(apiBase+path,{
  method,headers:{Authorization:`Bearer ${actors[role].access_token}`,'Content-Type':'application/json'},
  ...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(120000),
})
const campaign=await call('POST','/campaigns',{name:'Fictional deletion API acceptance',publication_date:'2026-11-12'})
const base=`/campaigns/${campaign.id}`
const source=await call('POST',base+'/sources',{title:'Fictional price',rule:{kind:'price',amount:'499',currency:'INR'}})
await call('POST',base+`/sources/${source.id}/confirm`,{expected_version:source.version})
await call('PUT',base+'/caption',{text:'Workshop price INR 599.',expected_revision:campaign.content_revision})
const before=await call('GET',base)
const snapshot={expected_content_revision:before.content_revision,expected_source_revision:before.source_revision}
const run=await call('POST',base+'/reviews',{...snapshot,external_ai_consent:false})
const beforeSources=await call('GET',base+'/sources')
const beforeReceipt=await call('GET',base+'/receipt')
const keeper=await call('POST','/campaigns',{name:'Unrelated fictional campaign',publication_date:'2026-11-12'})
for(const role of ['creator','reviewer'])await assert.rejects(call('DELETE',base,snapshot,role),error=>error.status===403)
await assert.rejects(call('DELETE',base,{...snapshot,expected_source_revision:snapshot.expected_source_revision+1}),error=>error.status===409)
const other=await requestJson(`${apiBase}/demo-sessions`,{method:'POST'})
await assert.rejects(call('DELETE',base,snapshot,'owner',other.actors),error=>error.status===404)
const removed=await call('DELETE',base,snapshot)
assert.equal(removed.deleted,true);assert.equal(removed.retained_history,true)
assert.deepEqual((await call('GET','/campaigns')).map(row=>row.id),[keeper.id])
for(const suffix of ['', '/sources','/reviews','/revisions','/receipt'])await assert.rejects(call('GET',base+suffix),error=>error.status===404)
await assert.rejects(call('PUT',base+'/caption',{text:'Must not save',expected_revision:before.content_revision}),error=>error.status===404)
const restore={...snapshot,expected_deletion_id:removed.deletion_id}
await assert.rejects(call('POST',base+'/restore',restore,'creator'),error=>error.status===403)
await assert.rejects(call('POST',base+'/restore',restore,'owner',other.actors),error=>error.status===404)
assert.deepEqual(await call('POST',base+'/restore',restore),before)
assert.deepEqual(await call('GET',base+'/sources'),beforeSources)
assert.deepEqual(await call('GET',base+'/reviews/'+run.id),run)
assert.deepEqual(await call('GET',base+'/receipt'),beforeReceipt)
const second=await call('DELETE',base,snapshot)
assert.notEqual(second.deletion_id,removed.deletion_id)
await assert.rejects(call('POST',base+'/restore',restore),error=>error.status===409)
assert.deepEqual(await call('POST',base+'/restore',{...snapshot,expected_deletion_id:second.deletion_id}),before)
assert.equal((await call('GET','/campaigns')).length,2)
console.log('PASS real HTTP removal/restore: owner-only, stale snapshot and workspace guards, hidden reads/writes, same campaign/source/review/receipt preservation, fresh deletion generation and stale-Undo rejection; no credentials logged')
