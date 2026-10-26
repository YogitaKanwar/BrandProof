def test_test_client_does_not_inherit_live_provider_credentials(client):
    settings = client.app.state.settings
    assert settings.ai_provider == "none"
    assert settings.ai_model == ""
    assert settings.ai_api_key.get_secret_value() == ""
    assert settings.external_ai_enabled is False


def test_unmocked_http_transport_is_blocked_in_tests():
    import httpx
    import pytest

    with pytest.raises(RuntimeError, match="Network access is disabled in tests"):
        httpx.get("http://127.0.0.1:1", timeout=0.1)
