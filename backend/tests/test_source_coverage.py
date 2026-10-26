import pytest
from test_reviews import add_source, review_copy


@pytest.mark.parametrize(
    "extra,confirm",
    [
        ({}, False),
        ({"valid_until": "2026-11-01"}, True),
        ({"valid_from": "2026-12-01"}, True),
    ],
)
def test_unavailable_sources_do_not_establish_a_complete_exact_review(
    client, owner, campaign, extra, confirm
):
    source = add_source(
        client,
        owner,
        campaign,
        {"kind": "price", "amount": "499", "currency": "INR"},
        confirm=confirm,
        **extra,
    )
    run = review_copy(client, owner, campaign, "Join for INR 599.")
    assert run["sources_used"] == []
    assert run["checks"]["exact_text"]["status"] == "not_assessed"
    assert run["excluded_sources"][0]["source_id"] == source["id"]
    assert not any(f["evidence_status"] == "contradicted" for f in run["findings"])
