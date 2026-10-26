import importlib

import pytest


def test_launch_configuration_is_single_worker_and_port_bounded(monkeypatch):
    serve = importlib.import_module("brandproof.serve")
    monkeypatch.setenv("PORT", "8123")
    seen = {}
    monkeypatch.setattr(
        serve.uvicorn, "run", lambda *args, **kwargs: seen.update(target=args[0], **kwargs)
    )
    serve.main()
    assert seen == {
        "target": "brandproof.main:create_app",
        "factory": True,
        "host": "0.0.0.0",
        "port": 8123,
        "workers": 1,
        "access_log": False,
    }
    for value in ["0", "65536", "not-a-port"]:
        monkeypatch.setenv("PORT", value)
        with pytest.raises(SystemExit):
            serve.main()
