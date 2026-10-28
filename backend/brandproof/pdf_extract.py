"""Isolated bounded PDF text extraction. Never execute document actions or links."""

import io
import json
import logging
import sys

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 30
MAX_PAGE_CHARS = 8000
MAX_TOTAL_CHARS = 60000


def extract(raw):
    import pypdf.filters
    from pypdf import PdfReader

    pypdf.filters.ZLIB_MAX_OUTPUT_LENGTH = 1024 * 1024
    if not raw.startswith(b"%PDF-") or len(raw) > MAX_BYTES:
        raise ValueError("Unsupported PDF")
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted or len(reader.pages) > MAX_PAGES:
        raise ValueError("Encrypted or oversized PDF")
    pages = []
    used = 0
    for number, page in enumerate(reader.pages, 1):
        try:
            content = page.get_contents()
            if content is not None and len(content.get_data()) > 1024 * 1024:
                raise ValueError("Page stream too large")
            text = page.extract_text() or ""
            remaining = min(MAX_PAGE_CHARS, MAX_TOTAL_CHARS - used)
            limited = len(text) > remaining
            text = text[:remaining]
            used += len(text)
            pages.append(
                {
                    "page_number": number,
                    "text": text,
                    "status": "partial"
                    if limited
                    else "completed"
                    if text.strip()
                    else "unavailable",
                    "reason": "text_limit"
                    if limited
                    else None
                    if text.strip()
                    else "no_extractable_text_scanned_or_blank",
                }
            )
        except Exception:
            pages.append(
                {
                    "page_number": number,
                    "text": "",
                    "status": "unavailable",
                    "reason": "unsupported_page",
                }
            )
    return {
        "status": "completed"
        if pages and all(p["status"] == "completed" for p in pages)
        else "partial"
        if any(p["text"] for p in pages)
        else "unavailable",
        "pages": pages,
        "scope": "PDF text layer only; scanned pages require manual transcription. Verify extracted quotes against the original page.",
    }


def main():
    logging.disable(logging.CRITICAL)
    try:
        if sys.platform != "win32":
            import resource

            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        result = extract(sys.stdin.buffer.read(MAX_BYTES + 1))
        print(json.dumps(result, ensure_ascii=True))
    except Exception:
        print(json.dumps({"error": "unsupported_or_resource_limited_pdf"}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
