export class ApiError extends Error {
  status: number
  code: string
  details: { location: (string | number)[]; message: string }[]
  constructor(message: string, status: number, code = 'request_failed', details: { location: (string | number)[]; message: string }[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

// Transport only. Routes must come from Rushab's confirmed API contract.
export async function requestResponse(url: string, options: RequestInit = {}): Promise<Response> {
  let response: Response
  try {
    const headers = new Headers(options.headers)
    if (!headers.has('Accept')) headers.set('Accept', 'application/json')
    response = await fetch(url, { ...options, headers, signal: options.signal ?? AbortSignal.timeout(10000) })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0)
  }
  if (!response.ok) {
    let payload
    try { payload = await response.json() } catch { /* Non-JSON proxy/server error. */ }
    const error = payload?.error
    throw new ApiError(typeof error?.message === 'string' ? error.message : `Request failed (${response.status}). Please try again.`, response.status,
      typeof error?.code === 'string' ? error.code : 'request_failed',
      Array.isArray(error?.details) ? error.details.filter((detail: { location?: unknown; message?: unknown }) => Array.isArray(detail?.location) && typeof detail?.message === 'string') : [])
  }
  return response
}
export async function requestJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await requestResponse(url, options)
  try { return await response.json() as T }
  catch { throw new ApiError('The server returned an unreadable response.', response.status) }
}

export function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return error instanceof Error ? error.message : 'Request failed. Please retry.'
  const actions: Record<number, string> = {
    401: 'Demo access expired or missing. Start a new demo; it creates a separate workspace.',
    403: 'Your demo role cannot perform this action.',
    404: 'This resource is missing or inaccessible in this workspace.',
    409: 'State changed. Reload and reconcile before trying again.',
    413: 'Image exceeds the upload limit.',
    415: 'Choose a PNG or JPEG file.',
    422: 'Check the supplied fields.',
  }
  const details = error.details.map(detail => `${detail.location.filter(part => part !== 'body').join('.')}: ${detail.message}`).join(' ')
  return [error.message, actions[error.status], details].filter(Boolean).join(' ')
}
