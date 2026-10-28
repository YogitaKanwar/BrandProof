"""Synthetic-demo browser continuity; never authentication for confidential workspaces."""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import token_hash
from brandproof.demo_session_models import DemoBrowserSession
from brandproof.errors import fail
from brandproof.models import Actor, Workspace

COOKIE_NAME = "brandproof_demo_session"
COOKIE_PATH = "/api/v1/demo-sessions"
ROLES = ("owner", "creator", "reviewer")


def role_tokens(secret: str) -> dict[str, str]:
    return {
        role: hmac.new(
            secret.encode("ascii"),
            f"brandproof:synthetic-demo:role:v1:{role}".encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        for role in ROLES
    }


def session_payload(workspace_id: str, expires: datetime, tokens: dict[str, str]):
    return {
        "workspace_id": workspace_id,
        "mode": "synthetic_demo",
        "expires_at": expires.replace(tzinfo=UTC),
        "notice": "Isolated fictional-data sandbox. Demo role switching is not production authentication. Do not upload confidential materials.",
        "actors": {role: {"role": role, "access_token": token} for role, token in tokens.items()},
    }


def check_browser_context(request: Request, *, resume: bool = False):
    """Validate browser provenance before writes or returning role credentials.

    Native clients may omit Origin. Resume still requires a non-simple header,
    so a cross-site HTML form cannot retrieve the bearer credentials.
    """
    if any(
        value.strip().lower() == "cross-site"
        for header in request.headers.getlist("sec-fetch-site")
        for value in header.split(",")
    ):
        fail(403, "forbidden", "Cross-site demo session requests are not permitted")
    origins = request.headers.getlist("origin")
    own_origin = f"{request.url.scheme}://{request.url.netloc}"
    # TLS may end at a hosting proxy. Use configured platform metadata, never
    # untrusted forwarded headers, to recognise its public HTTPS origin.
    allowed = [own_origin, *request.app.state.settings.cors_origins]
    if request.app.state.settings.public_origin:
        allowed.append(request.app.state.settings.public_origin)
    if origins and (len(origins) != 1 or origins[0] not in allowed):
        fail(403, "forbidden", "Demo session origin is not permitted")
    if resume and request.headers.getlist("x-brandproof-session") != ["resume"]:
        fail(403, "forbidden", "X-BrandProof-Session: resume is required")


def create_browser_session(request: Request, response: Response, session: Session):
    check_browser_context(request)
    secret = secrets.token_urlsafe(32)
    tokens = role_tokens(secret)
    expires = datetime.now(UTC) + timedelta(hours=24)
    workspace = Workspace()
    session.add(workspace)
    session.flush()
    session.add(
        DemoBrowserSession(
            workspace_id=workspace.id, token_hash=token_hash(secret), expires_at=expires
        )
    )
    for role, token in tokens.items():
        session.add(
            Actor(
                workspace_id=workspace.id,
                role=role,
                token_hash=token_hash(token),
                expires_at=expires,
            )
        )
    session.commit()
    response.set_cookie(
        COOKIE_NAME,
        secret,
        max_age=24 * 60 * 60,
        path=COOKIE_PATH,
        secure=request.app.state.settings.demo_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return session_payload(workspace.id, expires, tokens)


def resume_browser_session(request: Request, session: Session):
    check_browser_context(request, resume=True)
    secret = request.cookies.get(COOKIE_NAME, "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", secret):
        fail(401, "unauthenticated", "Browser demo session is invalid or expired")
    found = session.scalar(
        select(DemoBrowserSession).where(DemoBrowserSession.token_hash == token_hash(secret))
    )
    if not found or found.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
        fail(401, "unauthenticated", "Browser demo session is invalid or expired")
    tokens = role_tokens(secret)
    actors = session.scalars(select(Actor).where(Actor.workspace_id == found.workspace_id)).all()
    if len(actors) != len(ROLES) or {row.role for row in actors} != set(ROLES):
        fail(401, "unauthenticated", "Browser demo session is invalid or expired")
    for row in actors:
        if not hmac.compare_digest(
            row.token_hash, token_hash(tokens[row.role])
        ) or row.expires_at.replace(tzinfo=UTC) != found.expires_at.replace(tzinfo=UTC):
            fail(401, "unauthenticated", "Browser demo session is invalid or expired")
    return session_payload(found.workspace_id, found.expires_at, tokens)
