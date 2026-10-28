import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { reviewClient, deleteLocalReview } from './api/reviews'
import type { ReviewResult } from './api/reviews'
import ContentWorkspace from './ContentWorkspace'
import { createBackendClient } from './api/backend'
import type { BackendClient } from './api/backend'
import { ApiError, describeError } from './api/client'
import { UnsavedChangesContext, useDraftGuard } from './unsavedChanges'
import CampaignStatus from './CampaignStatus'
import GovernanceInsights from './GovernanceInsights'
import { loadInitialWorkspace } from './workspaceStartup'
import { exampleDetails, prepareExampleCampaign } from './exampleCampaign'

type Page = 'home' | 'new' | 'draft' | 'insights'
function currentRoute(): { page: Page; id: string; local?: boolean } {
  const hash = window.location.hash
  if(hash==='#/insights')return {page:'insights',id:''}
  if (hash === '#/new') return { page: 'new', id: '' }
  if (hash === '#/local-new') return {page:'new',id:'',local:true}
  if (hash.startsWith('#/review/')) { const id=hash.slice(9).split('?')[0];try{return {page:'draft',id:decodeURIComponent(id)}}catch{return {page:'draft',id}} }
  return { page: 'home', id: '' }
}
const steps = ['Sources', 'Content', 'Review']

