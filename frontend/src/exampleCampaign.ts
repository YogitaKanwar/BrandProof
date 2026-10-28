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
  return api.saveCaption(campaign.id, 'A cheap workshop on 2026-11-13. Book for INR 599.', campaign.content_revision)
}
