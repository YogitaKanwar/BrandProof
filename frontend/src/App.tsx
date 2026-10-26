import ReviewWorkspace from './ReviewWorkspace'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { campaignService } from './api/campaigns'
import type { Campaign } from './api/campaigns'
import './App.css'

function App() {
  const [page, setPage] = useState<'campaigns' | 'create'>('campaigns')
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [notice, setNotice] = useState('')
  const [name, setName] = useState('')
  const [brand, setBrand] = useState('')
  const [description, setDescription] = useState('')

  async function load() {
    setLoading(true)
    setLoadError('')
    try { setCampaigns(await campaignService.list()) }
    catch { setLoadError('Could not load development campaigns. Check browser storage access and retry.') }
    finally { setLoading(false) }
  }
  useEffect(() => {
    let active = true
    campaignService.list()
      .then(records => { if (active) setCampaigns(records) })
      .catch(() => { if (active) setLoadError('Could not load development campaigns. Check browser storage access and retry.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setSaving(true)
    setSaveError('')
    setNotice('')
    try {
      const campaign = await campaignService.create({ name, brand, description })
      setCampaigns(previous => [campaign, ...previous])
      setLoadError('')
      setName(''); setBrand(''); setDescription('')
      setNotice(`“${campaign.name}” saved in this browser as a development fixture.`)
      setPage('campaigns')
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Could not save. Please try again.')
    } finally { setSaving(false) }
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <aside className="sidebar">
        <a className="wordmark" href="#campaigns" onClick={() => setPage('campaigns')}><span aria-hidden="true">B</span> BrandProof</a>
        <p className="sidebar-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          <button aria-current={page === 'campaigns' ? 'page' : undefined} onClick={() => setPage('campaigns')}>Campaigns</button>
          <button aria-current={page === 'create' ? 'page' : undefined} onClick={() => setPage('create')}>Create campaign</button>
        </nav>
        <p className="sidebar-note">From campaign brief to evidence-backed review.</p>
      </aside>
      <div className="workspace">
        <header className="topbar"><span>Campaign workspace</span><span className="badge">Development fixtures</span></header>
        <main id="main">
          <div className="environment" role="note"><strong>Development mode</strong><p>Campaigns are stored only in this browser. No backend is connected; no AI review or approval has run.</p></div>
          <div role="status" className={notice ? 'notice' : ''}>{notice}</div>
          {page === 'campaigns' ? <>
            <div className="page-heading"><div><p className="eyebrow">YOUR WORKSPACE</p><h1>Campaigns</h1><p>Start with a brief. Build a review you can trace.</p></div><button className="primary" onClick={() => setPage('create')}>+ Create campaign</button></div>
            {loading ? <p role="status">Loading campaigns…</p> : loadError ? <div role="alert" className="error">{loadError} <button onClick={() => void load()}>Retry</button></div> : campaigns.length === 0 ? <section className="empty"><span className="empty-mark" aria-hidden="true">+</span><h2>Your first campaign starts here</h2><p>Add your campaign name, brand and brief to get organised.</p><button className="primary" onClick={() => setPage('create')}>Create a campaign</button></section> : <section className="campaign-grid" aria-label="Saved development campaigns">{campaigns.map(campaign => <article className="campaign-card" key={campaign.id}><span className="badge">Local fixture · Not reviewed</span><h2>{campaign.name}</h2><p className="brand">{campaign.brand}</p><p className="description">{campaign.description || 'No brief added.'}</p><small>Created {new Date(campaign.createdAt).toLocaleDateString()}</small></article>)}</section>}
          </> : <>
            <div className="page-heading"><div><p className="eyebrow">NEW CAMPAIGN</p><h1>Set the context</h1><p>Give your campaign a name and a clear brief.</p></div></div>
            <form className="campaign-form" onSubmit={submit} aria-busy={saving}>
              <h2>Campaign details</h2><p className="form-help">Fields marked * are required.</p>
              <fieldset disabled={saving}>
                <label htmlFor="name">Campaign name *</label><input id="name" value={name} onChange={event => setName(event.target.value)} required maxLength={120} placeholder="e.g. October workshop launch" />
                <label htmlFor="brand">Brand *</label><input id="brand" value={brand} onChange={event => setBrand(event.target.value)} required maxLength={120} placeholder="Your brand or organisation" />
                <label htmlFor="description">Campaign brief</label><textarea id="description" value={description} onChange={event => setDescription(event.target.value)} maxLength={2000} rows={5} placeholder="Describe the campaign’s purpose and audience" aria-describedby="brief-help" /><small id="brief-help">Optional · up to 2,000 characters</small>
              </fieldset>
              {saveError && <p className="error" role="alert">{saveError}</p>}
              <div className="form-actions"><button type="button" disabled={saving} onClick={() => setPage('campaigns')}>Cancel</button><button className="primary" disabled={saving} type="submit">{saving ? 'Saving…' : 'Save development campaign'}</button></div>
            </form>
          </>}
        </main>
      </div>
    </div>
  )
}

// Preserve the previous campaign-first workspace for reference and integration.
export { App as CampaignWorkspace }
export default ReviewWorkspace
