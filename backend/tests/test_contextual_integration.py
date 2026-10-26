"""Persisted API tests with simulated provider output; never live inference."""

import json

import httpx
import pytest
from brandproof import review_schemas
from brandproof.config import Settings
from brandproof.review_schemas import Location, ReviewCreate
from pydantic import SecretStr, ValidationError
from test_reviews import add_source, review_copy


def test_contextual_configuration_and_consent_are_explicit_and_strict():
    assert hasattr(review_schemas, "ReviewStart")
    ReviewStart = review_schemas.ReviewStart
    settings = Settings(_env_file=None)
    assert settings.ai_provider == "none"
    assert settings.ai_model == ""
    assert settings.ai_api_key.get_secret_value() == ""
    assert settings.external_ai_enabled is False
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ai_provider="unknown")
    expectations = {"expected_content_revision": 1, "expected_source_revision": 0}
    assert ReviewStart(**expectations).external_ai_consent is False
    for value in ["true", 1, None]:
        with pytest.raises(ValidationError):
            ReviewStart(**expectations, external_ai_consent=value)
    with pytest.raises(ValidationError):
        ReviewCreate(**expectations, external_ai_consent=True)
    location = Location(
        asset="poster",
        content_revision=1,
        poster_id="poster-id",
        boxes=[{"x": 1, "y": 2, "width": 3, "height": 4}],
        ocr_confidence=0.9,
    )
    assert location.poster_id == "poster-id"
    assert location.boxes[0].width == 3


def configured(client):
    settings = client.app.state.settings
    settings.ai_provider = "groq"
    settings.ai_model = "simulated-contract-model"
    settings.ai_api_key = SecretStr("simulated-key")
    settings.external_ai_enabled = True


def start_current(client, owner, campaign, consent=True):
    base = f"/api/v1/campaigns/{campaign['id']}"
    current = client.get(base, headers=owner).json()
    return client.post(
        base + "/reviews",
        headers=owner,
        json={
            "expected_content_revision": current["content_revision"],
            "expected_source_revision": current["source_revision"],
            "external_ai_consent": consent,
        },
    )


def test_contextual_result_is_integrated_and_requires_explicit_request_consent(
    client, owner, campaign
):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    tone = add_source(
        client, owner, campaign, {"kind": "tone", "guidance": "Use a respectful tone."}
    )
    review_copy(client, owner, campaign, "Stupid offer. Terms apply.")
    configured(client)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "findings": [
                                        {
                                            "category": "tone",
                                            "severity": "warning",
                                            "evidence_status": "contradicted",
                                            "start": 0,
                                            "end": 6,
                                            "quote": "Stupid",
                                            "source_id": tone["id"],
                                            "source_version": tone["version"],
                                            "source_quote": tone["text"],
                                            "message": "Replace the insulting description with respectful wording.",
                                        }
                                    ]
                                }
                            )
                        },
                    }
                ]
            },
        )

    client.app.state.contextual_transport = httpx.MockTransport(handler)
    denied = start_current(client, owner, campaign, consent=False)
    assert denied.status_code == 201
    assert calls == []
    response = start_current(client, owner, campaign)
    assert response.status_code == 201, response.text
    run = response.json()
    assert len(calls) == 1
    assert run["checks"]["contextual"]["status"] == "completed"
    assert run["checks"]["contextual"]["details"]["provider"] == "groq"
    assert run["findings"][0]["category"] == "tone"
    assert run["findings"][0]["evidence"]["source_id"] == tone["id"]
    assert "simulated-key" not in response.text
    stored = client.get(
        f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}", headers=owner
    ).json()
    assert stored["findings"] == run["findings"]
    assert stored["checks"] == run["checks"]
    assert run["status"] == "completed"


@pytest.mark.parametrize("exclusion", ["pending", "expired", "future"])
@pytest.mark.parametrize("with_active_policy", [False, True])
@pytest.mark.parametrize("kind", ["tone", "claim_policy"])
def test_excluded_contextual_policy_prevents_completed_coverage(
    client,
    owner,
    campaign,
    kind,
    with_active_policy,
    exclusion,
):
    # An unrelated exact source cannot make an excluded contextual policy applicable.
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    if with_active_policy:
        add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    bounds = (
        {"valid_until": "2026-11-11"}
        if exclusion == "expired"
        else {"valid_from": "2026-11-13"}
        if exclusion == "future"
        else {}
    )
    excluded = add_source(
        client,
        owner,
        campaign,
        {"kind": kind, "guidance": "Additional policy"},
        confirm=exclusion != "pending",
        **bounds,
    )
    review_copy(client, owner, campaign, "Workshop invitation")
    configured(client)
    disclosed_packs = []

    def provider(request):
        disclosed_packs.append(json.loads(json.loads(request.content)["messages"][1]["content"]))
        return completion_response({"findings": []})

    client.app.state.contextual_transport = httpx.MockTransport(provider)
    response = start_current(client, owner, campaign)
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["checks"]["exact_text"]["status"] == "completed"
    assert run["checks"]["contextual"]["status"] == "partial"
    assert run["checks"]["contextual"]["details"]["excluded_policy_source_ids"] == [excluded["id"]]
    assert run["checks"]["contextual"]["reason"]
    assert run["status"] == "partial"
    assert len(disclosed_packs) == int(with_active_policy)
    for pack in disclosed_packs:
        assert excluded["id"] not in [source["id"] for source in pack["sources"]]


