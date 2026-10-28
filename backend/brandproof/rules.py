import re
from decimal import Decimal

from brandproof.candidates import Candidate, date_candidates, money_candidates
from brandproof.models import new_id

# This finite scope grammar deliberately abstains on unknown or qualified prose.
EVENT = r"(?:workshop|event|session|class)"
MAIN_PRICE = re.compile(
    rf"(?:(?:join|book|register|enrol|enroll)(?: (?:our|the|a) {EVENT})? (?:for|at)"
    rf"|{EVENT}(?: (?:price|fee|cost))?(?: is| for| at)?"
    r"|(?:main campaign price|campaign price|price|fee|cost)(?: is)?\s*[:=]?)",
    re.IGNORECASE,
)
MAIN_DATE = re.compile(
    rf"(?:(?:(?:join|attend) (?:us for |our |the |a )?|(?:a|an|the|our) )?"
    rf"(?:(?:cheap|affordable) )?{EVENT}(?: is| takes place| is scheduled)? (?:on|for)"
    r"|(?:main campaign date|campaign date|workshop date|event date)\s*[:=]?)",
    re.IGNORECASE,
)
QUALIFIED_SCOPE = re.compile(
    r"\b(?:not|never|no|only|if|unless|maybe|perhaps|previously|formerly|cashback|rebate|"
    r"refund|deposit|discount|deadline|closes?|closing|until|before|by)\b"
    r"|n['’]t\b|\bearly[- ]bird\b",
    re.IGNORECASE,
)


def main_scope(text: str, match: Candidate, kind: str) -> bool:
    if QUALIFIED_SCOPE.search(text):
        return False
    prefix = re.split(r"[.!?;\n]", text[: match.start()])[-1].strip()
    suffix = re.split(r"[.!?;\n]", text[match.end() :])[0].strip()
    if kind == "price" and not prefix:
        return bool(re.fullmatch(r"for \d+ seats(?: on \d{4}-\d{2}-\d{2})?", suffix, re.IGNORECASE))
    pattern = MAIN_PRICE if kind == "price" else MAIN_DATE
    return not suffix and bool(pattern.fullmatch(prefix))


def evidence(source):
    return {
        "source_id": source["id"],
        "source_version_id": source["version_id"],
        "source_version": source["version"],
        "quote": source["text"],
    }


def finding(
    category,
    message,
    revision,
    source=None,
    match=None,
    replacement=None,
    status="contradicted",
    severity="error",
):
    return {
        "id": new_id(),
        "category": category,
        "severity": severity,
        "evidence_status": status,
        "message": message,
        "location": {
            "asset": "caption",
            "content_revision": revision,
            "start": match.start() if match else None,
            "end": match.end() if match else None,
            "quote": match.group(0) if match else None,
        },
        "evidence": evidence(source) if source else None,
        "suggested_replacement": replacement,
    }


def rule_value(rule):
    if rule["kind"] == "price":
        return rule["currency"], Decimal(rule["amount"])
    return rule["date"]


def candidate_value(candidate, kind):
    return (candidate.currency, candidate.value) if kind == "price" else candidate.value


def numeric_findings(text, revision, source, peers, candidates):
    rule = source["rule"]
    kind = rule["kind"]
    if len({rule_value(peer["rule"]) for peer in peers}) > 1:
        return [
            finding(
                kind,
                "Approved sources disagree for the same campaign scope; ask the owner to resolve them.",
                revision,
                source,
                status="needs_clarification",
                severity="warning",
            )
        ]

    # Classification precedes comparison for the WHOLE rule. One unknown
    # candidate prevents corrections to other candidates of the same kind.
    unknown = [candidate for candidate in candidates if not candidate.supported]
    if unknown:
        return [
            finding(
                kind,
                candidate.reason or "Unsupported expression; confirm its format and scope.",
                revision,
                source,
                candidate,
                status="needs_clarification",
                severity="warning",
            )
            for candidate in unknown
        ]
    if len({candidate_value(candidate, kind) for candidate in candidates}) > 1:
        return [
            finding(
                kind,
                "Multiple values need scope confirmation; no automatic correction is safe.",
                revision,
                source,
                status="needs_clarification",
                severity="warning",
            )
        ]
    ambiguous = [candidate for candidate in candidates if not main_scope(text, candidate, kind)]
    if ambiguous:
        return [
            finding(
                kind,
                "This expression is not an explicit unqualified main-campaign value in the supported grammar; confirm its scope.",
                revision,
                source,
                candidate,
                status="needs_clarification",
                severity="warning",
            )
            for candidate in ambiguous
        ]
    expected = rule_value(rule)
    replacement = (
        f"{rule['currency']} {format(Decimal(rule['amount']), 'f')}"
        if kind == "price"
        else rule["date"]
    )
    return [
        finding(
            kind,
            f"Campaign {kind} differs from the approved source.",
            revision,
            source,
            candidate,
            replacement,
        )
        for candidate in candidates
        if candidate_value(candidate, kind) != expected
    ]


def exact_checks(text: str, revision: int, sources: list[dict]) -> tuple[list[dict], list[dict]]:
    candidates = {"price": money_candidates(text), "date": date_candidates(text)}
    findings, coverage = [], []
    for source in sources:
        rule = source["rule"]
        kind = rule["kind"]
        if kind not in {"price", "date", "terminology", "required_text"}:
            continue
        local_findings = []
        if kind in candidates:
            peers = [peer for peer in sources if peer["rule"]["kind"] == kind]
            local_findings = numeric_findings(text, revision, source, peers, candidates[kind])
        elif kind == "required_text":
            phrase = r"\s+".join(re.escape(part) for part in rule["text"].split())
            if not re.search(r"(?<!\w)" + phrase + r"(?!\w)", text, re.IGNORECASE):
                local_findings = [
                    finding(
                        kind,
                        "Required campaign wording is missing; add it in context.",
                        revision,
                        source,
                        replacement=rule["text"],
                    )
                ]
        else:
            phrase = r"\s+".join(re.escape(part) for part in rule["term"].split())
            pattern = re.compile(r"(?<!\w)" + phrase + r"(?!\w)", re.IGNORECASE)
            local_findings = [
                finding(
                    kind,
                    "Use the approved terminology.",
                    revision,
                    source,
                    match,
                    rule["preferred"],
                )
                for match in pattern.finditer(text)
            ]
        findings.extend(local_findings)
        status, reason = "completed", None
        if kind in candidates and not any(candidate.supported for candidate in candidates[kind]):
            status = "not_assessed"
            reason = "No comparable supported expression was parsed; missing/unsupported formats are not a successful evaluation."
        elif any(f["evidence_status"] == "needs_clarification" for f in local_findings):
            status = "partial"
            reason = (
                "Some candidate expressions or approved sources require format/scope clarification."
            )
        coverage.append(
            {
                "source_id": source["id"],
                "source_version": source["version"],
                "kind": kind,
                "status": status,
                "reason": reason,
            }
        )
    return findings, coverage
