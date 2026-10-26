import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { BackendClient } from './api/backend'
import type { ReviewResult } from './api/reviews'
import { ApiError, describeError } from './api/client'
import { sourceValidity } from './api/sources'
import type { SourceCreate, SourceOut, SourceRule } from './api/sources'
import { readSource, saveSource } from './sourceDraft'

const labels = { price: 'Price', date: 'Date', terminology: 'Terminology', required_text: 'Required wording', tone: 'Tone guidance', claim_policy: 'Claim policy' }
type Editor = { kind: SourceRule['kind']; title: string; value: string; preferred: string; currency: 'INR' | 'USD' | 'EUR' | 'GBP'; from: string; until: string }
const emptyEditor: Editor = { kind: 'price', title: '', value: '', preferred: '', currency: 'INR', from: '', until: '' }
function editorFor(source: SourceOut): Editor {
  const rule = source.rule
  return { kind: rule.kind, title: source.title, currency: rule.kind === 'price' ? rule.currency : 'INR',
    value: rule.kind === 'price' ? rule.amount : rule.kind === 'date' ? rule.date : rule.kind === 'terminology' ? rule.term : rule.kind === 'required_text' ? rule.text : rule.guidance,
    preferred: rule.kind === 'terminology' ? rule.preferred : '', from: source.valid_from || '', until: source.valid_until || '' }
}
function payloadFor(editor: Editor): SourceCreate {
  const value = editor.value.trim()
  let rule: SourceRule
  switch (editor.kind) {
    case 'price': rule = { kind: 'price', amount: value, currency: editor.currency }; break
    case 'date': rule = { kind: 'date', date: value }; break
    case 'terminology': rule = { kind: 'terminology', term: value, preferred: editor.preferred.trim() }; break
    case 'required_text': rule = { kind: 'required_text', text: value }; break
    default: rule = { kind: editor.kind, guidance: value }
  }
  return { title: editor.title.trim() || labels[editor.kind], rule, valid_from: editor.from || null, valid_until: editor.until || null }
}

