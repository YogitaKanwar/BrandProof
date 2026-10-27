"""Local, bounded OCR; returned coordinates refer to the canonical display PNG."""

import csv
import io
import subprocess
import time
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait

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
        deadline = time.monotonic() + OCR_TIMEOUT_SECONDS

        def read_bounded(pipe, limit):
            data = bytearray()
            while chunk := pipe.read1(65536):
                if len(data) + len(chunk) > limit:
                    raise ValueError("OCR output limit")
                data.extend(chunk)
            return bytes(data)

        def write_input():
            try:
                process.stdin.write(png)
                process.stdin.flush()
            finally:
                process.stdin.close()

        # Windows selectors cannot monitor subprocess pipes. Concurrent bounded
        # readers also prevent either pipe from blocking the input writer.
        with ThreadPoolExecutor(max_workers=3) as workers:
            output = workers.submit(read_bounded, process.stdout, MAX_OCR_OUTPUT_BYTES)
            errors = workers.submit(read_bounded, process.stderr, MAX_OCR_ERROR_BYTES)
            writer = workers.submit(write_input)
            futures = {output, errors, writer}
            try:
                done, pending = wait(
                    futures,
                    timeout=max(0, deadline - time.monotonic()),
                    return_when=FIRST_EXCEPTION,
                )
                for future in done:
                    future.result()
                remaining = deadline - time.monotonic()
                if pending or remaining <= 0:
                    raise subprocess.TimeoutExpired("tesseract", OCR_TIMEOUT_SECONDS)
                if process.wait(timeout=remaining) != 0:
                    raise ValueError("OCR process failed")
                return output.result()
            except BaseException:
                if process.poll() is None:
                    process.kill()
                process.wait()
                # Killing the child unblocks all three pipe workers before the
                # executor and Popen close their resources. No images hit disk.
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
