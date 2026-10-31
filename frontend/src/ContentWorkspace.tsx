import WorkflowReadiness from './WorkflowReadiness'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { Campaign } from './api/campaigns'
import type { Review } from './api/reviews'
import { MAX_CAPTION_LENGTH, readCaption, saveCaption, validatePoster } from './contentDraft'
import SourcePreparation from './SourcePreparation'
import LiveSources from './LiveSources'
import BrandLogo from './BrandLogo'
import AdvertisingProfile from './AdvertisingProfile'
import type { BackendClient, CampaignOut } from './api/backend'
import type { ReviewResult } from './api/reviews'
import LiveCaption from './LiveCaption'
import AltTextEditor from './AltTextEditor'
import LivePoster from './LivePoster'
import { useUnsavedChanges } from './unsavedChanges'

export default function ContentWorkspace({ review, campaign, sourceClient, onCampaignChange }: { review: Review; campaign?: Campaign; sourceClient?: BackendClient; onCampaignChange?: (result: ReviewResult) => void }) {
  const [initial] = useState(() => {
    try { return { caption: readCaption(review.id), error: '' } }
    catch { return { caption: '', error: 'Could not read the saved caption. Check browser storage and reload; existing data has been preserved.' } }
  })
  const [caption, setCaption] = useState(initial.caption)
  const [savedCaption, setSavedCaption] = useState(initial.caption)
  const [captionError, setCaptionError] = useState(initial.error)
  const [captionNotice, setCaptionNotice] = useState('')
  const [poster, setPoster] = useState<{ file: File; url: string } | null>(null)
  const [imageError, setImageError] = useState('')
  const [imageNotice, setImageNotice] = useState('')
  const [checkingImage, setCheckingImage] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [contentDirty,setContentDirty]=useState(false),[readinessEpoch,setReadinessEpoch]=useState(0)
  const refreshGuide=useCallback(()=>setReadinessEpoch(value=>value+1),[])
  const [posterAttached,setPosterAttached]=useState(false)
  const [posterPending,setPosterPending]=useState(false)
  const posterUpload = useRef<{upload:()=>Promise<CampaignOut>} | null>(null)
  const [captionSaves,setCaptionSaves]=useState<{previous:number;current:number}[]>([])
  useUnsavedChanges(!sourceClient && (caption !== savedCaption || !!poster || checkingImage))
  const input = useRef<HTMLInputElement>(null)
  const imageRequest = useRef(0)
  useEffect(() => () => { imageRequest.current++ }, [])
  useEffect(() => () => { if (poster) URL.revokeObjectURL(poster.url) }, [poster])

  async function pick(files: File[]) {
    const request = ++imageRequest.current
    setImageError(''); setImageNotice(''); setDragging(false)
    if (files.length !== 1) { setCheckingImage(false); setImageError('Choose one PNG or JPEG image at a time.'); return }
    setCheckingImage(true)
    let url = ''
    try {
      const file = files[0]
      await validatePoster(file)
      url = URL.createObjectURL(file)
      const image = new Image()
      image.src = url
      await image.decode()
      if (request !== imageRequest.current) { URL.revokeObjectURL(url); return }
      setPoster({ file, url })
      setImageNotice('Image ready for preview. Not uploaded or saved.')
    } catch (error) {
      if (url) URL.revokeObjectURL(url)
      if (request === imageRequest.current) setImageError(error instanceof Error ? error.message : 'Could not open this image. Choose another file.')
    } finally {
      if (request === imageRequest.current) setCheckingImage(false)
    }
  }
  function save() {
    setCaptionNotice(''); setCaptionError('')
    try {
      saveCaption(review.id, caption)
      setSavedCaption(caption)
      setCaptionNotice('Caption saved')
    } catch { setCaptionError('Could not save the caption. Check browser storage access or space and retry. Your text is still here.') }
  }

  return <div className="content-workspace">
    <section className="review-context" aria-label="Review draft details">
      <div><span className="badge">{sourceClient ? 'Connected campaign' : 'Draft · Not reviewed'}</span><h2 className="draft-title">{review.title}</h2>{campaign?.brand && <p className="form-help">{campaign.brand}</p>}</div>
      {review.brief && <details className="review-brief"><summary>Campaign brief</summary><p className="description">{review.brief}</p></details>}
    </section>
    {sourceClient&&review.backendCampaign&&<WorkflowReadiness api={sourceClient} campaign={review.backendCampaign} epoch={readinessEpoch} dirty={contentDirty}/>}
    {sourceClient&&review.backendCampaign&&onCampaignChange&&<AdvertisingProfile key={review.backendCampaign.id} api={sourceClient} campaign={review.backendCampaign} onChanged={onCampaignChange}/>}
    <ol className="workspace-stages" aria-label="Review stages"><li><a href="#brand-information" onClick={event => { event.preventDefault(); document.getElementById('sources-heading')?.focus(); document.getElementById('brand-information')?.scrollIntoView() }}>1. References</a></li><li><a href="#marketing-content" onClick={event => { event.preventDefault(); document.getElementById('content-heading')?.focus(); document.getElementById('marketing-content')?.scrollIntoView() }}>2. Content</a></li><li>{hasResults ? <a href="#review-results" onClick={event => { event.preventDefault(); document.getElementById('results-heading')?.focus(); document.getElementById('review-results')?.scrollIntoView() }}>3. Results</a> : <span aria-disabled="true">3. Results</span>}</li></ol>
    {review.backendCampaign && <details className="campaign-revisions"><summary>Review details</summary><p className="form-help">Campaign saved on server · Publication {review.backendCampaign.publication_date} · Content revision {review.backendCampaign.content_revision} · Source revision {review.backendCampaign.source_revision}.</p></details>}
    <div id="brand-information">{sourceClient && review.backendCampaign && onCampaignChange ? <><LiveSources api={sourceClient} campaignId={review.campaignId} publicationDate={review.backendCampaign.publication_date} onCampaignChange={onCampaignChange} /><BrandLogo api={sourceClient} campaignId={review.campaignId} onCampaignChange={onCampaignChange}/></> : <SourcePreparation reviewId={review.id} />}</div>
    <div className="content-columns">
      <section id="marketing-content" className="content-panel" aria-labelledby="content-heading">
        <div className="panel-heading"><h2 id="content-heading" tabIndex={-1}>Marketing Content</h2><small>{sourceClient ? 'Caption and poster review' : 'Caption, poster or both'}</small></div>
        {sourceClient && review.backendCampaign && onCampaignChange ? <LiveCaption api={sourceClient} campaign={review.backendCampaign} onCampaignChange={onCampaignChange} onResultsAvailable={setHasResults} onDraftDirty={setContentDirty} onStateChange={refreshGuide} posterAttached={posterAttached} posterPending={posterPending} preparePoster={async()=>{if(!posterUpload.current)throw new Error("Poster upload is not ready. Try again.");return posterUpload.current.upload()}} onCaptionSaved={(previous,current)=>setCaptionSaves(records=>[...records,{previous,current}])}><LivePoster api={sourceClient} campaign={review.backendCampaign} onCampaignChange={onCampaignChange} onAttached={setPosterAttached} onPendingChange={setPosterPending} captionSaves={captionSaves} uploadRef={posterUpload}/><AltTextEditor api={sourceClient} campaign={review.backendCampaign} onCampaignChange={onCampaignChange}/></LiveCaption> : <><label htmlFor="marketing-caption">Marketing caption</label>
        <textarea id="marketing-caption" rows={7} maxLength={MAX_CAPTION_LENGTH} value={caption} onChange={event => { setCaption(event.target.value); setCaptionNotice('') }} placeholder="Paste the marketing caption you want to review…" aria-describedby="caption-help caption-state" />
        <div className="caption-footer"><small id="caption-help">{caption.length.toLocaleString()}/10,000 characters</small><button type="button" disabled={!!initial.error} onClick={save}>Save caption</button></div>
        <p id="caption-state" className="form-help">{caption !== savedCaption ? 'Unsaved changes' : ''}</p>
        {captionError && <p className="error" role="alert">{captionError}</p>}
        <p className="form-help" role="status">{captionNotice}</p></>}
        {!sourceClient && <><div className="poster-heading"><h3>Marketing poster <span className="optional">optional</span></h3><small>PNG or JPEG · up to 5 MB</small></div>
        <input ref={input} id="poster-file" tabIndex={-1} className="visually-hidden" type="file" accept="image/png,image/jpeg" aria-label="Choose marketing poster" aria-describedby="poster-help" onChange={event => { const files = Array.from(event.target.files || []); if (files.length) void pick(files); event.target.value = '' }} />
        <div className={`poster-dropzone${dragging ? ' dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false) }} onDrop={event => { event.preventDefault(); void pick(Array.from(event.dataTransfer.files)) }} aria-busy={checkingImage}>
          {poster ? <><img className="poster-preview" src={poster.url} alt={`Marketing poster preview: ${poster.file.name}`} /><div className="poster-file"><span>{poster.file.name}</span><small>{(poster.file.size / 1024 / 1024).toFixed(2)} MB</small></div></> : <p>Drop an image here, or choose a file.</p>}
          <div className="poster-actions"><button type="button" onClick={() => input.current?.click()}>{poster ? 'Replace image' : 'Choose image'}</button>{poster && <button type="button" onClick={() => { imageRequest.current++; setPoster(null); setCheckingImage(false); setImageError(''); setImageNotice('Image removed.'); }}>Remove</button>}</div>
        </div>
        <p id="poster-help" className="form-help">Preview only. Images are not uploaded or saved and are cleared when you leave this workspace or reload.</p>
        {imageError && <p className="error" role="alert">{imageError}</p>}
        <p className="form-help" role="status">{checkingImage ? 'Opening image…' : imageNotice}</p></>}
      </section>
      {!sourceClient && <aside className="review-rail">
        <section className="content-panel verification-panel" aria-labelledby="verification-heading"><h2 id="verification-heading">Ready to review?</h2><button type="button" className="primary" disabled aria-describedby="verification-reason">Run Review</button><p id="verification-reason" className="form-help">Live verification is not connected.</p></section>
      </aside>}
    </div>
    <a className="back-link" href="#/">Back to overview</a>
  </div>
}
