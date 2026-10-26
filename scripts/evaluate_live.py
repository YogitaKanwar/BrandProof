"""Explicit, bounded live API probe; cases are synthetic and frozen before execution."""

import argparse
import hashlib
import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx


def summarize(rows):
    def counts(items):
        result = dict.fromkeys(["matched_expectation", "mismatch", "unassessed"], 0)
        result.update(Counter(row["assessment"] for row in items))
        result["total"] = len(items)
        return result

    return {
        **counts(rows),
        "splits": {
            split: counts([row for row in rows if row["split"] == split])
            for split in sorted({row["split"] for row in rows})
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--cases", default="docs/evaluation-cases.json")
    parser.add_argument("--output", default="docs/examples/live-model-evaluation.json")
    parser.add_argument("--consent-send-fictional-data", action="store_true", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Use a new output path; do not overwrite held-out evaluation evidence.")
    raw = Path(args.cases).read_bytes()
    cases = json.loads(raw)["cases"]
    if not 1 <= len(cases) <= 6:
        raise SystemExit(
            "This script permits at most six explicit review attempts, no automatic retries."
        )
    rows = []
    report = {
        "type": "actual_live_api_synthetic_evaluation",
        "cases_sha256": hashlib.sha256(raw).hexdigest(),
        "started_at": datetime.now(UTC).isoformat(),
        "limitations": "Small author-labelled synthetic probe. Heldout cases frozen before this run; no independent annotation or representative accuracy claim. Matches require completed contextual coverage. No tuning or automatic retries.",
        "results": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        report["summary"] = summarize(rows)
        output.write_text(json.dumps(report, indent=2) + "\n")

    with httpx.Client(base_url=args.base_url, timeout=45) as client:

        def call(method, path, body=None):
            response = client.request(method, path, json=body)
            response.raise_for_status()
            return response.json()

        demo = call("POST", "/api/v1/demo-sessions")
        client.headers["Authorization"] = "Bearer " + demo["actors"]["owner"]["access_token"]
        campaign = call(
            "POST",
            "/api/v1/campaigns",
            {
                "name": "Fictional frozen evaluation — not user data",
                "publication_date": "2026-11-12",
            },
        )
        base = "/api/v1/campaigns/" + campaign["id"]
        for title, rule in [
            (
                "Respectful tone",
                {
                    "kind": "tone",
                    "guidance": "Use respectful language. Do not insult or demean the reader.",
                },
            ),
            (
                "Support for objective promises",
                {
                    "kind": "claim_policy",
                    "guidance": "Guaranteed job placement and guaranteed earnings require approved supporting evidence. No outcome guarantee is approved in this reference pack. Ask for evidence rather than declaring an unsupported promise false.",
                },
            ),
            ("Required disclosure", {"kind": "required_text", "text": "Terms apply"}),
        ]:
            source = call("POST", base + "/sources", {"title": title, "rule": rule})
            call(
                "POST",
                base + "/sources/" + source["id"] + "/confirm",
                {"expected_version": source["version"]},
            )
        for case in cases:
            current = call("GET", base)
            current = call(
                "PUT",
                base + "/caption",
                {"expected_revision": current["content_revision"], "text": case["text"]},
            )
            start = time.monotonic()
            run = call(
                "POST",
                base + "/reviews",
                {
                    "expected_content_revision": current["content_revision"],
                    "expected_source_revision": current["source_revision"],
                    "external_ai_consent": True,
                },
            )
            contextual = run["checks"]["contextual"]
            observed = [
                f for f in run["findings"] if f["category"] in {"tone", "claim", "messaging"}
            ]
            assessment = "unassessed"
            if contextual["status"] == "completed":
                expected = case["expected_contextual_category"]
                matched = (
                    (not observed)
                    if expected is None
                    else any(f["category"] == expected for f in observed)
                )
                assessment = "matched_expectation" if matched else "mismatch"
            stored = call("GET", base + "/reviews/" + run["id"])
            assert stored["findings"] == run["findings"] and stored["checks"] == run["checks"]
            row = {
                **case,
                "latency_seconds": round(time.monotonic() - start, 3),
                "assessment": assessment,
                "readback_verified": True,
                "review": stored,
            }
            rows.append(row)
            save()
            print(
                json.dumps(
                    {
                        "id": case["id"],
                        "status": contextual["status"],
                        "assessment": assessment,
                        "contextual_findings": len(observed),
                        "latency_seconds": row["latency_seconds"],
                    }
                ),
                flush=True,
            )
    report["finished_at"] = datetime.now(UTC).isoformat()
    save()
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
