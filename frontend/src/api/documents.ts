export interface DocumentCitation {document_id:string;filename:string;sha256:string;page_number:number;start:number;end:number;quote:string}
export interface GuidelineDocument {id:string;filename:string;sha256:string;created_at:string;status:string;scope:string;candidate_count:number;candidate_limit_reached:boolean;pages:{page_number:number;text:string;status:string;reason:string|null}[]}
