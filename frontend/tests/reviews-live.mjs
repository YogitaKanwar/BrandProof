import { apiBase, verifyBackend } from './live-config.mjs'
await verifyBackend()
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
const client=createBackendClient(apiBase)
await client.connect()
const data=await client.create({title:'Y03 review flow',publicationDate:'2026-11-12',brand:'',brief:''})
const id=data.data.reviews[0].id
const source=await client.createSource(id,{title:'Price',rule:{kind:'price',amount:'499',currency:'INR'}})
await client.confirmSource(id,source.id,source.version)
const saved=await client.saveCaption(id,'Book for INR 599.',1)
const caption=saved.data.reviews[0].backendCampaign
assert.equal(caption.content_revision,2)
const run=await client.runReview(id,caption.content_revision,caption.source_revision)
assert.equal(run.status,'partial');assert.equal(run.readiness,'not_approved')
assert.ok(run.findings.some(f=>f.evidence_status==='contradicted'&&f.evidence?.source_version===2))
assert.equal((await client.getReview(id,run.id)).id,run.id)
assert.equal((await client.listReviews(id)).length,1)
await assert.rejects(client.saveCaption(id,'Unsaved conflicting edit',1),error=>error.status===409)
await assert.rejects(client.saveCaption(id,'   ',2),error=>error.status===422)
await assert.rejects(client.runReview(id,1,caption.source_revision),error=>error.status===409)
await client.saveCaption(id,'Book for INR 499.',2)
assert.equal((await client.getReview(id,run.id)).is_current,false)
const current=(await client.get(id)).data.reviews[0].backendCampaign
const clean=await client.runReview(id,current.content_revision,current.source_revision)
assert.equal(clean.findings.length,0);assert.equal(clean.status,'partial');assert.equal(clean.readiness,'not_approved')
console.log('PASS Y03 real caption revisions, save/run conflicts, 422, partial reviews, persisted history and stale runs; zero findings is not approval.')
