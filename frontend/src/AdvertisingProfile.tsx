import {useEffect,useRef,useState} from 'react'
import type {BackendClient,CampaignOut} from './api/backend'
import type {AdvertisingProfile as Profile,AdvertisingProfileOut} from './api/legal'
import type {ReviewResult} from './api/reviews'
import {describeError} from './api/client'
import {useUnsavedChanges} from './unsavedChanges'

const empty:Profile={jurisdiction:'unknown',sector:'unknown',language:'unknown'}
export default function AdvertisingProfile({api,campaign,onChanged}:{api:BackendClient;campaign:CampaignOut;onChanged:(result:ReviewResult)=>void}){
  const [data,setData]=useState<AdvertisingProfileOut|null>(null),[profile,setProfile]=useState<Profile>(empty)
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  const editing=useRef(false)
  const dirty=JSON.stringify(profile)!==JSON.stringify(data?.profile||empty)
  useUnsavedChanges(dirty||busy)
  useEffect(()=>{let active=true;api.advertisingProfile(campaign.id).then(value=>{if(active){if(editing.current){setError('Saved campaign changed. Your profile draft is preserved; discard it to reload before saving.');return}setData(value);setProfile(value.profile||empty);setError('')}}).catch(e=>{if(active)setError(describeError(e))});return()=>{active=false}},[api,campaign.id,campaign.source_revision])
  function edit(next:Profile){editing.current=JSON.stringify(next)!==JSON.stringify(data?.profile||empty);setProfile(next)}
  async function save(){if(busy||!data)return;setBusy(true);setError('');setNotice('');try{
    const result=await api.saveAdvertisingProfile(campaign.id,profile,{expected_content_revision:campaign.content_revision,expected_source_revision:data.source_revision})
    editing.current=false;setData(result);setProfile(result.profile||empty);setNotice('Advertising profile saved. Run a new review; earlier approvals are stale.');onChanged(await api.get(campaign.id))
  }catch(e){setError(describeError(e))}finally{setBusy(false)}}
  return <details className="advertising-profile document-import"><summary>Advertising-risk checks · {data?.profile?'Profile saved':'Choose scope'}</summary>
    <p className="form-help">Owner action · Select the intended audience and language. Publication date: {campaign.publication_date}. These choices define the screening scope; brand confirmation does not override regulation.</p>
    <p className="form-help">Saved scope: {data?.profile?`${data.profile.jurisdiction} / ${data.profile.sector} / ${data.profile.language}`:"not selected"}.</p><fieldset disabled={busy||!data}><legend>Campaign advertising profile</legend>
      <label htmlFor="ad-jurisdiction">Target jurisdiction</label><select id="ad-jurisdiction" value={profile.jurisdiction} onChange={e=>edit({...profile,jurisdiction:e.target.value as Profile['jurisdiction']})}><option value="unknown">Unknown / not selected</option><option value="IN">India</option><option value="other">Outside India (unsupported)</option></select>
      <label htmlFor="ad-sector">Sector</label><select id="ad-sector" value={profile.sector} onChange={e=>edit({...profile,sector:e.target.value as Profile['sector']})}><option value="unknown">Unknown / not selected</option><option value="general">General advertising (no sector-specific assessment)</option><option value="coaching">Coaching / education</option><option value="healthcare">Healthcare</option><option value="finance">Finance</option><option value="other">Other sector</option></select>
      <label htmlFor="ad-language">Content language</label><select id="ad-language" value={profile.language} onChange={e=>edit({...profile,language:e.target.value as Profile['language']})}><option value="unknown">Unknown / not selected</option><option value="en">English</option><option value="other">Other / mixed (unsupported)</option></select>
      <button type="button" disabled={!dirty} onClick={()=>void save()}>Save advertising profile</button>
      {dirty&&<button type="button" onClick={()=>{editing.current=false;setBusy(true);api.advertisingProfile(campaign.id).then(value=>{setData(value);setProfile(value.profile||empty);setError('')}).catch(e=>setError(describeError(e))).finally(()=>setBusy(false))}}>Discard profile changes and reload</button>}
    </fieldset>
    {dirty&&<p className="form-help">Unsaved profile. Reviews use the saved scope shown above until you save.</p>}
    {data&&<><p className="form-help">Reference pack {data.pack.version} · retrieved {data.pack.retrieved_at} · source review due {data.pack.review_due}. <a href={data.pack.source_url} target="_blank" rel="noreferrer">Official CCPA source</a></p><p>{data.pack.supported_scope}</p><p className="form-help">Outside coverage: {data.pack.unsupported_scope}</p>{profile.sector!=='general'&&profile.sector!=='unknown'&&<p className="notice">Only the general substantiation check is available. Sector-specific regulation requires manual review.</p>}</>}
    {error&&<p role="alert" className="error">{error}</p>}<p role="status">{notice}</p>
  </details>
}
