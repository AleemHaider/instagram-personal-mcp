import os

import pytest


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path, monkeypatch):
    """Each test gets a clean env + temp session path + fresh client singleton."""
    monkeypatch.delenv("IG_USERNAME", raising=False)
    monkeypatch.delenv("IG_PASSWORD", raising=False)
    monkeypatch.setenv("IG_SESSION_PATH", str(tmp_path / "session.json"))

    from instagram_personal_mcp import client

    client.reset_client()
    yield
    client.reset_client()
