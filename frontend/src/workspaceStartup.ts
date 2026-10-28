import type { BackendClient } from './api/backend.ts'
import type { ReviewResult } from './api/reviews.ts'

type LocalClient = { list(): Promise<ReviewResult> }

// Restore an existing workspace only. Creating a new sandbox always requires a user action.
export async function loadInitialWorkspace(
  backend: Pick<BackendClient, 'resume'>,
  local: LocalClient,
  route: { page: string; id: string; local?: boolean },
): Promise<ReviewResult> {
  if (route.local) return local.list()
  let localData: ReviewResult | undefined
  let localError: unknown
  try { localData = await local.list() } catch (error) { localError = error }
  // An explicitly opened local draft must remain local even when a demo cookie exists.
  if (route.page === 'draft' && localData?.data.reviews.some(review => review.id === route.id)) return localData
  const restored = await backend.resume()
  if (restored) return restored
  if (!localData) throw localError
  return localData
}