@pytest.mark.parametrize("failure", ["quota", "malformed", "invalid_citation", "timeout"])
def test_provider_failure_is_fail_closed_and_persisted(client, owner, campaign, failure):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    review_copy(client, owner, campaign, "Stupid offer")
    configured(client)
    calls = []

    def provider(request):
        calls.append(request)
        if failure == "quota":
            return httpx.Response(429, json={"error": "simulated-key quota rejected"})
        if failure == "timeout":
            raise httpx.ReadTimeout("simulated-key timeout", request=request)
        if failure == "malformed":
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "not JSON simulated-key"}}],
                },
            )
        return completion_response(
            {
                "findings": [
                    {
                        "category": "tone",
                        "severity": "warning",
                        "evidence_status": "contradicted",
                        "start": 0,
                        "end": 6,
                        "quote": "Stupid",
                        "source_id": "invented-source",
                        "source_version": 1,
                        "source_quote": "invented quote",
                        "message": "Untrusted finding",
                    }
                ]
            }
        )

    client.app.state.contextual_transport = httpx.MockTransport(provider)
    response = start_current(client, owner, campaign)
    assert response.status_code == 201, response.text
    run = response.json()
    assert len(calls) == 1
    assert run["status"] == "partial"
    expected = "partial" if failure == "invalid_citation" else "unavailable"
    assert run["checks"]["contextual"]["status"] == expected
    assert run["checks"]["contextual"]["reason"]
    assert [finding["category"] for finding in run["findings"]] == ["required_text"]
    if failure == "invalid_citation":
        assert run["checks"]["contextual"]["details"]["rejected_finding_count"] == 1
    assert "simulated-key" not in response.text
    stored = client.get(
        f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}",
        headers=owner,
    ).json()
    assert stored["checks"] == run["checks"]
    assert stored["findings"] == run["findings"]
    assert stored["status"] == "partial"


@pytest.mark.parametrize(
    "gate", ["server", "omitted_consent", "false_consent", "provider", "model", "key"]
)
def test_every_external_disclosure_gate_prevents_http(client, owner, campaign, gate):
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    previous = review_copy(client, owner, campaign, "Workshop invitation")
    configured(client)
    settings = client.app.state.settings
    payload = {
        "expected_content_revision": previous["content_revision"],
        "expected_source_revision": previous["source_revision"],
        "external_ai_consent": True,
    }
    if gate == "server":
        settings.external_ai_enabled = False
    elif gate == "omitted_consent":
        payload.pop("external_ai_consent")
    elif gate == "false_consent":
        payload["external_ai_consent"] = False
    elif gate == "provider":
        settings.ai_provider = "none"
    elif gate == "model":
        settings.ai_model = ""
    else:
        settings.ai_api_key = SecretStr("")
    calls = []
    client.app.state.contextual_transport = httpx.MockTransport(
        lambda request: calls.append(request) or completion_response({"findings": []})
    )
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/reviews",
        headers=owner,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert calls == []
    assert response.json()["checks"]["contextual"]["status"] == "unavailable"
    assert response.json()["status"] == "partial"


@pytest.mark.parametrize("consent", ["true", "false", 1, 0, None])
def test_api_consent_never_coerces_non_booleans(client, owner, campaign, consent):
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    previous = review_copy(client, owner, campaign, "Workshop invitation")
    configured(client)
    calls = []
    client.app.state.contextual_transport = httpx.MockTransport(
        lambda request: calls.append(request) or completion_response({"findings": []})
    )
    response = start_current(client, owner, campaign, consent=consent)
    assert response.status_code == 422, response.text
    assert calls == []
    listed = client.get(f"/api/v1/campaigns/{campaign['id']}/reviews", headers=owner).json()
    assert [run["id"] for run in listed] == [previous["id"]]


@pytest.mark.parametrize(
    "actor_kind, status", [("reviewer", 403), ("outsider", 404), ("anonymous", 401)]
)
def test_forbidden_actor_cannot_trigger_external_review(
    client, owner, demo, campaign, actor_kind, status
):
    add_source(client, owner, campaign, {"kind": "tone", "guidance": "Respectful tone"})
    previous = review_copy(client, owner, campaign, "Workshop invitation")
    configured(client)
    calls = []
    client.app.state.contextual_transport = httpx.MockTransport(
        lambda request: calls.append(request) or completion_response({"findings": []})
    )
    if actor_kind == "anonymous":
        forbidden = {}
    elif actor_kind == "reviewer":
        forbidden = {"Authorization": f"Bearer {demo['actors']['reviewer']['access_token']}"}
    else:
        outsider = client.post("/api/v1/demo-sessions").json()
        forbidden = {"Authorization": f"Bearer {outsider['actors']['owner']['access_token']}"}
    base = f"/api/v1/campaigns/{campaign['id']}"
    response = client.post(
        base + "/reviews",
        headers=forbidden,
        json={
            "expected_content_revision": previous["content_revision"],
            "expected_source_revision": previous["source_revision"],
            "external_ai_consent": True,
        },
    )
    assert response.status_code == status, response.text
    assert calls == []
    assert len(client.get(base + "/reviews", headers=owner).json()) == 1


def completion_response(content):
    return httpx.Response(
        200,
        json={
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(content)}}],
        },
    )
