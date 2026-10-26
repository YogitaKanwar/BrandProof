import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, require_role, scoped_campaign, token_hash
from brandproof.models import Actor, Campaign, Workspace
from brandproof.schemas import CampaignCreate, CampaignOut, DemoSessionOut

router = APIRouter(prefix="/api/v1")


@router.post("/demo-sessions", status_code=201, response_model=DemoSessionOut, tags=["demo"])
def create_demo(session: Session = Depends(db)):
    workspace = Workspace()
    session.add(workspace)
    session.flush()
    expires = datetime.now(UTC) + timedelta(hours=24)
    actors = {}
    for role in ("owner", "creator", "reviewer"):
        token = secrets.token_urlsafe(32)
        session.add(
            Actor(
                workspace_id=workspace.id,
                role=role,
                token_hash=token_hash(token),
                expires_at=expires,
            )
        )
        actors[role] = {"role": role, "access_token": token}
    session.commit()
    return {
        "workspace_id": workspace.id,
        "mode": "synthetic_demo",
        "expires_at": expires,
        "notice": "Isolated fictional-data sandbox. Demo role switching is not production authentication. Do not upload confidential materials.",
        "actors": actors,
    }


@router.post("/campaigns", status_code=201, response_model=CampaignOut, tags=["campaigns"])
def create_campaign(
    payload: CampaignCreate, who: Actor = Depends(actor), session: Session = Depends(db)
):
    require_role(who, "owner", "creator")
    campaign = Campaign(workspace_id=who.workspace_id, **payload.model_dump())
    session.add(campaign)
    session.commit()
    return campaign


@router.get("/campaigns", response_model=list[CampaignOut], tags=["campaigns"])
def list_campaigns(who: Actor = Depends(actor), session: Session = Depends(db)):
    return session.scalars(
        select(Campaign)
        .where(Campaign.workspace_id == who.workspace_id)
        .order_by(Campaign.created_at)
    ).all()


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut, tags=["campaigns"])
def get_campaign(campaign_id: str, who: Actor = Depends(actor), session: Session = Depends(db)):
    return scoped_campaign(session, campaign_id, who)
