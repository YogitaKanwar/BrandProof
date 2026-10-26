import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createReviewClient, deleteLocalReview } from '../src/api/reviews.ts'
afterEach(() => { delete globalThis.localStorage })
test('local delete persists and removes linked caption/reference while retaining other drafts', async () => {
  const values=new Map()
  globalThis.localStorage={getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}
  const client=createReviewClient()
  const first=(await client.create({title:'First',brand:'',brief:''})).data.reviews[0]
  const second=(await client.create({title:'Second',brand:'',brief:''})).data.reviews[0]
  values.set(`brandproof.development.caption.${first.id}`,'"copy"')
  const result=await deleteLocalReview(first.id)
  assert.equal(result.warning,'')
  assert.deepEqual((await createReviewClient().list()).data.reviews.map(review=>review.id),[second.id])
  assert.equal(values.has(`brandproof.development.caption.${first.id}`),false)
  globalThis.localStorage.setItem=()=>{throw new Error('Storage blocked')}
  await assert.rejects(deleteLocalReview(second.id),/Storage blocked/)
  assert.equal((await client.list()).data.reviews.length,1)
})
