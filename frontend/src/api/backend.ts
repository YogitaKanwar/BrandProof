import { ApiError, requestJson } from './client.ts'
import type { ReviewInput, ReviewResult } from './reviews.ts'
import { isSource } from './sources.ts'
import type { SourceCreate, SourceOut } from './sources.ts'
import { isReview } from './reviewRuns.ts'
import type { ReviewOut } from './reviewRuns.ts'

export interface CampaignOut {
  id: string; workspace_id: string; name: string; publication_date: string
  caption: string; content_revision: number; source_revision: number; created_at: string
}
interface DemoSessionOut {
  workspace_id: string; mode: 'synthetic_demo'; notice: string; expires_at: string
  actors: Record<'owner' | 'creator' | 'reviewer', { role: string; access_token: string }>
}
export function createBackendClient(base = '/api/v1') {
  let session: DemoSessionOut | null = null
  let connecting: Promise<DemoSessionOut> | null = null
  const campaigns = new Map<string, CampaignOut>()
  const invalid = () => new ApiError('The API returned an unexpected response.', 502, 'invalid_response')
  function validateCampaign(value: CampaignOut): CampaignOut {
    if (!value || ['id', 'workspace_id', 'name', 'publication_date', 'caption', 'created_at'].some(key => typeof value[key as keyof CampaignOut] !== 'string') ||
      !Number.isInteger(value.content_revision) || !Number.isInteger(value.source_revision) || value.workspace_id !== session?.workspace_id) throw invalid()
    return value
  }
  function result(): ReviewResult {
    const records = [...campaigns.values()].sort((a, b) => b.created_at.localeCompare(a.created_at))
    return {
      mode: 'backend', notice: session?.notice || '',
      data: {
        campaigns: records.map(c => ({ id: c.id, name: c.name, brand: '', description: '', createdAt: c.created_at })),
        // A UI draft references a campaign; no persisted ReviewOut is invented.
        reviews: records.map(c => ({ id: c.id, campaignId: c.id, title: c.name, brief: '', createdAt: c.created_at, status: 'draft', backendCampaign: c })),
      },
    }
  }
  function auth(role: 'creator' | 'owner' | 'reviewer' = 'creator'): HeadersInit {
    if (!session || Date.parse(session.expires_at) <= Date.now()) throw new ApiError('Demo session is not active.', 401, 'unauthenticated')
    return { Authorization: `Bearer ${session.actors[role].access_token}` }
  }
  const sourcePath = (campaignId: string, sourceId?: string) => `${base}/campaigns/${encodeURIComponent(campaignId)}/sources${sourceId ? `/${encodeURIComponent(sourceId)}` : ''}`
  const checkedSource = (value: SourceOut) => { if (!isSource(value)) throw invalid(); return value }
  const checkedReview = (value: ReviewOut) => { if (!isReview(value)) throw invalid(); return value }
  return {
    async connect() {
      if (!session) {
        connecting ??= requestJson<DemoSessionOut>(`${base}/demo-sessions`, { method: 'POST' })
        try {
          const data = await connecting
          if (!data || data.mode !== 'synthetic_demo' || typeof data.workspace_id !== 'string' || typeof data.notice !== 'string' || !Number.isFinite(Date.parse(data.expires_at)) ||
            ['owner', 'creator', 'reviewer'].some(role => data.actors?.[role as keyof typeof data.actors]?.role !== role || typeof data.actors?.[role as keyof typeof data.actors]?.access_token !== 'string')) throw invalid()
          session = data
        } finally { connecting = null }
      }
      return this.list()
    },
    async list() {
      const records = await requestJson<CampaignOut[]>(`${base}/campaigns`, { headers: auth() })
      if (!Array.isArray(records)) throw invalid()
      records.forEach(validateCampaign)
      campaigns.clear(); records.forEach(record => campaigns.set(record.id, record))
      return result()
    },
    async get(id: string) {
      const record = validateCampaign(await requestJson<CampaignOut>(`${base}/campaigns/${encodeURIComponent(id)}`, { headers: auth() }))
      campaigns.set(record.id, record)
      return result()
    },
    async create(input: ReviewInput) {
      const record = validateCampaign(await requestJson<CampaignOut>(`${base}/campaigns`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: input.title.trim() || 'Untitled review', publication_date: input.publicationDate || '' }),
      }))
      campaigns.set(record.id, record)
      const data = result()
      // Ensure caller opens the created campaign even if another record has a later timestamp.
      data.data.reviews.sort((a, b) => Number(b.id === record.id) - Number(a.id === record.id))
      return data
    },
    async listSources(campaignId: string) {
      const records = await requestJson<SourceOut[]>(sourcePath(campaignId), { headers: auth() })
      if (!Array.isArray(records)) throw invalid()
      return records.map(checkedSource)
    },
    async createSource(campaignId: string, input: SourceCreate) {
      return checkedSource(await requestJson<SourceOut>(sourcePath(campaignId), {
        method: 'POST', headers: { ...auth('owner'), 'Content-Type': 'application/json' }, body: JSON.stringify(input),
      }))
    },
    async updateSource(campaignId: string, sourceId: string, expectedVersion: number, input: SourceCreate) {
      return checkedSource(await requestJson<SourceOut>(sourcePath(campaignId, sourceId), {
        method: 'PUT', headers: { ...auth('owner'), 'Content-Type': 'application/json' }, body: JSON.stringify({ ...input, expected_version: expectedVersion }),
      }))
    },
    async confirmSource(campaignId: string, sourceId: string, expectedVersion: number) {
      return checkedSource(await requestJson<SourceOut>(`${sourcePath(campaignId, sourceId)}/confirm`, {
        method: 'POST', headers: { ...auth('owner'), 'Content-Type': 'application/json' }, body: JSON.stringify({ expected_version: expectedVersion }),
      }))
    },
    async sourceVersions(campaignId: string, sourceId: string) {
      const records = await requestJson<SourceOut[]>(`${sourcePath(campaignId, sourceId)}/versions`, { headers: auth() })
      if (!Array.isArray(records)) throw invalid()
      return records.map(checkedSource)
    },
    async saveCaption(campaignId: string, text: string, expectedRevision: number) {
      const record = validateCampaign(await requestJson<CampaignOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/caption`, {
        method: 'PUT', headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify({ text, expected_revision: expectedRevision }),
      }))
      campaigns.set(record.id, record)
      return result()
    },
    async runReview(campaignId: string, contentRevision: number, sourceRevision: number) {
      return checkedReview(await requestJson<ReviewOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify({ expected_content_revision: contentRevision, expected_source_revision: sourceRevision }),
      }))
    },
    async listReviews(campaignId: string) {
      const records = await requestJson<ReviewOut[]>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews`, { headers: auth() })
      if (!Array.isArray(records)) throw invalid()
      return records.map(checkedReview)
    },
    async getReview(campaignId: string, reviewId: string) {
      return checkedReview(await requestJson<ReviewOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}`, { headers: auth() }))
    },
  }
}
export type BackendClient = ReturnType<typeof createBackendClient>
