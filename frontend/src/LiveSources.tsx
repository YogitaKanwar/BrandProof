import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { BackendClient } from './api/backend'
import type { ReviewResult } from './api/reviews'
import { ApiError, describeError } from './api/client'
import { sourceValidity } from './api/sources'
import type { SourceCreate, SourceOut, SourceRule } from './api/sources'
import { readSource, saveSource } from './sourceDraft'
import { useUnsavedChanges } from './unsavedChanges'
import DocumentImport from './DocumentImport'

const labels = { price: 'Price', date: 'Date', terminology: 'Words to avoid', required_text: 'Required wording', tone: 'Tone guidance (optional AI)', claim_policy: 'Claim policy (optional AI)',brand_color:'Flat background colour',contrast:'Minimum text contrast ratio',alt_text:'Poster description required' }
type Editor = { kind: SourceRule['kind']; title: string; value: string; preferred: string; currency: 'INR' | 'USD' | 'EUR' | 'GBP'; from: string; until: string }
const emptyEditor: Editor = { kind: 'price', title: '', value: '', preferred: '', currency: 'INR', from: '', until: '' }
function editorFor(source: SourceOut): Editor {
  const rule = source.rule
  return { kind: rule.kind, title: source.title, currency: rule.kind === 'price' ? rule.currency : 'INR',
    value: rule.kind === 'price' ? rule.amount : rule.kind === 'date' ? rule.date : rule.kind === 'terminology' ? rule.term : rule.kind === 'required_text' ? rule.text : rule.kind==='brand_color'?rule.hex:rule.kind==='contrast'?String(rule.minimum_ratio):rule.kind==='alt_text'?'Required':rule.guidance,
    preferred: rule.kind === 'terminology' ? rule.preferred : rule.kind==='brand_color'?String(rule.tolerance):'', from: source.valid_from || '', until: source.valid_until || '' }
}
function payloadFor(editor: Editor): SourceCreate {
  const value = editor.value.trim()
  let rule: SourceRule
  switch (editor.kind) {
    case 'price': rule = { kind: 'price', amount: value, currency: editor.currency }; break
    case 'date': rule = { kind: 'date', date: value }; break
    case 'terminology': rule = { kind: 'terminology', term: value, preferred: editor.preferred.trim() }; break
    case 'required_text': rule = { kind: 'required_text', text: value }; break
    case 'brand_color': rule={kind:'brand_color',hex:value,tolerance:editor.preferred.trim()?Number(editor.preferred):10};break
    case 'contrast':rule={kind:'contrast',minimum_ratio:Number(value)};break
    case 'alt_text':rule={kind:'alt_text',required:true};break
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
  const [newSourceId,setNewSourceId]=useState('')
  const [initialContext] = useState(() => {
    try { return { value: readSource(campaignId).input.guidelines, error: '' } }
    catch { return { value: '', error: 'Could not read saved context. Existing data has been preserved.' } }
  })
  const [context, setContext] = useState(initialContext.value)
  const [savedContext, setSavedContext] = useState(initialContext.value)
  const [contextStatus, setContextStatus] = useState('')
  const editorKind = editor?.kind
  useUnsavedChanges(context !== savedContext || busy || (!!editor && JSON.stringify(editor) !== JSON.stringify(editing ? editorFor(editing) : { ...emptyEditor, kind: editor.kind })))
  useEffect(() => { if (editorKind) document.getElementById('fact-value')?.focus() }, [editorKind, editing?.id])
  useEffect(()=>{if(!busy&&newSourceId){const button=document.querySelector<HTMLButtonElement>(`[data-source-id="${newSourceId}"] .confirm-source`);button?.scrollIntoView({block:'center'});button?.focus()}},[busy,newSourceId])
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
      const response=await action(); written = true
      if (mounted.current && closeEditor) { setEditor(null); setEditing(null); setConflict(false) }
      await refresh()
      if(mounted.current && closeEditor && response && typeof response==='object' && 'id' in response && typeof response.id==='string')setNewSourceId(response.id)
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
  function selectKind(kind: SourceRule['kind']) {
    if (!editor || editing) return
    setEditor({ ...editor, kind, title: '', value: kind==='contrast'?'4.5':kind==='alt_text'?'Required':kind==='brand_color'?'#FFFFFF':'', preferred: '' })
  }
  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor || conflict) return
    const payload = payloadFor(editor)
    void perform(() => editing ? api.updateSource(campaignId, editing.id, editing.version, payload) : api.createSource(campaignId, payload),
      editing ? 'New pending version saved. Owner confirmation is required again.' : 'Fact saved as pending. Confirm explicitly to use it as an approved source.', true)
  }
  function saveContext() {
    setContextStatus('')
    try {
      const current = readSource(campaignId)
      saveSource(campaignId, { ...current.input, guidelines: context })
      setSavedContext(context)
      setContextStatus('Context saved in this browser.')
    } catch (error) { setContextStatus(describeError(error)) }
  }
  async function viewHistory(sourceId: string) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { const versions = await api.sourceVersions(campaignId, sourceId); if (mounted.current) setHistory(versions) }
    catch (error) { if (mounted.current) setError(describeError(error)) }
    finally { lock.current = false; if (mounted.current) setBusy(false) }
  }
  return <section className="content-panel source-panel live-sources" aria-labelledby="sources-heading">
    <div className="panel-heading"><div><h2 id="sources-heading" tabIndex={-1}>Brand information</h2><small>Add details you know are true so we can compare them with your content.</small></div><span className="badge">Connected</span></div>
    <section className="brand-context" aria-labelledby="brand-context-heading">
      <div className="section-heading"><h3 id="brand-context-heading">Brand context</h3><span className="badge">Context only</span></div>
      <label htmlFor="brand-context-input">Background or guidelines</label>
      <textarea id="brand-context-input" rows={3} maxLength={10000} value={context} onChange={event => { setContext(event.target.value); setContextStatus('') }} placeholder="Add helpful background about the brand or campaign." aria-describedby="brand-context-help" />
      <div className="context-actions"><small id="brand-context-help">Notes for people, saved in this browser. To verify prices, dates or wording, add and confirm individual facts below.</small><button type="button" disabled={!!initialContext.error || context === savedContext} onClick={saveContext}>Save context</button></div>
      <p className="context-limit form-help">Pasted guidelines are not automatically extracted or checked.</p>
      {initialContext.error && <p className="error" role="alert">{initialContext.error}</p>}
      <p className="form-help" role="status">{contextStatus}</p>
    </section>
    <div className="section-heading"><div><h3>Facts to check</h3><small>For example: the correct price, event date, or required phrase.</small></div><div className="source-heading-actions">{error && <button type="button" disabled={busy} onClick={() => void reload()}>Reload</button>}<button type="button" disabled={busy || loading || !hasLoaded || !!editor} onClick={() => { setEditor({ ...emptyEditor }); setEditing(null); setConflict(false); setError('') }}>+ Add a fact</button></div></div>
    <p className="form-help">Add only information confirmed by the brand. You’ll confirm each fact before it is used.</p>
    {editor && <form className="fact-editor" onSubmit={save} aria-label="Source fact editor">
      <div className="panel-heading"><div><h3>{editing ? 'Edit this fact' : 'Add a fact'}</h3><small>Enter the correct information as provided by the brand.</small></div></div>
      <fieldset disabled={busy}>
        <label htmlFor="fact-kind">What kind of fact?</label><select id="fact-kind" value={editor.kind} disabled={!!editing} onChange={event => selectKind(event.target.value as SourceRule['kind'])}><optgroup label="Facts check">{(['price', 'date', 'terminology', 'required_text', 'brand_color', 'contrast', 'alt_text'] as SourceRule['kind'][]).map(kind => <option key={kind} value={kind}>{labels[kind]}</option>)}</optgroup><optgroup label="Requires optional AI check">{(['tone', 'claim_policy'] as SourceRule['kind'][]).map(kind => <option key={kind} value={kind}>{labels[kind]}</option>)}</optgroup></select>
        <label htmlFor="fact-value">{editor.kind === 'price' ? 'What is the correct price?' : editor.kind === 'date' ? 'What is the correct date?' : editor.kind === 'terminology' ? 'Which word should be avoided?' : editor.kind === 'required_text' ? 'What exact words are required?' : labels[editor.kind]}</label>
        {editor.kind === 'required_text' || editor.kind === 'tone' || editor.kind === 'claim_policy' ? <textarea id="fact-value" rows={3} required maxLength={editor.kind === 'required_text' ? 500 : 5000} value={editor.value} onChange={event => setEditor({ ...editor, value: event.target.value })} /> : <input id="fact-value" type={editor.kind === 'date' ? 'date' : 'text'} inputMode={editor.kind === 'price' ? 'decimal' : undefined} required maxLength={editor.kind === 'terminology' ? 100 : 32} value={editor.value} onChange={event => setEditor({ ...editor, value: event.target.value })} />}
        {editor.kind === 'price' && <><label htmlFor="fact-currency">Currency</label><select id="fact-currency" value={editor.currency} onChange={event => setEditor({ ...editor, currency: event.target.value as Editor['currency'] })}>{['INR', 'USD', 'EUR', 'GBP'].map(currency => <option key={currency}>{currency}</option>)}</select></>}
        {editor.kind === 'brand_color' && <><label htmlFor="colour-tolerance">CIE76 Delta-E tolerance (0?30)</label><input id="colour-tolerance" type="number" min="0" max="30" value={editor.preferred} placeholder="10" onChange={event=>setEditor({...editor,preferred:event.target.value})}/><p className="form-help">Only reliably uniform flat poster backgrounds are supported. Other regions, gradients and photographs require manual inspection.</p></>}{editor.kind === 'terminology' && <><label htmlFor="fact-preferred">What word should be used instead?</label><input id="fact-preferred" required maxLength={100} value={editor.preferred} onChange={event => setEditor({ ...editor, preferred: event.target.value })} /></>}
        {(editor.kind === 'tone' || editor.kind === 'claim_policy') && <p className="form-help">Requires an available contextual AI check and your consent for that review. Exact-text checks do not evaluate this guidance.</p>}
        <details className="source-metadata" open={!!(editing?.valid_from || editing?.valid_until) || undefined}><summary>Does this fact have a date limit? (optional)</summary><label htmlFor="fact-title">Short name (optional)</label><input id="fact-title" maxLength={160} value={editor.title} onChange={event => setEditor({ ...editor, title: event.target.value })} placeholder={labels[editor.kind]} /><div className="source-fields"><div><label htmlFor="fact-from">Use from</label><input id="fact-from" type="date" value={editor.from} onChange={event => setEditor({ ...editor, from: event.target.value })} /></div><div><label htmlFor="fact-until">Use until</label><input id="fact-until" type="date" value={editor.until} onChange={event => setEditor({ ...editor, until: event.target.value })} /></div></div></details>
      </fieldset>
      {conflict && <p className="error" role="alert">This edit is stale. Your entries are preserved. Reload sources, then cancel and reopen the latest version to reconcile; it will not be overwritten.</p>}
      <div className="form-actions"><button type="button" disabled={busy} onClick={() => { setEditor(null); setEditing(null); setConflict(false) }}>Cancel</button><button type="submit" className="primary" disabled={busy || conflict}>{busy ? 'Saving…' : editing ? 'Save changes' : 'Save fact'}</button></div>
    </form>}
    <DocumentImport api={api} campaignId={campaignId} disabled={busy||!!editor} onImported={refresh}/>
    {error && <p role="alert" className="error">{error}</p>}<p role="status" className="source-notice form-help">{notice}</p>
    {!!editor && sources.some(source=>source.status==='pending') && <p className="form-help">Save or cancel the open fact editor before confirming a pending source.</p>}
    {loading ? <p role="status">Loading facts…</p> : !hasLoaded ? <p className="form-help">Couldn’t load facts. Use Reload to try again.</p> : sources.length === 0 ? <p className="form-help">No facts added yet. Add one if there’s a confirmed detail to check.</p> : <div className="server-sources">{sources.map(source => <article className="server-source" key={source.id} data-source-id={source.id}>
      <div className="section-heading"><h3>{source.title}</h3><span className={`badge fact-status ${source.status}${sourceValidity(source, publicationDate)!=='Valid for publication'?' inactive':''}`}>{source.status === 'approved' ? `Confirmed${sourceValidity(source, publicationDate)==='Valid for publication'?'':` · ${sourceValidity(source, publicationDate).toLowerCase()}`}` : 'Needs your confirmation'}</span></div><p className="source-text">{source.text}</p>{source.document_evidence && <details className="document-citation"><summary>Document evidence ? {source.document_evidence.filename} ? page {source.document_evidence.page_number}</summary><blockquote>{source.document_evidence.quote}</blockquote><small>Extracted page offsets {source.document_evidence.start}?{source.document_evidence.end}. Confirm the interpretation against the original document.</small></details>}
      {source.status === 'pending' && <div className="fact-confirm"><p>{sourceValidity(source, publicationDate)==='Valid for publication'?'This fact won’t be used until you confirm it.':`${sourceValidity(source, publicationDate)}. Confirmation will not make it applicable to this publication date.`}</p><button type="button" className="confirm-source" disabled={busy || conflict || !!editor} onClick={() => void perform(() => api.confirmSource(campaignId, source.id, source.version), sourceValidity(source, publicationDate)==='Valid for publication'?'Fact confirmed and applicable to this publication date.':`Fact confirmed, but ${sourceValidity(source, publicationDate).toLowerCase()}. It remains excluded from checks.`)}>Confirm this fact</button></div>}
      {(source.rule.kind === 'tone' || source.rule.kind === 'claim_policy') && <p className="form-help">Used only with an available, consented contextual AI check. See the review’s actual coverage.</p>}
      <details className="source-more"><summary>More details and actions</summary><p className="form-help">{sourceValidity(source, publicationDate)}{source.valid_from || source.valid_until ? ` · ${source.valid_from || 'Any start date'} to ${source.valid_until || 'No end date'}` : ''} · Version {source.version}</p>
      {source.confirmed_by && <p className="form-help">Confirmed in this demo workspace.</p>}
      <div className="source-actions"><button type="button" disabled={busy || !!editor} onClick={() => edit(source)}>Edit</button><button type="button" disabled={busy} onClick={() => void viewHistory(source.id)}>See changes</button></div></details>
    </article>)}</div>}
    {history && <section className="source-history" aria-label="Source version history"><div className="section-heading"><h3>Version history</h3><button type="button" onClick={() => setHistory(null)}>Close history</button></div>{history.map(version => <article key={version.version_id}><h4>v{version.version} · {version.status} · {version.title}</h4><p>{version.text}</p><small>{version.valid_from || 'No start limit'} to {version.valid_until || 'No end limit'} · {new Date(version.created_at).toLocaleString()}</small></article>)}</section>}
  </section>
}
