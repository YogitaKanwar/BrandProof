"""Single-worker container entry point. Put TLS/body limits at the ingress."""

import os

import uvicorn


def main():
    try:
        port = int(os.environ.get("PORT", "8000"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit("PORT must be an integer between 1 and 65535") from None
    uvicorn.run(
        "brandproof.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=False,
    )


if __name__ == "__main__":
    main()
