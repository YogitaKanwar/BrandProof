import { ApiError, requestJson, requestResponse } from './client.ts'
import { createReadinessCheck } from './readiness.ts'
import type { ReadinessOptions } from './readiness.ts'
import type { PosterOut } from './posters.ts'
import type {Snapshot,Revision,Comment,FindingDecision,DemoRole,ReviewRequest,Approval,Receipt} from './workflow.ts'
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
export function createBackendClient(base = '/api/v1', readiness?: ReadinessOptions) {
  const ensureReady = readiness ? createReadinessCheck(base, readiness) : async () => {}
  let session: DemoSessionOut | null = null
  let connecting: Promise<DemoSessionOut> | null = null
  const campaigns = new Map<string, CampaignOut>()
  const invalid = () => new ApiError('The API returned an unexpected response.', 502, 'invalid_response')
  function validateSession(data: DemoSessionOut): DemoSessionOut {
    if (!data || data.mode !== 'synthetic_demo' || typeof data.workspace_id !== 'string' || typeof data.notice !== 'string' || !Number.isFinite(Date.parse(data.expires_at)) ||
      ['owner', 'creator', 'reviewer'].some(role => data.actors?.[role as keyof typeof data.actors]?.role !== role || typeof data.actors?.[role as keyof typeof data.actors]?.access_token !== 'string')) throw invalid()
    return data
  }
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
      await ensureReady()
      if (!session) {
        connecting ??= requestJson<DemoSessionOut>(`${base}/demo-sessions`, { method: 'POST', credentials: 'include', cache: 'no-store' })
        try {
          session = validateSession(await connecting)
        } finally { connecting = null }
      }
      return this.list()
    },
    async resume(): Promise<ReviewResult | null> {
      await ensureReady()
      let restored: DemoSessionOut
      try {
        restored = validateSession(await requestJson<DemoSessionOut>(`${base}/demo-sessions/resume`, {
          method: 'POST', credentials: 'include', cache: 'no-store', headers: { 'X-BrandProof-Session': 'resume' },
        }))
      } catch (error) {
        // A missing/expired cookie never creates another workspace or retries a write.
        if (error instanceof ApiError && error.status === 401) {
          session = null
          campaigns.clear()
          return null
        }
        throw error
      }
      session = restored
      campaigns.clear()
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
      await ensureReady()
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
    async clearCaption(campaignId: string, expectedRevision: number) {
      const record = validateCampaign(await requestJson<CampaignOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/caption/clear`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify({ expected_revision: expectedRevision }),
      }))
      campaigns.set(record.id, record)
      return result()
    },
    async runReview(campaignId: string, contentRevision: number, sourceRevision: number, externalConsent = false) {
      return checkedReview(await requestJson<ReviewOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews`, {
        method: 'POST', signal: AbortSignal.timeout(120000), headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify({ expected_content_revision: contentRevision, expected_source_revision: sourceRevision, external_ai_consent: externalConsent }),
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
    async poster(campaignId: string, posterId?: string) {
      return requestJson<PosterOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/posters${posterId ? `/${encodeURIComponent(posterId)}` : ''}`, {headers: auth()})
    },
    async posterContent(campaignId: string, posterId: string) {
      const response = await requestResponse(`${base}/campaigns/${encodeURIComponent(campaignId)}/posters/${encodeURIComponent(posterId)}/content`, {headers: {...auth(), Accept: 'image/png'}, cache:'no-store'})
      return response.blob()
    },
    async uploadPoster(campaignId: string, file: File, revision: number) {
      return requestJson<PosterOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/posters?expected_revision=${revision}`, {method:'PUT',headers:{...auth(),'Content-Type':file.type},body:file,signal:AbortSignal.timeout(45000)})
    },
    async logo(campaignId:string){return requestJson<BrandLogoOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/brand-logo`,{headers:auth()})},
    async logoContent(campaignId:string,logoId:string){return (await requestResponse(`${base}/campaigns/${encodeURIComponent(campaignId)}/brand-logo/${encodeURIComponent(logoId)}/content`,{headers:auth(),cache:'no-store'})).blob()},
    async uploadLogo(campaignId:string,file:File,revision:number){return requestJson<BrandLogoOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/brand-logo?expected_source_revision=${revision}`,{method:'PUT',headers:{...auth('owner'),'Content-Type':file.type},body:file,signal:AbortSignal.timeout(45000)})},
    async confirmLogo(campaignId:string,logo:BrandLogoOut,revision:number){return requestJson<BrandLogoOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/brand-logo/${encodeURIComponent(logo.id)}/confirm`,{method:'POST',headers:{...auth('owner'),'Content-Type':'application/json'},body:JSON.stringify({expected_version:logo.version,expected_source_revision:revision})})},
    async revisions(campaignId:string){return requestJson<Revision[]>(`${base}/campaigns/${encodeURIComponent(campaignId)}/revisions`,{headers:auth()})},
    async comments(campaignId:string){return requestJson<Comment[]>(`${base}/campaigns/${encodeURIComponent(campaignId)}/comments`,{headers:auth()})},
    async comment(campaignId:string,snapshot:Snapshot,text:string,reviewId:string|null,role:DemoRole='creator'){
      return requestJson<Comment>(`${base}/campaigns/${encodeURIComponent(campaignId)}/comments`,{method:'POST',headers:{...auth(role),'Content-Type':'application/json'},body:JSON.stringify({...snapshot,text,review_id:reviewId})})
    },
    async applySuggestion(campaignId:string,reviewId:string,findingId:string,snapshot:Snapshot){
      const record=validateCampaign(await requestJson<CampaignOut>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}/findings/${encodeURIComponent(findingId)}/apply`,{method:'POST',headers:{...auth(),'Content-Type':'application/json'},body:JSON.stringify(snapshot)}))
      campaigns.set(record.id,record);return result()
    },
    async decisions(campaignId:string,reviewId:string,findingId:string){return requestJson<FindingDecision[]>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}/findings/${encodeURIComponent(findingId)}/decisions`,{headers:auth()})},
    async decideFinding(campaignId:string,reviewId:string,findingId:string,snapshot:Snapshot,version:number,decision:FindingDecision['decision'],reason:string,role:DemoRole='reviewer'){
      return requestJson<FindingDecision>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}/findings/${encodeURIComponent(findingId)}/decisions`,{method:'POST',headers:{...auth(role),'Content-Type':'application/json'},body:JSON.stringify({...snapshot,expected_decision_version:version,decision,reason})})
    },
    async receipt(campaignId:string){return requestJson<Receipt>(`${base}/campaigns/${encodeURIComponent(campaignId)}/receipt`,{headers:auth()})},
    async requestReview(campaignId:string,reviewId:string,snapshot:Snapshot){return requestJson<ReviewRequest>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}/requests`,{method:'POST',headers:{...auth(),'Content-Type':'application/json'},body:JSON.stringify(snapshot)})},
    async approve(campaignId:string,reviewId:string,snapshot:Snapshot,requestId:string,decision:'approve'|'request_changes',reason:string,manualChecks:Record<string,string>,role:DemoRole='reviewer'){
      return requestJson<Approval>(`${base}/campaigns/${encodeURIComponent(campaignId)}/reviews/${encodeURIComponent(reviewId)}/approvals`,{method:'POST',headers:{...auth(role),'Content-Type':'application/json'},body:JSON.stringify({...snapshot,request_id:requestId,decision,reason,manual_checks:manualChecks})})
    },
  }
}
export type BackendClient = ReturnType<typeof createBackendClient>

export interface BrandLogoOut {id:string;campaign_id:string;version:number;status:"pending"|"approved";sha256:string;width:number;height:number;confirmed_by:string|null;created_at:string}
