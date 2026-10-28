# Local claim-risk screening

BrandProof now screens saved captions and extracted poster text for selected English promise patterns even when there are no approved facts and external AI is disabled. This complements source-backed rule checks; a pattern match does not establish falsity, missing brand approval, legal compliance or a policy violation.

## What a judge can try

1. Create a review with a publication date. No approved facts or AI consent are needed for this demonstration.
2. Save `Guaranteed results in 30 days.` and run review.
3. Open the `claim risk` finding: it highlights the actual phrase and asks for owner approval, supporting evidence and conditions. Its evidence status is `needs_clarification`; it has no fabricated source or suggested factual rewrite.
4. Change the caption to `The workshop lasts 30 days.`, save and review again. The pattern scan completes with no matches, while readiness stays `not approved`. The earlier finding remains in review history.
5. Upload a readable PNG/JPEG with the promise and review it. A match in actual OCR text uses the existing OCR word boxes. Inspect the poster, since OCR may miss text.

Selected patterns include guaranteed outcomes (including placement/admission/cure promises), results within a stated time, certainty language, `100% safe/effective`, `works for everyone`, `zero side effects`, numerical weight-loss claims and selected percentage performance claims. A trailing `Individual results may vary` does not erase an explicit guarantee.

## Human decision and persistence

- Findings use category `claim_risk`, severity `warning`, exact code-point spans and immutable review revisions. They never auto-approve or auto-rewrite the content.
- New runs include `checks.claim_risk` with screening version `claim-risk-v1`, per-asset coverage, scan size, match count and limits. Historical runs without this check keep their original contract; they are not retrospectively presented as screened.
- A run with a flagged promise has partial claim coverage. Approval requires an explicit finding disposition plus actual reviewer notes under `manual_checks.claim_risk`, alongside the existing required checks. Notes alone cannot bypass an unresolved finding. Approved sources and the existing role, revision and current-request requirements still apply.
- Local screening needs no provider key, consent or network call. Optional contextual AI keeps its existing explicit-consent requirements.

## Limits

This is a bounded English regex screen, not general language understanding or an accuracy-certified classifier. It inspects at most 20,000 characters and returns at most 20 merged findings per asset. Reaching either limit marks coverage partial and requests manual inspection. Blank captions are not assessed; incomplete poster OCR makes poster claim coverage partial even if no pattern matched.

Only a small explicit set of immediately preceding denials and hedges is suppressed. Quotation, complex negation, indirect promises, multilingual copy and unseen paraphrases can produce misses or false alarms. `Red Bull gives you wings` is outside this screen's patterns; its absence from findings does not establish brand approval or truth. Ordinary durations, cotton percentages and money-back terms in the test examples do not match, but that is not a claim that every such statement is valid.

Broader semantic claim recognition, linking evidence to individual promises and validating whether evidence actually supports a claim remain future work. Do not describe this feature as detecting every unsupported claim.
