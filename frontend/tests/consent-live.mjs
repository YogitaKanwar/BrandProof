import { apiBase, verifyBackend } from './live-config.mjs'
await verifyBackend()
import assert from 'node:assert/strict'
import {createBackendClient} from '../src/api/backend.ts'
const api=createBackendClient(apiBase);await api.connect()
const data=await api.create({title:'Explicit AI consent check',publicationDate:'2026-11-12',brand:'',brief:''}),id=data.data.reviews[0].id
const source=await api.createSource(id,{title:'Claim guidance',rule:{kind:'claim_policy',guidance:'Objective promises require approved evidence.'}});await api.confirmSource(id,source.id,1)
await api.saveCaption(id,'Workshop information.',1)
const campaign=(await api.get(id)).data.reviews[0].backendCampaign
const denied=await api.runReview(id,campaign.content_revision,campaign.source_revision,false)
assert.notEqual(denied.checks.contextual.status,'completed')
const opted=await api.runReview(id,campaign.content_revision,campaign.source_revision,true)
assert.ok(['completed','partial','unavailable','not_assessed'].includes(opted.checks.contextual.status))
console.log(`PASS consent false remains incomplete; explicit true returns actual contextual status: ${opted.checks.contextual.status} (${opted.checks.contextual.reason||'no warning'}). No provider credentials read or logged.`)
