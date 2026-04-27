import json
import pytest


def test_state_creates_new_file_if_missing(tmp_path):
    from app.state import StateManager
    sf = str(tmp_path / "state.json")
    sm = StateManager(sf)
    assert (tmp_path / "state.json").exists()
    assert not sm.is_processed("any-id")


def test_state_loads_existing_file(tmp_path):
    sf = tmp_path / "state.json"
    sf.write_text(json.dumps({
        "processed": {"msg-1": {"status": "calendar_written", "filename": "a.pdf", "timestamp": "2026-04-27T10:00:00", "details": {}}},
        "version": "1",
    }))
    from app.state import StateManager
    sm = StateManager(str(sf))
    assert sm.is_processed("msg-1")
    assert not sm.is_processed("msg-2")


def test_state_records_success(tmp_path):
    from app.state import StateManager
    sm = StateManager(str(tmp_path / "state.json"))
    sm.record(
        message_id="msg-abc",
        status="calendar_written",
        filename="wochenplan_kw17.pdf",
        details={"dates_written": ["2026-04-27"]},
    )
    sm2 = StateManager(str(tmp_path / "state.json"))
    assert sm2.is_processed("msg-abc")
    entry = sm2.get("msg-abc")
    assert entry["status"] == "calendar_written"
    assert entry["filename"] == "wochenplan_kw17.pdf"
    assert entry["details"]["dates_written"] == ["2026-04-27"]


def test_state_records_failure_with_error(tmp_path):
    from app.state import StateManager
    sm = StateManager(str(tmp_path / "state.json"))
    sm.record(
        message_id="msg-fail",
        status="failed",
        filename="bad.pdf",
        details={"error": "PDF parse failed: no table found"},
    )
    entry = sm.get("msg-fail")
    assert entry["status"] == "failed"
    assert "error" in entry["details"]


def test_state_invalid_status_raises(tmp_path):
    from app.state import StateManager
    sm = StateManager(str(tmp_path / "state.json"))
    with pytest.raises(ValueError, match="Invalid status"):
        sm.record(message_id="msg-x", status="unknown_status")


def test_state_multiple_entries_survive_reload(tmp_path):
    from app.state import StateManager
    sm = StateManager(str(tmp_path / "state.json"))
    sm.record(message_id="msg-1", status="downloaded", filename="a.pdf")
    sm.record(message_id="msg-2", status="calendar_written", filename="b.pdf")
    sm2 = StateManager(str(tmp_path / "state.json"))
    assert sm2.is_processed("msg-1")
    assert sm2.is_processed("msg-2")
