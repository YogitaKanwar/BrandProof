import {useEffect,useRef,useState} from 'react'
import type {BackendClient,CampaignOut} from './api/backend'
import type {ReviewResult} from './api/reviews'
import {describeError} from './api/client'
import {useUnsavedChanges} from './unsavedChanges'

export default function AltTextEditor({api,campaign,onCampaignChange}:{api:BackendClient;campaign:CampaignOut;onCampaignChange:(result:ReviewResult)=>void}){
  const [text,setText]=useState(''),[saved,setSaved]=useState(''),[posterId,setPosterId]=useState<string|null>(null),[revision,setRevision]=useState(campaign.content_revision),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  const dirty=text!==saved,dirtyRef=useRef(false)
  useEffect(()=>{dirtyRef.current=dirty},[dirty])
  useUnsavedChanges(dirty||busy)
  useEffect(()=>{let active=true;api.altText(campaign.id).then(value=>{if(active){if(dirtyRef.current){setError('Content changed while this description has unsaved edits. Compare with the saved description before saving.');return}setText(value.text);setSaved(value.text);setPosterId(value.poster_id);setRevision(value.content_revision)}}).catch(error=>{if(active)setError(describeError(error))});return()=>{active=false}},[api,campaign.id,campaign.content_revision])
  async function save(){if(busy||!posterId||!dirty)return;setBusy(true);setError('');try{const result=await api.saveAltText(campaign.id,text,revision);onCampaignChange(result);setSaved(text);setRevision(result.data.reviews.find(row=>row.id===campaign.id)!.backendCampaign!.content_revision);setNotice('Description saved as a new content revision. Run a fresh review.')}catch(error){setError(describeError(error))}finally{setBusy(false)}}
  async function reload(){setBusy(true);try{const value=await api.altText(campaign.id);setText(value.text);setSaved(value.text);setRevision(value.content_revision);setPosterId(value.poster_id);setError('')}catch(error){setError(describeError(error))}finally{setBusy(false)}}
  return <details className="alt-text-editor"><summary>Poster accessibility description</summary><p className="form-help">Describe the actual image and its key information. Owner-confirmed description requirements are checked for presence and literal OCR prices/dates; meaning still needs human review. Replacing the poster requires a new description.</p><label htmlFor="poster-alt-text">Alt text for the saved poster</label><textarea id="poster-alt-text" rows={3} maxLength={4000} disabled={busy||!posterId} value={text} onChange={event=>{setText(event.target.value);setNotice('')}}/><button type="button" disabled={busy||!posterId||!dirty} onClick={()=>void save()}>Save poster description</button><button type="button" disabled={busy} onClick={()=>void reload()}>Load saved description (discard draft)</button>{!posterId&&<p>Attach a poster first.</p>}{error&&<p role="alert" className="error">{error}</p>}<p role="status">{notice}</p></details>
}
