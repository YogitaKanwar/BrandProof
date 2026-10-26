import { ApiError } from './client.ts'
import type { Campaign } from './campaigns.ts'
import type { CampaignOut } from './backend.ts'

export interface ReviewInput { title: string; brand: string; brief: string; publicationDate?: string }
export interface Review {
  id: string
  campaignId: string
  title: string
  brief: string
  createdAt: string
  status: 'draft'
  backendCampaign?: CampaignOut
}
export interface ReviewWorkspace { campaigns: Campaign[]; reviews: Review[] }
export interface ReviewAdapter {
  list(): Promise<ReviewWorkspace>
  create(input: ReviewInput): Promise<ReviewWorkspace>
}
export interface ReviewResult { data: ReviewWorkspace; mode: 'local' | 'backend'; notice: string }
const storageKey = 'brandproof.development.reviews.v1'

function read(): ReviewWorkspace {
  const raw = localStorage.getItem(storageKey)
  if (!raw) return { campaigns: [], reviews: [] }
  const data = JSON.parse(raw) as ReviewWorkspace
  if (!data || !Array.isArray(data.campaigns) || !Array.isArray(data.reviews) ||
    !data.campaigns.every(c => c && ['id', 'name', 'brand', 'description', 'createdAt'].every(k => typeof c[k as keyof Campaign] === 'string')) ||
    !data.reviews.every(r => r && ['id', 'campaignId', 'title', 'brief', 'createdAt'].every(k => typeof r[k as keyof Review] === 'string') && r.status === 'draft' && data.campaigns.some(c => c.id === r.campaignId))) {
    throw new Error('Local review data could not be read. Existing data has been preserved.')
  }
  return data
}

export const localReviewAdapter: ReviewAdapter = {
  async list() { return read() },
  async create(input) {
    const title = input.title.trim() || 'Untitled review', brand = input.brand.trim(), brief = input.brief.trim()
    if (title.length > 120 || brand.length > 120 || brief.length > 2000) throw new Error('Please shorten the review details to the displayed limits.')
    const data = read()
    const createdAt = new Date().toISOString()
    const campaign: Campaign = { id: crypto.randomUUID(), name: title, brand, description: brief, createdAt }
    const review: Review = { id: crypto.randomUUID(), campaignId: campaign.id, title, brief, createdAt, status: 'draft' }
    const next = { campaigns: [campaign, ...data.campaigns], reviews: [review, ...data.reviews] }
    // A single write keeps the internal campaign and draft together on storage failure.
    localStorage.setItem(storageKey, JSON.stringify(next))
    return next
  },
}

// Inject Rushab's adapter once routes/auth/schema are confirmed. No guessed endpoints.
// Offline fallback is sticky per session so backend and local records never mix.
export function createReviewClient(remote?: ReviewAdapter, local: ReviewAdapter = localReviewAdapter) {
  let useLocal = !remote
  let notice = 'Development mode: drafts are saved only in this browser. No backend is connected.'
  async function run(operation: (adapter: ReviewAdapter) => Promise<ReviewWorkspace>): Promise<ReviewResult> {
    if (!useLocal && remote) {
      try { return { data: await operation(remote), mode: 'backend', notice: 'Connected to backend.' } }
      catch (error) {
        if (!(error instanceof ApiError) || ![0, 502, 503, 504].includes(error.status)) throw error
        useLocal = true
        notice = 'Backend unavailable. Working with separate browser-local drafts; nothing is synced. A failed server request may need reconciliation later.'
      }
    }
    return { data: await operation(local), mode: 'local', notice }
  }
  return {
    list: () => run(adapter => adapter.list()),
    create: (input: ReviewInput) => run(adapter => adapter.create(input)),
  }
}
export const reviewClient = createReviewClient()

export async function deleteLocalReview(id: string) {
  const data = read()
  const removed = data.reviews.find(review => review.id === id)
  if (!removed) throw new Error('Draft no longer exists. Reload the list.')
  const reviews = data.reviews.filter(review => review.id !== id)
  const next = { reviews, campaigns: data.campaigns.filter(campaign => campaign.id !== removed.campaignId || reviews.some(review => review.campaignId === campaign.id)) }
  localStorage.setItem(storageKey, JSON.stringify(next))
  let warning = ''
  try {
    localStorage.removeItem(`brandproof.development.caption.${id}`)
    localStorage.removeItem(`brandproof.development.source.${id}`)
  } catch { warning = 'Draft removed from the list, but browser storage blocked cleanup of its local content.' }
  return { data: next, warning }
}
