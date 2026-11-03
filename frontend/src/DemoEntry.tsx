import './DemoEntry.css'

export default function DemoEntry({busy,restoring,error,status,onTry,onSample,onLocal,onRetry,simple=false,hasSession=false}:{busy:boolean;restoring:boolean;error:string;status:string;onTry:()=>void;onSample:()=>void;onLocal:()=>void;onRetry:()=>void;simple?:boolean;hasSession?:boolean}) {
  return <main className="demo-entry" id="main">
    <section className="demo-story" aria-labelledby="demo-title">
      <a className="demo-wordmark" href="#/"><span aria-hidden="true">B</span>BrandProof</a>
      <div className="demo-story-content"><span className="demo-eyebrow">EVIDENCE BEFORE EVERY PUBLISH</span>
        <h1 id="demo-title">Your brand.<br/>Every claim.<br/><em>Accounted for.</em></h1>
        <p>Bring your references, marketing content and human decisions into one clear review workspace.</p>
        {!simple&&<div className="demo-evidence" aria-label="Fictional sample preview"><div><span>FICTIONAL SAMPLE REFERENCE</span><strong>Workshop price · INR 899</strong></div><span aria-hidden="true">↕</span><div><span>MARKETING CONTENT</span><strong>Book for INR 599.</strong></div><p>What changed? Run the review to find out.</p></div>}
      </div><small>Human judgment stays yours.</small>
    </section>
    <section className="demo-access" aria-labelledby="access-title" aria-busy={busy}>
      <div className="demo-access-inner"><span className="demo-tag">INTERACTIVE DEMO</span><h2 id="access-title">Meet your next <br/>review workspace.</h2><p className="demo-intro">Explore BrandProof in your own isolated sandbox. No account or password needed.</p>
        <button className="primary demo-cta" type="button" disabled={busy} onClick={onTry}>{busy&&<span className="spinner" aria-hidden="true"/>}{restoring?'Restoring your session…':busy?'Preparing your workspace…':hasSession?'Continue Demo':'Try Interactive Demo'}<span aria-hidden="true">↗</span></button>
        {!simple&&<button className="demo-sample" type="button" disabled={busy} onClick={onSample}>Explore Sample Review <span aria-hidden="true">→</span></button>}
        <p className="demo-explore">References → Content → Results → Human Review</p>
        {(error||status)&&<div className={error?'error demo-entry-message':'demo-entry-message'} role={error?'alert':'status'}>{error||status}{error&&<button type="button" disabled={busy} onClick={onRetry}>Retry session recovery</button>}</div>}
        <details className="demo-recovery"><summary>Session &amp; recovery</summary>
          <p>Saved demo work resumes in this browser for up to 24 hours.</p>
          <button className="demo-local" type="button" disabled={busy} onClick={onLocal}>Open local drafts</button>
        </details>
      </div>
    </section>
  </main>
}
