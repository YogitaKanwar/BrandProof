import { apiBase, verifyBackend } from './live-config.mjs'
await verifyBackend()
import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
import {incompleteChecks} from '../src/api/workflow.ts'
import {readFileSync} from 'node:fs'
const api=createBackendClient(apiBase);await api.connect()
const data=await api.create({title:'Y07 approval workflow',publicationDate:'2026-11-12',brand:'',brief:''}),id=data.data.reviews[0].id
const source=await api.createSource(id,{title:'Price',rule:{kind:'price',amount:'499',currency:'INR'}});await api.confirmSource(id,source.id,1)
await api.saveCaption(id,'Book for INR 499.',1)
const campaign=(await api.get(id)).data.reviews[0].backendCampaign,snapshot={expected_content_revision:campaign.content_revision,expected_source_revision:campaign.source_revision}
const run=await api.runReview(id,campaign.content_revision,campaign.source_revision)
const request=await api.requestReview(id,run.id,snapshot)
await assert.rejects(api.approve(id,run.id,snapshot,request.id,'approve','Creator must not approve their own work.',{},'creator'),e=>e.status===403)
await assert.rejects(api.approve(id,run.id,snapshot,request.id,'approve','Incomplete checks require real reviewer notes.',{}),e=>e.status===409&&e.code==='checks_incomplete')
const incomplete=incompleteChecks(run)
const manual=Object.fromEntries(incomplete.map(name=>[name,`Scripted test attestation for ${name}; not actual user feedback.`]))
await api.approve(id,run.id,snapshot,request.id,'approve','Scripted demo reviewer approval for workflow verification.',manual)
const receipt=await api.receipt(id);assert.equal(receipt.readiness,'approved_with_manual_checks');assert.equal(receipt.approvals.length,1)
await api.saveCaption(id,'Book for INR 499. ',campaign.content_revision)
assert.equal((await api.receipt(id)).readiness,'stale')
assert.equal((await api.receipt(id)).approvals[0].is_current,false)
const latest=(await api.get(id)).data.reviews[0].backendCampaign
const rerun=await api.runReview(id,latest.content_revision,latest.source_revision)
const nextSnapshot={expected_content_revision:latest.content_revision,expected_source_revision:latest.source_revision}
const nextRequest=await api.requestReview(id,rerun.id,nextSnapshot)
await api.approve(id,rerun.id,nextSnapshot,nextRequest.id,'request_changes','Please verify the campaign copy with its owner.',{})
assert.equal((await api.receipt(id)).readiness,'changes_requested')
const requestAgain=await api.requestReview(id,rerun.id,nextSnapshot)
await api.approve(id,rerun.id,nextSnapshot,requestAgain.id,'approve','Scripted second approval before poster replacement.',manual)
const image=new File([readFileSync(new URL('./fixtures/poster.png',import.meta.url))],'poster.png',{type:'image/png'})
await api.uploadPoster(id,image,latest.content_revision)
assert.equal((await api.receipt(id)).readiness,'stale')
const withPoster=(await api.get(id)).data.reviews[0].backendCampaign
const posterRun=await api.runReview(id,withPoster.content_revision,withPoster.source_revision)
const posterSnapshot={expected_content_revision:withPoster.content_revision,expected_source_revision:withPoster.source_revision}
const posterRequest=await api.requestReview(id,posterRun.id,posterSnapshot)
for(const finding of posterRun.findings.filter(f=>f.severity==='error'||['needs_clarification','insufficient_evidence'].includes(f.evidence_status))) {
  await api.decideFinding(id,posterRun.id,finding.id,posterSnapshot,0,'exception','Scripted reviewer exception for test workflow only; not real human evaluation.')
}
const required=incompleteChecks(posterRun)
const posterNotes=Object.fromEntries(required.map(name=>[name,`Scripted workflow check for ${name}; not a real human evaluation.`]))
await api.approve(id,posterRun.id,posterSnapshot,posterRequest.id,'approve','Scripted approval including actual incomplete-check keys.',posterNotes)
await api.updateSource(id,source.id,2,{title:'Revised price',rule:{kind:'price',amount:'599',currency:'INR'},valid_from:null,valid_until:null})
assert.equal((await api.receipt(id)).readiness,'stale')
console.log('PASS real creator request, reviewer approval/manual-note guard, creator denial, persisted receipt, stale approval after edit and request-changes.')
