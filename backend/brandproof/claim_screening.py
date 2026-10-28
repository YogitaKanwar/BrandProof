"""Bounded English promise-pattern screening, independent of brand facts or AI.

A match is a question for a reviewer, never evidence of falsity or missing
brand approval. Approved policies do not silently waive a matched promise.
"""

import re

from brandproof.models import new_id

VERSION = "claim-risk-v1"
MAX_CHARS = 20000
MAX_FINDINGS = 20
OUTCOME = r"(?:results?|outcomes?|success|profits?|returns?|earnings?|sales|revenue|recovery|weight\s+loss|placements?|jobs?|employment|admissions?|cures?)"
NUMBER = r"(?:\d{1,4}|a|an|one|two|three|four|five|six|seven|eight|nine|ten|thirty|sixty|ninety)"
TIME = rf"(?:in|within|after|under)\s+(?:just\s+)?{NUMBER}\s+(?:hours?|days?|weeks?|months?|years?)"
PATTERNS = [
    (
        "guaranteed outcome",
        rf"\bguarantee(?:d|s)?\s+(?:(?:you|your|our|the|a|an|visible|real|proven|positive|better|fast|certain)\s+){{0,4}}{OUTCOME}\b",
    ),
    (
        "guaranteed outcome",
        rf"\b{OUTCOME}\s+(?:(?:are|is|fully|absolutely)\s+){{0,2}}guarantee(?:d)?\b",
    ),
    ("time-bound outcome", rf"\b{OUTCOME}\s+{TIME}\b"),
    (
        "certain outcome",
        rf"\b(?:will\s+(?:definitely|certainly)|definitely\s+will|certain\s+to)\s+(?:(?:see|get|achieve|deliver|experience|increase|boost|your)\s+){{0,3}}{OUTCOME}\b",
    ),
    (
        "absolute performance or safety",
        r"\b100\s*%\s*(?:safe|effective|successful|success|risk[- ]free|guaranteed)\b",
    ),
    (
        "universal performance",
        r"\b(?:works?\s+for\s+(?:everyone|everybody)|never\s+fails?|zero\s+(?:risk|side\s+effects))\b",
    ),
    (
        "quantified outcome",
        r"\b(?:lose|shed)\s+\d{1,3}(?:\.\d{1,2})?\s*(?:kg|kilograms?|lbs?|pounds?)\b",
    ),
    (
        "quantified outcome",
        r"\b(?:boost|increase|double|improve|reduce|cut)\s+(?:your\s+)?(?:sales|revenue|profits?|productivity|conversion(?:\s+rate)?|costs?)\s+by\s+\d{1,3}(?:\.\d{1,2})?\s*%",
    ),
]
COMPILED = [(label, re.compile(pattern, re.IGNORECASE)) for label, pattern in PATTERNS]
# Suppress a small, explicit set of local denials/hedges. This is not general
# quotation, negation or metaphor understanding; uncertain matches need people.
DENIAL = re.compile(
    r"\b(?:no|not|never|without|cannot|can['’]t|don['’]t|doesn['’]t|do\s+not|avoid)"
    r"\s+(?:(?:offer(?:ing)?|promise|promising|guarantee|guaranteeing|claim(?:ing)?|say(?:ing)?|expect|advertise)\s+){0,2}[\s\"'‘’“”]*$",
    re.IGNORECASE,
)
HEDGE = re.compile(
    r"\b(?:may|might|could|aim(?:s)?\s+to|hope\s+to|target(?:ing)?)\s+"
    r"(?:(?:see|get|achieve|deliver|show|expect|provide|for|visible|positive)\s+){0,3}[\s\"'‘’“”]*$",
    re.IGNORECASE,
)


def screen_claims(text: str, revision: int):
    scanned = text[:MAX_CHARS]
    matches = []
    for label, pattern in COMPILED:
        for match in pattern.finditer(scanned):
            prefix = re.split(r"[.!?;:]", scanned[max(0, match.start() - 100) : match.start()])[-1]
            if DENIAL.search(prefix) or HEDGE.search(prefix):
                continue
            matches.append((match.start(), match.end(), label))
    matches.sort()
    groups = []
    for start, end, label in matches:
        if groups and start < groups[-1][1]:
            groups[-1][1] = max(end, groups[-1][1])
            groups[-1][2].add(label)
        else:
            groups.append([start, end, {label}])
    findings = [
        {
            "id": new_id(),
            "category": "claim_risk",
            "severity": "warning",
            "evidence_status": "needs_clarification",
            "message": f"Potential {', '.join(sorted(labels))}. Verify brand approval, supporting evidence and any conditions before publication. This pattern match does not establish that the claim is false or unapproved.",
            "location": {
                "asset": "caption",
                "content_revision": revision,
                "start": start,
                "end": end,
                "quote": text[start:end],
            },
            "evidence": None,
            "suggested_replacement": None,
            "unverified_draft_suggestion": "Explore the details and supporting evidence; outcomes are not promised.",
        }
        for start, end, labels in groups[:MAX_FINDINGS]
    ]
    limited = len(text) > MAX_CHARS or len(groups) > MAX_FINDINGS
    return findings, {
        "status": "not_assessed"
        if not text.strip()
        else "partial"
        if findings or limited
        else "completed",
        "reason": "Local English pattern screening for outcome promises, time-bound results and selected absolute/quantified claims. A clear scan does not verify truth, brand approval or all paraphrases."
        + (" Review flagged promises and record supporting evidence." if findings else "")
        + (" Screening limit reached; inspect the remaining content manually." if limited else ""),
        "details": {
            "version": VERSION,
            "method": "local_english_patterns",
            "scanned_characters": len(scanned),
            "total_characters": len(text),
            "finding_count": len(findings),
            "limited": limited,
        },
    }


def combined_coverage(caption_check, poster_check=None):
    checks = {"caption": caption_check}
    if poster_check is not None:
        checks["poster"] = poster_check
    active = [check for check in checks.values() if check["status"] != "not_assessed"]
    limited = any(check.get("details", {}).get("limited", False) for check in checks.values())
    return {
        "status": "not_assessed"
        if not active
        else "completed"
        if all(check["status"] == "completed" for check in active)
        else "partial",
        "reason": "Local English promise-pattern screening; no AI provider required. Flags request human evidence review, not a truth verdict. No matches does not cover all claims or metaphors."
        + (" Screening limit reached; inspect the remaining content manually." if limited else ""),
        "details": {
            "version": VERSION,
            "limited": limited,
            "assets": checks,
            "finding_count": sum(
                check.get("details", {}).get("finding_count", 0) for check in checks.values()
            ),
        },
    }
