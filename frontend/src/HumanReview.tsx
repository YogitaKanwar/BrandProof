import {useEffect,useRef,useState} from 'react'
import type {FormEvent} from 'react'
import type {BackendClient,CampaignOut} from './api/backend'
import type {ReviewOut} from './api/reviewRuns'
import type {Receipt} from './api/workflow'
import {describeError} from './api/client'
import {incompleteChecks} from './api/workflow'
import {useUnsavedChanges} from './unsavedChanges'
export default function HumanReview({api,campaign,run,stale,onChanged,epoch}:{api:BackendClient;campaign:CampaignOut;run:ReviewOut;stale:boolean;onChanged:()=>Promise<void>;epoch:number}){
  const [receipt,setReceipt]=useState<Receipt|null>(null),[error,setError]=useState(''),[notice,setNotice]=useState('')
  const [busy,setBusy]=useState(false),[decision,setDecision]=useState<'approve'|'request_changes'>('request_changes')
  const [reason,setReason]=useState(''),[notes,setNotes]=useState<Record<string,string>>({})
  const lock=useRef(false)
  useUnsavedChanges(busy || !!reason || Object.values(notes).some(note=>!!note))
  const incomplete=incompleteChecks(run)
  const latestRequest=receipt?.requests[receipt.requests.length-1]
  const requestCurrent=latestRequest?.review_id===run.id && !stale
  const alreadyDecided=receipt?.approvals.some(approval=>approval.request_id===latestRequest?.id)
  const receiptCurrent=!stale && receipt?.content_revision===campaign.content_revision && receipt?.source_revision===campaign.source_revision
  useEffect(()=>{let active=true;api.receipt(campaign.id).then(record=>{if(active){setReceipt(record);setError('')}}).catch(error=>{if(active){setReceipt(null);setError(describeError(error))}});return()=>{active=false}},[api,campaign.id,campaign.content_revision,campaign.source_revision,run.id,run.readiness,epoch])
  async function refresh(){setError('');try{setReceipt(null);setReceipt(await api.receipt(campaign.id));await onChanged()}catch(error){setError(describeError(error))}}
  async function request(){if(lock.current||stale||run.status==='running')return;lock.current=true;setBusy(true);setError('');setNotice('');try{await api.requestReview(campaign.id,run.id,{expected_content_revision:run.content_revision,expected_source_revision:run.source_revision});setReceipt(null);setReceipt(await api.receipt(campaign.id));await onChanged();setNotice('Creator review request saved. No approval has been granted.')}catch(error){setError(describeError(error))}finally{lock.current=false;setBusy(false)}}
  async function submit(event:FormEvent){event.preventDefault();if(lock.current||!latestRequest||!requestCurrent||alreadyDecided)return;lock.current=true;setBusy(true);setError('');setNotice('');try{
    const manual=decision==='approve'?Object.fromEntries(incomplete.map(name=>[name,notes[name]||''])):{}
    await api.approve(campaign.id,run.id,{expected_content_revision:run.content_revision,expected_source_revision:run.source_revision},latestRequest.id,decision,reason,manual)
    setReceipt(null);setReceipt(await api.receipt(campaign.id));await onChanged();setReason('');setNotes({});setNotice('Reviewer decision saved. Readiness comes from the server receipt, not the finding count.')
  }catch(error){setError(describeError(error))}finally{lock.current=false;setBusy(false)}}
  return <section className="human-review" aria-labelledby="human-review-heading"><div className="section-heading"><h3 id="human-review-heading" tabIndex={-1}>Human Review</h3><button type="button" disabled={busy} onClick={()=>void refresh()}>Refresh receipt</button></div>
    <p className="receipt-readiness">Readiness: <strong>{receipt ? receiptCurrent ? receipt.readiness.replaceAll('_',' ') : 'stale — refresh receipt' : 'not loaded'}</strong></p><small>Synthetic demo roles are not verified independent human identities. Source confirmation is separate from content approval.</small>
    <div className="creator-request"><h4>Creator</h4><button type="button" disabled={busy||stale||run.status==='running'} onClick={()=>void request()}>Request human review</button><p className="form-help">A new request supersedes previous requests and can stale earlier readiness.</p></div>
    <details open={requestCurrent && !alreadyDecided}><summary>Authorised reviewer decision</summary>{!requestCurrent ? <p className="form-help">Submit a creator request for the current run first.</p> : alreadyDecided ? <p className="form-help">This request already has a decision. A new decision requires a new creator request.</p> : <form onSubmit={submit} className="approval-form"><p className="form-help">Acts as the demo reviewer, who has not edited content. The backend enforces role, author and snapshot restrictions.</p><label htmlFor="approval-decision">Decision</label><select id="approval-decision" disabled={busy} value={decision} onChange={event=>setDecision(event.target.value as typeof decision)}><option value="request_changes">Request changes</option><option value="approve">Approve</option></select><label htmlFor="approval-reason">Reviewer reason</label><textarea id="approval-reason" required minLength={10} maxLength={2000} rows={2} disabled={busy} value={reason} onChange={event=>setReason(event.target.value)}/>
      {decision==='approve' && incomplete.length>0 && <fieldset><legend>Actual manual checks required</legend><p className="form-help">Automation is incomplete. Describe the checks you actually performed for each named scope. Notes do not turn automated coverage into a pass.</p>{incomplete.map(name=><div key={name}><label htmlFor={`manual-${name}`}>{name.replaceAll('_',' ')} reviewer notes</label><textarea id={`manual-${name}`} required minLength={20} maxLength={2000} rows={3} disabled={busy} value={notes[name]||''} onChange={event=>setNotes(previous=>({...previous,[name]:event.target.value}))}/></div>)}</fieldset>}
      <button type="submit" disabled={busy||stale||reason.trim().length<10||(decision==='approve'&&incomplete.some(name=>(notes[name]||'').trim().length<20))}>Record reviewer decision</button></form>}</details>
    {error && <p className="error" role="alert">{error}</p>}<p role="status" className="human-review-status form-help">{notice}</p>
    {receipt && <details className="receipt-history"><summary>Approval receipt &amp; history ({receipt.approvals.length})</summary><p className="form-help">{receipt.notice}</p><p>Scope: {receipt.scope} · Automated status: {receipt.automated_review_status||'none'}</p>{receipt.approvals.map(approval=><article key={approval.id}><h4>{approval.decision.replaceAll('_',' ')} · {approval.is_current&&receiptCurrent?'current':'historical'}</h4><p>{approval.reason}</p><p className="form-help">Advertising-risk coverage: {approval.advertising_snapshot?.status.replaceAll("_"," ")||"not assessed"} · pack {String((approval.advertising_snapshot?.details?.pack as {version?:string}|undefined)?.version||"none")}. This records the scope of that approval.</p><small>Reviewer {approval.reviewer_id} · content {approval.content_revision}/source {approval.source_revision} · {approval.coverage_mode}</small>{Object.entries(approval.manual_checks).map(([name,note])=><p key={name}><strong>{name}</strong>: {note}</p>)}</article>)}</details>}
  </section>
}
