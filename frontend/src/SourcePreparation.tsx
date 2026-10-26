import { useState } from 'react'
import type { FormEvent } from 'react'
import { emptySource, readSource, saveSource } from './sourceDraft'
import type { SourceInput } from './sourceDraft'

export default function SourcePreparation({ reviewId }: { reviewId: string }) {
  const [initial] = useState(() => {
    try { return { input: readSource(reviewId).input, error: '' } }
    catch { return { input: { ...emptySource }, error: 'Could not read source information. Existing data is preserved; check storage and reload.' } }
  })
  const [input, setInput] = useState(initial.input)
  const [saved, setSaved] = useState(initial.input)
  const [error, setError] = useState(initial.error)
  const [notice, setNotice] = useState('')
  const [facts, setFacts] = useState(() => ({ price: !!initial.input.price, date: !!initial.input.offerDates, wording: !!initial.input.mandatoryTerms, terminology: !!initial.input.term }))
  const dirty = JSON.stringify(input) !== JSON.stringify(saved)
  function change(field: keyof SourceInput, value: string) {
    setInput(previous => ({ ...previous, [field]: value }))
    setNotice('')
  }
  function submit(event: FormEvent) {
    event.preventDefault(); setNotice(''); setError('')
    try {
      const source = saveSource(reviewId, input)
      setSaved(source.input)
      setNotice('Brand information saved · Pending confirmation')
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not save source information. Your entries are still here.') }
  }
  return <section className="content-panel source-panel" aria-labelledby="sources-heading">
    <div className="panel-heading"><h2 id="sources-heading" tabIndex={-1}>Reference Information</h2><span className="badge">Local draft · Not confirmed</span></div>
    <form onSubmit={submit}>
      <label htmlFor="source-guidelines">Brand guidelines and policies</label><textarea id="source-guidelines" rows={5} value={input.guidelines} maxLength={10000} onChange={event => change('guidelines', event.target.value)} placeholder="Paste the guidance your marketing content should follow." /><p className="form-help">Context only. Verification needs typed, owner-confirmed facts.</p>

      <section className="approved-facts" aria-labelledby="facts-heading"><details className="facts-disclosure"><summary id="facts-heading">Add campaign facts <span className="optional">optional</span></summary><p className="form-help">Choose only what applies. No price is required.</p><div className="fact-options">{([['price', 'Price'], ['date', 'Date'], ['wording', 'Mandatory wording'], ['terminology', 'Terminology']] as const).map(([key, label]) => <label key={key}><input type="checkbox" checked={facts[key]} onChange={event => { setFacts(previous => ({ ...previous, [key]: event.target.checked })); if (!event.target.checked) { if (key === 'price') change('price', ''); if (key === 'date') change('offerDates', ''); if (key === 'wording') change('mandatoryTerms', ''); if (key === 'terminology') { change('term', ''); change('preferred', '') } } }} />{label}</label>)}</div><div className="source-fields">
        {facts.price && <div className="source-wide"><label htmlFor="source-price">Brand-approved reference price</label><input id="source-price" value={input.price} maxLength={2000} onChange={event => change('price', event.target.value)} placeholder="Amount and currency supplied by the brand" /><p className="form-help">The brand supplies the reference price; BrandProof detects conflicting prices in submitted content. No price is required if it does not apply.</p></div>}
        {facts.date && <div><label htmlFor="source-offer">Campaign date</label><input id="source-offer" value={input.offerDates} maxLength={2000} onChange={event => change('offerDates', event.target.value)} placeholder="YYYY-MM-DD" /></div>}
        {facts.wording && <div><label htmlFor="source-terms">Mandatory wording</label><textarea id="source-terms" rows={3} value={input.mandatoryTerms} maxLength={2000} onChange={event => change('mandatoryTerms', event.target.value)} /></div>}
        {facts.terminology && <><div><label htmlFor="source-term">Term to avoid</label><input id="source-term" value={input.term} maxLength={100} onChange={event => change('term', event.target.value)} /></div><div><label htmlFor="source-preferred">Preferred term</label><input id="source-preferred" value={input.preferred} maxLength={100} onChange={event => change('preferred', event.target.value)} /></div></>}
      </div></details></section>
      <details className="source-metadata"><summary>Advanced settings</summary><div className="source-fields">
        <div><label htmlFor="source-name">Source name</label><input id="source-name" value={input.name} maxLength={2000} onChange={event => change('name', event.target.value)} placeholder="e.g. Workshop brand policy" /></div>
        <div className="source-wide"><label htmlFor="source-applicability">Applicability</label><input id="source-applicability" value={input.applicability} maxLength={2000} onChange={event => change('applicability', event.target.value)} placeholder="Product, campaign, audience or region" /></div>
        <div><label htmlFor="source-from">Valid from</label><input id="source-from" type="date" value={input.validFrom} onChange={event => change('validFrom', event.target.value)} /></div>
        <div><label htmlFor="source-until">Valid until</label><input id="source-until" type="date" value={input.validUntil} onChange={event => change('validUntil', event.target.value)} /></div>
      </div></details>
      <div className="source-save"><small>{dirty ? 'Unsaved changes' : 'Local reference draft'}</small><button type="submit" disabled={!!initial.error}>Save reference draft</button></div>
      {error && <p className="error" role="alert">{error}</p>}<p className="form-help" role="status">{notice}</p>
    </form>
    <div className="confirmed-sources"><p className="form-help">Local draft: not connected to server approval. Y02 confirmation works in the connected backend demo.</p><button type="button" onClick={()=>{const connection=document.querySelector<HTMLDetailsElement>('.connection-status');if(connection){connection.open=true;connection.querySelector<HTMLButtonElement>('button')?.focus()}}}>Open backend connection</button><p className="form-help">Save local edits first. Connect a backend demo, create a server campaign, add a fact and save it as pending. Local drafts stay separate and are not automatically uploaded.</p></div>
  </section>
}
