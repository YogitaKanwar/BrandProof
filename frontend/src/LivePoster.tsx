import { useEffect, useImperativeHandle, useRef, useState } from 'react'
import type { RefObject } from 'react'
import type { BackendClient,CampaignOut } from './api/backend'
import type { ReviewResult } from './api/reviews'
import type { PosterOut } from './api/posters'
import {ApiError,describeError} from './api/client'
import {validatePoster} from './contentDraft'
import PrivatePoster from './PrivatePoster'
import {useUnsavedChanges} from './unsavedChanges'

export default function LivePoster({api,campaign,onCampaignChange,onAttached,onPendingChange,captionSaves,uploadRef}:{api:BackendClient;campaign:CampaignOut;onCampaignChange:(result:ReviewResult)=>void;onAttached:(attached:boolean)=>void;onPendingChange:(pending:boolean)=>void;captionSaves:{previous:number;current:number}[];uploadRef:RefObject<{upload:()=>Promise<CampaignOut>}|null>}) {
  const [poster,setPoster]=useState<PosterOut|null>(null)
  const [picked,setPicked]=useState<{file:File;url:string;revision:number}|null>(null)
  const [busy,setBusy]=useState(false)
  const [validating,setValidating]=useState(false)
  const [error,setError]=useState('')
  const [notice,setNotice]=useState('')
  const [conflict,setConflict]=useState(false)
  const picker=useRef<HTMLInputElement>(null), generation=useRef(0),lock=useRef(false)
  useUnsavedChanges(!!picked || busy || validating)
  useEffect(()=>{onPendingChange(!!picked || busy || validating)},[picked,busy,validating,onPendingChange])
  useEffect(()=>{let active=true;api.poster(campaign.id).then(value=>{if(active){setPoster(value);setError('');onAttached(true)}}).catch(error=>{if(active){if(error instanceof ApiError&&error.status===404)onAttached(false);else setError(describeError(error))}});return()=>{active=false}},[api,campaign.id,campaign.content_revision,onAttached])
  useEffect(()=>()=>{if(picked)URL.revokeObjectURL(picked.url)},[picked])
  useEffect(()=>()=>{generation.current++},[])
  async function choose(files:File[]) {
    if(lock.current)return
    const request=++generation.current;setError('');setNotice('');setConflict(false)
    if(files.length!==1){setValidating(false);setError('Choose one PNG or JPEG.');return}
    setValidating(true)
    let url=''
    try{await validatePoster(files[0]);url=URL.createObjectURL(files[0]);const image=new Image();image.src=url;await image.decode();if(image.naturalWidth*image.naturalHeight>16000000)throw new Error('Image exceeds 16 million pixels.');if(request!==generation.current){URL.revokeObjectURL(url);return}setPicked({file:files[0],url,revision:campaign.content_revision})}
    catch(error){if(url)URL.revokeObjectURL(url);if(request===generation.current)setError(describeError(error))}
    finally{if(request===generation.current)setValidating(false)}
  }
  useImperativeHandle(uploadRef,()=>({upload:async()=>{
    const updated=await upload(true)
    if(!updated)throw new Error('Poster upload did not complete.')
    return updated
  }}))
  async function upload(forReview=false) {
    if(!picked || lock.current || conflict || validating){
      if(forReview)throw new Error(conflict ? 'Resolve the poster version conflict before reviewing.' : 'Wait for the image to finish opening or uploading, then try again.')
      return
    }
    lock.current=true;setBusy(true);setError('');setNotice('Uploading and extracting text…')
    let saved=false
    // Advance only across our own successful revision-checked caption saves.
    // Concurrent writes are not rebased: their revision still produces a 409.
    const uploadRevision=captionSaves.reduce((revision,save)=>revision===save.previous ? save.current:revision,picked.revision)
    try{const value=await api.uploadPoster(campaign.id,picked.file,uploadRevision);saved=true;setPoster(value);setPicked(null);onAttached(true);const result=await api.get(campaign.id);const updated=result.data.reviews.find(record=>record.campaignId===campaign.id)?.backendCampaign;if(!updated)throw new Error('Saved campaign unavailable.');onCampaignChange(result);setNotice(`Poster saved privately · OCR ${value.ocr.status}${value.ocr.reason ? ` (${value.ocr.reason})`:''}`);return updated}
    catch(error){setError(saved?'Poster saved, but campaign reload failed. Reload before another upload.':describeError(error));setNotice('');if(error instanceof ApiError && error.status===409)setConflict(true);if(forReview)throw error}
    finally{lock.current=false;setBusy(false)}
  }
  async function reconcile(){if(!picked || lock.current)return;setBusy(true);try{const value=await api.get(campaign.id);const current=value.data.reviews.find(record=>record.id===campaign.id)?.backendCampaign;if(!current)throw new Error('Campaign unavailable.');onCampaignChange(value);setPicked({...picked,revision:current.content_revision});setConflict(false);setNotice('Latest revision loaded. Upload explicitly to replace its poster.')}catch(error){setError(describeError(error))}finally{setBusy(false)}}
  return <section className="live-poster" aria-labelledby="poster-heading"><h3 id="poster-heading">Marketing poster <span className="optional">optional</span></h3><small>PNG/JPEG · up to 5 MiB · 16 million pixels</small>
    {poster && !picked && <PrivatePoster key={poster.id} api={api} campaignId={campaign.id} posterId={poster.id}/>}
    <input ref={picker} type="file" className="visually-hidden" tabIndex={-1} accept="image/png,image/jpeg" aria-label="Choose poster for private upload" disabled={busy} onChange={event=>{const files=Array.from(event.target.files||[]);if(files.length)void choose(files);event.target.value=''}}/>
    <div className="poster-dropzone" onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();void choose(Array.from(event.dataTransfer.files))}}>{picked && <><img className="poster-preview" src={picked.url} alt={`Unsaved preview: ${picked.file.name}`}/><p className="poster-filename">{picked.file.name} · not uploaded yet</p></>}<div className="poster-actions"><button type="button" disabled={busy} onClick={()=>picker.current?.click()}>{poster||picked?'Choose replacement':'Choose image'}</button>{picked && <><button type="button" disabled={busy} onClick={()=>{generation.current++;setPicked(null);setValidating(false);setError('');setConflict(false)}}>Remove selection</button><button type="button" disabled={busy||validating||conflict} onClick={()=>void upload()}>Upload poster</button></>}</div><small>Or drop an image here.</small></div>
    {conflict && <button type="button" disabled={busy} onClick={()=>void reconcile()}>Use latest revision for this upload</button>}{error && <p className="error" role="alert">{error}</p>}<p role="status" className="poster-upload-status form-help">{validating ? 'Opening image…' : notice}</p><small>{picked ? 'Upload this selection before reviewing it.' : 'Uploaded images are saved privately. Upload a replacement to change the poster.'}</small>
    {poster && <details><summary>OCR text and confidence</summary><p>{poster.ocr.text||'No readable text returned.'}</p><p className="form-help">{poster.ocr.words.length} words · {poster.ocr.status} · {poster.ocr.reason||'No extraction warning'}</p></details>}
  </section>
}
