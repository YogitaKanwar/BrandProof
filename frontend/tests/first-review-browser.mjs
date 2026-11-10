// Real Chromium + API regression; credentials remain inside the browser.
import assert from 'node:assert/strict'
import {readFile, mkdir, writeFile} from 'node:fs/promises'

const url=process.env.BRANDPROOF_TEST_URL||'http://127.0.0.1:8021/#/demo'
const cdp='http://127.0.0.1:'+ (process.env.BRANDPROOF_CDP_PORT||'9223')
const mobile=process.env.BRANDPROOF_TEST_MOBILE==='1'
const exampleFirst=process.env.BRANDPROOF_EXAMPLE_FIRST==='1'
const slowSetup=process.env.BRANDPROOF_TEST_SLOW_SETUP!=='0'
const expectInitializationBug=process.env.BRANDPROOF_EXPECT_INIT_BUG==='1'
const reproducedInitializationBug=Symbol('reproduced initialization bug')
const firstReviewSmoke=process.env.BRANDPROOF_FIRST_REVIEW_SMOKE==='1'
const completedFirstReviewSmoke=Symbol('completed first review smoke')
const targetUrl=new URL(url)
const localTarget=['127.0.0.1','localhost'].includes(targetUrl.hostname)
const authorizedPreview=targetUrl.origin==='https://brandproof-round3-preview-20261102.onrender.com'&&process.env.BRANDPROOF_ALLOW_JUDGE_PREVIEW_TESTS==='1'&&exampleFirst&&!slowSetup&&!expectInitializationBug&&firstReviewSmoke
assert.ok(localTarget||authorizedPreview,'Hosted checks require the exact authorized judge preview and normal example-first smoke mode; timing regressions remain loopback-only')
const browser=await(await fetch(cdp+'/json/version')).json()
function protocol(socket){let id=0;const pending=new Map();socket.addEventListener('message',event=>{const data=JSON.parse(event.data),entry=pending.get(data.id);if(entry){pending.delete(data.id);if(data.error)entry.reject(new Error(data.error.message));else entry.resolve(data.result)}});return(method,params={})=>new Promise((resolve,reject)=>{const next=++id;pending.set(next,{resolve,reject});socket.send(JSON.stringify({id:next,method,params}))})}
const controlSocket=new WebSocket(browser.webSocketDebuggerUrl)
await new Promise(resolve=>controlSocket.addEventListener('open',resolve,{once:true}))
const control=protocol(controlSocket)
const {browserContextId}=await control('Target.createBrowserContext')
const {targetId}=await control('Target.createTarget',{url:'about:blank',browserContextId})
const target=(await(await fetch(cdp+'/json/list')).json()).find(row=>row.id===targetId)
const socket=new WebSocket(target.webSocketDebuggerUrl)
await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}))
const send=protocol(socket),exceptions=[]
let paused='',pausedCampaign='',pausedNetwork='',holdOneResponse=false,reviewPosts=0,captionClearPosts=0
const finished=new Set(),reviewRequests=new Set(),reviewStatuses=[]
socket.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.method==='Fetch.requestPaused'){if(holdOneResponse&&paused){void send('Fetch.continueResponse',{requestId:data.params.requestId});return}paused=data.params.requestId;pausedNetwork=data.params.networkId;pausedCampaign=new URL(data.params.request.url).pathname.split('/')[4]}if(data.method==='Runtime.exceptionThrown')exceptions.push(data.params.exceptionDetails.text);if(data.method==='Network.requestWillBeSent'&&data.params.request.method==='POST'&&data.params.request.url.endsWith('/reviews')){reviewPosts++;reviewRequests.add(data.params.requestId)}if(data.method==='Network.responseReceived'&&reviewRequests.has(data.params.requestId))reviewStatuses.push(data.params.response.status);if(data.method==='Network.loadingFinished')finished.add(data.params.requestId)})
socket.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.method==='Network.requestWillBeSent'&&data.params.request.method==='POST'&&data.params.request.url.endsWith('/caption/clear'))captionClearPosts++})
async function value(expression){const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error('Browser evaluation failed');return result.result.value}
async function wait(expression){const deadline=Date.now()+45000;while(Date.now()<deadline){if(await value(expression))return;await new Promise(resolve=>setTimeout(resolve,50))}throw new Error('Timed out: '+expression)}
const button=text=>`Array.from(document.querySelectorAll('button')).find(node=>node.textContent.trim()===${JSON.stringify(text)})`
async function click(expression){await wait(`!!(${expression})&&!(${expression}).disabled`);await value(`(${expression}).click()`)}
async function fill(selector,text){await value(`(()=>{const node=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(node.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(node,${JSON.stringify(text)});node.dispatchEvent(new Event('input',{bubbles:true}));node.dispatchEvent(new Event('change',{bubbles:true}))})()`)}
async function run(){const before=reviewPosts;await click(`document.querySelector('.run-caption button')`);await wait(`document.querySelector('.run-caption button').getAttribute('aria-busy')!=='true'`);assert.equal(await value(`document.querySelector('#caption-workflow-error')?.textContent||''`),'');assert.equal(reviewPosts,before+1);assert.ok(await value(`document.querySelectorAll('#review-history option').length>0`))}
async function freshCampaign(name){await click(`document.querySelector('a[href="#/new"]')`);await wait(`!!document.querySelector('#publication-date')`);await fill('#review-title',name);await fill('#publication-date','2026-11-12');await click(button('Continue'));await wait(`!!document.querySelector('#marketing-caption')`)}
const image=(await readFile(new URL('./fixtures/measured-poster.png',import.meta.url))).toString('base64')
async function pickPoster(){await value(`(()=>{const transfer=new DataTransfer();transfer.items.add(new File([Uint8Array.from(atob(${JSON.stringify(image)}),c=>c.charCodeAt(0))],'poster.png',{type:'image/png'}));const node=document.querySelector('.live-poster input[type=file]');node.files=transfer.files;node.dispatchEvent(new Event('change',{bubbles:true}))})()`);await wait(`!!document.querySelector('.poster-preview')&&document.querySelector('.poster-upload-status').textContent!=='Opening image…'`)}
async function concurrentEdit(text,id){await value(`(async()=>{const session=await(await fetch('/api/v1/demo-sessions/resume',{method:'POST',headers:{'X-BrandProof-Session':'resume'}})).json();const headers={Authorization:'Bearer '+session.actors.creator.access_token,'Content-Type':'application/json'},path='/api/v1/campaigns/'+${id?JSON.stringify(id):"location.hash.slice(9).split('?')[0]"};const campaign=await(await fetch(path,{headers})).json();const response=await fetch(path+'/caption',{method:'PUT',headers,body:JSON.stringify({expected_revision:campaign.content_revision,text:${JSON.stringify(text)}})});if(!response.ok)throw new Error('Concurrent test write failed')})()`)}
const evidence=new URL(process.env.BRANDPROOF_FIRST_REVIEW_EVIDENCE_URL||'../../docs/evidence/example-caption-init-20261110/'+(expectInitializationBug?'before-fix/':(slowSetup?'timing-regression/':'')+(mobile?'mobile-incognito/':'desktop-incognito/')),import.meta.url)
const expectedCaption='A cheap workshop on 2026-11-13. Book for INR 599. Guaranteed results in 30 days.'
const proof={freshIncognito:true,mobile,exampleFirst,setupTimingControlled:slowSetup,firstExample:null,refresh:null,staleResponsePreservedEdit:false}
async function screenshot(name){await mkdir(evidence,{recursive:true});const shot=await send('Page.captureScreenshot',{format:'png'});await writeFile(new URL(name+'.png',evidence),Buffer.from(shot.data,'base64'))}
try{
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable')
  await send('Emulation.setDeviceMetricsOverride',{width:mobile?390:1440,height:mobile?844:1000,deviceScaleFactor:1,mobile})
  await send('Page.navigate',{url});await click(`document.querySelector('.demo-cta')`);await wait(`!!document.querySelector('.reviews-empty')`)

  if(!exampleFirst){
  await freshCampaign('First caption review')
  await fill('#marketing-caption','Fictional caption. Book for INR 599.');await click(`document.querySelector('.caption-footer button')`);await wait(`!document.querySelector('.run-caption button').disabled`)
  await run()
  console.log('PASS first caption review without refresh')
  await pickPoster();await run()
  console.log('PASS upload and review without refresh')

  await freshCampaign('First poster review')
  await pickPoster();await click(button('Upload poster'));await wait(`document.querySelector('.poster-upload-status').textContent.includes('Poster saved privately')&&!document.querySelector('.poster-preview')`)
  await run()
  await value(`document.querySelector('.alt-text-editor').open=true`);await wait(`!document.querySelector('#poster-alt-text').disabled`)
  await fill('#poster-alt-text','Fictional test poster: black TEST text on a white background.');await click(button('Save poster description'));await wait(`document.querySelector('.alt-text-editor').textContent.includes('Description saved as a new content revision')`)
  await run()
  console.log('PASS first poster review and description revision without refresh')
  }

  await click(`document.querySelector('a.wordmark')`);await wait(`!!document.querySelector('.example-invitation')`)
  // Hold an actual setup request so the newly created card is opened before
  // preparation finishes. No API response, revision, or finding is fabricated.
  if(slowSetup){
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/*/sources',requestStage:'Request'}]})
  await click(button('Try an editable example'))
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused,'Example setup reached the controlled timing boundary')
  const earlyLink=`Array.from(document.querySelectorAll('.review-row h2 a')).find(node=>node.textContent==='Workshop Campaign')`
  if(await value(`!!(${earlyLink})`)){
    await click(earlyLink);await wait(`!!document.querySelector('#marketing-caption')`)
    assert.equal(await value(`document.querySelector('#marketing-caption').value`),'')
  }else{
    assert.match(await value(`document.querySelector('main .loading').textContent`),/Preparing your example/)
    // Also attempt a direct route during preparation: the editor must stay
    // unmounted until the complete acknowledged snapshot is available.
    await value(`location.hash=${JSON.stringify('/review/'+pausedCampaign)}`)
    await wait(`document.querySelector('main .loading')?.textContent.includes('Preparing your example')`)
    assert.equal(await value(`!!document.querySelector('#marketing-caption')`),false)
  }
  await send('Fetch.disable')
  }else await click(button('Try an editable example'))
  await wait(`document.querySelector('.notice')?.textContent.includes('Fictional example ready')&&!!document.querySelector('.live-poster img')&&!document.querySelector('.run-caption button').disabled`)
  if(expectInitializationBug){
    assert.equal(await value(`document.querySelector('#marketing-caption').value`),'')
    assert.match(await value(`document.querySelector('.campaign-revisions').textContent`),/Content revision 3/)
    await value(`document.querySelector('#marketing-caption').scrollIntoView({block:'center'})`)
    await screenshot('empty-editor-before-review')
    await click(`document.querySelector('.run-caption button')`)
    await wait(`!!document.querySelector('#caption-workflow-error')&&document.querySelector('.run-caption button').disabled`)
    assert.equal(await value(`document.querySelector('.caption-snapshot').textContent`),expectedCaption)
    await screenshot('empty-editor-saved-revision-3-conflict')
    await click(button('Use saved version'));await run()
    await writeFile(new URL('results.json',evidence),JSON.stringify({baseline:'Committed ReviewWorkspace.tsx without initialization gates; remaining candidate frontend unchanged',initialCaption:'',serverContentRevision:3,savedCaption:expectedCaption,firstReviewBlocked:true,explicitUseSavedVersionThenReviewStatus:reviewStatuses.at(-1)},null,2)+'\n')
    console.log('REPRODUCED baseline defect: empty mounted editor, saved revision 3, first review blocked, explicit Use saved version recovers')
    throw reproducedInitializationBug
  }
  assert.equal(await value(`document.querySelector('#marketing-caption').value`),expectedCaption)
  assert.match(await value(`document.querySelector('.campaign-revisions').textContent`),/Content revision 3/)
  await value(`document.querySelector('#marketing-caption').scrollIntoView({block:'center'})`)
  await screenshot('example-caption-hydrated')
  await run()
  proof.firstExample={caption:await value(`document.querySelector('#marketing-caption').value`),savedDetails:await value(`document.querySelector('.campaign-revisions').textContent`),summary:await value(`document.querySelector('.review-run-summary').textContent`),httpStatus:reviewStatuses.at(-1),manualReconciliation:false,captionClearPosts}
  assert.equal(proof.firstExample.httpStatus,201)
  assert.equal(captionClearPosts,0)
  await screenshot('first-review-results')
  console.log(slowSetup?'PASS first example review after slow setup and early navigation attempt':'PASS normal example-first workflow: saved caption loaded automatically and first review returned 201')
  if(firstReviewSmoke){
    await send('Page.reload')
    await wait(`document.querySelector('#marketing-caption')?.value===${JSON.stringify(expectedCaption)}&&!document.querySelector('.run-caption button').disabled`)
    await run()
    proof.refresh={caption:expectedCaption,httpStatus:reviewStatuses.at(-1),manualReconciliation:false}
    proof.reviewStatuses=reviewStatuses;proof.uncaughtExceptions=exceptions.length
    proof.storageEmpty=await value(`localStorage.length===0&&sessionStorage.length===0`)
    assert.equal(proof.storageEmpty,true);assert.deepEqual(exceptions,[])
    await writeFile(new URL('results.json',evidence),JSON.stringify(proof,null,2)+'\n')
    console.log('PASS same-session refresh/recovery and rerun; no browser exceptions or persisted credentials')
    throw completedFirstReviewSmoke
  }

  await fill('#marketing-caption','')
  await value(`document.querySelector('.caption-reconcile').open=true`)
  await click(button('Compare with saved version'))
  await wait(`!!document.querySelector('.caption-snapshot')&&!document.querySelector('#marketing-caption').disabled`)
  assert.equal(await value(`document.querySelector('#marketing-caption').value`),'')
  assert.equal(await value(`document.querySelector('.run-caption button').disabled`),true)
  assert.equal(captionClearPosts,0)
  await fill('#marketing-caption',expectedCaption)
  console.log('PASS an unsaved empty edit survives comparison and is never sent as caption deletion')

  const exampleId=await value(`location.hash.slice(9).split('?')[0]`)
  paused=''
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/'+exampleId,requestStage:'Response'}]})
  await send('Page.reload')
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused,'Fresh opening read reached the controlled timing boundary')
  await wait(`document.querySelector('main .loading')?.textContent.includes('Loading saved content')`)
  assert.equal(await value(`!!document.querySelector('#marketing-caption')||!!document.querySelector('.run-caption button')`),false)
  await screenshot('saved-content-loading')
  await send('Fetch.disable')
  await wait(`document.querySelector('#marketing-caption')?.value===${JSON.stringify(expectedCaption)}&&!document.querySelector('.run-caption button').disabled`)
  await run()
  proof.refresh={caption:expectedCaption,httpStatus:reviewStatuses.at(-1),manualReconciliation:false}
  console.log('PASS refresh waits for saved content and hydrates revision 3 without manual reconciliation')

  // Hold the old opening response, leave, load a newer snapshot, then edit.
  // Releasing the genuine old bytes must neither replace the draft nor its cache.
  await click(`document.querySelector('a.wordmark')`);await wait(`!!document.querySelector('.example-invitation')`)
  paused='';holdOneResponse=true
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/'+exampleId,requestStage:'Response'}]})
  await value(`location.hash='/review/'+${JSON.stringify(exampleId)}`)
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused)
  const oldResponse=paused,oldNetwork=pausedNetwork
  await click(`document.querySelector('a.wordmark')`);await wait(`!!document.querySelector('.example-invitation')`)
  await concurrentEdit('New saved snapshot after leaving the old opening request.',exampleId)
  await value(`location.hash='/review/'+${JSON.stringify(exampleId)}`)
  await wait(`document.querySelector('#marketing-caption')?.value==='New saved snapshot after leaving the old opening request.'`)
  await fill('#marketing-caption','My unsaved edit must survive the late response.')
  await send('Fetch.continueResponse',{requestId:oldResponse})
  for(const deadline=Date.now()+10000;!finished.has(oldNetwork)&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(finished.has(oldNetwork))
  await value(`new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`)
  assert.equal(await value(`document.querySelector('#marketing-caption').value`),'My unsaved edit must survive the late response.')
  assert.equal(await value(`document.querySelector('.run-caption button').disabled`),true)
  await send('Fetch.disable');holdOneResponse=false
  await click(`document.querySelector('.caption-footer button')`);await wait(`!document.querySelector('.run-caption button').disabled`);await run()
  proof.staleResponsePreservedEdit=true
  console.log('PASS old opening response cannot replace a newer unsaved edit; explicit save and review succeed')

  await click(`document.querySelector('a.wordmark')`);await wait(`!!document.querySelector('.example-invitation')`)
  paused=''
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/'+exampleId,requestStage:'Request'}]})
  await value(`location.hash='/review/'+${JSON.stringify(exampleId)}`)
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused)
  await send('Fetch.failRequest',{requestId:paused,errorReason:'ConnectionFailed'});await send('Fetch.disable')
  await wait(`!!(${button('Retry loading content')})`)
  assert.equal(await value(`!!document.querySelector('#marketing-caption')`),false)
  await click(button('Retry loading content'));await wait(`document.querySelector('#marketing-caption')?.value==='My unsaved edit must survive the late response.'`)
  await run()
  console.log('PASS failed opening read offers retry and does not expose a fake empty editable caption')

  // A genuine concurrent edit must still block review submission and preserve
  // the visible text until the user explicitly reconciles it.
  const original=await value(`document.querySelector('#marketing-caption').value`)
  const before=reviewPosts
  await value(`(async()=>{const session=await(await fetch('/api/v1/demo-sessions/resume',{method:'POST',headers:{'X-BrandProof-Session':'resume'}})).json();const headers={Authorization:'Bearer '+session.actors.creator.access_token,'Content-Type':'application/json'},path='/api/v1/campaigns/'+location.hash.slice(9).split('?')[0];const campaign=await(await fetch(path,{headers})).json();const response=await fetch(path+'/caption',{method:'PUT',headers,body:JSON.stringify({expected_revision:campaign.content_revision,text:'Fictional concurrent edit.'})});if(!response.ok)throw new Error('Concurrent test write failed')})()`)
  await click(`document.querySelector('.run-caption button')`);await wait(`!!document.querySelector('#caption-workflow-error')&&document.querySelector('.run-caption button').getAttribute('aria-busy')!=='true'`)
  assert.equal(reviewPosts,before);assert.equal(await value(`document.querySelector('#marketing-caption').value`),original)
  assert.equal(await value(`document.querySelector('.caption-reconcile').open&&document.querySelector('.run-caption button').disabled`),true)
  await screenshot('conflict-recovery-action')
  await click(button('Compare saved version'))
  await wait(`document.activeElement===document.querySelector('#caption-reconciliation summary')`)
  assert.match(await value(`document.querySelector('.caption-snapshot').textContent`),/Fictional concurrent edit/)
  await screenshot('saved-version-comparison')
  await click(button('Keep my text'))
  assert.equal(await value(`!!document.querySelector('#caption-workflow-error')`),false)
  assert.equal(await value(`document.querySelector('.run-caption button').disabled`),true)
  await click(`document.querySelector('.caption-footer button')`);await wait(`!document.querySelector('.run-caption button').disabled`);await run()
  console.log('PASS real concurrent edit blocked; explicit keep/save/rerun succeeds')

  await concurrentEdit('Fictional saved caption chosen explicitly.')
  await click(`document.querySelector('.run-caption button')`);await wait(`!!document.querySelector('#caption-workflow-error button')&&!document.querySelector('.run-caption button').getAttribute('aria-busy').includes('true')`)
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true})
  await value(`document.querySelector('#caption-workflow-error').scrollIntoView({block:'center'})`)
  assert.equal(await value(`document.documentElement.scrollWidth<=innerWidth+1`),true)
  await screenshot('conflict-recovery-mobile')
  await click(button('Compare saved version'));await wait(`document.activeElement===document.querySelector('#caption-reconciliation summary')`)
  await click(button('Use saved version'))
  assert.equal(await value(`document.querySelector('#marketing-caption').value`),'Fictional saved caption chosen explicitly.')
  await run()
  console.log('PASS mobile comparison and explicit saved-version recovery')
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false})

  // Change the real server revision after preflight, before the actual POST.
  paused=''
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/*/reviews',requestStage:'Request'}]})
  await click(`document.querySelector('.run-caption button')`)
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused,'Review POST reached the controlled timing boundary')
  await concurrentEdit('Fictional edit between preflight and review POST.')
  await send('Fetch.disable')
  await wait(`!!document.querySelector('#caption-workflow-error button')&&document.querySelector('.run-caption button').getAttribute('aria-busy')!=='true'`)
  assert.equal(await value(`document.querySelector('.run-caption button').disabled`),true)
  await click(button('Compare saved version'));await wait(`document.activeElement===document.querySelector('#caption-reconciliation summary')`)
  assert.match(await value(`document.querySelector('.caption-snapshot').textContent`),/between preflight/)
  await click(button('Use saved version'));await run()
  console.log('PASS genuine review POST 409 offers comparison and explicit recovery')

  await click(`document.querySelector('a.wordmark')`);await wait(`!!document.querySelector('.example-invitation')`)
  paused=''
  await send('Fetch.enable',{patterns:[{urlPattern:'*/api/v1/campaigns/*/sources',requestStage:'Request'}]})
  await click(button('Try an editable example'))
  for(const deadline=Date.now()+10000;!paused&&Date.now()<deadline;)await new Promise(resolve=>setTimeout(resolve,25))
  assert.ok(paused)
  await send('Fetch.failRequest',{requestId:paused,errorReason:'ConnectionFailed'});await send('Fetch.disable')
  await wait(`document.querySelector('.notice')?.textContent.includes('Example setup stopped')&&!!document.querySelector('#marketing-caption')`)
  assert.equal(await value(`!!document.querySelector('main .loading')`),false)
  await fill('#marketing-caption','Explicitly completed caption after interrupted example setup.');await click(`document.querySelector('.caption-footer button')`);await wait(`!document.querySelector('.run-caption button').disabled`);await run()
  console.log('PASS interrupted setup exposes the saved partial campaign and allows explicit completion')
  assert.deepEqual(exceptions,[])
  assert.equal(await value(`localStorage.length===0&&sessionStorage.length===0`),true)
  proof.reviewStatuses=reviewStatuses;proof.uncaughtExceptions=exceptions.length;proof.storageEmpty=true
  await writeFile(new URL('results.json',evidence),JSON.stringify(proof,null,2)+'\n')
}catch(error){if(error!==reproducedInitializationBug&&error!==completedFirstReviewSmoke)throw error}finally{await control('Target.disposeBrowserContext',{browserContextId});socket.close();controlSocket.close()}
