import {test} from 'node:test'
import assert from 'node:assert/strict'
import {copyCandidate} from '../src/draftSuggestion.ts'
test('explicit unverified copy uses code points, preserves surrounding copy and refuses stale text',()=>{
  const f={location:{asset:'caption',start:2,end:12,quote:'Guaranteed'},unverified_draft_suggestion:'Explore'}
  assert.equal(copyCandidate('🚀 Guaranteed outcomes',f),'🚀 Explore outcomes')
  assert.throws(()=>copyCandidate('A changed caption',f),/no longer matches/)
  assert.throws(()=>copyCandidate('🚀 Guaranteed outcomes',{...f,location:{...f.location,asset:'poster'}}))
})
