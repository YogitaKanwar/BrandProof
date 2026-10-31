"""Measure existing production using fictional assets; never changes host settings."""

import io
import json
import random
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw

ORIGIN = "https://brand-proof-tau.vercel.app"


def main():
    tokens = {}
    observations = []

    def call(method, path, payload=None, raw=None, mime=None, label="", expected=200):
        headers = {"Content-Type": mime or "application/json", "Origin": ORIGIN}
        if tokens:
            headers["Authorization"] = "Bearer " + tokens["owner"]["access_token"]
        request = Request(
            ORIGIN + "/api/v1" + path,
            method=method,
            headers=headers,
            data=raw
            if raw is not None
            else json.dumps(payload).encode()
            if payload is not None
            else None,
        )
        started = time.monotonic()
        try:
            with urlopen(request, timeout=120) as response:
                result = json.load(response)
                observations.append(
                    {
                        "check": label or path.split("?")[0].split("/")[-1],
                        "status": response.status,
                        "seconds": round(time.monotonic() - started, 3),
                    }
                )
                assert response.status == expected
                return result
        except HTTPError as error:
            observations.append(
                {
                    "check": label,
                    "status": error.code,
                    "seconds": round(time.monotonic() - started, 3),
                }
            )
            if method == "GET":
                return None
            raise RuntimeError("Production probe stopped on HTTP " + str(error.code)) from None

    health = call("GET", "/health", label="first_public_health")
    if not health:
        with urlopen(
            "https://brandproof-api-slz9.onrender.com/api/v1/health", timeout=120
        ) as response:
            assert response.status == 200
        health = call("GET", "/health", label="health_after_direct_warmup")
    assert health and health["database"] == "ok"
    tokens.update(call("POST", "/demo-sessions", expected=201, label="fictional_session")["actors"])
    campaign = call(
        "POST",
        "/campaigns",
        {"name": "Fictional production resource probe", "publication_date": "2026-11-12"},
        expected=201,
        label="fictional_campaign",
    )
    base = "/campaigns/" + campaign["id"]
    image = Image.frombytes("RGB", (1310, 1310), random.Random(20261028).randbytes(1310 * 1310 * 3))
    output = io.BytesIO()
    image.save(output, format="PNG")
    raw = output.getvalue()
    assert 4.8 * 1024 * 1024 < len(raw) < 5 * 1024 * 1024
    poster = call(
        "PUT",
        base + "/posters?expected_revision=1",
        raw=raw,
        mime="image/png",
        label="near_5_mib_png_upload",
    )
    observations.append(
        {
            "check": "near_limit_asset",
            "bytes": len(raw),
            "fraction_of_5_mib": round(len(raw) / (5 * 1024 * 1024), 4),
            "ocr_status": poster["ocr"]["status"],
            "ocr_reason": poster["ocr"]["reason"],
        }
    )
    image = Image.new("RGB", (80, 40), "navy")
    ImageDraw.Draw(image).polygon([(0, 0), (40, 40), (80, 0)], fill="teal")
    output = io.BytesIO()
    image.save(output, format="PNG")
    logo = call(
        "PUT",
        base + "/brand-logo?expected_source_revision=0",
        raw=output.getvalue(),
        mime="image/png",
        label="private_logo_reference",
    )
    campaign = call("GET", base, label="current_campaign")
    call(
        "POST",
        base + "/brand-logo/" + logo["id"] + "/confirm",
        {
            "expected_version": logo["version"],
            "expected_source_revision": campaign["source_revision"],
        },
        label="explicit_reference_confirmation",
    )
    campaign = call("GET", base, label="current_revisions")
    run = call(
        "POST",
        base + "/reviews",
        {
            "expected_content_revision": campaign["content_revision"],
            "expected_source_revision": campaign["source_revision"],
            "external_ai_consent": False,
        },
        expected=201,
        label="review_large_poster_with_logo",
    )
    logo_check = run["checks"]["poster"]["details"].get("logo", {})
    observations.append(
        {
            "check": "logo_free_compute",
            "status": logo_check.get("status"),
            "reason": logo_check.get("reason"),
            "run_status": run["status"],
            "contextual_status": run["checks"]["contextual"]["status"],
        }
    )
    result = {
        "origin": ORIGIN,
        "scope": "single warm/cold-observed sample, not p95, load or controlled 15-minute sleep acceptance",
        "observations": observations,
        "credentials_written": False,
        "host_settings_changed": False,
    }
    Path(".cache/improvements-20261028/production-resources.json").write_text(
        json.dumps(result, indent=2)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
