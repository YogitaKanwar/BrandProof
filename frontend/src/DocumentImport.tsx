import {useEffect,useState} from 'react'
import type {BackendClient} from './api/backend'
import type {GuidelineDocument} from './api/documents'
import {describeError} from './api/client'
import {useUnsavedChanges} from './unsavedChanges'

export default function DocumentImport({api,campaignId,disabled,onImported}:{api:BackendClient;campaignId:string;disabled:boolean;onImported:()=>Promise<unknown>}){
  const [documents,setDocuments]=useState<GuidelineDocument[]>([]),[file,setFile]=useState<File|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  useUnsavedChanges(busy||!!file)
  useEffect(()=>{let active=true;api.documents(campaignId).then(rows=>{if(active)setDocuments(rows)}).catch(error=>{if(active)setError(describeError(error))});return()=>{active=false}},[api,campaignId])
  async function upload(){if(!file||busy||disabled)return;setBusy(true);setError('');setNotice('');let written=false;try{
    const campaign=(await api.get(campaignId)).data.reviews.find(row=>row.id===campaignId)?.backendCampaign
    if(!campaign)throw new Error('Campaign unavailable')
    const result=await api.importDocument(campaignId,file,campaign.source_revision);written=true
    setDocuments(rows=>[...rows,result.document]);setFile(null);setNotice(result.notice);await onImported()
  }catch(error){setError(written?'Import was saved, but refreshing failed. Reload sources before importing again.':describeError(error))}finally{setBusy(false)}}
  return <details className="document-import"><summary>Import PDF guidelines</summary><p className="form-help">Owner action · PDF text layer only · up to 5 MiB / 30 pages. Only explicit supported directives become pending candidates. Check each exact page quote against your document before confirmation. Scans require manual transcription; nothing is sent to AI.</p><input aria-label="PDF brand guidelines" type="file" accept="application/pdf,.pdf" disabled={busy||disabled} onChange={event=>{const picked=event.target.files?.[0];setError('');setNotice('');if(picked&&picked.size>5*1024*1024){setError('PDF limit is 5 MiB');setFile(null)}else setFile(picked||null);event.target.value=''}}/>{file&&<p>{file.name} <button type="button" disabled={busy} onClick={()=>setFile(null)}>Cancel selection</button></p>}<button type="button" disabled={!file||busy||disabled} onClick={()=>void upload()}>{busy?'Extracting…':'Import as pending candidates'}</button>{error&&<p role="alert" className="error">{error}</p>}<p role="status">{notice}</p>{documents.map(document=><details key={document.id} id={`document-${document.id}`}><summary>{document.filename} · {document.status} · {document.candidate_count} candidates</summary><p>{document.scope}</p>{document.candidate_limit_reached&&<p>Candidate limit reached; inspect remaining text manually.</p>}{document.pages.map(page=><details key={page.page_number}><summary>Page {page.page_number} · {page.status}</summary><pre className="caption-snapshot">{page.text||page.reason}</pre></details>)}</details>)}</details>
}
