export interface Finding {
  id: string; category: string; severity: 'error' | 'warning' | 'info'
  evidence_status: 'contradicted' | 'needs_clarification' | 'insufficient_evidence'; message: string
  location: { asset: 'caption'; content_revision: number; start: number | null; end: number | null; quote: string | null }
  evidence: { source_id: string; source_version_id: string; source_version: number; quote: string } | null
  suggested_replacement?: string | null
}
export interface CheckStatus { status: 'completed' | 'partial' | 'unavailable' | 'not_assessed'; reason?: string | null; rules: {source_id: string; source_version: number; kind: string; status: string; reason?: string | null}[] }
export interface ReviewOut {
  id: string; campaign_id: string; content_revision: number; source_revision: number; caption: string
  status: 'partial' | 'completed' | 'failed'; is_current: boolean; readiness: 'not_approved'
  checks: Record<string, CheckStatus>; sources_used: Record<string, unknown>[]; excluded_sources: Record<string, unknown>[]
  findings: Finding[]; created_at: string
}
export function isReview(value: ReviewOut): boolean {
  return !!value && typeof value.id === 'string' && typeof value.campaign_id === 'string' && typeof value.caption === 'string' &&
    Number.isInteger(value.content_revision) && Number.isInteger(value.source_revision) && typeof value.is_current === 'boolean' &&
    ['partial', 'completed', 'failed'].includes(value.status) && value.readiness === 'not_approved' &&
    !!value.checks && typeof value.checks === 'object' && !Array.isArray(value.checks) &&
    Object.values(value.checks).every(check => check && ['completed','partial','unavailable','not_assessed'].includes(check.status) && (check.rules === undefined || Array.isArray(check.rules))) &&
    Array.isArray(value.findings) && value.findings.every(finding => finding && typeof finding.id === 'string' && typeof finding.category === 'string' && typeof finding.message === 'string' &&
      ['error','warning','info'].includes(finding.severity) && ['contradicted','needs_clarification','insufficient_evidence'].includes(finding.evidence_status) &&
      finding.location && finding.location.asset === 'caption' && Number.isInteger(finding.location.content_revision) &&
      [finding.location.start,finding.location.end].every(offset => offset === null || Number.isInteger(offset)) &&
      (finding.evidence === null || (finding.evidence && typeof finding.evidence.quote === 'string' && typeof finding.evidence.source_id === 'string' && typeof finding.evidence.source_version_id === 'string' && Number.isInteger(finding.evidence.source_version)))) &&
    Array.isArray(value.sources_used) && value.sources_used.every(source => source && typeof source === 'object') && Array.isArray(value.excluded_sources) && value.excluded_sources.every(source => source && typeof source === 'object') && typeof value.created_at === 'string'
}
export function codePointExcerpt(caption: string, start: number | null, end: number | null): string | null {
  if (start === null || end === null || !Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end > Array.from(caption).length) return null
  return Array.from(caption).slice(start, end).join('')
}
