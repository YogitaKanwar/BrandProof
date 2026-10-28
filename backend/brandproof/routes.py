from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandproof.auth import actor, db, require_role, scoped_campaign
from brandproof.demo_sessions import create_browser_session, resume_browser_session
from brandproof.models import Actor, Campaign
from brandproof.schemas import CampaignCreate, CampaignOut, DemoSessionOut

router = APIRouter(prefix="/api/v1")


@router.post("/demo-sessions", status_code=201, response_model=DemoSessionOut, tags=["demo"])
def create_demo(request: Request, response: Response, session: Session = Depends(db)):
    return create_browser_session(request, response, session)


@router.post("/demo-sessions/resume", response_model=DemoSessionOut, tags=["demo"])
def resume_demo(request: Request, session: Session = Depends(db)):
    return resume_browser_session(request, session)


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
