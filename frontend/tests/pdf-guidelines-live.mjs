// Verify the actual distributed PDFs through the real API. No findings are seeded.
import assert from 'node:assert/strict'
import {writeFile} from 'node:fs/promises'
import {createBackendClient} from '../src/api/backend.ts'
const base=(process.env.BRANDPROOF_TEST_API_URL||'http://127.0.0.1:8017/api/v1').replace(/\/$/,'')
const origin=new URL(base).origin
const health=await fetch(`${base}/health`)
assert.equal(health.status,200)
assert.equal((await health.json()).database,'ok')
const api=createBackendClient(base)
const records=[]
await api.connect()
try{
  for(const [asset,count] of [['/demo/workshop-guidelines.pdf',3],['/fictional-guidelines.pdf',7]]){
    const response=await fetch(origin+asset,{cache:'no-store'})
    assert.equal(response.status,200)
    const file=new File([await response.arrayBuffer()],asset.split('/').at(-1),{type:'application/pdf'})
    const created=await api.create({title:'Fictional PDF verification',publicationDate:'2026-11-12',brand:'',brief:''})
    const campaign=created.data.reviews[0].backendCampaign
    const imported=await api.importDocument(campaign.id,file,campaign.source_revision)
    assert.equal(imported.document.status,'completed')
    assert.equal(imported.sources.length,count)
    const price=imported.sources.find(s=>s.rule.kind==='price')
    assert.equal(Number(price.rule.amount),899)
    assert.equal(imported.sources.find(s=>s.rule.kind==='date').rule.date,'2026-11-12')
    assert.equal(imported.sources.find(s=>s.rule.kind==='required_text').rule.text,'Terms apply')
    assert.equal(imported.sources.every(s=>s.status==='pending'&&s.confirmed_by===null),true)
    assert.equal(imported.sources.every(s=>{const e=s.document_evidence;const page=imported.document.pages[e.page_number-1].text;return Array.from(page).slice(e.start,e.end).join('')===e.quote}),true)
    async function current(){return(await api.get(campaign.id)).data.reviews.find(r=>r.id===campaign.id).backendCampaign}
    async function review(){const c=await current();return api.runReview(c.id,c.content_revision,c.source_revision,false)}
    await api.saveCaption(campaign.id,'A cheap workshop on 2026-11-13. Book for INR 599.',(await current()).content_revision)
    const pending=await review()
    assert.equal(pending.sources_used.length,0)
    assert.equal(pending.excluded_sources.length,count)
    for(const source of imported.sources)await api.confirmSource(campaign.id,source.id,source.version)
    const conflict=await review()
    const wrongPrice=conflict.findings.find(f=>f.category==='price')
    assert.equal(wrongPrice.evidence_status,'contradicted')
    assert.equal(wrongPrice.location.quote,'INR 599')
    assert.equal(wrongPrice.evidence.quote.includes('899'),true)
    assert.equal(wrongPrice.evidence.source_version,2)
    for(const kind of ['date','required_text',...(count===7?['terminology']:[])])assert.equal(conflict.findings.some(f=>f.category===kind&&f.evidence_status==='contradicted'),true)
    await api.saveCaption(campaign.id,'An affordable workshop on 2026-11-12. Book for INR 899. Terms apply.',(await current()).content_revision)
    const aligned=await review()
    assert.equal(aligned.findings.some(f=>['price','date','required_text','terminology'].includes(f.category)),false)
    const receipt=await api.receipt(campaign.id)
    assert.equal(receipt.readiness,'not_approved')
    assert.equal(receipt.approvals.length,0)
    records.push({asset,candidates:count,reference_price:'INR 899',pending_before_confirmation:true,page_quotes_verified:true,conflicting_copy_detected:true,aligned_supported_caption_rules_match:true,automatic_approval:false})
  }
  const result={passed:true,pdfs:records,scope:'Supported text directives and caption checks; not complete brand compliance or document authenticity.'}
  if(process.env.BRANDPROOF_PDF_REPORT)await writeFile(process.env.BRANDPROOF_PDF_REPORT,JSON.stringify(result,null,2)+'\n')
  console.log('PASS actual Workshop/extended PDF import, exact page citations, pending/confirmed versions, INR 899 reference vs INR 599 conflict, corrected caption and no automatic approval.')
}finally{await api.logout()}
