"""Hold a fictional pre-release session in memory and verify it after deployment.

No cookie, bearer or workspace identifier is serialized or printed. Only safe
pass/fail evidence is written. Run against the existing authorized backend only.
"""

import hashlib
import json
import time
from pathlib import Path

import httpx


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    base = "https://brandproof-api-slz9.onrender.com"
    output = Path(".cache/judge-release-retention.json")
    report = {"passed": False, "stage": "starting"}
    try:
        with httpx.Client(base_url=base, timeout=60) as client:
            for _attempt in range(6):
                response = client.get("/api/v1/health")
                if response.status_code == 200:
                    break
                time.sleep(5)
            response.raise_for_status()
            identity = client.post("/api/v1/demo-sessions")
            identity.raise_for_status()
            identity = identity.json()
            roles = {
                role: {"Authorization": f"Bearer {actor['access_token']}"}
                for role, actor in identity["actors"].items()
            }

            def request(method, path, role="creator", **kwargs):
                response = client.request(method, path, headers=roles[role], **kwargs)
                response.raise_for_status()
                return response.json()

            campaign = request(
                "POST",
                "/api/v1/campaigns",
                json={
                    "name": "Fictional deployment continuity check",
                    "publication_date": "2026-11-12",
                },
            )
            path = "/api/v1/campaigns/" + campaign["id"]
            source = request(
                "POST",
                path + "/sources",
                "owner",
                json={
                    "title": "Fictional approved price",
                    "rule": {"kind": "price", "amount": "899", "currency": "INR"},
                },
            )
            request(
                "POST",
                path + "/sources/" + source["id"] + "/confirm",
                "owner",
                json={"expected_version": source["version"]},
            )
            campaign = request(
                "PUT",
                path + "/caption",
                json={
                    "text": "Book for INR 599.",
                    "expected_revision": campaign["content_revision"],
                },
            )
            review = request(
                "POST",
                path + "/reviews",
                json={
                    "expected_content_revision": campaign["content_revision"],
                    "expected_source_revision": campaign["source_revision"],
                    "external_ai_consent": False,
                },
            )
            if not any(
                f["category"] == "price" and f["evidence_status"] == "contradicted"
                for f in review["findings"]
            ):
                raise ValueError("Real contradiction not detected")
            resources = [path, path + "/sources", path + "/reviews", path + "/revisions"]
            before = [digest(request("GET", resource)) for resource in resources]
            report["stage"] = "ready"
            print(
                "RETENTION_PROBE_READY: fictional source, caption and real review saved; credentials held only in memory",
                flush=True,
            )
            deadline = time.monotonic() + 1200
            while time.monotonic() < deadline:
                try:
                    contract = client.get("/openapi.json")
                    if (
                        contract.status_code == 200
                        and "/api/v1/demo-sessions/logout" in contract.json().get("paths", {})
                    ):
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(10)
            else:
                raise TimeoutError("Updated deployment not observed")
            resumed = client.post(
                "/api/v1/demo-sessions/resume", headers={"X-BrandProof-Session": "resume"}
            )
            resumed.raise_for_status()
            resumed = resumed.json()
            report.update(
                {
                    "stage": "checked",
                    "same_workspace": resumed["workspace_id"] == identity["workspace_id"],
                    "same_credentials": resumed["actors"] == identity["actors"],
                    "same_records": before
                    == [digest(request("GET", resource)) for resource in resources],
                    "all_roles_valid": all(
                        client.get(path, headers=value).status_code == 200
                        for value in roles.values()
                    ),
                }
            )
            report["passed"] = all(
                report[key]
                for key in ("same_workspace", "same_credentials", "same_records", "all_roles_valid")
            )
    except Exception:
        # Never print HTTP request/response objects or exception representations.
        report["error"] = "retention_probe_incomplete"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
