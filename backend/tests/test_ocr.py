import importlib
import os
from io import BytesIO

import pytest
from PIL import Image, ImageDraw, ImageFont


def fixture_font(size):
    configured = os.environ.get("BRANDPROOF_TEST_FONT")
    candidates = (
        [configured]
        if configured
        else [
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    raise OSError("Install a TrueType fixture font or set BRANDPROOF_TEST_FONT to its path")


def poster_bytes(text="SUMMER SALE 2026", *, size=(1000, 240), mode="RGB", fmt="PNG"):
    image = Image.new(mode, size, "white")
    if text:
        ImageDraw.Draw(image).text((35, 60), text, fill="black", font=fixture_font(64))
    output = BytesIO()
    image.save(output, format=fmt)
    return output.getvalue()


def test_real_tesseract_extracts_words_with_coordinates_and_offsets():
    from importlib.util import find_spec

    assert find_spec("brandproof.ocr") is not None, "Real OCR module is missing"
    ocr = importlib.import_module("brandproof.ocr")
    result = ocr.extract_text(poster_bytes(), 1000, 240)
    assert result["status"] == "completed"
    assert "SUMMER SALE 2026" in result["text"]
    assert result["engine"] == "tesseract"
    for word in result["words"]:
        assert result["text"][word["start"] : word["end"]] == word["text"]
        assert 0 <= word["confidence"] <= 1
        assert 0 <= word["x"] < 1000
        assert 0 <= word["y"] < 240
        assert 0 < word["width"] <= 1000 - word["x"]
        assert 0 < word["height"] <= 240 - word["y"]


def test_blank_image_is_unreadable_not_success():
    from brandproof.ocr import extract_text

    result = extract_text(poster_bytes(""), 1000, 240)
    assert result["status"] == "partial"
    assert result["reason"] == "unreadable"
    assert result["text"] == ""
    assert result["words"] == []


def test_timeout_is_visible_unavailable(monkeypatch):
    from brandproof import ocr

    monkeypatch.setattr(ocr, "OCR_TIMEOUT_SECONDS", 0)
    result = ocr.extract_text(poster_bytes(), 1000, 240)
    assert result["status"] == "unavailable"
    assert result["reason"] == "timeout"
    assert result["words"] == []


@pytest.mark.parametrize("confidence,expected", [(69, "partial"), (70, "completed")])
def test_low_confidence_is_partial(confidence, expected):
    from brandproof import ocr

    assert hasattr(ocr, "parse_tsv"), "TSV parser is missing"
    tsv = (
        f"level\tleft\ttop\twidth\theight\tconf\ttext\n5\t2\t3\t15\t10\t{confidence}\tSALE\n"
    ).encode()
    result = ocr.parse_tsv(tsv, 100, 100)
    assert result["status"] == expected
    assert result["reason"] == ("low_confidence" if confidence < 70 else None)


def test_tsv_preserves_literal_quotes():
    from brandproof.ocr import parse_tsv

    raw = b'level\tleft\ttop\twidth\theight\tconf\ttext\n5\t2\t3\t15\t10\t95\t"SALE"\n'
    assert parse_tsv(raw, 100, 100)["text"] == '"SALE"'


@pytest.mark.parametrize(
    "raw",
    [
        b"bad header\n",
        b"x" * (1024 * 1024 + 1),
        b"level\tleft\ttop\twidth\theight\tconf\ttext\n5\t2\n",
    ],
    ids=["header", "size", "incomplete-row"],
)
def test_tsv_rejects_malformed_or_oversize_output(raw):
    from brandproof.ocr import parse_tsv

    with pytest.raises(ValueError):
        parse_tsv(raw, 100, 100)


def test_missing_real_executable_is_unavailable():
    import json
    import os
    import subprocess
    import sys

    code = (
        "import json,sys; from brandproof.ocr import extract_text; "
        "print(json.dumps(extract_text(sys.stdin.buffer.read(), 1000, 240)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=poster_bytes(),
        capture_output=True,
        env={**os.environ, "PATH": ""},
        check=True,
        timeout=20,
    )
    extraction = json.loads(result.stdout)
    assert extraction["status"] == "unavailable"
    assert extraction["reason"] == "tool_missing"
    assert extraction["words"] == []
