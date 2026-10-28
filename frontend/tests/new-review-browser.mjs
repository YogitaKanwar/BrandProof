// Dedicated disposable Chrome profile on :9223; never reads or prints tokens.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
const localBundle=process.env.BRANDPROOF_TEST_BUNDLE ? (await readFile(process.env.BRANDPROOF_TEST_BUNDLE)).toString('base64') : null
const url=process.env.BRANDPROOF_TEST_URL || 'http://127.0.0.1:4180/'
const target=await(await fetch('http://127.0.0.1:9223/json/new?about:blank',{method:'PUT'})).json()
const socket=new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve);socket.addEventListener('error',reject)})
let sequence=0,campaignPosts=0,sessionPosts=0
const pending=new Map(),errors=[]
socket.addEventListener('message',event=>{
  const data=JSON.parse(event.data)
  if(data.method==='Fetch.requestPaused' && localBundle)void send('Fetch.fulfillRequest',{requestId:data.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/javascript'}],body:localBundle}).catch(()=>errors.push('Test bundle interception failed'))
  if(data.method==='Runtime.exceptionThrown')errors.push('Uncaught browser exception')
  if(data.method==='Network.requestWillBeSent' && data.params.request.method==='POST'){
    const path=new URL(data.params.request.url).pathname
    if(path==='/api/v1/campaigns')campaignPosts++
    if(path==='/api/v1/demo-sessions')sessionPosts++
  }
  const handler=pending.get(data.id)
  if(handler){pending.delete(data.id);if(data.error)handler.reject(new Error(data.error.message));else handler.resolve(data.result)}
})
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error('Browser expression failed');return result.result.value}
async function wait(expression){for(let attempt=0;attempt<2000;attempt++){if(await evaluate(expression))return;await new Promise(resolve=>setTimeout(resolve,50))}throw new Error(`Timed out: ${expression}`)}
try{
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable')
  await send('Network.clearBrowserCookies')
  if(localBundle)await send('Fetch.enable',{patterns:[{urlPattern:'*/assets/index-*.js',requestStage:'Request'}]})
  // Simulates only failed health GETs. All session/campaign writes hit the real API.
  if(process.env.BRANDPROOF_TEST_COLD)await send('Page.addScriptToEvaluateOnNewDocument',{source:`{const original=window.fetch;let failures=0;window.fetch=(url,options)=>String(url).endsWith('/api/v1/health')&&failures++<2?Promise.resolve(new Response('Starting',{status:502})):original(url,options)}`})
  await send('Page.navigate',{url})
  await wait(`!!document.querySelector('h1')`)
  await evaluate(`localStorage.clear();location.reload()`)
  if(process.env.BRANDPROOF_TEST_COLD)await wait(`document.querySelector('main')?.innerText.includes('Starting the review service')`)
  await wait(`!!document.querySelector('.reviews-empty')`)
  await evaluate(`document.querySelector('.page-heading .primary').click()`)
  await wait(`!!document.querySelector('#publication-date')`)
  await evaluate(`{const set=(selector,value)=>{const element=document.querySelector(selector);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(element,value);element.dispatchEvent(new Event('input',{bubbles:true}));element.dispatchEvent(new Event('change',{bubbles:true}))};set('#review-title','New Review availability check');set('#publication-date','2026-11-12')}`)
  await evaluate(`document.querySelector('.campaign-form').requestSubmit()`)
  await wait(`location.hash.startsWith('#/review/') && !!document.querySelector('#sources-heading')`)
  const reviewHash=await evaluate('location.hash')
  assert.equal(campaignPosts,1);assert.equal(sessionPosts,1)
  await evaluate('location.reload()')
  await wait(`document.querySelector('.connection-status summary')?.textContent==='Demo connected' && !!document.querySelector('#sources-heading')`)
  assert.equal(await evaluate('location.hash'),reviewHash)
  assert.equal(campaignPosts,1);assert.equal(sessionPosts,1)
  assert.equal(await evaluate(`Object.keys(localStorage).some(key=>/token/i.test(key))`),false)
  assert.deepEqual(errors,[])
  console.log('PASS New Review: real session and campaign creation, Sources workspace, refresh persistence, exactly one creation, no token storage or uncaught exceptions'+(process.env.BRANDPROOF_TEST_COLD?'; simulated cold-start health failures recovered':''))
}finally{await fetch(`http://127.0.0.1:9223/json/close/${target.id}`);socket.close()}
