"""Simulate TLS termination over real HTTP. Keep all demo credentials in memory."""

import argparse
import json
from http.cookies import SimpleCookie
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--public-origin", required=True)
    args = parser.parse_args()
    base = "/api/v1/demo-sessions"

    def post(path, headers):
        request = Request(args.base_url + path, method="POST", headers=headers)
        return urlopen(request, timeout=15)

    with post(base, {"Origin": args.public_origin}) as response:
        assert response.status == 201
        original = json.load(response)
        cookie = SimpleCookie()
        cookie.load(response.headers["Set-Cookie"])
        browser_cookie = cookie["brandproof_demo_session"]
        assert browser_cookie["secure"] and browser_cookie["httponly"]
        assert browser_cookie["samesite"] == "strict"
        assert response.headers["Cache-Control"] == "no-store"
    # Simulate a cookie sent over public HTTPS then forwarded internally as HTTP.
    with post(
        base + "/resume",
        {
            "Origin": args.public_origin,
            "X-BrandProof-Session": "resume",
            "Cookie": "brandproof_demo_session=" + browser_cookie.value,
        },
    ) as response:
        assert response.status == 200
        assert json.load(response) == original
        assert response.headers["Cache-Control"] == "no-store"
    try:
        post(
            base + "/resume",
            {
                "Origin": "https://attacker.example",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "attacker.example",
                "X-BrandProof-Session": "resume",
                "Cookie": "brandproof_demo_session=" + browser_cookie.value,
            },
        )
    except HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("Forged origin was accepted")
    print(
        json.dumps(
            {
                "tls_offload_origin": "passed",
                "secure_cookie_resume": "same_workspace",
                "forged_origin": "rejected",
            }
        )
    )


if __name__ == "__main__":
    main()
