import { useEffect, useState } from 'react'
import type { BackendClient } from './api/backend'
import type { Receipt } from './api/workflow'
import { describeError } from './api/client'

function statusLabel(receipt: Receipt) {
  if (receipt.readiness === 'approved') return 'Approved'
  if (receipt.readiness === 'approved_with_manual_checks') return 'Approved with manual checks'
  if (receipt.readiness === 'changes_requested') return 'Changes requested'
  if (receipt.readiness === 'stale') return 'Review out of date'
  if (!receipt.automated_review_status) return 'Draft · Not reviewed'
  if (receipt.automated_review_status === 'failed') return 'Review failed'
  if (receipt.automated_review_status === 'running') return 'Review running'
  return receipt.automated_review_status === 'partial' ? 'Partial checks · Needs human review' : 'Needs human review'
}

export default function CampaignStatus({ api, campaignId }: { api: BackendClient; campaignId: string }) {
  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    api.receipt(campaignId).then(record => { if (active) { setReceipt(record); setError('') } })
      .catch(error => { if (active) { setReceipt(null); setError(describeError(error)) } })
    return () => { active = false }
  }, [api, campaignId, attempt])
  return <span className="campaign-status"><span className="badge" role="status">{receipt ? statusLabel(receipt) : error ? 'Status unavailable' : 'Loading status…'}</span>{error && <button type="button" title={error} onClick={() => { setError(''); setAttempt(value => value + 1) }}>Retry status</button>}</span>
}
