"""Find bounded lexical candidates before interpreting/comparing their values.

Candidate discovery is deliberately broader than supported parsing. Unknown
formats remain explicit candidates; they cannot disappear behind a valid match.
This is not general natural-language or commercial-scope understanding.
"""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

CURRENCY_NAMES = r"INR|USD|EUR|GBP|Rs\.?|₹|\$|€|£"
PREFIX = re.compile(rf"(?<!\w)(?P<currency>{CURRENCY_NAMES})\s*(?=[+\-.0-9])", re.IGNORECASE)
SUFFIX = re.compile(
    rf"(?<![\w.,])(?P<number>[+\-]?[0-9][0-9.,]*(?:[eE][+\-]?[0-9]+)?)\s*(?P<currency>{CURRENCY_NAMES})(?!\w)",
    re.IGNORECASE,
)
AMOUNT = re.compile(r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?")
CURRENCIES = {"RS": "INR", "RS.": "INR", "₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_PATTERNS = [
    re.compile(r"(?<!\w)[0-9]{4}[-/.][0-9]{1,2}[-/.][0-9]{1,2}"),
    re.compile(r"(?<!\w)[0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4}"),
    re.compile(
        rf"(?<!\w)[0-9]{{1,2}}(?:st|nd|rd|th)?\s+{MONTH}\.?(?:\s*,?\s*[0-9]{{2,4}})?(?!\w)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?<!\w){MONTH}\.?\s+[0-9]{{1,2}}(?:st|nd|rd|th)?(?:\s*,?\s*[0-9]{{2,4}})?(?!\w)",
        re.IGNORECASE,
    ),
]


@dataclass(frozen=True)
class Candidate:
    raw: str
    begin: int
    finish: int
    supported: bool
    value: Decimal | str | None = None
    currency: str | None = None
    reason: str | None = None

    # Match-compatible location methods keep all finding offsets end-exclusive.
    def start(self):
        return self.begin

    def end(self):
        return self.finish

    def group(self, index=0):
        if index != 0:
            raise IndexError(index)
        return self.raw


def overlaps(start, end, candidates):
    return any(start < c.finish and c.begin < end for c in candidates)


def numeric_token_end(text: str, start: int, *, separators: str = ".,_") -> int:
    """Consume full adjoining numeric-looking text without regex backtracking."""
    end = start
    if end < len(text) and text[end] in "+-":
        end += 1
    while end < len(text) and (text[end].isalnum() or text[end] in separators):
        end += 1
    # One terminal full stop is sentence punctuation. Repeated punctuation is
    # retained as ambiguous/malformed, never reinterpreted as a valid prefix.
    if end > start and text[end - 1] == "." and not text[start:end].endswith(".."):
        end -= 1
    return end


def money_candidates(text: str) -> list[Candidate]:
    found = []
    for anchor in PREFIX.finditer(text):
        end = numeric_token_end(text, anchor.end())
        body = text[anchor.end() : end]
        valid = bool(AMOUNT.fullmatch(body))
        currency = CURRENCIES.get(
            anchor.group("currency").upper(), anchor.group("currency").upper()
        )
        found.append(
            Candidate(
                text[anchor.start() : end],
                anchor.start(),
                end,
                valid,
                Decimal(body.replace(",", "")) if valid else None,
                currency,
                None if valid else "Malformed or unsupported currency-qualified numeric token.",
            )
        )
    for anchor in SUFFIX.finditer(text):
        if not overlaps(anchor.start(), anchor.end(), found):
            found.append(
                Candidate(
                    anchor.group(),
                    anchor.start(),
                    anchor.end(),
                    False,
                    reason="Suffix-currency notation is recognised but not supported for exact comparison.",
                )
            )
    return sorted(found, key=lambda c: c.begin)


def date_candidates(text: str) -> list[Candidate]:
    found = []
    for pattern in DATE_PATTERNS:
        for anchor in pattern.finditer(text):
            start, end = anchor.span()
            if overlaps(start, end, found):
                continue
            # ISO-looking strings with attached digits/letters/separators are
            # one unsupported candidate, not a supported calendar-date prefix.
            if text[start].isdigit():
                end = max(end, numeric_token_end(text, start, separators=".,_-/"))
            raw = text[start:end]
            valid = False
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw):
                try:
                    date.fromisoformat(raw)
                    valid = True
                except ValueError:
                    pass
            found.append(
                Candidate(
                    raw,
                    start,
                    end,
                    valid,
                    raw if valid else None,
                    reason=None
                    if valid
                    else "Recognised date expression is outside the supported valid ISO-date grammar.",
                )
            )
    return sorted(found, key=lambda c: c.begin)
