import { useEffect, useRef, useState } from 'react'
import type { BackendClient, CampaignOut } from './api/backend'
import type { ReviewResult } from './api/reviews'
import type { ReviewOut } from './api/reviewRuns'
import { ApiError, describeError } from './api/client'
import ReviewResults from './ReviewResults'

export default function LiveCaption({ api, campaign, onCampaignChange, onResultsAvailable }: { api: BackendClient; campaign: CampaignOut; onCampaignChange: (result: ReviewResult) => void; onResultsAvailable: (available: boolean) => void }) {
  const [text, setText] = useState(campaign.caption)
  const [saved, setSaved] = useState(campaign.caption)
  const [revision, setRevision] = useState(campaign.content_revision)
  const [busy, setBusy] = useState(false)
  const lock = useRef(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [conflict, setConflict] = useState(false)
  const [server, setServer] = useState<CampaignOut | null>(null)
  const [runs, setRuns] = useState<ReviewOut[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [historyError, setHistoryError] = useState('')
  const historyRequest = useRef(0)
  const current = runs.find(run => run.id === selectedId) || runs[0]
  const dirty = text !== saved
  useEffect(() => {
    let active = true
    const request = ++historyRequest.current
    api.listReviews(campaign.id).then(records => { if (active && request === historyRequest.current) { setRuns(records.sort((a,b) => b.created_at.localeCompare(a.created_at))); setHistoryError(''); onResultsAvailable(records.length > 0) } })
      .catch(error => { if (active) setHistoryError(describeError(error)) })
    return () => { active = false }
  }, [api, campaign.id, campaign.content_revision, campaign.source_revision, onResultsAvailable])
  async function save() {
    if (lock.current || conflict) return
    lock.current = true; setBusy(true); setError(''); setStatus('Saving caption…')
    try {
      const result = await api.saveCaption(campaign.id, text, revision)
      const updated = result.data.reviews.find(record => record.campaignId === campaign.id)?.backendCampaign
      if (!updated) throw new Error('Saved response did not contain the campaign.')
      setSaved(updated.caption); setRevision(updated.content_revision); onCampaignChange(result)
      setStatus(`Caption saved on server · revision ${updated.content_revision}`)
    } catch (error) { setError(describeError(error)); setStatus('Caption was not confirmed saved. Your text is preserved.'); if (error instanceof ApiError && error.status === 409) setConflict(true) }
    finally { lock.current = false; setBusy(false) }
  }
  async function loadServerCaption() {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    try {
      const result = await api.get(campaign.id)
      const updated = result.data.reviews.find(record => record.campaignId === campaign.id)?.backendCampaign
      if (!updated) throw new Error('Campaign is unavailable.')
      setServer(updated); onCampaignChange(result)
    } catch (error) { setError(describeError(error)) }
    finally { lock.current = false; setBusy(false) }
  }
  function reconcile(useServer: boolean) {
    if (!server) return
    if (useServer) setText(server.caption)
    setSaved(server.caption); setRevision(server.content_revision); setConflict(false); setServer(null)
    setStatus(useServer ? 'Loaded server caption.' : 'Your text is preserved against the latest revision. Save it explicitly to update the server.')
  }
  async function run() {
    if (lock.current || dirty || conflict || !saved.trim()) return
    lock.current = true; setBusy(true); setError(''); setStatus('Checking exact text…')
    try {
      const result = await api.get(campaign.id)
      const latest = result.data.reviews.find(record => record.campaignId === campaign.id)?.backendCampaign
      if (!latest) throw new Error('Campaign is unavailable.')
      onCampaignChange(result)
      if (latest.content_revision !== revision || latest.caption !== saved) { setConflict(true); setServer(latest); throw new Error('Caption changed on the server. Reconcile before running a review.') }
      const review = await api.runReview(campaign.id, latest.content_revision, latest.source_revision)
      historyRequest.current++
      onResultsAvailable(true)
      setRuns(previous => [review, ...previous.filter(record => record.id !== review.id)]); setSelectedId(review.id)
      setStatus(review.status === 'failed' ? 'Review failed. No successful verification is claimed.' : `Exact-text review returned ${review.status}. Not approved.`)
    } catch (error) { setError(describeError(error)); setStatus('Review did not complete successfully. No success is claimed.') }
    finally { lock.current = false; setBusy(false) }
  }
  return <div className="live-caption">
    <label htmlFor="marketing-caption">Marketing caption</label><textarea id="marketing-caption" rows={7} maxLength={20000} value={text} disabled={busy} onChange={event => { setText(event.target.value); setStatus('') }} aria-describedby="live-caption-state" placeholder="Paste the marketing caption to verify." />
    <div className="caption-footer"><small>{text.length.toLocaleString()}/20,000 characters · revision {revision}</small><button type="button" disabled={busy || conflict || !dirty || !text.trim()} onClick={() => void save()}>Save caption</button></div>
    <p id="live-caption-state" className="form-help">{dirty ? 'Unsaved changes · save before running.' : 'Caption is saved on the server.'}</p>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="caption-reconcile"><button type="button" disabled={busy} onClick={() => void loadServerCaption()}>Compare server caption</button>{conflict && <p className="form-help">Stale revision. Your edits have not been overwritten.</p>}{server && <div><h3>Server revision {server.content_revision}</h3><pre className="caption-snapshot">{server.caption || '(empty caption)'}</pre><button type="button" onClick={() => reconcile(true)}>Use server version</button><button type="button" onClick={() => reconcile(false)}>Keep my text against this revision</button></div>}</div>
    <div className="run-caption"><button type="button" className="primary" disabled={busy || dirty || conflict || !saved.trim()} onClick={() => void run()}>Run Review</button><small>{!saved.trim() ? 'Add and save a caption first. ' : dirty ? 'Save your changes first. ' : ''}Exact-text only; AI, poster checks and human approval are unavailable.</small></div>
    <p role="status" className="live-review-status form-help">{status}</p>
    {historyError && <p className="error" role="alert">Could not load review history. {historyError}</p>}
    {runs.length > 0 && <section id="review-results" aria-labelledby="results-heading"><h3 id="results-heading" tabIndex={-1}>Review Results</h3><label htmlFor="review-history">Saved runs</label><select id="review-history" value={current?.id || ''} onChange={event => setSelectedId(event.target.value)}>{runs.map(record => <option key={record.id} value={record.id}>{new Date(record.created_at).toLocaleString()} · {record.status} · content {record.content_revision}/source {record.source_revision}</option>)}</select>{current && <><p className="review-run-summary">{current.status} · {current.is_current && current.content_revision === campaign.content_revision && current.source_revision === campaign.source_revision ? 'Current' : 'Stale'} · Not approved · {current.findings.length} findings</p><ReviewResults run={current} stale={!current.is_current || current.content_revision !== campaign.content_revision || current.source_revision !== campaign.source_revision} currentCaption={campaign.caption} /></>}</section>}
  </div>
}
