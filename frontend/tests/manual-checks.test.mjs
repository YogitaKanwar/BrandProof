import {test} from 'node:test'
import assert from 'node:assert/strict'
import {incompleteChecks} from '../src/api/workflow.ts'
test('claim-risk review notes are required only for recorded incomplete screening, with legacy runs supported',()=>{
  const checks={exact_text:{status:'completed'},contextual:{status:'completed'}}
  assert.deepEqual(incompleteChecks({checks}),[])
  assert.deepEqual(incompleteChecks({checks:{...checks,claim_risk:{status:'partial'}}}),['claim_risk'])
  assert.deepEqual(incompleteChecks({checks:{...checks,claim_risk:{status:'completed'}}}),[])
})
test('reviewer notes cover exactly the incomplete required checks',()=>{
  assert.deepEqual(incompleteChecks({checks:{exact_text:{status:'completed'},contextual:{status:'unavailable'},poster:{status:'not_assessed'}}}),['contextual'])
  assert.deepEqual(incompleteChecks({checks:{exact_text:{status:'partial'},contextual:{status:'completed'},poster:{status:'partial',details:{asset_id:'real-poster'}}}}),['exact_text','poster'])
})
