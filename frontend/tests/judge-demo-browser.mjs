// Genuine Chromium + API acceptance. Public QA requires an explicit opt-in and known host.
// Credentials and workspace IDs remain in memory; screenshots contain fictional UI only.
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
const origin=process.env.BRANDPROOF_TEST_URL||'http://127.0.0.1:8017/'
const targetOrigin=new URL(origin)
const localTarget=targetOrigin.protocol==='http:'&&['127.0.0.1','localhost'].includes(targetOrigin.hostname)
const authorizedPublicTarget=process.env.BRANDPROOF_ALLOW_PUBLIC_DEMO_TESTS==='1'&&targetOrigin.protocol==='https:'&&['brand-proof-tau.vercel.app','brandproof-api-slz9.onrender.com'].includes(targetOrigin.hostname)
assert.ok(localTarget||authorizedPublicTarget,'Public QA requires explicit opt-in and an authorized BrandProof host')
const evidenceRoot=process.env.BRANDPROOF_DEMO_EVIDENCE_DIR||'../docs/evidence/judge-demo'
const browser=await(await fetch('http://127.0.0.1:9223/json/version')).json()
const browserSocket=new WebSocket(browser.webSocketDebuggerUrl)
await new Promise(resolve=>browserSocket.addEventListener('open',resolve,{once:true}))
function protocol(socket){let id=0;const pending=new Map();socket.addEventListener('message',event=>{const data=JSON.parse(event.data);const entry=pending.get(data.id);if(entry){pending.delete(data.id);if(data.error)entry.reject(new Error(data.error.message));else entry.resolve(data.result)}});return(method,params={})=>new Promise((resolve,reject)=>{const next=++id;pending.set(next,{resolve,reject});socket.send(JSON.stringify({id:next,method,params}))})}
const control=protocol(browserSocket)
async function open(){const {browserContextId}=await control('Target.createBrowserContext');const {targetId}=await control('Target.createTarget',{url:'about:blank',browserContextId});const targets=await(await fetch('http://127.0.0.1:9223/json/list')).json();const target=targets.find(row=>row.id===targetId);const socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}));const send=protocol(socket);const errors=[];socket.addEventListener('message',event=>{const d=JSON.parse(event.data);if(d.method==='Runtime.exceptionThrown')errors.push(d.params.exceptionDetails.text)});await send('Page.enable');await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});return{send,socket,browserContextId,errors}}
async function evaluate(page,expression){const data=await page.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw new Error(data.exceptionDetails.text);return data.result.value}
async function wait(page,expression){for(const deadline=Date.now()+45000;Date.now()<deadline;){try{if(await evaluate(page,expression))return}catch(error){if(!/navigated|context|Cannot find/.test(error.message))throw error}await new Promise(resolve=>setTimeout(resolve,50))}throw new Error('Timed out: '+expression)}
const button=text=>`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(text)})`
async function click(page,expression){await wait(page,`!!(${expression})&&!(${expression}).disabled`);const point=await evaluate(page,`(()=>{const element=${expression};element.scrollIntoView({block:'center'});const r=element.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);await page.send('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1})}
async function fill(page,selector,value){await evaluate(page,`(()=>{const input=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(input.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(value)});input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))})()`)}
async function reload(page){const loaded=new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('Reload did not complete')),20000);const handler=event=>{if(JSON.parse(event.data).method==='Page.loadEventFired'){clearTimeout(timeout);page.socket.removeEventListener('message',handler);resolve()}};page.socket.addEventListener('message',handler)});await page.send('Page.reload');await loaded}
async function screenshot(page,name){await mkdir(evidenceRoot,{recursive:true});const data=await page.send('Page.captureScreenshot',{format:'png'});await writeFile(`${evidenceRoot}/${name}.png`,Buffer.from(data.data,'base64'))}
const a=await open(),b=await open()
const access=`async()=>{const response=await fetch('/api/v1/demo-sessions/resume',{method:'POST',headers:{'X-BrandProof-Session':'resume'}});if(!response.ok)throw new Error('Session recovery failed');return response.json()}`
try{
  await a.send('Page.navigate',{url:origin});await wait(a,`!!document.querySelector('.demo-entry')&&!document.querySelector('.demo-cta').disabled`)
  assert.equal(await evaluate(a,`document.querySelectorAll('.demo-role button').length`),2)
  assert.equal(await evaluate(a,`!!document.querySelector('input[type=password]')`),false)
  await screenshot(a,'login-desktop')
  await a.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});await a.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9})
  assert.equal(await evaluate(a,`document.activeElement.tagName==='A'||document.activeElement.tagName==='BUTTON'`),true)
  for(const width of [390,320]){await a.send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:true});assert.equal(await evaluate(a,`document.documentElement.scrollWidth<=innerWidth`),true)}
  await screenshot(a,'login-mobile')
  await a.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false})
  await click(a,`document.querySelector('.demo-cta')`);await wait(a,`!!document.querySelector('.demo-mode-bar')&&!!document.querySelector('.reviews-empty')`)
  await evaluate(a,`(async()=>{window.__entryWorkspace=(await (${access})()).workspace_id;location.hash='/demo'})()`)
  await wait(a,`!!document.querySelector('.demo-entry')&&document.querySelector('.demo-cta').textContent.includes('Continue Demo')`)
  assert.equal(await evaluate(a,`!document.querySelector('.demo-sample')&&!document.querySelector('.demo-evidence')`),true)
  await reload(a);await wait(a,`!!document.querySelector('.demo-entry')&&document.querySelector('.demo-cta').textContent.includes('Continue Demo')`)
  await screenshot(a,'direct-demo-entry')
  await evaluate(a,`(async()=>{window.__entryWorkspace=(await (${access})()).workspace_id})()`)
  await click(a,`document.querySelector('.demo-cta')`);await wait(a,`!!document.querySelector('.demo-mode-bar')&&!!document.querySelector('.reviews-empty')`)
  assert.equal(await evaluate(a,`(async()=>{return(await (${access})()).workspace_id===window.__entryWorkspace})()`),true)
  assert.equal(await evaluate(a,`localStorage.length===0&&sessionStorage.length===0`),true)
  await click(a,`document.querySelector('a[href="#/new"]')`);await wait(a,`!!document.querySelector('#publication-date')`)
  await click(a,button('Continue'));assert.equal(await evaluate(a,`!!document.querySelector('#publication-error')`),true)
  await fill(a,'#review-title','Judge custom campaign');await fill(a,'#publication-date','2026-11-12');await click(a,button('Continue'))
  await wait(a,`document.querySelector('.draft-title')?.textContent==='Judge custom campaign'`)
  const customHash=await evaluate(a,'location.hash');await reload(a);await wait(a,`document.querySelector('.draft-title')?.textContent==='Judge custom campaign'`)
  assert.equal(await evaluate(a,'location.hash=== '+JSON.stringify(customHash)),true)
  await click(a,`document.querySelector('a.wordmark')`);await wait(a,`!!document.querySelector('.example-invitation')`)
  await click(a,button('Try an editable example'));await wait(a,`document.querySelectorAll('.server-source').length===5&&!!document.querySelector('.live-poster img')&&!document.querySelector('.run-caption button').disabled`)
  assert.equal(await evaluate(a,`document.querySelector('.draft-title').textContent==='Workshop Campaign'&&document.querySelector('#marketing-caption').value.includes('INR 599')&&document.querySelector('#brand-information').textContent.includes('899')`),true)
  assert.equal(await evaluate(a,`document.querySelectorAll('.findings-list').length`),0)
  await evaluate(a,`document.querySelector('.server-source').scrollIntoView({block:'center'})`);await screenshot(a,'workshop-references-content')
  await evaluate(a,`document.querySelector('.live-poster').scrollIntoView({block:'center'})`);await screenshot(a,'workshop-poster-ocr')
  await click(a,`document.querySelector('.run-caption button')`);await wait(a,`!!document.querySelector('.findings-list')&&!document.querySelector('.run-caption button').disabled`)
  const campaignId=await evaluate(a,`decodeURIComponent(location.hash.slice(9).split('?')[0])`)
  const sampleChecks=await evaluate(a,`(async()=>{const identity=await (${access})();const h={Authorization:'Bearer '+identity.actors.creator.access_token};const campaign=${JSON.stringify(campaignId)};const runs=await(await fetch('/api/v1/campaigns/'+campaign+'/reviews',{headers:h})).json();const run=runs.at(-1);const poster=await(await fetch('/api/v1/campaigns/'+campaign+'/posters',{headers:h})).json();return{caption:run.findings.some(f=>f.evidence_status==='contradicted'&&f.location.asset==='caption'&&JSON.stringify(f.evidence).includes('899')),poster:run.findings.some(f=>f.evidence_status==='contradicted'&&f.location.asset==='poster'&&f.location.boxes.length>0&&JSON.stringify(f.evidence).includes('899')),ocr:poster.ocr.status,ai:run.checks.contextual.status}})()`)
  assert.equal(sampleChecks.caption,true);assert.equal(sampleChecks.poster,true);assert.equal(sampleChecks.ocr,'completed');assert.equal(sampleChecks.ai,'unavailable')
  assert.equal(await evaluate(a,`document.querySelector('.ai-consent input').checked`),false)
  await evaluate(a,`document.querySelector('.finding').scrollIntoView({block:'center'})`);await screenshot(a,'real-contradiction-results')
  await wait(a,`!!Array.from(document.querySelectorAll('.finding')).find(n=>n.querySelector('h4')?.textContent==='price'&&n.querySelector('.ocr-box'))`)
  await evaluate(a,`Array.from(document.querySelectorAll('.finding')).find(n=>n.querySelector('h4')?.textContent==='price'&&n.querySelector('.ocr-box')).scrollIntoView({block:'center'})`);await screenshot(a,'poster-price-evidence')
  await click(a,button('Request human review'));await wait(a,`document.querySelector('.human-review-status').textContent.includes('request saved')`)
  await fill(a,'#approval-reason','Fictional test review: the caption and poster both need price corrections before publication.')
  await click(a,button('Record reviewer decision'));await wait(a,`document.querySelector('.receipt-readiness').textContent.includes('changes requested')`)
  await evaluate(a,`document.querySelector('.human-review').scrollIntoView()`);await screenshot(a,'human-review-changes-requested')
  await click(a,`document.querySelector('.live-sources .document-import > summary')`);await click(a,button('Load fictional workshop guidelines'));await click(a,button('Import as pending candidates'))
  await wait(a,`document.querySelectorAll('.server-source').length===8&&document.querySelector('.live-sources .document-import').textContent.includes('3 imported candidates')`)
  assert.equal(await evaluate(a,`document.querySelectorAll('.confirm-source').length`),4)
  await b.send('Page.navigate',{url:new URL('#/demo',origin).href});await wait(b,`!!document.querySelector('.demo-cta')&&!document.querySelector('.demo-cta').disabled`);await click(b,`document.querySelector('.demo-cta')`);await wait(b,`!!document.querySelector('.reviews-empty')`)
  const permissions=await evaluate(b,`(async()=>{const identity=await (${access})();const bad=await fetch('/api/v1/campaigns',{headers:{Authorization:'Bearer invalid-public-credentials'}});const foreign=await fetch('/api/v1/campaigns/'+${JSON.stringify(campaignId)},{headers:{Authorization:'Bearer '+identity.actors.creator.access_token}});const forbidden=await fetch('/api/v1/campaigns',{method:'POST',headers:{Authorization:'Bearer '+identity.actors.reviewer.access_token,'Content-Type':'application/json'},body:JSON.stringify({name:'Forbidden',publication_date:'2026-11-12'})});return[bad.status,foreign.status,forbidden.status]})()`)
  assert.deepEqual(permissions,[401,404,403])
  await evaluate(a,`(async()=>{window.__testDemo=await (${access})()})()`)
  await click(a,button('Reset Demo'));await click(a,button('Keep current demo'));assert.equal(await evaluate(a,`!!document.querySelector('.draft-title')`),true)
  await click(a,button('Reset Demo'));await click(a,button('Confirm Reset Demo'));await wait(a,`!!document.querySelector('.reviews-empty')&&!document.querySelector('.demo-reset-confirm')`)
  assert.equal(await evaluate(a,`(async()=>{const response=await fetch('/api/v1/campaigns',{headers:{Authorization:'Bearer '+window.__testDemo.actors.creator.access_token}});const current=await (${access})();return response.status===401&&current.workspace_id!==window.__testDemo.workspace_id})()`),true)
  // Revoke outside the UI to exercise stale-tab recovery without creating a replacement.
  await evaluate(a,`(async()=>{await fetch('/api/v1/demo-sessions/logout',{method:'POST',headers:{'X-BrandProof-Session':'resume'}})})()`)
  await click(a,button('Reload recent reviews'));await wait(a,`!!document.querySelector('.session-expiry')`)
  await click(a,button('Restore session'));await wait(a,`document.querySelector('.notice')?.textContent.includes('expired or was revoked')`)
  await click(a,button('Exit Demo'));await wait(a,`!!document.querySelector('.demo-entry')`)
  await reload(a);await wait(a,`!!document.querySelector('.demo-entry')&&!document.querySelector('.demo-cta').disabled`)
  await click(a,`document.querySelector('.demo-sample')`);await wait(a,`document.querySelectorAll('.server-source').length===5&&!!document.querySelector('.live-poster img')`)
  const pdf=await open()
  try{
    await pdf.send('Page.navigate',{url:new URL('/demo/workshop-guidelines.pdf',origin).href})
    await wait(pdf,`!!document.querySelector('embed[type="application/pdf"]')||document.contentType==='application/pdf'`)
    await new Promise(resolve=>setTimeout(resolve,1000))
    await screenshot(pdf,'fictional-guidelines')
  }finally{await control('Target.disposeBrowserContext',{browserContextId:pdf.browserContextId});pdf.socket.close()}
  // Save only sanitized evidence; do not serialize session credentials or workspace identifiers.
  await writeFile(`${evidenceRoot}/browser-results.json`,JSON.stringify({passed:true,sample:sampleChecks,permissions,checks:['explicit demo route with restored session','simple demo screen without sample prompts','continue preserves current sandbox','passwordless entry','keyboard and mobile layout','one-click sandbox','required field validation','custom campaign and refresh','real sample caption and poster contradictions','explicit human request and reviewer changes decision','PDF pending extraction','separate judge cookies and workspace isolation','reset cancellation and revocation','stale tab recovery','logout and reload','direct sample entry','no browser credential storage']},null,2)+'\n')
  assert.equal(a.errors.length+b.errors.length,0)
  console.log('PASS judge demo: real UI, OCR/evidence, human workflow, PDF, permissions, isolation, refresh, reset/revocation, expired/revoked recovery and logout. No credentials persisted.')
} catch(error) { await screenshot(a,'failure');console.error(await evaluate(a,`document.querySelector('.live-sources .document-import')?.innerText||document.querySelector('main')?.innerText.slice(0,500)`));throw error }
finally {for(const page of [a,b]){await control('Target.disposeBrowserContext',{browserContextId:page.browserContextId});page.socket.close()}browserSocket.close()}
