import httpx
from brandproof.contextual import analyze_context
from test_contextual import enabled, source


def test_provider_http_error_records_status_without_raw_error_or_secret():
    result = analyze_context(
        "Workshop invitation",
        1,
        [source()],
        enabled(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                429, json={"error": "private provider diagnostic secret-key"}
            )
        ),
    )
    assert result.status == "unavailable"
    assert result.metadata["http_status"] == 429
    assert result.metadata["failure_kind"] == "rate_limited"
    assert "private provider diagnostic" not in str(result)
    assert "secret-key" not in str(result)
