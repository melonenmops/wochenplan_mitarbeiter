from unittest.mock import patch, MagicMock


def test_sends_when_enabled():
    from app.notify import Notifier
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="test-topic")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        n.send("Title", "Body")
    mock_post.assert_called_once()
    assert "test-topic" in mock_post.call_args[0][0]


def test_skips_when_disabled():
    from app.notify import Notifier
    n = Notifier(enabled=False, url="https://ntfy.sh", topic="test-topic")
    with patch("requests.post") as mock_post:
        n.send("Title", "Body")
    mock_post.assert_not_called()


def test_does_not_raise_on_network_error():
    from app.notify import Notifier
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="test-topic")
    with patch("requests.post", side_effect=Exception("timeout")):
        n.send("Title", "Body")  # must not raise


def test_skips_when_no_topic():
    from app.notify import Notifier
    n = Notifier(enabled=True, url="https://ntfy.sh", topic="")
    with patch("requests.post") as mock_post:
        n.send("Title", "Body")
    mock_post.assert_not_called()
