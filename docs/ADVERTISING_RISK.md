# Advertising-risk screening: implementation and limits

Status: implemented and tested locally, 31 October 2026. Not publicly accepted. This complements the three submitted Round 3 improvements.

## What happens

An owner selects jurisdiction, sector and content language in the campaign's advertising profile. The existing publication date applies. A saved profile is a new immutable `legal_profile_versions` row, advances `source_revision`, and invalidates older review/approval currentness. Only owner actors can write; expected content/source revisions, campaign locks and workspace access checks apply.

Selected English claim signals reuse local `claim-risk-v2` findings. An applicable India profile attaches `regulatory_evidence` to the same finding ID rather than producing a duplicate alert. Brand `evidence` remains separate. Caption spans use code points; poster findings retain actual OCR identity, confidence and coordinates. Detection requests evidence; it does not establish falsity, missing brand approval or a legal breach.

The built-in pack, `backend/brandproof/legal_pack.json`, freezes an official source, a brief verified quotation, rule ID/clause/page, interpretation, reviewer action, instrument identity, retrieval/effective dates, source digest and pack version. The citation is CCPA 2022 guideline 12(a), PDF page 10. Supporting quote: “shall be capable of substantiation”. The official downloaded PDF is retained at `backend/tests/fixtures/ccpa-2022.pdf`; a regression verifies its checksum and quotation against the pack. A source citation is not proof that the heuristic understands every claim.

Official source: [2022 CCPA Gazette notification](https://consumeraffairs.gov.in/public/upload/files/CCPA_Notification_1732707665.pdf). Retrieval/check date: 31 October 2026. SHA-256: `d97e8ab663ebdab8b3e2139465013da14f65dead4fa3e3aa8023df8617fe32f1`.

The [Department of Consumer Affairs Acts index](https://consumeraffairs.gov.in/pages/consumer-protection-acts) and CCPA listings were consulted for current references. This is a limited frozen pack, not proof that every amendment or applicable law has been captured. Pack source review is due 1 December 2026. The date is an application maintenance deadline, not a statutory expiry. Past that deadline, fresh screening pauses with partial coverage and no new regulation annotations; older assessed snapshots become stale. Fresh paused reviews remain explicitly available for manual assessment.

## Applicability and outcomes

| Condition | Outcome |
| --- | --- |
| Profile absent or any selection unknown | Not assessed; no inferred jurisdiction |
| Jurisdiction outside India | India pack not applicable; no other jurisdiction assessed |
| Other/mixed content language selected | Not assessed; English matching only |
| Publication before verified effective date / after a configured end date | Pack not applicable; no substitute legal verdict |
| India, English, general advertising | Selected signals checked; findings/limits keep coverage partial |
| Coaching, healthcare, finance or other sector | General substantiation check only; partial because sector regulation is not implemented |
| OCR uncertainty, scan limits, expired source-review window | Partial; manual review required |

The final coaching instrument linked by [PIB's November 2024 announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2073013&lang=2&reg=48) could not be retrieved from its official document host in this session. Its pack stays disabled. A draft or press summary is not substituted for verified final clause evidence. Selection/placement promises can still trigger the general 2022 substantiation prompt; the UI does not claim a coaching-specific legal verdict.

Uploaded brand PDFs cannot become trusted legal packs. Owner-confirmed brand wording does not waive regulation. ASCI codes are not presented as statutes. Other jurisdictions/languages, complete consumer-law analysis, sector rules, disclaimer typography, general truth and metaphor understanding are outside coverage.

## Reviewer and receipt behaviour

Every new review stores the selected profile, profile-version ID, publication date, complete pack and digest under `checks.advertising_risk.details`. Historical snapshots are not rewritten. Installing changed pack content invalidates currentness, even when an unchanged caption/source revision would otherwise look current. A profile update uses the existing source revision, so existing race guards continue to apply. Legacy runs retain their original coverage and are displayed as not legally assessed.

Unresolved claim findings still require explicit reasoned dismissal/exception or content correction and rerun. Reasons should reference supporting material, audience and conditions; supplied evidence is a human attestation, not independently verified truth. Incomplete `advertising_risk` coverage adds an exact required reviewer-note key in API validation, readiness, frontend controls and approval guards. Manual notes never change automated coverage into a pass. A recorded exception does not waive law.

Approval readback now includes `advertising_snapshot` from that approval's own review, so a later pack/profile cannot replace its historical scope. Receipts remain human decision records, not legal certification. Regulatory Insights groups retain rule/pack identity and never produce a suggestion to weaken regulation.

## Maintenance and API

- Public, read-only `GET /api/v1/advertising-risk-pack` returns the installed public pack and digest.
- Workspace-scoped `GET /api/v1/campaigns/{id}/advertising-profile` reads current selections.
- Owner `PUT` at the same path accepts both expected revisions plus jurisdiction/sector/language; arbitrary source URLs, quotations or pack edits are rejected by the strict request schema.
- Schema step `0006_advertising_profile` adds one table without altering legacy columns. Rollback to an old executable after applying this step is not automatic: this app deliberately refuses unknown schema versions. Retain data and use a compatible application or forward repair.
- To update a pack, verify official final text and any amendments, retain evidence, update metadata/interpretation/limits and version, rerun the evaluation matrix, then release the frontend/API pair. The digest is computed from complete pack content; do not change a citation without treating it as a new reference snapshot.

## Evaluated examples

Thirteen labelled caption fixtures cover six expected signals and seven controls: time-bound/absolute promises, selection/placement promises, disclaimers, Unicode offsets, negation, quoted avoidance instructions, hedging, refund guarantees, ordinary delivery and metaphors. All matched their expected bounded outcomes locally. This is a small developer fixture set, not a representative legal benchmark or accuracy claim.

Additional tests cover five applicability profiles, unset profiles, permissions, stale writes, workspace isolation, immutable snapshots after restart, source-review expiry, installed-pack changes, approval/manual-note enforcement and real Tesseract poster coordinates. See `ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md` for the full test results and limits.
