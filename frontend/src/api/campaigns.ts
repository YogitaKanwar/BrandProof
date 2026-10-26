export interface CampaignInput { name: string; brand: string; description: string }
export interface Campaign extends CampaignInput { id: string; createdAt: string }
export interface CampaignService {
  list(): Promise<Campaign[]>
  create(input: CampaignInput): Promise<Campaign>
}
const key = 'brandproof.development.campaigns.v1'
function read(): Campaign[] {
  const raw = localStorage.getItem(key)
  if (!raw) return []
  const records: unknown = JSON.parse(raw)
  if (!Array.isArray(records) || !records.every(record =>
    record && ['id', 'name', 'brand', 'description', 'createdAt'].every(field => typeof record[field] === 'string'),
  )) throw new Error('Development campaign data is unreadable. Please clear this site’s local data.')
  return records
}
// Development fixture adapter. Browser storage is not backend persistence.
export const campaignService: CampaignService = {
  async list() { return read() },
  async create(input) {
    const trimmed = { name: input.name.trim(), brand: input.brand.trim(), description: input.description.trim() }
    if (!trimmed.name || !trimmed.brand) throw new Error('Campaign name and brand are required.')
    if (trimmed.name.length > 120 || trimmed.brand.length > 120 || trimmed.description.length > 2000) {
      throw new Error('Campaign details exceed the allowed length.')
    }
    const campaign = { ...trimmed, id: crypto.randomUUID(), createdAt: new Date().toISOString() }
    const campaigns = read()
    localStorage.setItem(key, JSON.stringify([campaign, ...campaigns]))
    return campaign
  },
}
