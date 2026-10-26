import {test} from 'node:test'
import assert from 'node:assert/strict'
import {overlayBox} from '../src/api/posters.ts'
test('OCR overlay uses canonical image percentages at every responsive width',()=>{
  const box=overlayBox({x:100,y:50,width:200,height:40},1000,500)
  assert.deepEqual(box,{left:'10%',top:'10%',width:'20%',height:'8%'})
  assert.equal(overlayBox({x:-1,y:0,width:10,height:10},100,100),null)
  assert.equal(overlayBox({x:90,y:0,width:20,height:10},100,100),null)
  assert.equal(overlayBox({x:0,y:0,width:0,height:10},100,100),null)
})
