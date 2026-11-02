// Local-only real Chromium acceptance with explicit network fault injection.
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
const origin=process.env.BRANDPROOF_TEST_URL||'http://127.0.0.1:8019/#/demo'
assert.ok(['127.0.0.1','localhost'].includes(new URL(origin).hostname),'Fault injection is local only')
const dir=process.env.BRANDPROOF_FINAL_EVIDENCE_DIR||'../docs/evidence/round3-final/errors'
await mkdir(dir,{recursive:true})
function protocol(socket){let id=0;const pending=new Map();socket.addEventListener('message',event=>{const row=JSON.parse(event.data),entry=pending.get(row.id);if(entry){pending.delete(row.id);if(row.error)entry.reject(new Error(row.error.message));else entry.resolve(row.result)}});return(method,params={})=>new Promise((resolve,reject)=>{const next=++id;pending.set(next,{resolve,reject});socket.send(JSON.stringify({id:next,method,params}))})}
const browser=await(await fetch('http://127.0.0.1:9223/json/version')).json()
const browserSocket=new WebSocket(browser.webSocketDebuggerUrl)
await new Promise(resolve=>browserSocket.addEventListener('open',resolve,{once:true}))
const control=protocol(browserSocket),{browserContextId}=await control('Target.createBrowserContext')
const {targetId}=await control('Target.createTarget',{url:'about:blank',browserContextId})
const target=(await(await fetch('http://127.0.0.1:9223/json/list')).json()).find(row=>row.id===targetId)
const socket=new WebSocket(target.webSocketDebuggerUrl)
await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}))
const send=protocol(socket),errors=[]
let mode='pass',writes=0,held
socket.addEventListener('message',event=>{
  const data=JSON.parse(event.data)
  if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text)
  if(data.method!=='Fetch.requestPaused')return
  const {requestId,request}=data.params
  // Never serialize the intercepted headers: they contain in-memory credentials.
  if(request.method==='POST'&&new URL(request.url).pathname==='/api/v1/campaigns'){
    writes++
    if(mode==='timeout'){held=requestId;return}
    if(mode==='unavailable'){void send('Fetch.fulfillRequest',{requestId,responseCode:503,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({error:{code:'qa_injected',message:'Temporary QA service failure. Try again after checking saved reviews.'}})).toString('base64')});return}
  }
  void send('Fetch.continueRequest',{requestId})
})
async function evaluate(expression){const data=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw new Error(data.exceptionDetails.text);return data.result.value}
async function wait(expression){for(const end=Date.now()+30000;Date.now()<end;){try{if(await evaluate(expression))return}catch(error){if(!/context|navigated|Cannot find/.test(error.message))throw error}await new Promise(resolve=>setTimeout(resolve,50))}throw new Error('Timed out: '+expression)}
const button=text=>`Array.from(document.querySelectorAll('button')).find(row=>row.textContent.trim()===${JSON.stringify(text)})`
async function click(expression){await wait(`!!(${expression})&&!(${expression}).disabled`);await evaluate(`(${expression}).click()`)}
async function fill(selector,value){await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}))})()`)}
async function screenshot(name){const result=await send('Page.captureScreenshot',{format:'png'});await writeFile(`${dir}/${name}.png`,Buffer.from(result.data,'base64'))}
async function chooseFile(name,type,size){await evaluate(`(()=>{const dt=new DataTransfer();dt.items.add(new File([new Uint8Array(${size})],${JSON.stringify(name)},{type:${JSON.stringify(type)}}));const input=document.querySelector('.document-import input[type=file]');input.files=dt.files;input.dispatchEvent(new Event('change',{bubbles:true}))})()`)}
try{
  await send('Page.enable');await send('Runtime.enable')
  await send('Emulation.setDeviceMetricsOverride',{width:768,height:1024,deviceScaleFactor:1,mobile:false})
  await send('Page.navigate',{url:origin});await wait(`!!document.querySelector('.demo-cta')&&!document.querySelector('.demo-cta').disabled`)
  assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true)
  await click(`document.querySelector('.demo-cta')`);await wait(`!!document.querySelector('.reviews-empty')`)
  await click(`document.querySelector('a[href="#/new"]')`);await wait(`!!document.querySelector('#publication-date')`)
  await fill('#review-title','Fictional resilience test');await fill('#publication-date','2026-11-12')
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns',requestStage:'Request'}]})
  mode='unavailable';await click(button('Continue'))
  await wait(`document.body.textContent.includes('Temporary QA service failure')&&!(${button('Continue')}).disabled`)
  assert.equal(await evaluate(`document.querySelector('#review-title').value`),'Fictional resilience test')
  assert.equal(writes,1)
  mode='timeout';await click(button('Continue'))
  await wait(`document.body.textContent.includes('check whether it was saved before submitting again')&&!(${button('Continue')}).disabled`)
  assert.equal(writes,2);assert.equal(await evaluate(`!!document.querySelector('.draft-title')`),false)
  if(held)await send('Fetch.failRequest',{requestId:held,errorReason:'TimedOut'}).catch(()=>{})
  await screenshot('timeout-recovery-tablet')
  mode='pass'
  // Two DOM activations in one turn are stricter than a physical double click.
  await evaluate(`(()=>{const button=${button('Continue')};button.click();button.click()})()`)
  await wait(`document.querySelector('.draft-title')?.textContent==='Fictional resilience test'`)
  assert.equal(writes,3,'Only one real create request is sent after duplicate activation')
  await send('Fetch.disable')
  await click(`document.querySelector('.live-sources .document-import > summary')`)
  await chooseFile('wrong.txt','text/plain',12);await wait(`document.querySelector('.document-import .error')?.textContent.includes('Choose a PDF')`)
  await chooseFile('empty.pdf','application/pdf',0);await wait(`document.querySelector('.document-import .error')?.textContent.includes('non-empty')`)
  await chooseFile('large.pdf','application/pdf',5*1024*1024+1);await wait(`document.querySelector('.document-import .error')?.textContent.includes('5 MiB')`)
  await chooseFile('corrupt.pdf','application/pdf',32);await click(button('Import as pending candidates'))
  await wait(`!!document.querySelector('.document-import .error')&&!(${button('Import as pending candidates')}).disabled`)
  assert.equal(await evaluate(`document.querySelectorAll('.server-source').length`),0)
  await screenshot('invalid-pdf-recovery')
  await click(button('Load fictional workshop guidelines'));await click(button('Import as pending candidates'))
  await wait(`document.querySelectorAll('.server-source').length===3`)
  assert.equal(await evaluate(`document.querySelectorAll('.confirm-source').length`),3)
  assert.equal(await evaluate(`localStorage.length===0&&sessionStorage.length===0`),true)
  assert.deepEqual(errors,[])
  await writeFile(`${dir}/results.json`,JSON.stringify({passed:true,local_fault_injection:true,campaign_posts:{injected_503:1,injected_timeout:1,real_after_double_activation:1},checks:['768px tablet layout','503 preserves draft and re-enables action','real 10-second transport timeout and recovery advice','duplicate activation sends one write','wrong/empty/oversized/corrupt PDF recovery','successful retry creates only pending rules','no browser credential storage']},null,2)+'\n')
  console.log('PASS local Chromium fault injection: 503, real timeout, preserved draft, one write after double activation, invalid PDFs, successful retry and tablet layout.')
}catch(error){await screenshot('failure');throw error}
finally{await control('Target.disposeBrowserContext',{browserContextId});socket.close();browserSocket.close()}
