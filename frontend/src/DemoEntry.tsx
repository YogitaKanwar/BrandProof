import { useState } from 'react'
import './DemoEntry.css'

export default function DemoEntry({busy,restoring,error,status,onTry,onSample,onLocal,onRetry}:{busy:boolean;restoring:boolean;error:string;status:string;onTry:()=>void;onSample:()=>void;onLocal:()=>void;onRetry:()=>void}) {
  const [copied,setCopied]=useState('')
  async function copy(role:string) {
    try { await navigator.clipboard.writeText(`BrandProof Demo ${role} — synthetic guest role; no password required. Start at ${location.origin}.`);setCopied(`${role} access instructions copied.`) }
    catch {setCopied('Copy is unavailable. Select the access instructions below to copy them manually.')}
  }
  return <main className="demo-entry" id="main">
    <section className="demo-story" aria-labelledby="demo-title">
      <a className="demo-wordmark" href="#/"><span aria-hidden="true">B</span>BrandProof</a>
      <div className="demo-story-content"><span className="demo-eyebrow">EVIDENCE BEFORE EVERY PUBLISH</span>
        <h1 id="demo-title">Your brand.<br/>Every claim.<br/><em>Accounted for.</em></h1>
        <p>Bring your references, marketing content and human decisions into one clear review workspace.</p>
        <div className="demo-evidence" aria-label="Fictional sample preview"><div><span>FICTIONAL SAMPLE REFERENCE</span><strong>Workshop price · INR 899</strong></div><span aria-hidden="true">↕</span><div><span>MARKETING CONTENT</span><strong>Book for INR 599.</strong></div><p>What changed? Run the review to find out.</p></div>
      </div><small>Fictional material. Real review engine. Human judgment stays yours.</small>
    </section>
    <section className="demo-access" aria-labelledby="access-title" aria-busy={busy}>
      <div className="demo-access-inner"><span className="demo-tag">INTERACTIVE DEMO</span><h2 id="access-title">Meet your next <br/>review workspace.</h2><p className="demo-intro">Explore BrandProof in your own isolated sandbox. No account or password needed.</p>
        <button className="primary demo-cta" type="button" disabled={busy} onClick={onTry}>{busy&&<span className="spinner" aria-hidden="true"/>}{restoring?'Restoring your session…':busy?'Preparing your workspace…':'Try Interactive Demo'}<span aria-hidden="true">↗</span></button>
        <button className="demo-sample" type="button" disabled={busy} onClick={onSample}>Explore Sample Review <span aria-hidden="true">→</span></button>
        <p className="demo-explore">References → Content → Results → Human Review</p>
        {(error||status)&&<div className={error?'error demo-entry-message':'demo-entry-message'} role={error?'alert':'status'}>{error||status}{error&&<button type="button" disabled={busy} onClick={onRetry}>Retry session recovery</button>}</div>}
        <section className="demo-credentials" aria-labelledby="credentials-title"><h3 id="credentials-title">Demo Credentials</h3><p>Passwordless public guest access. These roles are synthetic and do not verify a person’s identity.</p>
          {['Creator','Reviewer'].map(role=><div className="demo-role" key={role}><div><strong>Demo {role}</strong><small>{role==='Creator'?'Edit content and request human review.':'Inspect evidence and record review decisions.'}</small></div><button type="button" onClick={()=>void copy(role)} aria-label={`Copy Demo ${role} access instructions`}>Copy</button></div>)}
          <p className="demo-role-note">Choose actions labelled Creator or Reviewer in the workspace. Source setup uses the sandbox’s synthetic Owner role. No administrative access.</p><p className="demo-copy-status" role="status">{copied}</p>
        </section>
        <p className="demo-privacy">Saved demo work resumes in this browser for up to 24 hours. Use fictional material only. AI is optional and requires your consent; OCR and other checks report actual server availability.</p>
        <button className="demo-local" type="button" disabled={busy} onClick={onLocal}>Open local drafts</button>
      </div>
    </section>
  </main>
}
