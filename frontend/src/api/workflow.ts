export type DemoRole='owner'|'creator'|'reviewer'
export interface Snapshot {expected_content_revision:number;expected_source_revision:number}
export interface Revision {revision:number;caption:string;created_at:string}
export interface Comment {id:string;campaign_id:string;review_id:string|null;actor_id:string;actor_role:string;content_revision:number;source_revision:number;text:string;created_at:string}
export interface FindingDecision {id:string;review_id:string;finding_id:string;version:number;actor_id:string;decision:'dismiss'|'exception'|'reopen';reason:string;created_at:string}
export interface ReviewRequest {id:string;campaign_id:string;review_id:string;requested_by:string;created_at:string}
export interface Approval {id:string;campaign_id:string;review_id:string;request_id:string;reviewer_id:string;content_revision:number;source_revision:number;decision:string;reason:string;coverage_mode:string;manual_checks:Record<string,string>;decision_snapshot:Record<string,string>;created_at:string;is_current:boolean}
export interface Receipt {campaign_id:string;content_revision:number;source_revision:number;readiness:'not_approved'|'approved'|'approved_with_manual_checks'|'changes_requested'|'stale';scope:string;automated_review_status:string|null;checks:Record<string,unknown>;sources_used:Record<string,unknown>[];requests:ReviewRequest[];approvals:Approval[];finding_decisions:{finding_id:string;decision_id:string;decision:string;reason:string;actor_id:string;version:number}[];notice:string}
export function incompleteChecks(run:import('./reviewRuns.ts').ReviewOut){
  const required=['exact_text','contextual',...(run.checks.poster?.details?.asset_id ? ['poster']:[]),...(run.checks.claim_risk ? ['claim_risk']:[])]
  return required.filter(name=>run.checks[name]?.status!=='completed')
}
