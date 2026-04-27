import logging
from unittest.mock import patch, MagicMock

import app.notify as notify_module
from app.notify import Notifier


def test_sends_when_enabled():
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="test-topic")
    with patch("app.notify._requests") as mock_requests:
        mock_requests.post.return_value.status_code = 200
        n.send("Title", "Body")
    mock_requests.post.assert_called_once()
    assert "test-topic" in mock_requests.post.call_args[0][0]


def test_skips_when_disabled():
    n = Notifier(enabled=False, url="https://ntfy.sh", topic="test-topic")
    with patch("app.notify._requests") as mock_requests:
        n.send("Title", "Body")
    mock_requests.post.assert_not_called()


def test_does_not_raise_on_network_error():
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="test-topic")
    with patch("app.notify._requests") as mock_requests:
        mock_requests.post.side_effect = Exception("timeout")
        n.send("Title", "Body")  # must not raise


def test_skips_when_no_topic():
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="")
    with patch("app.notify._requests") as mock_requests:
        n.send("Title", "Body")
    mock_requests.post.assert_not_called()


def test_skips_when_requests_not_installed(caplog):
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="test-topic")
    original = notify_module._HAS_REQUESTS
    try:
        notify_module._HAS_REQUESTS = False
        with caplog.at_level(logging.WARNING, logger="wochenplan.notify"):
            n.send("Title", "Body")  # must not raise
        assert any("requests not installed" in r.message for r in caplog.records)
    finally:
        notify_module._HAS_REQUESTS = original
