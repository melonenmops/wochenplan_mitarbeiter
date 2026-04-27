import pytest


def _set_all_env(monkeypatch):
    monkeypatch.setenv("GMAIL_IMAP_HOST", "imap.gmail.com")
    monkeypatch.setenv("GMAIL_IMAP_PORT", "993")
    monkeypatch.setenv("GMAIL_EMAIL", "test@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setenv("ICLOUD_CALDAV_URL", "https://caldav.icloud.com")
    monkeypatch.setenv("ICLOUD_USERNAME", "user@icloud.com")
    monkeypatch.setenv("ICLOUD_APP_PASSWORD", "appsecret")
    monkeypatch.setenv("ICLOUD_CALENDAR_NAME", "Wochenplan")
    monkeypatch.setenv("CALENDAR_EVENT_TITLE", "Kollegen laut Wochenplan")
    monkeypatch.setenv("CALENDAR_EVENT_PREFIX", "[WEEKLY_PLAN_COLLEAGUES]")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("DEBUG_PDF_TEXT", "false")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("STATE_FILE", "data/state.json")
    monkeypatch.setenv("DOWNLOAD_DIR", "data/downloads")
    monkeypatch.setenv("DEBUG_DIR", "data/debug")
    monkeypatch.setenv("LOG_DIR", "data/logs")


def test_config_loads_required_values(monkeypatch):
    _set_all_env(monkeypatch)
    from importlib import reload
    import app.config as m
    reload(m)
    cfg = m.Config()

    assert cfg.gmail_email == "test@gmail.com"
    assert cfg.gmail_imap_port == 993
    assert cfg.dry_run is True
    assert cfg.debug_pdf_text is False
    assert cfg.calendar_event_prefix == "[WEEKLY_PLAN_COLLEAGUES]"
    assert cfg.icloud_calendar_name == "Wochenplan"


def test_config_raises_on_missing_gmail_password(monkeypatch):
    _set_all_env(monkeypatch)
    monkeypatch.delenv("GMAIL_APP_PASSWORD")
    from importlib import reload
    import app.config as m
    reload(m)
    with pytest.raises(EnvironmentError, match="GMAIL_APP_PASSWORD"):
        m.Config()


def test_config_raises_on_missing_icloud_password(monkeypatch):
    _set_all_env(monkeypatch)
    monkeypatch.delenv("ICLOUD_APP_PASSWORD")
    from importlib import reload
    import app.config as m
    reload(m)
    with pytest.raises(EnvironmentError, match="ICLOUD_APP_PASSWORD"):
        m.Config()


def test_config_repr_does_not_leak_secrets(monkeypatch):
    _set_all_env(monkeypatch)
    from importlib import reload
    import app.config as m
    reload(m)
    cfg = m.Config()
    r = repr(cfg)
    assert "secret" not in r
    assert "appsecret" not in r
