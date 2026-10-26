import pytest
from test_reviews import add_source, review_copy


@pytest.mark.parametrize(
    "amount",
    ["499.999", "599.999", "1,00,000", "5,99", "499abc", "4.99e2", "-499", ".99"],
)
def test_malformed_money_is_clarification_not_truncated_comparison(client, owner, campaign, amount):
    source = add_source(
        client,
        owner,
        campaign,
        {"kind": "price", "amount": "499.99", "currency": "INR"},
    )
    text = f"Book our workshop for INR{amount}."
    run = review_copy(client, owner, campaign, text)
    assert len(run["findings"]) == 1
    finding = run["findings"][0]
    assert finding["evidence_status"] == "needs_clarification"
    assert finding["suggested_replacement"] is None
    assert finding["location"]["quote"] == f"INR{amount}"
    assert text[finding["location"]["start"] : finding["location"]["end"]] == f"INR{amount}"
    assert finding["evidence"]["quote"] == source["text"]


@pytest.mark.parametrize(
    "rule,text",
    [
        (
            {"kind": "price", "amount": "499", "currency": "INR"},
            "Workshop for INR1,00,000.",
        ),
        (
            {"kind": "price", "amount": "499", "currency": "INR"},
            "Workshop for 599 INR.",
        ),
        ({"kind": "price", "amount": "499", "currency": "INR"}, "Join our workshop."),
        ({"kind": "date", "date": "2026-11-12"}, "Workshop on 13 November 2026."),
        ({"kind": "date", "date": "2026-11-12"}, "Join our workshop."),
    ],
)
def test_unparsed_comparisons_are_not_reported_as_completed(client, owner, campaign, rule, text):
    source = add_source(client, owner, campaign, rule)
    run = review_copy(client, owner, campaign, text)
    exact = run["checks"]["exact_text"]
    assert exact["status"] in ("not_assessed", "partial")
    coverage = exact["rules"]
    assert len(coverage) == 1
    assert coverage[0]["source_id"] == source["id"]
    assert coverage[0]["status"] == "not_assessed"
    assert coverage[0]["reason"]


def test_unparsed_price_does_not_hide_independently_assessed_required_text(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Book for 599 INR.")
    exact = run["checks"]["exact_text"]
    assert exact["status"] == "partial"
    assert {r["kind"]: r["status"] for r in exact["rules"]} == {
        "price": "not_assessed",
        "required_text": "completed",
    }
    assert any(f["category"] == "required_text" for f in run["findings"])


@pytest.mark.parametrize(
    "kind,text",
    [
        ("price", "Get INR100 cashback when you register."),
        ("price", "Receive INR100 as a registration rebate."),
        ("price", "Book for INR100 cashback after registration."),
        ("price", "Early-bird workshop price INR100."),
        ("price", "Workshop price is not INR100."),
        ("price", "Do not book for INR100."),
        ("price", "INR100 is a deposit, not the workshop fee."),
        ("price", "A refund of INR100 is available."),
        ("price", "Maybe book for INR100."),
        ("date", "Early-bird registration closes on 2026-11-10."),
        ("date", "Register by 2026-11-10 for our workshop."),
        ("date", "Workshop booking deadline: 2026-11-10."),
        ("date", "Our workshop is not on 2026-11-10."),
        ("date", "Workshop on 2026-11-10 is not confirmed."),
        ("date", "Tickets go on sale on 2026-11-10."),
        ("date", "The workshop was previously scheduled for 2026-11-10."),
        ("date", "Perhaps the workshop is on 2026-11-10."),
    ],
)
def test_single_qualified_or_ambiguous_token_is_not_assumed_main_scope(
    client, owner, campaign, kind, text
):
    rule = (
        {"kind": "price", "amount": "499", "currency": "INR"}
        if kind == "price"
        else {"kind": "date", "date": "2026-11-12"}
    )
    add_source(client, owner, campaign, rule)
    run = review_copy(client, owner, campaign, text)
    assert run["findings"]
    assert all(f["evidence_status"] == "needs_clarification" for f in run["findings"])
    assert all(f["suggested_replacement"] is None for f in run["findings"])
    assert run["checks"]["exact_text"]["status"] == "partial"


def test_corrected_demo_copy_has_no_findings_and_completed_exact_text(client, owner, campaign):
    rules = [
        {"kind": "price", "amount": "499", "currency": "INR"},
        {"kind": "date", "date": "2026-11-12"},
        {"kind": "terminology", "term": "cheap", "preferred": "affordable"},
        {"kind": "required_text", "text": "Terms apply"},
    ]
    sources = [add_source(client, owner, campaign, rule) for rule in rules]
    run = review_copy(
        client,
        owner,
        campaign,
        "An affordable workshop on 2026-11-12. Book for INR 499. Terms apply.",
    )
    assert run["findings"] == []
    exact = run["checks"]["exact_text"]
    assert exact["status"] == "completed"
    assert {rule["source_id"]: (rule["kind"], rule["status"]) for rule in exact["rules"]} == {
        source["id"]: (source["rule"]["kind"], "completed") for source in sources
    }
    assert len(exact["rules"]) == len(sources)


def test_narrow_main_scope_preserves_positive_demo_smoke(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "price", "amount": "499", "currency": "INR"})
    add_source(client, owner, campaign, {"kind": "date", "date": "2026-11-12"})
    add_source(
        client,
        owner,
        campaign,
        {"kind": "terminology", "term": "cheap", "preferred": "affordable"},
    )
    run = review_copy(client, owner, campaign, "A cheap workshop on 2026-11-13. Book for INR599.")
    assert {f["category"]: f["suggested_replacement"] for f in run["findings"]} == {
        "price": "INR 499",
        "date": "2026-11-12",
        "terminology": "affordable",
    }
    assert all(f["evidence_status"] == "contradicted" for f in run["findings"])
    assert run["checks"]["exact_text"]["status"] == "completed"
