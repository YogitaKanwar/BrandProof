"""Exact rules on an immutable OCR snapshot, not a complete visual review."""

from sqlalchemy import select

from brandproof.poster_models import PosterAsset
from brandproof.rules import exact_checks


def review_poster(session, campaign, active, excluded):
    asset = session.scalar(
        select(PosterAsset)
        .where(
            PosterAsset.campaign_id == campaign.id,
            PosterAsset.content_revision <= campaign.content_revision,
        )
        .order_by(PosterAsset.content_revision.desc())
        .limit(1)
    )
    if not asset:
        return [], {"status": "not_assessed", "reason": "No poster attached.", "details": {}}
    extraction = asset.ocr
    details = {
        "asset_id": asset.id,
        "asset_revision": asset.content_revision,
        "sha256": asset.sha256,
        "width": asset.width,
        "height": asset.height,
        "ocr_status": extraction["status"],
        "ocr_reason": extraction["reason"],
        "ocr_text": extraction["text"],
        "visual_branding": "not_assessed",
        "accessibility": "not_assessed",
        "contextual_claims": "not_assessed",
    }
    if not extraction["text"]:
        details["exact_text_status"] = extraction["status"]
        return [], {
            "status": extraction["status"],
            "reason": "Poster text extraction is incomplete; inspect the image manually.",
            "details": details,
        }
    findings, rules = exact_checks(extraction["text"], campaign.content_revision, active)
    for finding in findings:
        location = finding["location"]
        words = []
        if location.get("start") is not None and location.get("end") is not None:
            words = [
                word
                for word in extraction["words"]
                if word["start"] < location["end"] and word["end"] > location["start"]
            ]
        location.update(
            {
                "asset": "poster",
                "poster_id": asset.id,
                "boxes": [
                    {key: word[key] for key in ("x", "y", "width", "height")} for word in words
                ],
                "ocr_confidence": min((word["confidence"] for word in words), default=None),
            }
        )
        finding["suggested_replacement"] = None  # An image must be revised and reuploaded.
        finding["message"] = (
            "OCR text: " + finding["message"] + " Verify the displayed image before deciding."
        )
        if (
            finding["category"] == "required_text"
            and location.get("start") is None
            and extraction["status"] != "completed"
        ):
            finding["evidence_status"] = "needs_clarification"
            finding["severity"] = "warning"
            finding["message"] = (
                "Required campaign wording was not found in incomplete OCR; "
                "visually confirm its presence in the displayed image before deciding."
            )
        if words and any(word["confidence"] < 0.7 for word in words):
            finding["evidence_status"] = "needs_clarification"
            finding["severity"] = "warning"
            finding["message"] += " The affected text has low OCR confidence."
    uncertain_sources = {
        (finding["evidence"]["source_id"], finding["evidence"]["source_version"])
        for finding in findings
        if finding["evidence_status"] == "needs_clarification" and finding["evidence"]
    }
    for rule in rules:
        if (
            rule["status"] == "completed"
            and (rule["source_id"], rule["source_version"]) in uncertain_sources
        ):
            rule["status"] = "partial"
            rule["reason"] = "OCR-based evidence requires visual confirmation."
    exact_incomplete = (
        extraction["status"] != "completed"
        or any(rule["status"] != "completed" for rule in rules)
        or any(
            source["kind"] in {"price", "date", "terminology", "required_text"}
            for source in excluded
        )
    )
    details["exact_text_status"] = (
        "partial" if exact_incomplete else ("completed" if rules else "not_assessed")
    )
    return findings, {
        "status": "partial",  # OCR is not visual brand, accessibility or contextual review.
        "reason": "Only OCR-based exact text checks were attempted. Visual branding, accessibility and contextual poster claims require manual review.",
        "rules": rules,
        "details": details,
    }
