export interface AdvertisingProfile {jurisdiction:'IN'|'other'|'unknown';sector:'general'|'coaching'|'healthcare'|'finance'|'other'|'unknown';language:'en'|'other'|'unknown'}
export interface AdvertisingPack {id:string;version:string;source_title:string;source_url:string;retrieved_at:string;review_due:string;supported_scope:string;unsupported_scope:string;disabled_packs:{id:string;reason:string}[]}
export interface AdvertisingProfileOut {profile:AdvertisingProfile|null;source_revision:number;pack:AdvertisingPack}
export interface RegulatoryEvidence {id:string;clause:string;page:number;quote:string;interpretation:string;review_action:string;pack_id:string;pack_version:string;source_title:string;source_url:string;source_sha256:string;retrieved_at:string;jurisdiction:string;sector:string}
