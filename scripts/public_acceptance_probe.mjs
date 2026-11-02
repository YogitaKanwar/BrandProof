// Read-only identity/health/asset checks. No sessions or credentials are involved.
import {createHash} from 'node:crypto'
import {readFile,writeFile} from 'node:fs/promises'
const root=new URL('../',import.meta.url)
const result={observed_at:new Date().toISOString(),origins:[]}
const sha=bytes=>createHash('sha256').update(bytes).digest('hex')
for(const origin of ['https://brand-proof-tau.vercel.app','https://brandproof-api-slz9.onrender.com']){
  const record={origin,assets:[]}
  for(const path of ['/api/v1/health','/openapi.json','/']){
    const start=Date.now()
    try{
      const response=await fetch(origin+path,{signal:AbortSignal.timeout(60000)})
      const bytes=Buffer.from(await response.arrayBuffer())
      record[path]={status:response.status,ms:Date.now()-start,sha256:sha(bytes)}
      if(path==='/api/v1/health')record[path].body=bytes.toString().slice(0,300)
      if(path==='/openapi.json'&&response.ok)record[path].matches_saved=JSON.stringify(JSON.parse(bytes))===JSON.stringify(JSON.parse(await readFile(new URL('docs/openapi.json',root))))
      if(path==='/'&&response.ok){
        const paths=[...bytes.toString().matchAll(/(?:src|href)="(\/assets\/[^\"]+)"/g)].map(match=>match[1])
        for(const asset of [...paths,'/demo/workshop-guidelines.pdf','/fictional-guidelines.pdf']){
          const served=await fetch(origin+asset,{signal:AbortSignal.timeout(30000)})
          const value=Buffer.from(await served.arrayBuffer())
          let local
          try{local=await readFile(new URL('frontend/'+(asset.startsWith('/assets/')?'dist':'public')+asset,root))}catch{}
          record.assets.push({path:asset,status:served.status,sha256:sha(value),matches_candidate:local?sha(value)===sha(local):false})
        }
      }
    }catch(error){record[path]={error:error.name,cause:error.cause?.code,ms:Date.now()-start}}
  }
  result.origins.push(record)
}
const output=new URL('docs/evidence/round3-final/public-readonly.json',root)
await writeFile(output,JSON.stringify(result,null,2)+'\n')
console.log(JSON.stringify(result,null,2))
