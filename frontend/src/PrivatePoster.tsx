import { useEffect, useState } from 'react'
import type { BackendClient } from './api/backend'
import type { Box, PosterOut } from './api/posters'
import { overlayBox } from './api/posters'
import { describeError } from './api/client'

export default function PrivatePoster({api,campaignId,posterId,boxes=[]}: {api:BackendClient;campaignId:string;posterId:string;boxes?:Box[]}) {
  const [loaded,setLoaded]=useState<{poster:PosterOut;url:string}|null>(null)
  const [error,setError]=useState('')
  useEffect(()=> {
    let active=true, url=''
    Promise.all([api.poster(campaignId,posterId),api.posterContent(campaignId,posterId)]).then(([poster,blob])=>{
      if(!active)return
      url=URL.createObjectURL(blob);setLoaded({poster,url});setError('')
    }).catch(error=>{if(active)setError(describeError(error))})
    return()=>{active=false;if(url)URL.revokeObjectURL(url)}
  },[api,campaignId,posterId])
  if(error)return <p role="alert" className="error">Private poster could not be loaded. {error}</p>
  if(!loaded || loaded.poster.id!==posterId)return <p role="status">Loading private poster…</p>
  return <figure className="private-poster"><div className="poster-canvas"><img src={loaded.url} width={loaded.poster.width} height={loaded.poster.height} alt="Canonical poster associated with this saved record" />{boxes.map((box,index)=>{const style=overlayBox(box,loaded.poster.width,loaded.poster.height);return style?<span key={index} className="ocr-box" style={style} aria-hidden="true"/>:null})}</div><figcaption>OCR: {loaded.poster.ocr.status}{loaded.poster.ocr.reason ? ` · ${loaded.poster.ocr.reason.replaceAll('_',' ')}`:''} · {loaded.poster.width} × {loaded.poster.height}. Highlighted boxes locate extracted text, not a complete visual assessment.</figcaption></figure>
}
