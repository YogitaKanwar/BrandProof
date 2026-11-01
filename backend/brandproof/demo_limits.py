"""Bounded admission for the supported single-worker demo deployment.

No request bodies, credentials, or forwarded IP headers are stored. Multiple
workers/replicas require shared gateway admission before public release.
"""

import hashlib
import secrets
from threading import Lock
from time import monotonic

from starlette.responses import JSONResponse


class DemoLimits:
    def __init__(self, settings):
        self.settings = settings
        self.salt = secrets.token_bytes(32)
        self.buckets = {}
        self.lock = Lock()

    def admit(self, request):
        path = request.url.path.rstrip("/")
        if request.method not in {"POST", "PUT", "DELETE"}:
            return None
        if path in {"/api/v1/demo-sessions", "/api/v1/demo-sessions/reset"}:
            kind, limit = "sessions", self.settings.demo_sessions_hourly_limit
        elif path.startswith("/api/v1/campaigns"):
            kind, limit = "operations", self.settings.demo_operations_hourly_limit
        else:
            return None
        # Never trust caller-supplied X-Forwarded-For. Proxy trust belongs in Uvicorn.
        peer = request.client.host if request.client else "unknown"
        key = hashlib.sha256(self.salt + peer.encode()).hexdigest()
        now = monotonic()
        with self.lock:
            self.buckets = {k: v for k, v in self.buckets.items() if v[0] > now}
            checks = [((kind, key), limit), (("global", kind), limit * 10)]
            for bucket, maximum in checks:
                expiry, count = self.buckets.get(bucket, (now + 3600, 0))
                if count >= maximum or (bucket not in self.buckets and len(self.buckets) >= 4096):
                    return JSONResponse(
                        {
                            "error": {
                                "code": "demo_rate_limit",
                                "message": "Demo request limit reached. Please try again later.",
                            }
                        },
                        status_code=429,
                        headers={
                            "Retry-After": str(max(1, int(expiry - now) + 1)),
                            "Cache-Control": "no-store",
                        },
                    )
            for bucket, _ in checks:
                expiry, count = self.buckets.get(bucket, (now + 3600, 0))
                self.buckets[bucket] = (expiry, count + 1)
        return None
