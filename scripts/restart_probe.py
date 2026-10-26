"""Two-phase actual API restart probe. State file contains a demo token: keep private."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["seed", "verify"])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()
    state_path = Path(args.state_file)

    def call(method, path, payload=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(
            args.base_url + path,
            method=method,
            headers=headers,
            data=None if payload is None else json.dumps(payload).encode(),
        )
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    if args.stage == "seed":
        demo = call("POST", "/api/v1/demo-sessions")
        token = demo["actors"]["owner"]["access_token"]
        campaign = call(
            "POST",
            "/api/v1/campaigns",
            {"name": "Synthetic process-restart verification", "publication_date": "2026-11-12"},
            token,
        )
        base = "/api/v1/campaigns/" + campaign["id"]
        source = call(
            "POST",
            base + "/sources",
            {
                "title": "Synthetic required wording",
                "rule": {"kind": "required_text", "text": "Terms apply"},
            },
            token,
        )
        call(
            "POST",
            base + "/sources/" + source["id"] + "/confirm",
            {"expected_version": source["version"]},
            token,
        )
        current = call(
            "PUT",
            base + "/caption",
            {"expected_revision": 1, "text": "Workshop. Terms apply."},
            token,
        )
        run = call(
            "POST",
            base + "/reviews",
            {
                "expected_content_revision": current["content_revision"],
                "expected_source_revision": current["source_revision"],
            },
            token,
        )
        state = {
            "token": token,
            "base": base,
            "review_id": run["id"],
            "review_hash": hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest(),
        }
        fd = os.open(state_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream)
        print(
            json.dumps(
                {
                    "stage": "seed",
                    "saved_private_state": True,
                    "action_required": "Stop and restart the API using the same database, then run verify.",
                }
            )
        )
    else:
        state = json.loads(state_path.read_text())
        run = call("GET", state["base"] + "/reviews/" + state["review_id"], token=state["token"])
        assert (
            hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest()
            == state["review_hash"]
        )
        assert (
            call("GET", state["base"], token=state["token"])["caption"] == "Workshop. Terms apply."
        )
        state_path.unlink()
        print(
            json.dumps(
                {
                    "stage": "verify",
                    "persisted_campaign_and_review_unchanged": True,
                    "private_state_removed": True,
                }
            )
        )


if __name__ == "__main__":
    main()
