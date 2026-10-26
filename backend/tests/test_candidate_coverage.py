import pytest
from test_reviews import add_source, review_copy


@pytest.mark.parametrize("raw", ["2026-11-12..99", "2026-11-13..99", "2026-11-12abc", "2026-02-30"])
def test_date_candidates_do_not_compare_invalid_or_truncated_calendar_tokens(
    client, owner, campaign, raw
):
    add_source(client, owner, campaign, {"kind": "date", "date": "2026-11-12"})
    run = review_copy(client, owner, campaign, f"Workshop on {raw}.")
    assert run["checks"]["exact_text"]["status"] != "completed"
    assert run["findings"]
    assert all(f["evidence_status"] == "needs_clarification" for f in run["findings"])
    assert run["findings"][0]["location"]["quote"] == raw
    assert all(f["suggested_replacement"] is None for f in run["findings"])


@pytest.mark.parametrize("amount", ["499..99", "599..99", "499,,99", "499...99"])
def test_repeated_separators_never_compare_or_replace_a_numeric_prefix(
    client, owner, campaign, amount
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, f"Book for INR{amount}.")
    stored = client.get(
        f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}", headers=owner
    ).json()
    assert stored["checks"]["exact_text"]["status"] != "completed"
    assert stored["findings"]
    assert all(f["evidence_status"] == "needs_clarification" for f in stored["findings"])
    assert all(f["suggested_replacement"] is None for f in stored["findings"])
    assert stored["findings"][0]["location"]["quote"] == f"INR{amount}"


@pytest.mark.parametrize(
    "rule,text",
    [
        (
            {"kind": "price", "amount": "499", "currency": "INR"},
            "Book for INR499. Book for 599 INR.",
        ),
        (
            {"kind": "price", "amount": "499", "currency": "INR"},
            "Book for INR599. Book for 499 INR.",
        ),
        (
            {"kind": "date", "date": "2026-11-12"},
            "Workshop on 2026-11-12. Workshop on 13 November 2026.",
        ),
        (
            {"kind": "date", "date": "2026-11-12"},
            "Workshop on 2026-11-13. Workshop on November 12, 2026.",
        ),
        ({"kind": "date", "date": "2026-11-12"}, "Workshop on 2026-11-12. Workshop on 13/11/2026."),
    ],
)
def test_unsupported_candidate_cannot_hide_behind_a_supported_value(
    client, owner, campaign, rule, text
):
    add_source(client, owner, campaign, rule)
    run = review_copy(client, owner, campaign, text)
    stored = client.get(
        f"/api/v1/campaigns/{campaign['id']}/reviews/{run['id']}", headers=owner
    ).json()
    exact = stored["checks"]["exact_text"]
    assert exact["status"] == "partial"
    assert exact["rules"][0]["status"] == "partial"
    assert stored["findings"]
    assert all(f["suggested_replacement"] is None for f in stored["findings"])


@pytest.mark.parametrize(
    "text", ["Book for INR499.999. Book for INR499.", "Book for INR499. Book for INR499..99."]
)
def test_malformed_and_supported_amounts_do_not_produce_completed_coverage(
    client, owner, campaign, text
):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    run = review_copy(client, owner, campaign, text)
    assert run["checks"]["exact_text"]["status"] == "partial"
    assert run["checks"]["exact_text"]["rules"][0]["status"] == "partial"
    assert all(f["suggested_replacement"] is None for f in run["findings"])
