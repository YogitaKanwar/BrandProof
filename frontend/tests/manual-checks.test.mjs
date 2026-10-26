import {test} from 'node:test'
import assert from 'node:assert/strict'
import {incompleteChecks} from '../src/api/workflow.ts'
test('reviewer notes cover exactly the incomplete required checks',()=>{
  assert.deepEqual(incompleteChecks({checks:{exact_text:{status:'completed'},contextual:{status:'unavailable'},poster:{status:'not_assessed'}}}),['contextual'])
  assert.deepEqual(incompleteChecks({checks:{exact_text:{status:'partial'},contextual:{status:'completed'},poster:{status:'partial',details:{asset_id:'real-poster'}}}}),['exact_text','poster'])
})
