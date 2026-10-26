from test_reviews import add_source, review_copy


def test_wrong_iso_campaign_date_has_located_source_evidence(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "date", "date": "2026-11-12"})
    run = review_copy(client, owner, campaign, "Join our workshop on 2026-11-13.")
    assert len(run["findings"]) == 1
    finding = run["findings"][0]
    assert finding["category"] == "date"
    assert finding["location"]["quote"] == "2026-11-13"
    assert finding["suggested_replacement"] == "2026-11-12"


def test_terminology_matches_whole_words_without_changing_related_words(client, owner, campaign):
    add_source(
        client, owner, campaign, {"kind": "terminology", "term": "cheap", "preferred": "affordable"}
    )
    run = review_copy(
        client, owner, campaign, "A cheaper option is not the same as a CHEAP workshop."
    )
    assert len(run["findings"]) == 1
    finding = run["findings"][0]
    assert finding["category"] == "terminology"
    assert finding["location"]["quote"] == "CHEAP"
    assert finding["suggested_replacement"] == "affordable"


def test_required_text_is_missing_without_claiming_a_nonexistent_span(client, owner, campaign):
    add_source(client, owner, campaign, {"kind": "required_text", "text": "Terms apply"})
    run = review_copy(client, owner, campaign, "Join our workshop.")
    assert len(run["findings"]) == 1
    finding = run["findings"][0]
    assert finding["category"] == "required_text"
    assert finding["location"]["start"] is None
    assert finding["suggested_replacement"] == "Terms apply"
    clean = review_copy(client, owner, campaign, "Join our workshop. TERMS APPLY.")
    assert clean["findings"] == []
