"""Real HTTP / local Tesseract workflow; all reviewer choices are scripted demo actions."""

import argparse
import hashlib
import json
import os
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont


def fixture_font(size):
    configured = os.environ.get("BRANDPROOF_TEST_FONT")
    candidates = (
        [configured]
        if configured
        else [
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    raise OSError("Install a TrueType fixture font or set BRANDPROOF_TEST_FONT to its path")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="docs/examples/workflow-smoke.json")
    args = parser.parse_args()
    tokens = {}

    def call(method, path, payload=None, role="owner", raw=None, expected=200):
        headers = {"Content-Type": "image/png" if raw is not None else "application/json"}
        if role in tokens:
            headers["Authorization"] = "Bearer " + tokens[role]
        data = (
            raw
            if raw is not None
            else json.dumps(payload).encode()
            if payload is not None
            else None
        )
        request = Request(args.base_url + path, method=method, headers=headers, data=data)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            assert error.code == expected, (path, error.code, error.read().decode())
            return json.load(error)
        with response:
            assert response.status == expected, (path, response.status)
            return (
                response.read()
                if response.headers.get_content_type() == "image/png"
                else json.load(response)
            )

    def expectation(row):
        return {
            key: row[value]
            for key, value in [
                ("expected_content_revision", "content_revision"),
                ("expected_source_revision", "source_revision"),
            ]
        }

    def poster(text):
        image = Image.new("RGB", (1100, 220), "white")
        ImageDraw.Draw(image).text(
            (25, 55),
            text,
            fill="black",
            font=fixture_font(48),
        )
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    assert call("GET", "/api/v1/health")["database"] == "ok"
    demo = call("POST", "/api/v1/demo-sessions", expected=201)
    tokens.update({role: actor["access_token"] for role, actor in demo["actors"].items()})
    campaign = call(
        "POST",
        "/api/v1/campaigns",
        {"name": "Fictional collaboration and real OCR smoke", "publication_date": "2026-11-12"},
        expected=201,
    )
    base = f"/api/v1/campaigns/{campaign['id']}"
    for rule in [
        {"kind": "terminology", "term": "cheap", "preferred": "affordable"},
        {"kind": "required_text", "text": "Terms apply"},
    ]:
        source = call(
            "POST",
            base + "/sources",
            {"title": "Synthetic workshop rule", "rule": rule},
            expected=201,
        )
        call(
            "POST",
            base + f"/sources/{source['id']}/confirm",
            {"expected_version": source["version"]},
        )
    current = call(
        "PUT",
        base + "/caption",
        {"expected_revision": 1, "text": "Our cheap workshop. Terms apply."},
        role="creator",
    )
    run = call("POST", base + "/reviews", expectation(current), role="creator", expected=201)
    assert len(run["findings"]) == 1
    comment = call(
        "POST",
        base + "/comments",
        {
            **expectation(run),
            "review_id": run["id"],
            "text": "Scripted demo comment: use the owner-confirmed preferred term.",
        },
        role="creator",
        expected=201,
    )
    assert call("GET", base + "/comments")[0]["id"] == comment["id"]
    apply = base + f"/reviews/{run['id']}/findings/{run['findings'][0]['id']}/apply"
    corrected = call("POST", apply, expectation(run), role="creator")
    assert corrected["caption"] == "Our affordable workshop. Terms apply."
    call("POST", apply, expectation(run), role="creator", expected=409)
    uploaded = call(
        "PUT",
        base + f"/posters?expected_revision={corrected['content_revision']}",
        role="creator",
        raw=poster("Our cheap workshop. Terms apply."),
    )
    canonical = call("GET", base + f"/posters/{uploaded['id']}/content")
    assert hashlib.sha256(canonical).hexdigest() == uploaded["sha256"]
    current = call("GET", base)
    reviewed = call("POST", base + "/reviews", expectation(current), role="creator", expected=201)
    found = [
        finding for finding in reviewed["findings"] if finding["location"]["asset"] == "poster"
    ]
    assert len(found) == 1 and found[0]["location"]["boxes"]
    assert reviewed["checks"]["poster"]["status"] == "partial"
    assert reviewed["checks"]["contextual"]["status"] == "unavailable"
    stored = call("GET", base + f"/reviews/{reviewed['id']}")
    assert stored["findings"] == reviewed["findings"]
    decision_path = base + f"/reviews/{reviewed['id']}/findings/{found[0]['id']}/decisions"
    decision = call(
        "POST",
        decision_path,
        {
            **expectation(reviewed),
            "expected_decision_version": 0,
            "decision": "exception",
            "reason": "Scripted synthetic exception for exercising the decision record; not a real campaign sign-off.",
        },
        role="reviewer",
        expected=201,
    )
    assert call("GET", decision_path)[0]["id"] == decision["id"]
    request = call(
        "POST",
        base + f"/reviews/{reviewed['id']}/requests",
        expectation(reviewed),
        role="creator",
        expected=201,
    )
    approval_path = base + f"/reviews/{reviewed['id']}/approvals"
    payload = {
        **expectation(reviewed),
        "request_id": request["id"],
        "decision": "approve",
        "reason": "Scripted demo approval, not a human user study or external publication permission.",
        "manual_checks": {},
    }
    denied = call("POST", approval_path, payload, role="reviewer", expected=409)
    assert denied["error"]["code"] == "checks_incomplete"
    payload["manual_checks"] = {
        "contextual": "Scripted attestation to exercise manual tone/claim coverage, not a model result.",
        "poster": "Scripted attestation for visual branding, contextual claims and accessibility, not automated completion.",
    }
    approval = call("POST", approval_path, payload, role="reviewer", expected=201)
    receipt = call("GET", base + "/receipt")
    assert receipt["approvals"][0]["id"] == approval["id"]
    assert receipt["readiness"] == "approved_with_manual_checks"
    assert receipt["scope"] == "caption_and_attached_poster"
    changed = call(
        "PUT",
        base + f"/posters?expected_revision={current['content_revision']}",
        role="creator",
        raw=poster("Our affordable workshop. Terms apply."),
    )
    stale = call("GET", base + "/receipt")
    assert stale["readiness"] == "stale"
    assert stale["approvals"][0]["is_current"] is False
    historical = call("GET", base + f"/reviews/{reviewed['id']}")
    assert historical["checks"]["poster"]["details"]["asset_id"] == uploaded["id"]
    assert historical["findings"] == reviewed["findings"]
    revisions = call("GET", base + "/revisions")
    assert revisions[-1]["revision"] == changed["content_revision"]
    report = {
        "type": "actual_local_http_workflow",
        "fictional_data": True,
        "reviewer_actions": "scripted API demonstration, not real user feedback",
        "live_model_used": False,
        "comment": comment,
        "poster": uploaded,
        "review": reviewed,
        "decision": decision,
        "approval": approval,
        "approved_receipt": receipt,
        "after_edit_receipt": stale,
        "revision_count": len(revisions),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                "real_ocr": uploaded["ocr"]["status"],
                "poster_findings": len(found),
                "explicit_suggestion": "passed",
                "persisted_records": "verified",
                "approval": receipt["readiness"],
                "after_poster_edit": stale["readiness"],
                "result_file": str(output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
