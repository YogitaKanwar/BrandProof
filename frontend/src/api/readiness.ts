import { ApiError } from './client.ts'

export interface ReadinessOptions {
  onStatus?: (message: string) => void
  timeoutMs?: number
  retryMs?: number
}

// Retry only a credential-free health GET. A POST is never replayed.
export function createReadinessCheck(base: string, options: ReadinessOptions = {}) {
  let pending: Promise<void> | undefined
  let readyUntil = 0
  async function check() {
    const deadline = Date.now() + (options.timeoutMs ?? 90000)
    options.onStatus?.('Connecting to the review service…')
    try {
      while (Date.now() < deadline) {
        try {
          const response = await fetch(`${base}/health`, {
            method: 'GET', credentials: 'omit', cache: 'no-store',
            headers: { Accept: 'application/json' },
            signal: AbortSignal.timeout(Math.max(1, Math.min(10000, deadline - Date.now()))),
          })
          if (response.ok) {
            const health = await response.json()
            if (health.status === 'ok' && health.database === 'ok') {
              readyUntil = Date.now() + 15000
              return
            }
          }
        } catch { /* A sleeping service may time out or return a proxy page. */ }
        options.onStatus?.('Starting the review service. This can take up to 90 seconds. Please keep this page open…')
        const remaining = deadline - Date.now()
        if (remaining > 0) await new Promise(resolve => setTimeout(resolve, Math.min(options.retryMs ?? 2000, remaining)))
      }
      throw new ApiError('The review service is still unavailable. Your request has not been submitted. Please try again shortly.', 503, 'service_starting')
    } finally { options.onStatus?.('') }
  }
  return async () => {
    if (Date.now() < readyUntil) return
    pending ??= check().finally(() => { pending = undefined })
    await pending
  }
}
