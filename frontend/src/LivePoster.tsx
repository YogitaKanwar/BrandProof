import { useEffect, useRef, useState } from 'react'
import type { BackendClient,CampaignOut } from './api/backend'
import type { ReviewResult } from './api/reviews'
import type { PosterOut } from './api/posters'
import {ApiError,describeError} from './api/client'
import {validatePoster} from './contentDraft'
import PrivatePoster from './PrivatePoster'

export default function LivePoster({api,campaign,onCampaignChange,onAttached}:{api:BackendClient;campaign:CampaignOut;onCampaignChange:(result:ReviewResult)=>void;onAttached:(attached:boolean)=>void}) {
  const [poster,setPoster]=useState<PosterOut|null>(null)
  const [picked,setPicked]=useState<{file:File;url:string;revision:number}|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [notice,setNotice]=useState('')
  const [conflict,setConflict]=useState(false)
  const picker=useRef<HTMLInputElement>(null), generation=useRef(0),lock=useRef(false)
  useEffect(()=>{let active=true;api.poster(campaign.id).then(value=>{if(active){setPoster(value);setError('');onAttached(true)}}).catch(error=>{if(active){if(error instanceof ApiError&&error.status===404)onAttached(false);else setError(describeError(error))}});return()=>{active=false}},[api,campaign.id,campaign.content_revision,onAttached])
  useEffect(()=>()=>{if(picked)URL.revokeObjectURL(picked.url)},[picked])
  useEffect(()=>()=>{generation.current++},[])
  async function choose(files:File[]) {
    if(lock.current)return
    const request=++generation.current;setError('');setNotice('');setConflict(false)
    if(files.length!==1){setError('Choose one PNG or JPEG.');return}
    let url=''
    try{await validatePoster(files[0]);url=URL.createObjectURL(files[0]);const image=new Image();image.src=url;await image.decode();if(image.naturalWidth*image.naturalHeight>16000000)throw new Error('Image exceeds 16 million pixels.');if(request!==generation.current){URL.revokeObjectURL(url);return}setPicked({file:files[0],url,revision:campaign.content_revision})}
    catch(error){if(url)URL.revokeObjectURL(url);if(request===generation.current)setError(describeError(error))}
  }
  async function upload() {
    if(!picked || lock.current || conflict)return
    lock.current=true;setBusy(true);setError('');setNotice('Uploading and extracting text…')
    let saved=false
    try{const value=await api.uploadPoster(campaign.id,picked.file,picked.revision);saved=true;setPoster(value);setPicked(null);onCampaignChange(await api.get(campaign.id));setNotice(`Poster saved privately · OCR ${value.ocr.status}${value.ocr.reason ? ` (${value.ocr.reason})`:''}`)}
    catch(error){setError(saved?'Poster saved, but campaign reload failed. Reload before another upload.':describeError(error));setNotice('');if(error instanceof ApiError && error.status===409)setConflict(true)}
    finally{lock.current=false;setBusy(false)}
  }
  async function reconcile(){if(!picked || lock.current)return;setBusy(true);try{const value=await api.get(campaign.id);const current=value.data.reviews.find(record=>record.id===campaign.id)?.backendCampaign;if(!current)throw new Error('Campaign unavailable.');onCampaignChange(value);setPicked({...picked,revision:current.content_revision});setConflict(false);setNotice('Latest revision loaded. Upload explicitly to replace its poster.')}catch(error){setError(describeError(error))}finally{setBusy(false)}}
  return <section className="live-poster" aria-labelledby="poster-heading"><h3 id="poster-heading">Marketing poster <span className="optional">optional</span></h3><small>PNG/JPEG · 5 MiB · 16 million pixels · private canonical PNG</small>
    {poster && !picked && <PrivatePoster key={poster.id} api={api} campaignId={campaign.id} posterId={poster.id}/>}
    <input ref={picker} type="file" className="visually-hidden" tabIndex={-1} accept="image/png,image/jpeg" aria-label="Choose poster for private upload" disabled={busy} onChange={event=>{const files=Array.from(event.target.files||[]);if(files.length)void choose(files);event.target.value=''}}/>
    <div className="poster-dropzone" onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();void choose(Array.from(event.dataTransfer.files))}}>{picked && <><img className="poster-preview" src={picked.url} alt={`Unsaved preview: ${picked.file.name}`}/><p className="poster-filename">{picked.file.name} · not uploaded yet</p></>}<div className="poster-actions"><button type="button" disabled={busy} onClick={()=>picker.current?.click()}>{poster||picked?'Choose replacement':'Choose image'}</button>{picked && <><button type="button" disabled={busy} onClick={()=>{generation.current++;setPicked(null);setError('');setConflict(false)}}>Remove selection</button><button type="button" disabled={busy||conflict} onClick={()=>void upload()}>Upload poster</button></>}</div><small>Or drop an image here.</small></div>
    {conflict && <button type="button" disabled={busy} onClick={()=>void reconcile()}>Use latest revision for this upload</button>}{error && <p className="error" role="alert">{error}</p>}<p role="status" className="poster-upload-status form-help">{notice}</p><small>Saved posters persist on the server. There is no delete-poster API; replace by uploading a new revision. OCR failures are not clean reviews.</small>
    {poster && <details><summary>OCR text and confidence</summary><p>{poster.ocr.text||'No readable text returned.'}</p><p className="form-help">{poster.ocr.words.length} words · {poster.ocr.status} · {poster.ocr.reason||'No extraction warning'}</p></details>}
  </section>
}
