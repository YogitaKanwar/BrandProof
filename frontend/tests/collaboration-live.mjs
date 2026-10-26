import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
const api=createBackendClient('http://127.0.0.1:8000/api/v1');await api.connect()
const initial=await api.create({title:'Y06 collaboration',publicationDate:'2026-11-12',brand:'',brief:''});const id=initial.data.reviews[0].id
const source=await api.createSource(id,{title:'Price',rule:{kind:'price',amount:'499',currency:'INR'}});await api.confirmSource(id,source.id,1)
await api.saveCaption(id,'Book for INR 599.',1)
const campaign=(await api.get(id)).data.reviews[0].backendCampaign
const snapshot={expected_content_revision:campaign.content_revision,expected_source_revision:campaign.source_revision}
const run=await api.runReview(id,campaign.content_revision,campaign.source_revision)
const finding=run.findings.find(f=>f.category==='price');assert.ok(finding)
await api.comment(id,snapshot,'Please verify the advertised workshop price.',run.id)
assert.equal((await api.comments(id)).length,1)
const decisions=await api.decisions(id,run.id,finding.id);assert.equal(decisions.length,0)
await assert.rejects(api.decideFinding(id,run.id,finding.id,snapshot,0,'exception','Reviewer reason for exception','creator'),e=>e.status===403)
const decision=await api.decideFinding(id,run.id,finding.id,snapshot,0,'exception','Demo reviewer independently records a permitted exception.')
assert.equal(decision.version,1)
await assert.rejects(api.decideFinding(id,run.id,finding.id,snapshot,0,'dismiss','Stale decision must be rejected.'),e=>e.status===409)
const updated=await api.applySuggestion(id,run.id,finding.id,snapshot)
assert.equal(updated.data.reviews[0].backendCampaign.caption,'Book for INR 499.')
assert.equal((await api.revisions(id)).length,3)
await assert.rejects(api.applySuggestion(id,run.id,finding.id,snapshot),e=>e.status===409)
assert.equal((await api.comments(id))[0].text,'Please verify the advertised workshop price.')
console.log('PASS Y06 persisted comments, explicit correction, revision history, reviewer decisions, creator denial and stale/replay conflicts.')
