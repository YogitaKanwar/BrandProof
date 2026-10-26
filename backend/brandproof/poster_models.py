"""Immutable poster snapshots keyed by the shared content revision."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, LargeBinary, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow


class PosterAsset(Base):
    __tablename__ = "poster_assets"
    __table_args__ = (UniqueConstraint("campaign_id", "content_revision"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    content_revision: Mapped[int] = mapped_column()
    normalized_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    mime: Mapped[str] = mapped_column(String(32))
    sha256: Mapped[str] = mapped_column(String(64))
    width: Mapped[int] = mapped_column()
    height: Mapped[int] = mapped_column()
    ocr: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(PosterAsset, "before_update")
@event.listens_for(PosterAsset, "before_delete")
def reject_poster_mutation(_mapper, _connection, _target):
    raise ValueError("Poster assets are immutable")