export default function LiveSources({ api, campaignId, publicationDate, onCampaignChange }: {
  api: BackendClient; campaignId: string; publicationDate: string; onCampaignChange: (result: ReviewResult) => void
}) {
  const [sources, setSources] = useState<SourceOut[]>([])
  const [loading, setLoading] = useState(true)
  const [hasLoaded, setHasLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const lock = useRef(false)
  const mounted = useRef(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editor, setEditor] = useState<Editor | null>(null)
  const [editing, setEditing] = useState<SourceOut | null>(null)
  const [conflict, setConflict] = useState(false)
  const [history, setHistory] = useState<SourceOut[] | null>(null)
  const [initialContext] = useState(() => {
    try { return { value: readSource(campaignId).input.guidelines, error: '' } }
    catch { return { value: '', error: 'Could not read local guidelines. Existing data is preserved.' } }
  })
  const [guidelines, setGuidelines] = useState(initialContext.value)
  const [contextNotice, setContextNotice] = useState('')
  const [contextError, setContextError] = useState(initialContext.error)
  const editorKind = editor?.kind
  useEffect(() => { if (editorKind) document.getElementById('fact-value')?.focus() }, [editorKind, editing?.id])
  useEffect(() => {
    mounted.current = true
    let active = true
    api.listSources(campaignId).then(records => { if (active) { setSources(records); setHasLoaded(true) } })
      .catch(error => { if (active) setError(describeError(error)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; mounted.current = false }
  }, [api, campaignId])
  async function refresh() {
    const [records, result] = await Promise.all([api.listSources(campaignId), api.get(campaignId)])
    if (mounted.current) { setSources(records); setHasLoaded(true); onCampaignChange(result) }
    return records
  }
  async function perform(action: () => Promise<unknown>, success: string, closeEditor = false) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError(''); setNotice('')
    let written = false
    try {
      await action(); written = true
      if (mounted.current && closeEditor) { setEditor(null); setEditing(null); setConflict(false) }
      await refresh()
      if (mounted.current) { setHistory(null); setNotice(success) }
    } catch (error) {
      if (mounted.current) {
        setError(written ? 'The server saved the change, but reloading failed. Reload sources before continuing; do not submit again.' : describeError(error))
        if (error instanceof ApiError && error.status === 409) setConflict(true)
      }
    } finally { lock.current = false; if (mounted.current) setBusy(false) }
  }
  async function reload() {
    if (lock.current) return
    lock.current = true; setBusy(true); setError(''); setNotice('')
    try { await refresh(); if (!editor) setConflict(false); setNotice('Sources refreshed. Any unsaved edit is unchanged; cancel and reopen it to use the latest version.') }
    catch (error) { setError(describeError(error)) }
    finally { lock.current = false; if (mounted.current) { setBusy(false); setLoading(false) } }
  }
  function edit(source: SourceOut) { setEditing(source); setEditor(editorFor(source)); setConflict(false); setError(''); setNotice('') }
  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor || conflict) return
    const payload = payloadFor(editor)
    void perform(() => editing ? api.updateSource(campaignId, editing.id, editing.version, payload) : api.createSource(campaignId, payload),
      editing ? 'New pending version saved. Owner confirmation is required again.' : 'Fact saved as pending. Confirm explicitly to use it as an approved source.', true)
  }
  function saveContext() {
    setContextNotice(''); setContextError('')
    try {
      const current = readSource(campaignId)
      saveSource(campaignId, { ...current.input, guidelines })
      setContextNotice('Guidelines saved locally as context only.')
    } catch (error) { setContextError(describeError(error)) }
  }
  async function viewHistory(sourceId: string) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { const versions = await api.sourceVersions(campaignId, sourceId); if (mounted.current) setHistory(versions) }
    catch (error) { if (mounted.current) setError(describeError(error)) }
    finally { lock.current = false; if (mounted.current) setBusy(false) }
  }
  return <section className="content-panel source-panel live-sources" aria-labelledby="sources-heading">
    <div className="panel-heading"><h2 id="sources-heading" tabIndex={-1}>Reference Information</h2><span className="badge">Real API · Demo owner actions</span></div>
    <label htmlFor="source-guidelines">Brand Guidelines</label><textarea id="source-guidelines" rows={4} maxLength={10000} value={guidelines} onChange={event => { setGuidelines(event.target.value); setContextNotice('') }} placeholder="Paste guidelines for context." />
    <div className="context-actions"><small>Context only · not parsed or approved. Contextual AI is unavailable.</small><button type="button" disabled={!!initialContext.error} onClick={saveContext}>Save context</button></div>
    {contextError && <p className="error" role="alert">{contextError}</p>}<p role="status" className="form-help">{contextNotice}</p>
    <div className="section-heading"><h3>Approved Campaign Facts <span className="optional">optional</span></h3><button type="button" disabled={busy} onClick={() => void reload()}>Reload sources</button></div>
    <p className="form-help">Add a fact supplied by the brand, then explicitly confirm it as the demo owner. A source confirmation is not content approval.</p>
    <div className="add-facts">{(Object.keys(labels) as SourceRule['kind'][]).map(kind => <button type="button" key={kind} disabled={busy || loading || !hasLoaded || !!editor} onClick={() => { setEditor({ ...emptyEditor, kind }); setEditing(null); setConflict(false); setError('') }}>+ {labels[kind]}</button>)}</div>
    {editor && <form className="fact-editor" onSubmit={save} aria-label="Source fact editor">
      <div className="panel-heading"><h3>{editing ? `Edit ${labels[editor.kind]} · v${editing.version}` : `Add ${labels[editor.kind]}`}</h3><span className="badge">Saves as pending</span></div>
      <fieldset disabled={busy}>
        <label htmlFor="fact-value">{editor.kind === 'price' ? 'Brand-approved price' : editor.kind === 'date' ? 'Campaign date' : editor.kind === 'terminology' ? 'Term to avoid' : editor.kind === 'required_text' ? 'Exact required wording' : labels[editor.kind]}</label>
        {editor.kind === 'required_text' || editor.kind === 'tone' || editor.kind === 'claim_policy' ? <textarea id="fact-value" rows={3} required maxLength={editor.kind === 'required_text' ? 500 : 5000} value={editor.value} onChange={event => setEditor({ ...editor, value: event.target.value })} /> : <input id="fact-value" type={editor.kind === 'date' ? 'date' : 'text'} inputMode={editor.kind === 'price' ? 'decimal' : undefined} required maxLength={editor.kind === 'terminology' ? 100 : 32} value={editor.value} onChange={event => setEditor({ ...editor, value: event.target.value })} />}
        {editor.kind === 'price' && <><label htmlFor="fact-currency">Currency</label><select id="fact-currency" value={editor.currency} onChange={event => setEditor({ ...editor, currency: event.target.value as Editor['currency'] })}>{['INR', 'USD', 'EUR', 'GBP'].map(currency => <option key={currency}>{currency}</option>)}</select><p className="form-help">The brand supplies this price; BrandProof checks submitted copy for conflicts. No price is required unless it applies.</p></>}
        {editor.kind === 'terminology' && <><label htmlFor="fact-preferred">Preferred term</label><input id="fact-preferred" required maxLength={100} value={editor.preferred} onChange={event => setEditor({ ...editor, preferred: event.target.value })} /></>}
        {(editor.kind === 'tone' || editor.kind === 'claim_policy') && <p className="form-help">Stored guidance only. Contextual checks are unavailable, even after confirmation.</p>}
        <details className="source-metadata" open={!!(editing?.valid_from || editing?.valid_until) || undefined}><summary>Advanced source details</summary><label htmlFor="fact-title">Source name</label><input id="fact-title" maxLength={160} value={editor.title} onChange={event => setEditor({ ...editor, title: event.target.value })} placeholder={labels[editor.kind]} /><div className="source-fields"><div><label htmlFor="fact-from">Valid from</label><input id="fact-from" type="date" value={editor.from} onChange={event => setEditor({ ...editor, from: event.target.value })} /></div><div><label htmlFor="fact-until">Valid until</label><input id="fact-until" type="date" value={editor.until} onChange={event => setEditor({ ...editor, until: event.target.value })} /></div></div><small>Applies to this campaign. Owner identity and version are assigned by the server.</small></details>
      </fieldset>
      {conflict && <p className="error" role="alert">This edit is stale. Your entries are preserved. Reload sources, then cancel and reopen the latest version to reconcile; it will not be overwritten.</p>}
      <div className="form-actions"><button type="button" disabled={busy} onClick={() => { setEditor(null); setEditing(null); setConflict(false) }}>Cancel</button><button type="submit" className="primary" disabled={busy || conflict}>{busy ? 'Saving…' : editing ? 'Save new version' : 'Save pending fact'}</button></div>
    </form>}
    {error && <p role="alert" className="error">{error}</p>}<p role="status" className="source-notice form-help">{notice}</p>
    {loading ? <p role="status">Loading sources…</p> : !hasLoaded ? <p className="form-help">Sources unavailable. Use Reload sources to try again.</p> : sources.length === 0 ? <p className="form-help">No source facts yet.</p> : <div className="server-sources">{sources.map(source => <article className="server-source" key={source.id} data-source-id={source.id}>
      <div className="section-heading"><h3>{source.title}</h3><span className="badge">{source.status === 'approved' ? 'Approved' : 'Pending'} · v{source.version}</span></div><p className="source-text">{source.text}</p>
      <p className="form-help">{sourceValidity(source, publicationDate)} · {source.valid_from || 'No start limit'} to {source.valid_until || 'No end limit'}{source.status === 'pending' ? ' · Excluded until confirmed' : ''}</p>
      {(source.rule.kind === 'tone' || source.rule.kind === 'claim_policy') && <p className="form-help">Contextual checks unavailable.</p>}
      {source.confirmed_by && <details><summary className="form-help">Confirmation record</summary><p className="form-help">Demo owner {source.confirmed_by} · Server version {source.version}</p></details>}
      <div className="source-actions">{source.status === 'pending' && <button type="button" className="confirm-source" disabled={busy || conflict || !!editor} onClick={() => void perform(() => api.confirmSource(campaignId, source.id, source.version), 'Source confirmed by the demo owner; campaign revisions refreshed.')}>Confirm as owner</button>}<button type="button" disabled={busy || !!editor} onClick={() => edit(source)}>Edit</button><button type="button" disabled={busy} onClick={() => void viewHistory(source.id)}>Version history</button></div>
    </article>)}</div>}
    {history && <section className="source-history" aria-label="Source version history"><div className="section-heading"><h3>Version history</h3><button type="button" onClick={() => setHistory(null)}>Close history</button></div>{history.map(version => <article key={version.version_id}><h4>v{version.version} · {version.status} · {version.title}</h4><p>{version.text}</p><small>{version.valid_from || 'No start limit'} to {version.valid_until || 'No end limit'} · {new Date(version.created_at).toLocaleString()}</small></article>)}</section>}
  </section>
}
