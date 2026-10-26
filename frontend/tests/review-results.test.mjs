import { test } from 'node:test'
import assert from 'node:assert/strict'
import { codePointExcerpt, isReview } from '../src/api/reviewRuns.ts'
test('backend offsets use Unicode code points rather than UTF-16 indices',()=> {
  assert.equal(codePointExcerpt('🎉 INR 599',2,9),'INR 599')
  assert.equal(codePointExcerpt('Caption',null,null),null)
  assert.equal(codePointExcerpt('Caption',-1,2),null)
  assert.equal(codePointExcerpt('Caption',0,99),null)
})
test('invalid result envelopes are rejected',()=> {
  assert.equal(isReview({status:'completed',readiness:'approved'}),false)
  assert.equal(isReview(null),false)
})
