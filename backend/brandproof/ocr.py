"""Local, bounded OCR; returned coordinates refer to the canonical display PNG."""

import csv
import io
import selectors
import subprocess
import time

OCR_TIMEOUT_SECONDS = 15
MAX_OCR_OUTPUT_BYTES = 1024 * 1024
MAX_OCR_ERROR_BYTES = 64 * 1024


def _run_tesseract(png: bytes) -> bytes:
    """Drain pipes incrementally: neither stderr nor TSV may grow without bound."""
    with subprocess.Popen(
        ["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "6", "tsv"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    ) as process:
        try:
            output = bytearray()
            errors = 0
            offset = 0
            deadline = time.monotonic() + OCR_TIMEOUT_SECONDS
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdin, selectors.EVENT_WRITE, "input")
                selector.register(process.stdout, selectors.EVENT_READ, "output")
                selector.register(process.stderr, selectors.EVENT_READ, "error")
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired("tesseract", OCR_TIMEOUT_SECONDS)
                    for key, _ in selector.select(min(remaining, 0.1)):
                        if key.data == "input":
                            if offset < len(png):
                                offset += key.fileobj.write(png[offset : offset + 4096])
                                key.fileobj.flush()
                            else:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            chunk = key.fileobj.read1(65536)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            if key.data == "output":
                                output.extend(chunk)
                                if len(output) > MAX_OCR_OUTPUT_BYTES:
                                    raise ValueError("OCR output limit")
                            else:
                                errors += len(chunk)
                                if errors > MAX_OCR_ERROR_BYTES:
                                    raise ValueError("OCR diagnostic limit")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired("tesseract", OCR_TIMEOUT_SECONDS)
            if process.wait(timeout=remaining) != 0:
                raise ValueError("OCR process failed")
            return bytes(output)
        except BaseException:
            process.kill()
            process.wait()
            raise


def extract_text(png: bytes, width: int, height: int) -> dict:
    try:
        return parse_tsv(_run_tesseract(png), width, height)
    except subprocess.TimeoutExpired:
        reason = "timeout"
    except FileNotFoundError:
        reason = "tool_missing"
    except (OSError, ValueError, KeyError, csv.Error, UnicodeError):
        reason = "extraction_failed"
    return {
        "engine": "tesseract",
        "status": "unavailable",
        "reason": reason,
        "text": "",
        "words": [],
    }


def parse_tsv(raw: bytes, width: int, height: int) -> dict:
    if len(raw) > MAX_OCR_OUTPUT_BYTES:
        raise ValueError("OCR output limit")
    reader = csv.DictReader(
        io.StringIO(raw.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE
    )
    required = {"level", "text", "left", "top", "width", "height", "conf"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("Invalid OCR header")
    words = []
    text = ""
    for row in reader:
        if None in row or any(row.get(key) is None for key in required):
            raise ValueError("Invalid OCR row")
        if row["level"] != "5" or not row["text"].strip():
            continue
        value = row["text"].strip()
        x, y, w, h = (int(row[k]) for k in ("left", "top", "width", "height"))
        confidence = float(row["conf"]) / 100
        if not (0 <= x < width and 0 <= y < height and 0 < w <= width - x and 0 < h <= height - y):
            raise ValueError("Invalid OCR coordinates")
        if not 0 <= confidence <= 1:
            raise ValueError("Invalid OCR confidence")
        start = len(text) + bool(text)
        text += (" " if text else "") + value
        words.append(
            {
                "text": value,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "confidence": confidence,
                "start": start,
                "end": len(text),
            }
        )
    reason = (
        "unreadable"
        if not words
        else ("low_confidence" if any(word["confidence"] < 0.7 for word in words) else None)
    )
    return {
        "engine": "tesseract",
        "status": "partial" if reason else "completed",
        "reason": reason,
        "text": text,
        "words": words,
    }
