from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from brandproof.db import Base
from brandproof.models import new_id, utcnow


class GuidelineDocument(Base):
    __tablename__ = "guideline_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    filename: Mapped[str] = mapped_column(String(160))
    sha256: Mapped[str] = mapped_column(String(64))
    extraction: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentEvidence(Base):
    __tablename__ = "document_evidence"
    source_version_id: Mapped[str] = mapped_column(
        ForeignKey("source_versions.id"), primary_key=True
    )
    document_id: Mapped[str] = mapped_column(ForeignKey("guideline_documents.id"))
    page_number: Mapped[int] = mapped_column()
    start: Mapped[int] = mapped_column()
    end: Mapped[int] = mapped_column()
    quote: Mapped[str] = mapped_column(Text)


@event.listens_for(GuidelineDocument, "before_update")
@event.listens_for(GuidelineDocument, "before_delete")
@event.listens_for(DocumentEvidence, "before_update")
@event.listens_for(DocumentEvidence, "before_delete")
def immutable_document(*_args):
    raise ValueError("Imported document evidence is immutable")


def evidence_for(session, version_id):
    row = session.get(DocumentEvidence, version_id)
    if not row:
        return None
    document = session.get(GuidelineDocument, row.document_id)
    return {
        "document_id": document.id,
        "filename": document.filename,
        "sha256": document.sha256,
        "page_number": row.page_number,
        "start": row.start,
        "end": row.end,
        "quote": row.quote,
    }