export default function ReviewWorkspace() {
  const [route, setRoute] = useState(currentRoute)
  const [result, setResult] = useState<ReviewResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [dateError, setDateError] = useState('')
  const [title, setTitle] = useState('')
  const [brand, setBrand] = useState('')
  const [brief, setBrief] = useState('')
  const [notice, setNotice] = useState('')
  const [deletingId, setDeletingId] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [publicationDate, setPublicationDate] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [creatingExample, setCreatingExample] = useState(false)
  const [sourceClient, setSourceClient] = useState<BackendClient | null>(null)
  const service = useRef< typeof reviewClient | ReturnType<typeof createBackendClient>>(reviewClient)
  const connectionInFlight = useRef(false)
  const needsInitialLoad = useRef(true)
  const workspaceLoadVersion = useRef(0)
  const heading = useRef<HTMLHeadingElement>(null)
  const savingRef = useRef(false)
  const { register, confirmLeave } = useDraftGuard()
  const acceptedUrl = useRef(window.location.href)
  const allowedHash = useRef('')
  function goTo(destination: string) {
    const hash = `#${destination}`
    if (window.location.hash === hash) return
    allowedHash.current = hash
    window.location.hash = destination
  }

  useEffect(() => {
    const update = () => {
      if (window.location.hash !== allowedHash.current && !confirmLeave()) {
        window.history.replaceState(null, '', acceptedUrl.current)
        return
      }
      allowedHash.current = ''
      acceptedUrl.current = window.location.href
      setRoute(currentRoute())
    }
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [confirmLeave])
  useEffect(() => { heading.current?.focus() }, [route.page, route.id])
  useEffect(() => {
    const client = service.current
    if (route.page !== 'draft' || !('get' in client)) return
    let active = true
    client.get(route.id).then(data => { if (active && client===service.current) setResult(data) })
      .catch(error => { if (active && client===service.current) setNotice(describeError(error)) })
    return () => { active = false }
  }, [route.page, route.id])
  useEffect(() => {
    let active = true
    const version = ++workspaceLoadVersion.current
    const client = createBackendClient(import.meta.env.VITE_API_BASE_URL || '/api/v1')
    loadInitialWorkspace(client, reviewClient, currentRoute()).then(data => {
      if (!active || version !== workspaceLoadVersion.current) return
      needsInitialLoad.current = false
      service.current = data.mode === 'backend' ? client : reviewClient
      setSourceClient(data.mode === 'backend' ? client : null)
      setResult(data)
    })
      .catch(error => { if (active && version === workspaceLoadVersion.current) setLoadError(`Could not restore your workspace. ${describeError(error)} No new workspace was created.`) })
      .finally(() => { if (active && version === workspaceLoadVersion.current) setLoading(false) })
    return () => { active = false }
  }, [])
  async function retry() {
    const version = ++workspaceLoadVersion.current
    const selectedService = service.current
    setLoading(true); setLoadError('')
    try {
      if (needsInitialLoad.current) {
        const client = createBackendClient(import.meta.env.VITE_API_BASE_URL || '/api/v1')
        const data = await loadInitialWorkspace(client, reviewClient, currentRoute())
        if (version !== workspaceLoadVersion.current) return
        service.current = data.mode === 'backend' ? client : reviewClient
        setSourceClient(data.mode === 'backend' ? client : null)
        needsInitialLoad.current = false
        setResult(data)
      } else {
        const data = await selectedService.list()
        if (version === workspaceLoadVersion.current) setResult(data)
      }
    }
    catch (error) { if (version === workspaceLoadVersion.current) setLoadError(describeError(error)) }
    finally { if (version === workspaceLoadVersion.current) setLoading(false) }
  }
  async function connectDemo(destination='/') {
    if (loading || connectionInFlight.current || !confirmLeave()) return
    connectionInFlight.current = true
    setConnecting(true); setNotice('')
    // Explicit action always means a new isolated demo, never silent session renewal.
    const client = createBackendClient(import.meta.env.VITE_API_BASE_URL || '/api/v1')
    try {
      const data = await client.connect()
      service.current = client
      needsInitialLoad.current = false
      setSourceClient(client)
      setResult(data); setLoadError(''); goTo(destination)
    } catch (error) { setNotice(describeError(error)) }
    finally { connectionInFlight.current = false; setConnecting(false) }
  }
  async function startReview(){if(loading || creatingExample)return;if(result?.mode==='backend'){window.location.hash='/new';return}await connectDemo('/new')}
  async function startExample() {
    if (loading || connecting || creatingExample || connectionInFlight.current || !confirmLeave()) return
    connectionInFlight.current = true
    setCreatingExample(true); setNotice('')
    const client = sourceClient || createBackendClient(import.meta.env.VITE_API_BASE_URL || '/api/v1')
    let created: ReviewResult | undefined
    try {
      if (!sourceClient) await client.connect()
      created = await client.create(exampleDetails)
      service.current = client
      needsInitialLoad.current = false
      setSourceClient(client); setResult(created); setLoadError('')
      const campaign = created.data.reviews[0].backendCampaign!
      // Keep a partly prepared example visible if a later request fails.
      const prepared = await prepareExampleCampaign(client, campaign)
      setResult(prepared)
      goTo(`/review/${campaign.id}`)
      setNotice('Fictional example ready: four confirmed sample rules, one pending policy, a deliberately flawed caption and a sample poster are saved. Run review to generate findings, then choose a correction or human decision.')
    } catch (error) {
      if (created) {
        try { setResult(await client.get(created.data.reviews[0].id)) } catch { /* Preserve the last acknowledged result. */ }
        goTo(`/review/${created.data.reviews[0].id}`)
      }
      setNotice(`Example setup stopped. ${describeError(error)}${created ? ' The partly prepared example is saved; inspect it before continuing.' : ''}`)
    } finally { connectionInFlight.current = false; setCreatingExample(false) }
  }
  async function openLocalDrafts(destination = '/') {
    if (connectionInFlight.current || !confirmLeave()) return
    workspaceLoadVersion.current++
    service.current = reviewClient
    needsInitialLoad.current = false
    setSourceClient(null)
    await retry(); goTo(destination)
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (savingRef.current) return
    setSaveError(''); setNotice('')
    setDateError('')
    const dateInput = event.currentTarget.querySelector<HTMLInputElement>('#publication-date')
    if (dateInput && (!dateInput.value || !dateInput.validity.valid)) {
      setDateError('Choose a valid publication date.')
      dateInput.focus()
      return
    }
    savingRef.current = true; setSaving(true)
    try {
      const saved = await service.current.create({ title, brand, brief, publicationDate })
      setResult(saved)
      setNotice('')
      setTitle(''); setBrand(''); setBrief('')
      goTo(`/review/${saved.data.reviews[0].id}`)
    } catch (error) {
      if (error instanceof ApiError && error.status === 422 && error.details.some(detail => detail.location.includes('publication_date'))) {
        setDateError('Choose a valid publication date.'); dateInput?.focus()
      } else setSaveError(`${describeError(error)} Your form entries are preserved.`)
    } finally { savingRef.current = false; setSaving(false) }
  }
  async function removeDraft(id: string) {
    if (deleting || result?.mode !== 'local') return
    setDeleting(true); setNotice('')
    try {
      const deleted = await deleteLocalReview(id)
      setResult(previous => previous ? { ...previous, data: deleted.data } : previous)
      setDeletingId(''); setNotice(deleted.warning || 'Local draft deleted.')
    } catch (error) { setNotice(describeError(error)) }
    finally { setDeleting(false) }
  }
  const draft = result?.data.reviews.find(review => review.id === route.id)
  const campaign = result?.data.campaigns.find(item => item.id === draft?.campaignId)
  const pageName = route.page==='insights'?'Governance Insights':route.page === 'home' ? 'Overview' : route.page === 'new' ? 'New review' : 'Content workspace'
  return <UnsavedChangesContext.Provider value={register}><div className="app-shell">
    <a className="skip-link" href="#main" onClick={event => { event.preventDefault(); document.getElementById('main')?.focus() }}>Skip to content</a>
    <aside className="sidebar">
      <a className="wordmark" href="#/"><span aria-hidden="true">B</span> BrandProof</a>
      <p className="sidebar-label">WORKSPACE</p>
      <nav aria-label="Main navigation" className="main-nav">
        <a href="#/" aria-current={route.page === 'home' ? 'page' : undefined}>Overview</a>
        <a href="#/new" onClick={event=>{event.preventDefault();void startReview()}} aria-current={route.page === 'new' ? 'page' : undefined}>New review</a>
        <a href="#/insights" aria-current={route.page==='insights'?'page':undefined}>Governance Insights</a>
      </nav>
      <p className="sidebar-note">Brand governance</p>
    </aside>
    <div className="workspace">
      <header className="topbar"><span>{pageName}</span><details className="connection-status"><summary>{loading ? 'Connecting…' : result?.mode === 'backend' ? 'Demo connected' : 'Preview mode'}</summary><div className="connection-popover"><p>{result?.mode === 'backend' ? 'Connected demo: use fictional material only. Saved work can be restored in this browser for up to 24 hours. A new demo creates a separate workspace.' : 'Drafts are stored in this browser. Live verification is not connected.'}</p><details className="connection-details"><summary>About this demo</summary><p className="form-help">{result?.notice} Demo roles are synthetic. A protected browser cookie restores the demo; role tokens stay in memory. Server deletion is unavailable. AI and OCR coverage depend on server configuration.</p></details><button type="button" disabled={loading || connecting || saving} onClick={() => void connectDemo()}>{connecting ? 'Connecting…' : result?.mode === 'backend' ? 'Start a new demo workspace' : 'Start connected demo'}</button>{result?.mode === 'backend' ? <><button type="button" disabled={saving} onClick={() => void retry()}>Reload campaigns</button><button type="button" disabled={saving} onClick={() => void openLocalDrafts()}>Open local drafts</button></> : <p><a className="local-draft-link" href="#/local-new" onClick={event => { event.preventDefault(); void openLocalDrafts("/local-new") }}>Create a local-only draft instead</a></p>}</div></details></header>
      <main id="main" tabIndex={-1}>
        <div role="status" className={notice ? 'notice' : ''}>{notice}</div>
        <div className="page-heading"><div><h1 ref={heading} tabIndex={-1}>{route.page==='insights'?'Governance Insights':route.page === 'home' ? 'Every claim, accounted for.' : route.page === 'new' ? 'New review' : 'Review workspace'}</h1><p>{route.page==='insights'?'Trace repeated finding signals to their evidence and human decisions.':route.page === 'home' ? 'Review marketing content against approved brand information.' : route.page === 'new' ? 'Add a name, or continue straight to your brand information.' : 'Brand information first. Marketing content next.'}</p></div>{route.page === 'home' && <a className="button primary" href="#/new" onClick={event=>{event.preventDefault();void startReview()}} aria-disabled={connecting}>{connecting?'Connecting…':'New Review'}</a>}</div>
        {route.page === 'home' && <ol aria-label="Review workflow" className="workflow">{steps.map((name, index) => <li key={name}>{index > 0 && <span aria-hidden="true" className="step-divider">→</span>}{name}</li>)}</ol>}
        {loading ? <div className="loading" role="status"><span className="spinner" aria-hidden="true" />Loading your workspace…</div> : loadError ? <div className="error" role="alert">{loadError} <button onClick={() => void retry()}>Retry</button></div> : route.page==='insights'?<GovernanceInsights api={sourceClient}/>: route.page === 'home' ? <section aria-labelledby="drafts-heading">
          <div className="section-heading"><h2 id="drafts-heading">Recent Reviews</h2><span>{result?.data.reviews.length || 0} total</span></div>
          <p className="form-help">Want to explore first? <button type="button" disabled={loading || connecting || creatingExample} onClick={() => void startExample()}>{creatingExample ? 'Preparing example…' : 'Try an editable example'}</button> Creates a separate fictional campaign; existing campaigns are unchanged. <button type="button" disabled={loading||connecting||creatingExample} onClick={()=>void startReview()}>New blank campaign</button> Findings and human approval still require your actions.</p>
          {!result?.data.reviews.length ? <p className="reviews-empty">No reviews yet</p> : <div className="review-list">{result.data.reviews.map(review => <article className="campaign-card review-row" key={review.id}>
            <h2><a href={`#/review/${review.id}`}>{review.title}</a></h2>
            {result.mode === 'backend' && sourceClient ? <CampaignStatus api={sourceClient} campaignId={review.id}/> : <span className="badge">Draft · Not checked</span>}
            <small><time dateTime={review.createdAt}>{new Date(review.createdAt).toLocaleDateString()}</time></small>
            {result.mode === 'local' && <div className="review-delete">{deletingId === review.id ? <div role="group" aria-label={`Delete ${review.title}?`}><span>Delete this local draft?</span><button type="button" disabled={deleting} onClick={() => void removeDraft(review.id)}>Confirm delete</button><button type="button" disabled={deleting} onClick={() => setDeletingId('')}>Cancel</button></div> : <button type="button" disabled={deleting} aria-label={`Delete ${review.title}`} onClick={() => setDeletingId(review.id)}>Delete</button>}</div>}
          </article>)}</div>}
        </section> : route.page==='new' && result?.mode!=='backend' && !route.local ? <section className="campaign-form connected-entry"><h2>Start a connected review</h2><p className="form-help">Create a real demo workspace to save sources and confirm them as owner. Saved work can be restored in this browser for up to 24 hours; unsaved edits are not restored. No local draft is uploaded automatically.</p><button type="button" className="primary" disabled={connecting} onClick={()=>void connectDemo('/new')}>{connecting?'Connecting…':'Start connected review'}</button><p className="form-help"><a href="#/local-new" onClick={event => { event.preventDefault(); void openLocalDrafts("/local-new") }}>Create a local-only draft instead</a></p></section> : route.page === 'new' ? <form className="campaign-form" onSubmit={submit} noValidate aria-busy={saving}>
          <h2>Review details</h2>
          <fieldset disabled={saving}>
            <label htmlFor="review-title">Review title <span className="optional">optional</span></label><input id="review-title" maxLength={120} value={title} onChange={event => setTitle(event.target.value)} placeholder="Untitled review" aria-describedby="title-help" />
            <small id="title-help">Leave blank to use “Untitled review”.</small>
            {result?.mode === 'backend' && <><label className="publication-label" htmlFor="publication-date">Publication date <span className="required-label">required</span></label><input id="publication-date" type="date" required value={publicationDate} aria-invalid={!!dateError} aria-describedby={`publication-help${dateError ? ' publication-error' : ''}`} onChange={event => { setPublicationDate(event.target.value); setDateError('') }} /><small id="publication-help">When this content will be published. Used to check whether facts are valid.</small>{dateError && <p id="publication-error" className="field-error error" role="alert">{dateError}</p>}</>}
            {result?.mode !== 'backend' && <details className="review-optional-details"><summary>Campaign details</summary>
            <label htmlFor="review-brand">Brand <span className="optional">optional</span></label><input id="review-brand" maxLength={120} value={brand} onChange={event => setBrand(event.target.value)} placeholder="Brand or organisation" />
            <label htmlFor="review-brief">Brief <span className="optional">optional</span></label><textarea id="review-brief" maxLength={2000} rows={4} value={brief} onChange={event => setBrief(event.target.value)} placeholder="Campaign context" aria-describedby="brief-help" /><small id="brief-help">Context only · not an approved source</small></details>}
          </fieldset>
          {saveError && <p className="error" role="alert">{saveError}</p>}
          <div className="form-actions"><button type="button" disabled={saving} onClick={() => { window.location.hash = '/' }}>Cancel</button><button className="primary" disabled={saving} type="submit">{saving && <span className="spinner" aria-hidden="true" />}{saving ? 'Saving…' : 'Continue'}</button></div>
        </form> : draft ? <ContentWorkspace key={draft.id} review={draft} campaign={campaign} sourceClient={result?.mode === 'backend' ? sourceClient || undefined : undefined} onCampaignChange={setResult} /> : <section className="empty session-ended"><h2>Review access unavailable</h2><p>This review is not available in the current workspace. The demo cookie may have expired, been blocked or been cleared, or you may have started another demo. Refreshing does not delete saved server data.</p><p>A new demo starts a separate workspace. Local drafts are available only in the browser where they were saved.</p><button type="button" disabled={connecting} onClick={()=>void connectDemo('/new')}>{connecting ? 'Connecting…' : 'Start a separate demo'}</button><a className="button" href="#/">Back to overview</a></section>}
      </main>
    </div>
  </div></UnsavedChangesContext.Provider>
}
