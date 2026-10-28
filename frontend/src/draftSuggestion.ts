import type {Finding} from './api/reviewRuns'

export function copyCandidate(caption:string,finding:Finding):string {
  const {start,end,quote,asset}=finding.location
  const points=Array.from(caption)
  if(asset!=='caption'||start===null||end===null||!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<=start||end>points.length||points.slice(start,end).join('')!==quote||!finding.unverified_draft_suggestion?.trim())throw new Error('The saved excerpt no longer matches. Reconcile or run a new review.')
  const draft=points.slice(0,start).join('')+finding.unverified_draft_suggestion+points.slice(end).join('')
  if(Array.from(draft).length>20000)throw new Error('This draft exceeds the caption limit. Edit it manually.')
  return draft
}
