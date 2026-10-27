import { useEffect, useRef, useState } from 'react'
import type { BackendClient, CampaignOut } from './api/backend'
import type {ReactNode} from 'react'
import type { ReviewResult } from './api/reviews'
import type { ReviewOut } from './api/reviewRuns'
import { ApiError, describeError } from './api/client'
import ReviewResults from './ReviewResults'
import Collaboration from './Collaboration'
import HumanReview from './HumanReview'
import { useUnsavedChanges } from './unsavedChanges'

export default function LiveCaption({ api, campaign, onCampaignChange, onResultsAvailable,posterAttached,posterPending,preparePoster,onCaptionSaved,children }: { api: BackendClient; campaign: CampaignOut; onCampaignChange: (result: ReviewResult) => void; onResultsAvailable: (available: boolean) => void;posterAttached:boolean;posterPending:boolean;preparePoster:()=>Promise<CampaignOut>;onCaptionSaved:(previous:number,current:number)=>void;children?:ReactNode }) {
  const [text, setText] = useState(campaign.caption)
  const [saved, setSaved] = useState(campaign.caption)
  const [revision, setRevision] = useState(campaign.content_revision)
  const [busy, setBusy] = useState(false)
  const [action, setAction] = useState<'save' | 'review' | 'other'>('other')
  const lock = useRef(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [conflict, setConflict] = useState(false)
  const [server, setServer] = useState<CampaignOut | null>(null)
  const [runs, setRuns] = useState<ReviewOut[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [returnedRunId, setReturnedRunId] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [correctionId,setCorrectionId]=useState('')
  const [externalConsent,setExternalConsent]=useState(false)
  const [workflowEpoch,setWorkflowEpoch]=useState(0)
  const historyRequest = useRef(0)
  const current = runs.find(run => run.id === selectedId) || runs[0]
  const dirty = text !== saved
  useUnsavedChanges(dirty || busy)
  const effectiveRevision=campaign.caption===saved ? campaign.content_revision : revision
  const stale=!!current && (!current.is_current||current.content_revision!==campaign.content_revision||current.source_revision!==campaign.source_revision)
  const correction=current?.findings.find(finding=>finding.id===correctionId)
  useEffect(() => {
    if (!returnedRunId) return
    const heading = document.getElementById('results-heading')
    heading?.scrollIntoView({ block: 'start' })
    heading?.focus({ preventScroll: true })
  }, [returnedRunId])
  useEffect(() => {
    if (!error) return
    const alert = document.getElementById('caption-workflow-error')
    alert?.scrollIntoView({ block: 'center' })
    alert?.focus({ preventScroll: true })
  }, [error])
  useEffect(() => {
    let active = true
    const request = ++historyRequest.current
    api.listReviews(campaign.id).then(records => { if (active && request === historyRequest.current) { setRuns(records.sort((a,b) => b.created_at.localeCompare(a.created_at))); setHistoryError(''); onResultsAvailable(records.length > 0) } })
      .catch(error => { if (active) setHistoryError(describeError(error)) })
    return () => { active = false }
  }, [api, campaign.id, campaign.content_revision, campaign.source_revision, onResultsAvailable])
  async function save() {
    if (lock.current || conflict) return
    lock.current = true; setBusy(true); setAction('save'); setError(''); setStatus('Saving caption…')
    try {
      const result = await api.saveCaption(campaign.id, text, effectiveRevision)
      const updated = result.data.reviews.find(record => record.campaignId === campaign.id)?.backendCampaign
      if (!updated) throw new Error('Saved response did not contain the campaign.')
      setSaved(updated.caption); setRevision(updated.content_revision); onCampaignChange(result)
      onCaptionSaved(effectiveRevision, updated.content_revision)
      setStatus(`Caption saved on server · revision ${updated.content_revision}`)
    } catch (error) { setError(describeError(error)); setStatus('Caption was not confirmed saved. Your text is preserved.'); if (error instanceof ApiError && error.status === 409) setConflict(true) }
    finally { lock.current = false; setBusy(false); setAction('other') }
  }
  async function loadServerCaption() {
    if (lock.current) return
    lock.current = true; setBusy(true); setAction('other'); setError('')
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
    if (lock.current || dirty || conflict || (!saved.trim()&&!posterAttached&&!posterPending)) return
    lock.current = true; setBusy(true); setAction('review'); setError(''); setStatus('Running review…')
    try {
      const expectedRevision=posterPending ? (await preparePoster()).content_revision : effectiveRevision
      const result = await api.get(campaign.id)
      const latest = result.data.reviews.find(record => record.campaignId === campaign.id)?.backendCampaign
      if (!latest) throw new Error('Campaign is unavailable.')
      onCampaignChange(result)
      if (latest.content_revision !== expectedRevision || latest.caption !== saved) { setConflict(true); setServer(latest); throw new Error('Caption changed on the server. Reconcile before running a review.') }
      const review = await api.runReview(campaign.id, latest.content_revision, latest.source_revision,externalConsent)
      historyRequest.current++
      onResultsAvailable(true)
      setRuns(previous => [review, ...previous.filter(record => record.id !== review.id)]); setSelectedId(review.id); setReturnedRunId(review.id)
      setStatus(review.status === 'failed' ? 'Review failed. No successful verification is claimed.' : `Review returned ${review.status}. Readiness requires its separate human-review receipt.`)
    } catch (error) { setError(describeError(error)); setStatus('Review did not complete successfully. No success is claimed.') }
    finally { lock.current = false; setBusy(false); setAction('other');setExternalConsent(false) }
  }
  async function refreshWorkflow(){setWorkflowEpoch(value=>value+1);const [result,records]=await Promise.all([api.get(campaign.id),api.listReviews(campaign.id)]);onCampaignChange(result);setRuns(records.sort((a,b)=>b.created_at.localeCompare(a.created_at)))}
  async function applyCorrection(){if(lock.current||!current||!correction||dirty||stale)return;lock.current=true;setBusy(true);setError('');try{const result=await api.applySuggestion(campaign.id,current.id,correction.id,{expected_content_revision:current.content_revision,expected_source_revision:current.source_revision});const updated=result.data.reviews.find(row=>row.id===campaign.id)?.backendCampaign;if(!updated)throw new Error('Campaign missing from response.');setText(updated.caption);setSaved(updated.caption);setRevision(updated.content_revision);setCorrectionId('');onCampaignChange(result);setStatus('Explicit correction saved as a new revision. Run a new review.')}catch(error){setError(describeError(error))}finally{lock.current=false;setBusy(false)}}
  return <div className="live-caption">
    <label htmlFor="marketing-caption">What should we review?</label><textarea id="marketing-caption" rows={6} maxLength={20000} value={text} disabled={busy} onChange={event => { setText(event.target.value); setStatus('') }} aria-describedby="live-caption-state" placeholder="Paste your marketing caption here." />
    <div className="caption-footer"><small>{text.length.toLocaleString()} characters</small><button type="button" aria-describedby="live-caption-state" disabled={busy || conflict || !dirty || !text.trim()} onClick={() => void save()}>{busy && action === 'save' ? 'Saving…' : !dirty && saved.trim() ? 'Caption saved' : 'Save caption'}</button></div>
    <p id="live-caption-state" className="form-help">{busy ? 'Please wait for the current request to finish.' : conflict ? 'Saving is paused because the server version changed. Open “Having trouble saving?” below, compare versions, then choose which text to keep.' : !text.trim() ? 'Enter a caption to enable Save caption.' : dirty ? 'Unsaved changes. Save your caption to enable Run review.' : 'Caption saved. Edit the text to save changes, or select Run review below.'}</p>
    <details className="caption-reconcile" open={conflict || undefined}><summary>Having trouble saving?</summary><button type="button" disabled={busy} onClick={() => void loadServerCaption()}>Compare with saved version</button>{conflict && <p className="form-help">Your edits are safe. Compare versions before choosing which to keep.</p>}{server && <div><h3>Saved version {server.content_revision}</h3><pre className="caption-snapshot">{server.caption || '(empty caption)'}</pre><button type="button" onClick={() => reconcile(true)}>Use saved version</button><button type="button" onClick={() => reconcile(false)}>Keep my text</button></div>}</details>
    {children}
    <details className="ai-options"><summary>Optional AI check</summary><label className="ai-consent"><input type="checkbox" checked={externalConsent} disabled={busy} onChange={event=>setExternalConsent(event.target.checked)}/><span>Allow this review to send the caption and selected approved facts to the server-configured AI provider. Off unless you opt in; availability depends on server setup.</span></label></details>
    <div className="run-caption"><button type="button" className="primary" aria-busy={busy && action === 'review'} aria-describedby="run-review-help" disabled={busy || dirty || conflict || (!saved.trim()&&!posterAttached&&!posterPending)} onClick={() => void run()}>{busy && action === 'review' ? <><span className="spinner" aria-hidden="true"/>Reviewing…</> : posterPending ? 'Upload poster and run review' : 'Run review'}</button><small id="run-review-help">{dirty ? 'Save your caption first.' : posterPending ? 'This uploads your selected image privately, then reviews the saved content.' : conflict ? 'Resolve the saved-version conflict first.' : !saved.trim()&&!posterAttached ? 'Add a caption or upload a poster to start.' : 'Checks use saved content and confirmed facts.'}</small></div>
    <p role="status" className="live-review-status form-help">{status}</p>
    {error && <p id="caption-workflow-error" className="error" role="alert" tabIndex={-1}>{error}</p>}
    {historyError && <p className="error" role="alert">Could not load review history. {historyError}</p>}
    {runs.length > 0 && <section id="review-results" aria-labelledby="results-heading">
      <div className="section-heading"><h3 id="results-heading" tabIndex={-1}>Review results</h3><div className="results-actions"><a href="#human-review-heading" onClick={event=>{event.preventDefault();const target=document.getElementById('human-review-heading');target?.scrollIntoView();target?.focus({preventScroll:true})}}>Human review</a><button type="button" disabled={busy} onClick={()=>void refreshWorkflow().catch(error=>setError(describeError(error)))}>Refresh</button></div></div>
      <label htmlFor="review-history">Previous reviews</label><select id="review-history" value={current?.id || ''} onChange={event => setSelectedId(event.target.value)}>{runs.map(record => <option key={record.id} value={record.id}>{new Date(record.created_at).toLocaleString()} · {record.status} · content {record.content_revision}/source {record.source_revision}</option>)}</select>
      {current && <>
        <p className="review-run-summary">{current.status} checks · {stale ? 'Stale content or references' : 'Current content'} · {current.findings.length} {current.findings.length===1 ? 'finding' : 'findings'}</p>
        <ReviewResults run={current} stale={stale} currentCaption={campaign.caption} api={api} onApply={findingId=>{if(dirty){setError('Save or reconcile your caption edits before applying a correction.');return}setCorrectionId(findingId)}} />
        {correction && <div className="correction-confirm" role="group" aria-label="Confirm explicit correction"><h4>Apply this caption correction?</h4><p>Original: {correction.location.quote || 'whole-caption action'}</p><p>Replacement: {correction.suggested_replacement}</p><button type="button" disabled={busy||dirty||stale} onClick={()=>void applyCorrection()}>Apply correction</button><button type="button" onClick={()=>setCorrectionId('')}>Cancel</button></div>}
        <Collaboration key={current.id} api={api} campaign={campaign} run={current} stale={stale} onChanged={refreshWorkflow}/>
        <HumanReview key={`human-${current.id}`} api={api} campaign={campaign} run={current} stale={stale} onChanged={refreshWorkflow} epoch={workflowEpoch}/>
      </>}
    </section>}
  </div>
}
