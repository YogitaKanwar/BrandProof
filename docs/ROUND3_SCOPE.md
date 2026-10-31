# Round 3 — submitted commitments

Source of truth: Rushab supplied the actual Round 2 submission wording in conversation. This supersedes the different proposed additions in `ROUND2_SUBMISSION.md`; that older document remains a historical draft, not the final submitted scope.

## Improvement 1: PDF guideline import with traceable evidence

We will let owners import PDF brand guidelines and review supported rule candidates with exact page quotations. Candidates remain pending until explicitly confirmed. This reduces manual entry while preserving document evidence and version history. Unsupported or scanned pages will be reported clearly instead of producing invented rules.

## Improvement 2: Measured visual consistency and accessibility checks

We will add supported brand-background colour checks, text/background contrast measurements where reliable, and poster alt-text requirements. Users will see measurements and specific issues requiring attention. We will test supported and unsupported images and return partial coverage when reliable verification is impossible.

## Improvement 3: Governance Insights

We will summarize recurring finding categories across campaigns and identify guideline versions frequently dismissed or excepted by reviewers. Owners can inspect the underlying findings, source versions and decision reasons before clarifying a guideline. Minimum sample requirements will prevent misleading conclusions from a few decisions.

## Scope boundaries

- Production team authentication, a new team review queue, automatic typography verification and expanded logo placement/clear-space verification are not among these submitted commitments.
- Connected-review deletion is additional work, not a substitute for one of the three promised improvements.
- PDF candidates do not become authoritative rules without explicit owner confirmation. Unsupported or scanned content must remain visibly unsupported; no invented quotations or rules.
- Measurements are limited to supported inputs. Unsupported images or unreliable text/background attribution must not receive a clean accessibility or brand-compliance result.
- Governance summaries are descriptive evidence, not proof that a guideline is incorrect. Underlying runs, source versions and decision reasons must remain inspectable; small samples must not produce misleading conclusions.
- Rushab owns backend/AI/OCR/database work. Yogita owns frontend/integration unless Rushab explicitly expands scope.
- Branch implementation, local test success and public deployment acceptance are separate states. Do not describe a branch-only feature as working publicly.

## Submitted Round 2 baseline — reported by Rushab, not reverified here

Completed publicly: isolated fictional demo workspaces and saved campaigns; owner-confirmed versioned reference rules and publication-date validity; caption revisions and explicit caption removal; private PNG/JPEG uploads; Tesseract OCR/confidence and responsive word boxes; bounded price/date/terminology/required-wording checks; local English claim-risk screening; explained source/version findings; explicit supported corrections; persisted comments and reasoned finding decisions; human review requests/approval/request-changes; stale approval receipts; same-browser session recovery; editable fictional example; owner-confirmed reference-logo upload; desktop/mobile workspace.

Reported architecture: React 19/TypeScript/Vite frontend on Vercel, API proxy to a Render Docker service, Render PostgreSQL storing campaigns/images/source versions/review snapshots/decisions; Python/FastAPI/Pydantic/SQLAlchemy, Pillow, local Tesseract, deterministic parsers and versioned English regex patterns. This replaces older draft assumptions about Neon hosting. Public URLs were not supplied in this scope update and deployment has not been independently checked here.

## Reported limitations and branch status

- Live external contextual AI is not accepted as working publicly. Optional Groq/OpenRouter requires server configuration and explicit consent.
- Automatic logo comparison can time out on Render Free; manual inspection remains necessary.
- PDF import, measured accessibility, Governance Insights and connected-review deletion reportedly exist on a review branch, not at the public link. Identify and inspect that exact branch before implementing duplicates or claiming completion.
- OCR may miss text; complex layouts and unsupported expressions require manual checks.
- Claim screening is bounded English matching, not general truth verification.
- Demo actors are synthetic, not production team authentication.
- Free-backend cold starts can cause initial API failures.
- The current free PostgreSQL database reportedly expires 27 November 2026; continued availability needs a separate operational decision.

## Acceptance evidence to prepare

These are proposed verification criteria, not additional submitted promises:

1. PDF: real supported PDF import → exact page quotation readback → pending candidate → explicit owner confirmation → source version/history; scanned/unsupported input remains explicitly incomplete.
2. Visual/accessibility: supported colour and contrast measurements with reproducible inputs/results; alt-text missing/present behaviour; unsupported images return partial coverage; edits invalidate affected currentness/readiness.
3. Insights: persisted multi-campaign findings and reviewer decisions → workspace-scoped category/version summaries → exact evidence drilldown; minimum-sample and cross-workspace isolation tests. Define and disclose the denominator and treatment of repeated runs/decision changes before reporting rates.
4. Release: exercise each feature at the actual public link, including persistence and existing review/approval regressions, before marking it delivered.
