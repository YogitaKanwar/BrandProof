// Genuine UI acceptance in the documented disposable Chrome CDP profile.
import assert from 'node:assert/strict'
import {readFile,mkdir,writeFile} from 'node:fs/promises'
const origin=process.env.BRANDPROOF_TEST_URL||'http://127.0.0.1:8013/'
const pdf=(await readFile(new URL('./fixtures/guidelines.pdf',import.meta.url))).toString('base64')
const target=await(await fetch('http://127.0.0.1:9223/json/new?about:blank',{method:'PUT'})).json()
const socket=new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve);socket.addEventListener('error',reject)})
let sequence=0;const pending=new Map(),errors=[]
socket.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text);const handler=pending.get(data.id);if(handler){pending.delete(data.id);if(data.error){handler.reject(new Error(data.error.message))}else{handler.resolve(data.result)}}})
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const data=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw new Error(data.exceptionDetails.text);return data.result.value}
async function wait(expression){for(let i=0;i<600;i++){try{if(await evaluate(expression))return}catch(error){if(!/navigated|context|Cannot find/.test(error.message))throw error}await new Promise(r=>setTimeout(r,50))}throw new Error('Timed out: '+expression)}
async function click(expression){await wait(`!!(${expression})&&!(${expression}).disabled`);const point=await evaluate(`(()=>{const element=${expression};element.scrollIntoView({block:'center'});const r=element.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);await send('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});await send('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1})}
const button=text=>`Array.from(document.querySelectorAll('button')).find(b=>b.textContent===${JSON.stringify(text)})`
async function snapshot(name){if(!process.env.BRANDPROOF_SCREENSHOTS)return;const dir='node_modules/.cache/improvements';await mkdir(dir,{recursive:true});const data=await send('Page.captureScreenshot',{format:'png'});await writeFile(`${dir}/${name}.png`,Buffer.from(data.data,'base64'))}
try{
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.clearBrowserCookies')
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false})
  await send('Page.navigate',{url:origin});await wait(`!!document.querySelector('h1')`)
  await evaluate(`localStorage.clear()`);await send('Page.reload');await wait(`document.querySelector('.reviews-empty')?.textContent==='No reviews yet'`)
  await click(button('Try an editable example'))
  await wait(`document.querySelectorAll('.server-source').length===5&&!!document.querySelector('.live-poster img')&&!document.querySelector('.run-caption button').disabled`)
  assert.equal(await evaluate(`Array.from(document.querySelectorAll('.server-source .fact-status')).filter(n=>n.textContent==='Confirmed').length`),4)
  await wait(`document.querySelector('.workflow-readiness').textContent.includes('pending source')`)
  assert.match(await evaluate(`document.querySelector('#marketing-caption').value`),/Guaranteed results/)
  await snapshot('demo-readiness-desktop')
  await click(`document.querySelector('.confirm-source')`)
  await wait(`!document.querySelector('.confirm-source')`)
  await click(`document.querySelector('.run-caption button')`)
  await wait(`!!document.querySelector('.findings-list')&&!document.querySelector('.run-caption button').disabled`)
  assert.match(await evaluate(`document.querySelector('.findings-list').textContent`),/Potential promise/)
  assert.equal(await evaluate(`document.querySelector('.ai-consent input').checked`),false)
  const original=await evaluate(`document.querySelector('#marketing-caption').value`)
  await click(`Array.from(document.querySelectorAll('.unverified-draft button')).find(b=>b.textContent.startsWith('Copy to caption'))`)
  assert.notEqual(await evaluate(`document.querySelector('#marketing-caption').value`),original)
  assert.match(await evaluate(`document.querySelector('.caption-comparison > div:last-child pre').textContent`),/Guaranteed results/)
  assert.equal(await evaluate(`document.querySelector('.run-caption button').disabled`),true)
  await click(`document.querySelector('.caption-footer button')`)
  await wait(`document.querySelector('.live-review-status').textContent.includes('revision 4')`)
  await click(`document.querySelector('.run-caption button')`)
  await wait(`document.querySelectorAll('#review-history option').length===2&&!document.querySelector('.run-caption button').disabled`)
  await click(`document.querySelector('.document-import > summary')`)
  await evaluate(`(()=>{const bytes=Uint8Array.from(atob(${JSON.stringify(pdf)}),c=>c.charCodeAt(0));const transfer=new DataTransfer();transfer.items.add(new File([bytes],'acceptance-guidelines.pdf',{type:'application/pdf'}));const input=document.querySelector('.document-import input[type=file]');input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}))})()`)
  await click(button('Import as pending candidates'))
  await wait(`document.querySelectorAll('.server-source').length===8&&document.querySelector('.document-import').textContent.includes('3 candidates')`)
  assert.match(await evaluate(`document.querySelector('.document-citation').textContent`),/page 1/)
  for(let remaining=3;remaining>0;remaining--){await click(`document.querySelector('.confirm-source')`);await wait(`document.querySelectorAll('.confirm-source').length===${remaining-1}`)}
  await click(`document.querySelector('.alt-text-editor > summary')`)
  await wait(`!!document.querySelector('#poster-alt-text')&&!document.querySelector('#poster-alt-text').disabled`)
  await evaluate(`(()=>{const input=document.querySelector('#poster-alt-text');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,'Fictional workshop launch. Book for INR 599. The poster promises results and needs supporting evidence.');input.dispatchEvent(new Event('input',{bubbles:true}))})()`)
  await click(button('Save poster description'))
  await wait(`document.querySelector('.alt-text-editor').textContent.includes('Description saved as a new content revision')`)
  await click(`document.querySelector('.run-caption button')`)
  await wait(`document.querySelectorAll('#review-history option').length===3&&!document.querySelector('.run-caption button').disabled`)
  assert.match(await evaluate(`document.querySelector('.measured-checks').textContent`),/visual.*completed/s)
  assert.equal(await evaluate(`Array.from(document.querySelectorAll('.finding h4')).some(n=>n.textContent==='alt text')`),false)
  await click(`document.querySelector('a[href="#/insights"]')`)
  await wait(`!!document.querySelector('.insight-card')`)
  assert.match(await evaluate(`document.querySelector('.governance-insights').textContent`),/Insufficient sample/)
  await snapshot('governance-desktop')
  await click(`Array.from(document.querySelectorAll('.insight-card details')).find(n=>n.querySelector('a')?.getAttribute('href')?.includes('source_version=')).querySelector('summary')`)
  const linked=await evaluate(`Array.from(document.querySelectorAll('.insight-card a')).find(n=>n.getAttribute('href').includes('source_version=')).getAttribute('href')`)
  await click(`Array.from(document.querySelectorAll('.insight-card a')).find(n=>n.getAttribute('href').includes('source_version='))`)
  await wait(`!!document.querySelector('#review-history')&&document.querySelector('#review-history').value===new URLSearchParams(${JSON.stringify(linked.split('?')[1])}).get('run')`)
  await wait(`!!document.querySelector('.finding')`)
  const finding=new URLSearchParams(linked.split('?')[1]).get('finding')
  await wait(`document.activeElement?.id===${JSON.stringify('finding-'+finding)}`)
  for(const width of [390,320]){await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:true});assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true)}
  await evaluate(`document.getElementById(${JSON.stringify('finding-'+finding)}).scrollIntoView({block:'center'})`)
  await snapshot('historical-finding-mobile')
  const hash=await evaluate(`location.hash`)
  await send('Page.reload');await wait(`!!document.querySelector('.review-evidence')`)
  assert.equal(await evaluate(`location.hash`),hash)
  assert.deepEqual(errors,[])
  console.log('PASS expanded real demo/poster and pending source, server readiness guidance, explicit unverified draft/save/rerun, PDF import/quotes/confirmation, alt-text revision and measured checks, governance sample guard, historical finding/source links, responsive layout and same-session reload; no credentials persisted.')
}finally{await fetch('http://127.0.0.1:9223/json/close/'+target.id);socket.close()}
