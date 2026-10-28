import hashlib
from datetime import UTC, datetime

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from brandproof.errors import fail
from brandproof.models import Actor, Campaign
from brandproof.removal_models import CampaignRemoval, active_campaigns

bearer = HTTPBearer(auto_error=False)


def db(request: Request):
    with request.app.state.sessions() as session:
        yield session


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(db),
) -> Actor:
    if not credentials:
        fail(401, "unauthenticated", "A demo session bearer token is required")
    found = session.scalar(
        select(Actor).where(Actor.token_hash == token_hash(credentials.credentials))
    )
    if not found or found.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
        fail(401, "unauthenticated", "Session token is invalid or expired")
    return found


def require_role(who: Actor, *roles: str):
    if who.role not in roles:
        fail(403, "forbidden", "This action is not permitted for the current actor")


def scoped_campaign(session: Session, campaign_id: str, who: Actor) -> Campaign:
    found = session.scalar(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == who.workspace_id,
            active_campaigns(),
        )
    )
    if not found:
        fail(404, "not_found", "Campaign not found")
    return found


def lock_campaign(session: Session, campaign: Campaign, *, allow_removed=False):
    """Serialize snapshot readers and all mutators until this transaction ends.

    A no-op UPDATE takes a database write lock on SQLite and a row lock on
    PostgreSQL (unlike SELECT FOR UPDATE, which SQLite ignores). Acquire before
    reading content/sources, always before any Source lock, then refresh the
    possibly stale identity-map object. Currentness is guaranteed at review
    insertion/commit, not indefinitely after delivery to a client.
    """
    session.execute(
        update(Campaign)
        .where(Campaign.id == campaign.id)
        .values(content_revision=Campaign.content_revision),
        execution_options={"synchronize_session": False},
    )
    session.refresh(campaign)
    if not allow_removed and session.get(CampaignRemoval, campaign.id):
        fail(404, "not_found", "Campaign not found")
