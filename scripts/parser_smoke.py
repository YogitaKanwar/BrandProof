"""Read back real HTTP reviews for parser regressions using fictional inputs."""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="docs/examples/parser-regressions.json")
    args = parser.parse_args()

    def call(method, path, payload=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            args.base_url + path,
            method=method,
            headers=headers,
            data=json.dumps(payload).encode() if payload is not None else None,
        )
        try:
            with urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    code, demo = call("POST", "/api/v1/demo-sessions")
    assert code == 201
    token = demo["actors"]["owner"]["access_token"]
    price = {"kind": "price", "amount": "499", "currency": "INR"}
    date = {"kind": "date", "date": "2026-11-12"}
    cases = [
        ("repeated_decimal_same_prefix", price, "Book for INR499..99."),
        ("repeated_decimal_other_prefix", price, "Book for INR599..99."),
        ("extra_fractional_digits", price, "Book for INR499.999."),
        ("indian_grouping_unassessed", price, "Book for INR1,00,000."),
        ("cashback_scope", price, "Get INR100 cashback when you register."),
        ("mixed_price_formats", price, "Book for INR499. Book for 599 INR."),
        ("deadline_scope", date, "Early-bird registration closes on 2026-11-10."),
        ("mixed_date_formats", date, "Workshop on 2026-11-12. Workshop on 13 November 2026."),
        ("malformed_date", date, "Workshop on 2026-11-12..99."),
        ("prose_date_unassessed", date, "Workshop on 13 November 2026."),
    ]
    observations = []
    for name, rule, caption in cases:
        code, campaign = call(
            "POST", "/api/v1/campaigns", {"name": name, "publication_date": "2026-11-12"}, token
        )
        assert code == 201
        base = f"/api/v1/campaigns/{campaign['id']}"
        code, source = call("POST", base + "/sources", {"title": name, "rule": rule}, token)
        assert code == 201
        code, _ = call(
            "POST", f"{base}/sources/{source['id']}/confirm", {"expected_version": 1}, token
        )
        assert code == 200
        code, current = call(
            "PUT", base + "/caption", {"expected_revision": 1, "text": caption}, token
        )
        assert code == 200
        code, run = call(
            "POST",
            base + "/reviews",
            {
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
            },
            token,
        )
        assert code == 201
        code, stored = call("GET", f"{base}/reviews/{run['id']}", token=token)
        assert code == 200
        assert stored["checks"]["exact_text"]["status"] != "completed", (name, stored)
        assert stored["findings"]
        assert all(
            f["evidence_status"] == "needs_clarification" and f["suggested_replacement"] is None
            for f in stored["findings"]
        ), (name, stored["findings"])
        observations.append({"case": name, "caption": caption, "persisted_review": stored})
    overflow_base = "/api/v1/campaigns/" + observations[-1]["persisted_review"]["campaign_id"]
    code, error = call(
        "PUT",
        overflow_base + "/caption",
        {"expected_revision": 2**100, "text": "Valid caption"},
        token,
    )
    assert code == 422
    result = {
        "type": "actual_local_http_parser_regressions",
        "fictional_input": True,
        "cases": observations,
        "oversized_revision_http_status": code,
        "oversized_revision_error": error,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "readback_cases_passed": len(observations),
                "oversized_revision_http_status": code,
                "result": str(output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
