export type SourceRule =
  | { kind: 'price'; amount: string; currency: 'INR' | 'USD' | 'EUR' | 'GBP'; scope?: 'campaign_main_price' }
  | { kind: 'date'; date: string; scope?: 'campaign_main_date' }
  | { kind: 'terminology'; term: string; preferred: string }
  | { kind: 'required_text'; text: string }
  | { kind: 'tone' | 'claim_policy'; guidance: string }
export interface SourceCreate { title: string; rule: SourceRule; valid_from?: string | null; valid_until?: string | null }
export interface SourceOut extends SourceCreate {
  id: string; version_id: string; version: number; status: 'pending' | 'approved'
  text: string; confirmed_by: string | null; created_at: string
  valid_from: string | null; valid_until: string | null
}
export function sourceValidity(source: SourceOut, publicationDate: string) {
  if (source.valid_from && publicationDate < source.valid_from) return 'Not yet valid'
  if (source.valid_until && publicationDate > source.valid_until) return 'Expired for publication'
  return 'Valid for publication'
}
export function isSource(value: SourceOut): boolean {
  if (!value || !Number.isInteger(value.version) || value.version < 1 ||
    !['pending', 'approved'].includes(value.status) ||
    ['id', 'version_id', 'title', 'text', 'created_at'].some(key => typeof value[key as keyof SourceOut] !== 'string') ||
    ![value.valid_from, value.valid_until, value.confirmed_by].every(field => field === null || typeof field === 'string') ||
    (value.status === 'approved' && !value.confirmed_by)) return false
  const rule = value.rule
  if (!rule) return false
  switch (rule.kind) {
    case 'price': return typeof rule.amount === 'string' && ['INR', 'USD', 'EUR', 'GBP'].includes(rule.currency)
    case 'date': return typeof rule.date === 'string'
    case 'terminology': return typeof rule.term === 'string' && typeof rule.preferred === 'string'
    case 'required_text': return typeof rule.text === 'string'
    case 'tone': case 'claim_policy': return typeof rule.guidance === 'string'
    default: return false
  }
}
