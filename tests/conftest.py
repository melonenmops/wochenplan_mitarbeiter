import pytest


@pytest.fixture(autouse=True)
def no_env_leak(monkeypatch):
    for key in [
        "GMAIL_APP_PASSWORD", "ICLOUD_APP_PASSWORD",
        "NTFY_PASSWORD", "DRY_RUN",
    ]:
        monkeypatch.delenv(key, raising=False)
