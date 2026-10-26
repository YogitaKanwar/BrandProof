import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createBackendClient} from '../src/api/backend.ts'
import {requestResponse} from '../src/api/client.ts'
const file=new File([readFileSync(new URL('./fixtures/poster.png',import.meta.url))],'poster.png',{type:'image/png'})
const api=createBackendClient('http://127.0.0.1:8000/api/v1');await api.connect()
const initial=await api.create({title:'Real private poster test',publicationDate:'2026-11-12',brand:'',brief:''});const id=initial.data.reviews[0].id
await assert.rejects(api.poster(id),e=>e.status===404)
await api.saveCaption(id,'Caption retained',1)
const first=await api.uploadPoster(id,file,2)
assert.equal(first.width,600);assert.equal(first.height,200);assert.equal(first.content_revision,3)
assert.equal((await api.get(id)).data.reviews[0].backendCampaign.caption,'Caption retained')
assert.ok(['completed','partial','unavailable'].includes(first.ocr.status))
assert.equal((await api.posterContent(id,first.id)).type,'image/png')
await assert.rejects(requestResponse(`http://127.0.0.1:8000/api/v1/campaigns/${id}/posters/${first.id}/content`),e=>e.status===401)
await assert.rejects(api.uploadPoster(id,file,2),e=>e.status===409)
const second=await api.uploadPoster(id,file,3);assert.notEqual(first.id,second.id)
assert.equal((await api.poster(id)).id,second.id);assert.equal((await api.poster(id,first.id)).id,first.id)
assert.equal((await api.posterContent(id,first.id)).size,(await api.posterContent(id,second.id)).size)
const posterOnly=await api.create({title:'Poster-only review',publicationDate:'2026-11-12',brand:'',brief:''})
const posterOnlyId=posterOnly.data.reviews[0].id
await api.uploadPoster(posterOnlyId,file,1)
const posterRun=await api.runReview(posterOnlyId,2,0,false)
assert.equal(posterRun.caption,'');assert.equal(posterRun.status,'partial');assert.ok(posterRun.checks.poster.details.asset_id)
await assert.rejects(api.uploadPoster(id,new File(['invalid'],'bad.png',{type:'image/png'}),4),e=>e.status===422)
await assert.rejects(api.uploadPoster(id,new File(['text'],'bad.txt',{type:'text/plain'}),4),e=>e.status===415)
await assert.rejects(api.uploadPoster(id,new File([new Uint8Array(5*1024*1024+1)],'large.png',{type:'image/png'}),4),e=>e.status===413)
console.log(`PASS real poster upload/replacement/private historical retrieval, caption persistence and 401/409/413/415/422. Actual OCR: ${first.ocr.status} (${first.ocr.reason||'no warning'}).`)
