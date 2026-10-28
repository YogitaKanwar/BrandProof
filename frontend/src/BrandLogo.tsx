import {useEffect,useState} from 'react'
import type {BackendClient,BrandLogoOut} from './api/backend'
import type {ReviewResult} from './api/reviews'
import {ApiError,describeError} from './api/client'
import {validatePoster} from './contentDraft'
import {useUnsavedChanges} from './unsavedChanges'

export default function BrandLogo({api,campaignId,onCampaignChange}:{api:BackendClient;campaignId:string;onCampaignChange:(result:ReviewResult)=>void}){
  const [logo,setLogo]=useState<BrandLogoOut|null>(null),[url,setUrl]=useState(''),[file,setFile]=useState<File|null>(null)
  const [busy,setBusy]=useState(false),[error,setError]=useState('')
  const [loadedId,setLoadedId]=useState('')
  useUnsavedChanges(!!file||busy)
  useEffect(()=>{let active=true;api.logo(campaignId).then(value=>{if(active)setLogo(value)}).catch(error=>{if(active&&!(error instanceof ApiError&&error.status===404))setError(describeError(error))});return()=>{active=false}},[api,campaignId])
  useEffect(()=>{let active=true,objectUrl='';if(logo)api.logoContent(campaignId,logo.id).then(blob=>{if(active){objectUrl=URL.createObjectURL(blob);setUrl(objectUrl);setLoadedId(logo.id)}}).catch(error=>{if(active)setError(describeError(error))});return()=>{active=false;if(objectUrl)URL.revokeObjectURL(objectUrl)}},[api,campaignId,logo])
  async function perform(confirm=false){if(busy)return;setBusy(true);setError('');try{const current=await api.get(campaignId);const campaign=current.data.reviews.find(row=>row.campaignId===campaignId)?.backendCampaign;if(!campaign)throw new Error('Campaign unavailable.');if(confirm&&logo)setLogo(await api.confirmLogo(campaignId,logo,campaign.source_revision));else if(file){await validatePoster(file);setLogo(await api.uploadLogo(campaignId,file,campaign.source_revision));setFile(null)}onCampaignChange(await api.get(campaignId))}catch(error){setError(describeError(error))}finally{setBusy(false)}}
  return <section className="brand-logo" aria-labelledby="brand-logo-heading"><h3 id="brand-logo-heading">Brand logo</h3><p className="form-help">Upload a tightly cropped reference logo on a plain background, then confirm it as demo owner. Local comparison flags possible changes; small, rotated or obscured logos require manual review. Logo comparison never approves a poster.</p>{url&&loadedId===logo?.id&&<img src={url} alt="Saved reference brand logo" style={{maxWidth:220,maxHeight:120,objectFit:'contain'}}/>}{logo&&<p>Reference v{logo.version} · {logo.status==='approved'?'Owner confirmed':'Pending owner confirmation'}</p>}<label>Reference logo (PNG/JPEG)<input type="file" accept="image/png,image/jpeg" disabled={busy} onChange={event=>{setFile(event.target.files?.[0]||null);setError('')}}/></label><button type="button" disabled={busy||!file} onClick={()=>void perform()}>Upload reference logo</button>{logo?.status==='pending'&&<button type="button" disabled={busy||!!file} onClick={()=>void perform(true)}>Confirm reference logo as owner</button>}{busy&&<p role="status">Saving brand logo…</p>}{error&&<p className="error" role="alert">{error}</p>}</section>
}

export function LogoReferencePreview({api,campaignId,logoId}:{api:BackendClient;campaignId:string;logoId:string}){
  const [url,setUrl]=useState(''),[error,setError]=useState('')
  useEffect(()=>{let active=true,local='';api.logoContent(campaignId,logoId).then(blob=>{if(active){local=URL.createObjectURL(blob);setUrl(local)}}).catch(error=>{if(active)setError(describeError(error))});return()=>{active=false;if(local)URL.revokeObjectURL(local)}},[api,campaignId,logoId])
  return <figure>{url&&<img src={url} alt="Historical owner-confirmed reference logo" style={{maxWidth:220,maxHeight:120,objectFit:'contain'}}/>}<figcaption>Reference logo used in this review</figcaption>{error&&<p className="error" role="alert">{error}</p>}</figure>
}
