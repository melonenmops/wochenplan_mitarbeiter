import pytest
from datetime import date
from unittest.mock import MagicMock, patch


def _make_client(mock_calendar=None):
    from app.calendar_client import CalendarClient
    client = CalendarClient.__new__(CalendarClient)
    client.event_title = "Kollegen laut Wochenplan"
    client.event_prefix = "[WEEKLY_PLAN_COLLEAGUES]"
    client.logger = MagicMock()
    client._calendar = mock_calendar or MagicMock()
    return client


def test_dry_run_does_not_touch_calendar():
    client = _make_client()
    client.upsert_event(date(2026, 4, 27), ["Alice"], dry_run=True)
    client._calendar.save_event.assert_not_called()
    client._calendar.search.assert_not_called()


def test_upsert_creates_event_when_none_exists():
    mock_cal = MagicMock()
    mock_cal.search.return_value = []
    client = _make_client(mock_cal)
    client.upsert_event(date(2026, 4, 27), ["Alice", "Bob"], dry_run=False)
    mock_cal.save_event.assert_called_once()
    ical = mock_cal.save_event.call_args[0][0]
    assert "Alice" in ical
    assert "Bob" in ical


def test_upsert_deletes_old_event_before_creating():
    mock_cal = MagicMock()
    existing = MagicMock()
    existing.vobject_instance.vevent.summary.value = "[WEEKLY_PLAN_COLLEAGUES] Kollegen laut Wochenplan"
    mock_cal.search.return_value = [existing]
    client = _make_client(mock_cal)
    client.upsert_event(date(2026, 4, 27), ["Updated"], dry_run=False)
    existing.delete.assert_called_once()
    mock_cal.save_event.assert_called_once()


def test_build_ical_produces_valid_structure():
    client = _make_client()
    ical = client._build_ical(date(2026, 4, 27), ["Alice", "Bob"])
    assert "BEGIN:VCALENDAR" in ical
    assert "BEGIN:VEVENT" in ical
    assert "DTSTART;VALUE=DATE:20260427" in ical
    assert "DTEND;VALUE=DATE:20260428" in ical
    assert "[WEEKLY_PLAN_COLLEAGUES]" in ical
    assert "Alice" in ical
    assert "END:VEVENT" in ical
    assert "END:VCALENDAR" in ical


def test_upsert_raises_without_connect():
    from app.calendar_client import CalendarClient
    client = CalendarClient.__new__(CalendarClient)
    client._calendar = None
    client.event_title = "Test"
    client.event_prefix = "[TEST]"
    client.logger = MagicMock()
    with pytest.raises(RuntimeError, match="Not connected"):
        client.upsert_event(date(2026, 4, 27), ["Alice"], dry_run=False)
