import json
import pytest
from unittest.mock import MagicMock, patch


def _set_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GMAIL_EMAIL", "test@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setenv("GMAIL_IMAP_HOST", "imap.gmail.com")
    monkeypatch.setenv("GMAIL_IMAP_PORT", "993")
    monkeypatch.setenv("ICLOUD_CALDAV_URL", "https://caldav.icloud.com")
    monkeypatch.setenv("ICLOUD_USERNAME", "user@icloud.com")
    monkeypatch.setenv("ICLOUD_APP_PASSWORD", "calpass")
    monkeypatch.setenv("ICLOUD_CALENDAR_NAME", "Wochenplan")
    monkeypatch.setenv("CALENDAR_EVENT_TITLE", "Kollegen laut Wochenplan")
    monkeypatch.setenv("CALENDAR_EVENT_PREFIX", "[WEEKLY_PLAN_COLLEAGUES]")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("DEBUG_PDF_TEXT", "false")
    monkeypatch.setenv("NTFY_ENABLED", "false")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("DEBUG_DIR", str(tmp_path / "debug"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))


def test_dry_run_does_not_connect_calendar(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path)

    mock_gmail = MagicMock()
    mock_gmail.find_relevant_emails.return_value = [
        {"message_id": "msg-1", "subject": "Wochenplan KW17", "date": "", "raw": b""}
    ]
    mock_gmail.download_email_attachments.return_value = [str(tmp_path / "plan.pdf")]

    mock_parser = MagicMock()
    mock_parser.parse.return_value = {"2026-04-27": ["Alice", "Bob"]}

    mock_calendar = MagicMock()

    with patch("app.main.GmailClient", return_value=mock_gmail), \
         patch("app.main.PDFParser", return_value=mock_parser), \
         patch("app.main.CalendarClient", return_value=mock_calendar), \
         patch("app.main.Notifier", return_value=MagicMock()):
        from importlib import reload
        import app.main as m
        reload(m)
        exit_code = m.run()

    mock_calendar.connect.assert_not_called()
    mock_calendar.upsert_event.assert_called()
    for call in mock_calendar.upsert_event.call_args_list:
        assert call.kwargs.get("dry_run", True) is True
    assert exit_code == 0


def test_already_processed_message_skipped(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path)
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({
        "processed": {"msg-1": {"status": "calendar_written", "filename": "a.pdf", "timestamp": "2026-04-27T10:00:00", "details": {}}},
        "version": "1",
    }))

    mock_gmail = MagicMock()
    mock_gmail.find_relevant_emails.return_value = [
        {"message_id": "msg-1", "subject": "Wochenplan KW17", "date": "", "raw": b""}
    ]
    mock_parser = MagicMock()
    mock_calendar = MagicMock()

    with patch("app.main.GmailClient", return_value=mock_gmail), \
         patch("app.main.PDFParser", return_value=mock_parser), \
         patch("app.main.CalendarClient", return_value=mock_calendar), \
         patch("app.main.Notifier", return_value=MagicMock()):
        from importlib import reload
        import app.main as m
        reload(m)
        m.run()

    mock_parser.parse.assert_not_called()


def test_parser_failure_records_failed_state(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path)

    mock_gmail = MagicMock()
    mock_gmail.find_relevant_emails.return_value = [
        {"message_id": "msg-parse-fail", "subject": "Wochenplan", "date": "", "raw": b""}
    ]
    mock_gmail.download_email_attachments.return_value = [str(tmp_path / "plan.pdf")]

    mock_parser = MagicMock()
    mock_parser.parse.return_value = {}

    mock_calendar = MagicMock()

    with patch("app.main.GmailClient", return_value=mock_gmail), \
         patch("app.main.PDFParser", return_value=mock_parser), \
         patch("app.main.CalendarClient", return_value=mock_calendar), \
         patch("app.main.Notifier", return_value=MagicMock()):
        from importlib import reload
        import app.main as m
        reload(m)
        exit_code = m.run()

    from app.state import StateManager
    sm = StateManager(str(tmp_path / "state.json"))
    entry = sm.get("msg-parse-fail")
    assert entry is not None
    assert entry["status"] == "failed"
    assert exit_code == 1
