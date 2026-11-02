"""Actual isolated API process restart; credentials and cookie stay in memory."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / ".cache" / "round3-final" / ("restart-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "PYTHONPATH": str(root / "backend"),
        "BRANDPROOF_DATABASE_URL": "sqlite:///" + (directory / "acceptance.db").as_posix(),
        "BRANDPROOF_PUBLIC_ORIGIN": origin,
        "BRANDPROOF_DEMO_COOKIE_SECURE": "false",
        "BRANDPROOF_EXTERNAL_AI_ENABLED": "false",
        "BRANDPROOF_AI_PROVIDER": "none",
        "BRANDPROOF_AI_API_KEY": "",
        "BRANDPROOF_AI_MODEL": "",
    }
    process = None

    def start():
        return subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "brandproof.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(child):
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)

    def ready(client):
        for _ in range(100):
            try:
                if client.get("/api/v1/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        raise RuntimeError("Isolated startup did not complete")

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    report = {"passed": False, "actual_process_restart": False, "credentials_written": False}
    try:
        process = start()
        with httpx.Client(base_url=origin, timeout=20) as client:
            ready(client)
            response = client.post("/api/v1/demo-sessions")
            response.raise_for_status()
            identity = response.json()
            roles = {
                role: {"Authorization": "Bearer " + actor["access_token"]}
                for role, actor in identity["actors"].items()
            }

            def call(method, path, role="owner", **kwargs):
                response = client.request(method, path, headers=roles[role], **kwargs)
                response.raise_for_status()
                return response.json()

            campaign = call(
                "POST",
                "/api/v1/campaigns",
                json={"name": "Fictional restart acceptance", "publication_date": "2026-11-12"},
            )
            base = "/api/v1/campaigns/" + campaign["id"]
            response = client.post(
                base + "/guideline-documents?expected_source_revision=0",
                headers={**roles["owner"], "Content-Type": "application/pdf"},
                content=(root / "frontend/public/demo/workshop-guidelines.pdf").read_bytes(),
            )
            response.raise_for_status()
            imported = response.json()
            for source in imported["sources"]:
                call(
                    "POST",
                    base + f"/sources/{source['id']}/confirm",
                    json={"expected_version": 1},
                )
            current = call("GET", base)
            current = call(
                "PUT",
                base + "/caption",
                json={
                    "text": "Book for INR 599.",
                    "expected_revision": current["content_revision"],
                },
            )
            expected = {
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
            }
            review = call("POST", base + "/reviews", json=expected)
            finding = next(row for row in review["findings"] if row["category"] == "price")
            call(
                "POST",
                base + f"/reviews/{review['id']}/findings/{finding['id']}/decisions",
                "reviewer",
                json={
                    **expected,
                    "expected_decision_version": 0,
                    "decision": "exception",
                    "reason": "Fictional restart QA exception; no content approval is asserted.",
                },
            )
            paths = [
                base,
                base + "/guideline-documents",
                base + "/sources",
                base + "/revisions",
                base + "/reviews",
                base + "/receipt",
                "/api/v1/governance-insights",
                *[base + f"/sources/{source['id']}/versions" for source in imported["sources"]],
            ]
            before = [digest(call("GET", path)) for path in paths]
            stop(process)
            process = start()
            ready(client)
            response = client.post(
                "/api/v1/demo-sessions/resume", headers={"X-BrandProof-Session": "resume"}
            )
            response.raise_for_status()
            resumed = response.json()
            report.update(
                actual_process_restart=True,
                same_workspace=resumed["workspace_id"] == identity["workspace_id"],
                same_credentials=resumed["actors"] == identity["actors"],
                same_saved_records=before == [digest(call("GET", path)) for path in paths],
                all_roles_valid=all(
                    client.get(base, headers=value).status_code == 200 for value in roles.values()
                ),
                compared_resources=len(paths),
            )
            report["passed"] = all(
                report[key]
                for key in (
                    "same_workspace",
                    "same_credentials",
                    "same_saved_records",
                    "all_roles_valid",
                )
            )
    except Exception:
        report["error"] = "isolated_restart_acceptance_incomplete"
    finally:
        if process and process.poll() is None:
            stop(process)
    output = root / "docs/evidence/round3-final/restart.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
