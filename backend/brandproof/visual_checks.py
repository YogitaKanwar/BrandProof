"""Measured flat-background and OCR-local contrast checks with explicit abstention.

No font recognition, semantic image understanding or full WCAG certification.
Only owner-confirmed supported rules are evaluated. All flags need image review.
"""

import math
import re
from collections import Counter
from io import BytesIO

from PIL import Image

from brandproof.models import new_id


def linear(value):
    value /= 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return sum(linear(c) * weight for c, weight in zip(rgb, (0.2126, 0.7152, 0.0722), strict=True))


def contrast_ratio(foreground, background):
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + 0.05) / (low + 0.05)


def lab(rgb):
    r, g, b = map(linear, rgb)
    xyz = (
        (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047,
        0.2126729 * r + 0.7151522 * g + 0.072175 * b,
        (0.0193339 * r + 0.119192 * g + 0.9503041 * b) / 1.08883,
    )
    x, y, z = [
        value ** (1 / 3) if value > 216 / 24389 else (24389 / 27 * value + 16) / 116
        for value in xyz
    ]
    return (116 * y - 16, 500 * (x - y), 200 * (y - z))


def delta_e(first, second):
    return math.dist(lab(first), lab(second))


def hex_rgb(value):
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def flag(category, message, campaign, asset, source=None, word=None):
    return {
        "id": new_id(),
        "category": category,
        "severity": "warning",
        "evidence_status": "needs_clarification",
        "message": message,
        "location": {
            "asset": "poster",
            "poster_id": asset.id,
            "content_revision": campaign.content_revision,
            "start": word["start"] if word else None,
            "end": word["end"] if word else None,
            "quote": word["text"] if word else None,
            "boxes": [{k: word[k] for k in ("x", "y", "width", "height")}] if word else [],
            "ocr_confidence": word["confidence"] if word else None,
        },
        "evidence": {
            "source_id": source["id"],
            "source_version_id": source["version_id"],
            "source_version": source["version"],
            "quote": source["text"],
        }
        if source
        else None,
        "suggested_replacement": None,
    }


def background_colour(image):
    sample = image.copy()
    sample.thumbnail((160, 160))
    pixels = sample.load()
    border = [pixels[x, y] for x in range(sample.width) for y in (0, sample.height - 1)] + [
        pixels[x, y] for y in range(sample.height) for x in (0, sample.width - 1)
    ]
    colour, count = Counter(border).most_common(1)[0]
    if (
        count / len(border) < 0.95
        or Counter(sample.getdata())[colour] / (sample.width * sample.height) < 0.35
    ):
        return None
    return colour


def word_colours(image, word):
    if word["confidence"] < 0.7:
        return None
    x, y, w, h = (int(word[k]) for k in ("x", "y", "width", "height"))
    if (
        not (0 <= x < x + w <= image.width and 0 <= y < y + h <= image.height)
        or w * h > 100000
        or w < 2
        or h < 2
    ):
        return None
    # Only an actual ring outside the OCR box can support background separation.
    if x < 2 or y < 2 or x + w + 2 > image.width or y + h + 2 > image.height:
        return None
    outer = image.crop((x - 2, y - 2, x + w + 2, y + h + 2))
    pixels = outer.load()
    ring = [pixels[a, b] for a in range(outer.width) for b in (0, outer.height - 1)] + [
        pixels[a, b] for b in range(outer.height) for a in (0, outer.width - 1)
    ]
    background, count = Counter(ring).most_common(1)[0]
    if count / len(ring) < 0.95:
        return None
    colors = Counter(image.crop((x, y, x + w, y + h)).getdata())
    ink = {color: count for color, count in colors.items() if math.dist(color, background) > 15}
    if not ink:
        return None
    foreground, count = max(ink.items(), key=lambda pair: pair[1])
    if count < 3 or count / sum(ink.values()) < 0.8:
        return None
    return foreground, background


def evaluate_visuals(asset, campaign, active, alt_text):
    image = Image.open(BytesIO(asset.normalized_bytes)).convert("RGB")
    findings = []
    palette = [source for source in active if source["rule"]["kind"] == "brand_color"]
    visual = {
        "status": "not_assessed",
        "scope": "supported flat background only",
        "measurements": [],
    }
    if palette:
        colour = background_colour(image)
        if colour is None:
            visual.update(
                status="partial",
                reason="No reliable uniform flat background; gradients/photos are unsupported.",
            )
        else:
            distances = [
                (delta_e(colour, hex_rgb(source["rule"]["hex"])), source) for source in palette
            ]
            supported = any(
                distance <= source["rule"]["tolerance"] for distance, source in distances
            )
            visual.update(
                status="completed",
                observed_hex="#" + "".join(f"{v:02X}" for v in colour),
                method="CIE76_D65_sRGB",
                measurements=[
                    {
                        "source_id": source["id"],
                        "delta_e": round(distance, 4),
                        "tolerance": source["rule"]["tolerance"],
                    }
                    for distance, source in distances
                ],
            )
            if not supported:
                closest = min(distances, key=lambda pair: pair[0])[1]
                findings.append(
                    flag(
                        "brand_color",
                        "Measured flat background is outside the approved background palette tolerances. Inspect the image; other visual regions were not assessed.",
                        campaign,
                        asset,
                        closest,
                    )
                )
    rules = [source for source in active if source["rule"]["kind"] == "contrast"]
    measurements = []
    words = asset.ocr["words"][:100]
    uncertain = 0
    for word in words if rules else []:
        colors = word_colours(image, word)
        if not colors:
            uncertain += 1
            continue
        ratio = contrast_ratio(*colors)
        measurements.append(
            {
                "text": word["text"],
                "ratio": round(ratio, 4),
                "foreground": colors[0],
                "background": colors[1],
                "box": {k: word[k] for k in ("x", "y", "width", "height")},
            }
        )
        strictest = max(rules, key=lambda source: source["rule"]["minimum_ratio"])
        if ratio < strictest["rule"]["minimum_ratio"]:
            findings.append(
                flag(
                    "contrast",
                    f"Measured OCR word contrast {ratio:.2f}:1 is below the approved {strictest['rule']['minimum_ratio']}:1 target. Verify text/background separation and intended display size manually.",
                    campaign,
                    asset,
                    strictest,
                    word,
                )
            )
    contrast = {
        "status": "not_assessed"
        if not rules
        else "partial"
        if uncertain
        or not measurements
        or len(asset.ocr["words"]) > 100
        or asset.ocr["status"] != "completed"
        else "completed",
        "scope": "uniform text/background samples only; no font/large-text inference or WCAG certification",
        "measurements": measurements,
        "unmeasured_words": uncertain,
        "word_limit": 100,
    }
    alt_sources = [source for source in active if source["rule"]["kind"] == "alt_text"]
    accessibility = {
        "status": "not_assessed",
        "scope": "presence and literal high-confidence OCR prices/ISO dates only",
    }
    if alt_sources:
        normalized = " ".join(alt_text.casefold().split())
        reliable = " ".join(w["text"] for w in asset.ocr["words"] if w["confidence"] >= 0.7)
        keys = re.findall(
            r"\b(?:INR|USD|EUR|GBP)\s*\d[\d,.]*|\b\d{4}-\d{2}-\d{2}\b", reliable, re.I
        )
        missing = [key for key in keys if " ".join(key.casefold().split()) not in normalized]
        accessibility.update(
            status="partial"
            if not normalized or missing or asset.ocr["status"] != "completed"
            else "completed",
            missing_key_text=missing,
        )
        if not normalized or missing:
            findings.append(
                flag(
                    "alt_text",
                    "Poster description is missing."
                    if not normalized
                    else "Poster description omits literal OCR price/date text: "
                    + ", ".join(missing)
                    + ". Inspect the image and describe its meaning manually.",
                    campaign,
                    asset,
                    alt_sources[0],
                )
            )
    return findings, {"visual": visual, "contrast": contrast, "accessibility": accessibility}
