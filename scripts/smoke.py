"""Exercise the actual running API with fictional data; never fabricate model output."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="docs/examples/live-review.json")
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
        with urlopen(request, timeout=15) as response:
            return json.load(response)

    assert call("GET", "/api/v1/health")["database"] == "ok"
    demo = call("POST", "/api/v1/demo-sessions")
    token = demo["actors"]["owner"]["access_token"]
    campaign = call(
        "POST",
        "/api/v1/campaigns",
        {"name": "Fictional workshop smoke test", "publication_date": "2026-11-12"},
        token,
    )
    base = f"/api/v1/campaigns/{campaign['id']}"
    for title, rule in [
        ("Price", {"kind": "price", "amount": "499", "currency": "INR"}),
        ("Date", {"kind": "date", "date": "2026-11-12"}),
        ("Terminology", {"kind": "terminology", "term": "cheap", "preferred": "affordable"}),
        ("Required wording", {"kind": "required_text", "text": "Terms apply"}),
    ]:
        source = call("POST", base + "/sources", {"title": title, "rule": rule}, token)
        call(
            "POST",
            f"{base}/sources/{source['id']}/confirm",
            {"expected_version": source["version"]},
            token,
        )

    def review(text):
        current = call("GET", base, token=token)
        current = call(
            "PUT",
            base + "/caption",
            {"expected_revision": current["content_revision"], "text": text},
            token,
        )
        return call(
            "POST",
            base + "/reviews",
            {
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
            },
            token,
        )

    flawed = review("A cheap workshop on 2026-11-13. Book for INR 599.")
    assert {f["category"] for f in flawed["findings"]} == {
        "price",
        "date",
        "terminology",
        "required_text",
    }
    stored = call("GET", f"{base}/reviews/{flawed['id']}", token=token)
    assert stored["findings"] == flawed["findings"]
    clean = review("An affordable workshop on 2026-11-12. Book for INR 499. Terms apply.")
    assert clean["findings"] == []
    assert clean["status"] == "partial" and clean["readiness"] == "not_approved"
    historical = call("GET", f"{base}/reviews/{flawed['id']}", token=token)
    assert historical["is_current"] is False
    result = {
        "type": "actual_local_api_smoke_result",
        "fictional_input": True,
        "flawed_review": flawed,
        "clean_review": clean,
        "historical_review_is_current_after_edit": historical["is_current"],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "health": "ok",
                "flawed_findings": len(flawed["findings"]),
                "clean_findings": len(clean["findings"]),
                "overall_review": clean["status"],
                "historical_run_is_current": historical["is_current"],
                "result_file": str(output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
