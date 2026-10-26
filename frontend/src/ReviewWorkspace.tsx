import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { reviewClient, deleteLocalReview } from './api/reviews'
import type { ReviewResult } from './api/reviews'
import ContentWorkspace from './ContentWorkspace'
import { createBackendClient } from './api/backend'
import type { BackendClient } from './api/backend'
import { describeError } from './api/client'

type Page = 'home' | 'new' | 'draft'
function currentRoute(): { page: Page; id: string } {
  const hash = window.location.hash
  if (hash === '#/new') return { page: 'new', id: '' }
  if (hash.startsWith('#/review/')) return { page: 'draft', id: hash.slice(9) }
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
  const [title, setTitle] = useState('')
  const [brand, setBrand] = useState('')
  const [brief, setBrief] = useState('')
  const [notice, setNotice] = useState('')
  const [deletingId, setDeletingId] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [publicationDate, setPublicationDate] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [sourceClient, setSourceClient] = useState<BackendClient | null>(null)
  const service = useRef< typeof reviewClient | ReturnType<typeof createBackendClient>>(reviewClient)
  const connectionInFlight = useRef(false)
  const heading = useRef<HTMLHeadingElement>(null)
  const savingRef = useRef(false)

  useEffect(() => {
    const update = () => setRoute(currentRoute())
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])
  useEffect(() => { heading.current?.focus() }, [route.page, route.id])
  useEffect(() => {
    const client = service.current
    if (route.page !== 'draft' || !('get' in client)) return
    let active = true
    client.get(route.id).then(data => { if (active) setResult(data) })
      .catch(error => { if (active) setNotice(describeError(error)) })
    return () => { active = false }
  }, [route.page, route.id])
  useEffect(() => {
    let active = true
    reviewClient.list().then(data => { if (active) setResult(data) })
      .catch(() => { if (active) setLoadError('Could not open local drafts. Browser storage may be blocked or contain unreadable data. Your existing data has not been cleared.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])
  async function retry() {
    setLoading(true); setLoadError('')
    try { setResult(await service.current.list()) }
    catch (error) { setLoadError(describeError(error)) }
    finally { setLoading(false) }
  }
  async function connectDemo() {
    if (connectionInFlight.current) return
    connectionInFlight.current = true
    setConnecting(true); setNotice('')
    // Explicit action always means a new isolated demo, never silent session renewal.
    const client = createBackendClient()
    try {
      const data = await client.connect()
      service.current = client
      setSourceClient(client)
      setResult(data); setLoadError(''); window.location.hash = '/'
    } catch (error) { setNotice(describeError(error)) }
    finally { connectionInFlight.current = false; setConnecting(false) }
  }
  async function openLocalDrafts() {
    service.current = reviewClient
    setSourceClient(null)
    await retry(); window.location.hash = '/'
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (savingRef.current) return
    setSaveError(''); setNotice('')
    savingRef.current = true; setSaving(true)
    try {
      const saved = await service.current.create({ title, brand, brief, publicationDate })
      setResult(saved)
      setNotice('')
      setTitle(''); setBrand(''); setBrief('')
      window.location.hash = `/review/${saved.data.reviews[0].id}`
    } catch (error) {
      setSaveError(`${describeError(error)} Your form entries are preserved.`)
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
  const pageName = route.page === 'home' ? 'Overview' : route.page === 'new' ? 'New review' : 'Content workspace'
  return <div className="app-shell">
    <a className="skip-link" href="#main" onClick={event => { event.preventDefault(); document.getElementById('main')?.focus() }}>Skip to content</a>
    <aside className="sidebar">
      <a className="wordmark" href="#/"><span aria-hidden="true">B</span> BrandProof</a>
      <p className="sidebar-label">WORKSPACE</p>
      <nav aria-label="Main navigation" className="main-nav">
        <a href="#/" aria-current={route.page === 'home' ? 'page' : undefined}>Overview</a>
        <a href="#/new" aria-current={route.page !== 'home' ? 'page' : undefined}>Review workspace</a>
      </nav>
      <p className="sidebar-note">Brand governance</p>
    </aside>
    <div className="workspace">
      <header className="topbar"><span>{pageName}</span><details className="connection-status"><summary>{loading ? 'Connecting…' : result?.mode === 'backend' ? 'Synthetic demo · connected' : 'Preview mode'}</summary><div className="connection-popover"><p>{result?.mode === 'backend' ? result.notice : 'Drafts are stored in this browser. Live verification is not connected.'}</p><p className="form-help">Demo tokens stay in memory. Refresh ends access; a new demo creates a new workspace. Typed sources use the real API with demo owner permissions. Guidelines are local context. Captions and exact-text reviews use the backend; AI, OCR and human approval remain unavailable.</p><button type="button" disabled={connecting || saving} onClick={() => void connectDemo()}>{connecting ? 'Connecting…' : result?.mode === 'backend' ? 'Start new demo workspace' : 'Connect backend demo'}</button>{result?.mode === 'backend' && <><button type="button" disabled={saving} onClick={() => void retry()}>Reload campaigns</button><button type="button" disabled={saving} onClick={() => void openLocalDrafts()}>Open local drafts</button></>}</div></details></header>
      <main id="main" tabIndex={-1}>
        {result?.mode === 'backend' && <p className="form-help">Fictional-data demo · Creator role · Refresh ends workspace access.</p>}
        <div role="status" className={notice ? 'notice' : ''}>{notice}</div>
        <div className="page-heading"><div><h1 ref={heading} tabIndex={-1}>{route.page === 'home' ? 'Every claim, accounted for.' : route.page === 'new' ? 'New review' : 'Review workspace'}</h1><p>{route.page === 'home' ? 'Review marketing content against approved brand information.' : route.page === 'new' ? 'Add a name, or continue straight to your brand information.' : 'Brand information first. Marketing content next.'}</p></div>{route.page === 'home' && <a className="button primary" href="#/new">New Review</a>}</div>
        {route.page === 'home' && <ol aria-label="Review workflow" className="workflow">{steps.map((name, index) => <li key={name}>{index > 0 && <span aria-hidden="true" className="step-divider">→</span>}{name}</li>)}</ol>}
        {loading ? <div className="loading" role="status"><span className="spinner" aria-hidden="true" />Loading your workspace…</div> : loadError ? <div className="error" role="alert">{loadError} <button onClick={() => void retry()}>Retry</button></div> : route.page === 'home' ? <section aria-labelledby="drafts-heading">
          <div className="section-heading"><h2 id="drafts-heading">Recent Reviews</h2><span>{result?.data.reviews.length || 0} total</span></div>
          {!result?.data.reviews.length ? <p className="reviews-empty">No reviews yet</p> : <div className="review-list">{result.data.reviews.map(review => <article className="campaign-card review-row" key={review.id}><h2><a href={`#/review/${review.id}`}>{review.title}</a></h2><span className="badge">{result.mode === 'backend' ? 'Campaign' : 'Draft · Not checked'}</span><small><time dateTime={review.createdAt}>{new Date(review.createdAt).toLocaleDateString()}</time></small><div className="review-delete">{result.mode === 'backend' ? <><button type="button" disabled aria-describedby={`server-delete-${review.id}`}>Delete</button><small id={`server-delete-${review.id}`}>Backend deletion unavailable</small></> : deletingId === review.id ? <div role="group" aria-label={`Delete ${review.title}?`}><span>Delete this local draft?</span><button type="button" disabled={deleting} onClick={() => void removeDraft(review.id)}>Confirm delete</button><button type="button" disabled={deleting} onClick={() => setDeletingId('')}>Cancel</button></div> : <button type="button" disabled={deleting} aria-label={`Delete ${review.title}`} onClick={() => setDeletingId(review.id)}>Delete</button>}</div></article>)}</div>}
        </section> : route.page === 'new' ? <form className="campaign-form" onSubmit={submit} noValidate aria-busy={saving}>
          <h2>Review details</h2>
          <fieldset disabled={saving}>
            <label htmlFor="review-title">Review title <span className="optional">optional</span></label><input id="review-title" maxLength={120} value={title} onChange={event => setTitle(event.target.value)} placeholder="Untitled review" aria-describedby="title-help" />
            <small id="title-help">Leave blank to use “Untitled review”.</small>
            {result?.mode === 'backend' && <><label className="publication-label" htmlFor="publication-date">Publication date</label><input id="publication-date" type="date" required value={publicationDate} onChange={event => setPublicationDate(event.target.value)} /><small>Used to assess source validity.</small></>}
            {result?.mode !== 'backend' && <details className="review-optional-details"><summary>Campaign details</summary>
            <label htmlFor="review-brand">Brand <span className="optional">optional</span></label><input id="review-brand" maxLength={120} value={brand} onChange={event => setBrand(event.target.value)} placeholder="Brand or organisation" />
            <label htmlFor="review-brief">Brief <span className="optional">optional</span></label><textarea id="review-brief" maxLength={2000} rows={4} value={brief} onChange={event => setBrief(event.target.value)} placeholder="Campaign context" aria-describedby="brief-help" /><small id="brief-help">Context only · not an approved source</small></details>}
          </fieldset>
          {saveError && <p className="error" role="alert">{saveError}</p>}
          <div className="form-actions"><button type="button" disabled={saving} onClick={() => { window.location.hash = '/' }}>Cancel</button><button className="primary" disabled={saving} type="submit">{saving && <span className="spinner" aria-hidden="true" />}{saving ? 'Saving…' : 'Continue'}</button></div>
        </form> : draft ? <ContentWorkspace key={draft.id} review={draft} campaign={campaign} sourceClient={result?.mode === 'backend' ? sourceClient || undefined : undefined} onCampaignChange={setResult} /> : <section className="empty"><h2>Draft not found</h2><p>This draft is not available in this browser.</p><a className="button" href="#/">Back to overview</a></section>}
      </main>
    </div>
  </div>
}
