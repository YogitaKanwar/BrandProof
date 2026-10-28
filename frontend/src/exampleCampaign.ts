import type { BackendClient, CampaignOut } from './api/backend.ts'
import type { SourceCreate } from './api/sources.ts'

export const exampleDetails = {
  title: 'Example: workshop launch', publicationDate: '2026-11-12', brand: '', brief: '',
}

// Fictional reference data only. Findings and approvals are never seeded.
export async function prepareExampleCampaign(api: BackendClient, campaign: CampaignOut) {
  const sources: SourceCreate[] = [
    { title: 'Example workshop price', rule: { kind: 'price', amount: '499', currency: 'INR' } },
    { title: 'Example workshop date', rule: { kind: 'date', date: '2026-11-12' } },
    { title: 'Example preferred wording', rule: { kind: 'terminology', term: 'cheap', preferred: 'affordable' } },
    { title: 'Example required disclosure', rule: { kind: 'required_text', text: 'Terms apply' } },
  ]
  for (const source of sources) {
    const saved = await api.createSource(campaign.id, source)
    await api.confirmSource(campaign.id, saved.id, saved.version)
  }
  await api.createSource(campaign.id,{title:'Example claim policy — inspect and confirm',rule:{kind:'claim_policy',guidance:'Outcome promises require documented evidence and explicit conditions. This fictional example is not evidence.'}})
  let result=await api.saveCaption(campaign.id, 'A cheap workshop on 2026-11-13. Book for INR 599. Guaranteed results in 30 days.', campaign.content_revision)
  const canvas=document.createElement('canvas');canvas.width=1400;canvas.height=440
  const context=canvas.getContext('2d')
  if(!context)throw new Error('Sample poster could not be prepared. The example sources and caption are saved.')
  context.fillStyle='white';context.fillRect(0,0,canvas.width,canvas.height);context.fillStyle='#142C44'
  context.font='bold 64px Arial';context.fillText('Fictional workshop launch',40,90)
  context.font='56px Arial';context.fillText('Book for INR 599.',40,175);context.fillText('Guaranteed results in 30 days.',40,260)
  context.font='32px Arial';context.fillText('Synthetic demonstration — inspect and edit before review',40,360)
  const blob=await new Promise<Blob|null>(resolve=>canvas.toBlob(resolve,'image/png'))
  if(!blob)throw new Error('Sample poster could not be encoded. Saved example content is preserved.')
  await api.uploadPoster(campaign.id,new File([blob],'fictional-workshop.png',{type:'image/png'}),result.data.reviews.find(row=>row.id===campaign.id)!.backendCampaign!.content_revision)
  result=await api.get(campaign.id)
  return result
}
