import { apiBase, verifyBackend } from './live-config.mjs'
await verifyBackend()
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { requestJson } from '../src/api/client.ts'
const base=apiBase
const client=createBackendClient(base)
await client.connect()
const result=await client.create({title:'Y02 source integration',publicationDate:'2026-11-12',brand:'',brief:''})
const campaignId=result.data.reviews[0].id
const revision=async()=> (await client.get(campaignId)).data.reviews.find(record=>record.id===campaignId).backendCampaign.source_revision
assert.equal(await revision(),0)
assert.deepEqual(await client.listSources(campaignId),[])
const payload={title:'Workshop price',rule:{kind:'price',amount:'499',currency:'INR'},valid_from:'2026-11-01',valid_until:'2026-11-30'}
const pending=await client.createSource(campaignId,payload)
assert.equal(pending.status,'pending');assert.equal(pending.version,1);assert.equal(await revision(),1)
const approved=await client.confirmSource(campaignId,pending.id,pending.version)
assert.equal(approved.status,'approved');assert.equal(approved.version,2);assert.ok(approved.confirmed_by)
assert.equal((await client.listSources(campaignId))[0].version,2);assert.equal(await revision(),2)
await assert.rejects(client.confirmSource(campaignId,pending.id,1),error=>error.status===409)
assert.equal(await revision(),2)
const edited=await client.updateSource(campaignId,approved.id,2,{...payload,rule:{kind:'price',amount:'599',currency:'INR'},valid_from:null,valid_until:null})
assert.equal(edited.status,'pending');assert.equal(edited.version,3);assert.equal(edited.valid_from,null);assert.equal(await revision(),3)
await assert.rejects(client.updateSource(campaignId,approved.id,2,payload),error=>error.status===409)
const history=await client.sourceVersions(campaignId,pending.id)
assert.deepEqual(history.map(record=>record.version),[1,2,3]);assert.equal(history[1].rule.amount,'499')
assert.equal((await client.confirmSource(campaignId,pending.id,3)).version,4)
for(const rule of [{kind:'date',date:'2026-11-12'},{kind:'terminology',term:'cheap',preferred:'affordable'},{kind:'required_text',text:'Terms apply'},{kind:'tone',guidance:'Be clear.'},{kind:'claim_policy',guidance:'Objective promises require evidence.'}]) {
  assert.equal((await client.createSource(campaignId,{title:rule.kind,rule})).status,'pending')
}
await assert.rejects(client.createSource(campaignId,{...payload,rule:{kind:'price',amount:'-1',currency:'INR'}}),error=>error.status===422)
await assert.rejects(client.createSource(campaignId,{...payload,valid_from:'2026-12-01',valid_until:'2026-11-01'}),error=>error.status===422)

// Test-only HTTP review verifies source authority; no Y03 UI or review method is implemented.
const demo=await requestJson(`${base}/demo-sessions`,{method:'POST'})
const owner={Authorization:`Bearer ${demo.actors.owner.access_token}`,'Content-Type':'application/json'}
const creator={Authorization:`Bearer ${demo.actors.creator.access_token}`,'Content-Type':'application/json'}
const campaign=await requestJson(`${base}/campaigns`,{method:'POST',headers:creator,body:JSON.stringify({name:'Pending exclusion test',publication_date:'2026-11-12'})})
const path=`${base}/campaigns/${campaign.id}`
await assert.rejects(requestJson(`${path}/sources`),error=>error.status===401&&error.code==='unauthenticated')
const price=await requestJson(`${path}/sources`,{method:'POST',headers:owner,body:JSON.stringify(payload)})
await assert.rejects(requestJson(`${path}/sources/${price.id}/confirm`,{method:'POST',headers:creator,body:JSON.stringify({expected_version:1})}),error=>error.status===403)
const caption=await requestJson(`${path}/caption`,{method:'PUT',headers:creator,body:JSON.stringify({expected_revision:campaign.content_revision,text:'Book for INR 599.'})})
const run=await requestJson(`${path}/reviews`,{method:'POST',headers:creator,body:JSON.stringify({expected_content_revision:caption.content_revision,expected_source_revision:caption.source_revision})})
assert.ok(run.excluded_sources.some(record=>record.source_id===price.id))
assert.equal(run.sources_used.length,0);assert.equal(run.findings.length,0)
await requestJson(`${path}/sources/${price.id}/confirm`,{method:'POST',headers:owner,body:JSON.stringify({expected_version:price.version})})
const current=await requestJson(path,{headers:creator})
const confirmedRun=await requestJson(`${path}/reviews`,{method:'POST',headers:creator,body:JSON.stringify({expected_content_revision:current.content_revision,expected_source_revision:current.source_revision})})
assert.ok(confirmedRun.findings.some(finding=>finding.evidence_status==='contradicted'&&finding.evidence?.source_version===2))
assert.equal(confirmedRun.status,'partial');assert.equal(confirmedRun.readiness,'not_approved')
console.log('PASS Y02 real API: INR 499 pending v1 -> approved v2; edits/history, source revisions, all six rule kinds, 403/409/422, pending excluded and approved source evidence verified. No tokens logged.')
