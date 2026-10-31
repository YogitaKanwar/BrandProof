import json
from types import SimpleNamespace

import httpx
from brandproof.contextual import analyze_context, poster_context
from test_contextual import enabled, response, source


def asset(confidence=0.99):
    return SimpleNamespace(
        id="poster-id",
        ocr={
            "text": "Rude text",
            "status": "completed" if confidence >= 0.7 else "partial",
            "words": [
                {
                    "text": "Rude",
                    "start": 0,
                    "end": 4,
                    "confidence": confidence,
                    "x": 5,
                    "y": 10,
                    "width": 40,
                    "height": 20,
                },
                {
                    "text": "text",
                    "start": 5,
                    "end": 9,
                    "confidence": 0.99,
                    "x": 50,
                    "y": 10,
                    "width": 40,
                    "height": 20,
                },
            ],
        },
    )


def test_poster_only_context_uses_one_separate_asset_request_and_real_boxes():
    calls = []

    def provider(request):
        payload = json.loads(request.content)
        data = json.loads(payload["messages"][1]["content"])
        assert data["draft"] == "" and data["assets"]["poster"]["text"] == "Rude text"
        assert "words" not in data["assets"]["poster"]
        calls.append(request)
        return response(
            [
                {
                    "asset": "poster",
                    "category": "tone",
                    "severity": "warning",
                    "evidence_status": "needs_clarification",
                    "start": 0,
                    "end": 4,
                    "quote": "Rude",
                    "source_id": "tone",
                    "source_version": 2,
                    "source_quote": "calm",
                    "message": "Possible tone issue",
                    "unverified_draft_suggestion": "Welcome",
                }
            ]
        )

    result = analyze_context(
        "",
        2,
        [source()],
        enabled(),
        transport=httpx.MockTransport(provider),
        poster=poster_context(asset()),
    )
    assert result.status == "completed" and len(calls) == 1
    finding = result.findings[0]
    assert finding["location"]["asset"] == "poster" and finding["location"]["boxes"][0]["x"] == 5
    assert finding["suggested_replacement"] is None
    assert finding["unverified_draft_suggestion"] == "Welcome"


def test_uncertain_ocr_is_masked_and_provider_cannot_invent_its_span():
    poster = poster_context(asset(0.2))
    assert poster["text"] == "     text"

    def provider(_request):
        return response(
            [
                {
                    "asset": "poster",
                    "category": "tone",
                    "severity": "warning",
                    "evidence_status": "needs_clarification",
                    "start": 0,
                    "end": 4,
                    "quote": "Rude",
                    "source_id": "tone",
                    "source_version": 2,
                    "source_quote": "calm",
                    "message": "Invalid invisible words",
                }
            ]
        )

    result = analyze_context(
        "Caption", 2, [source()], enabled(), transport=httpx.MockTransport(provider), poster=poster
    )
    assert result.status == "partial" and not result.findings
    assert result.metadata["rejected_finding_count"] == 1


def test_no_consent_never_calls_provider_even_with_poster():
    def forbidden(_request):
        raise AssertionError("No consent")

    result = analyze_context(
        "Caption",
        2,
        [source()],
        enabled(allow_external=False),
        transport=httpx.MockTransport(forbidden),
        poster=poster_context(asset()),
    )
    assert result.status == "unavailable" and not result.findings
