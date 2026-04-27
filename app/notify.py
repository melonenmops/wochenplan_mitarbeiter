import logging
from typing import Optional

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class Notifier:
    def __init__(
        self,
        enabled: bool,
        url: str,
        topic: str,
        username: str = "",
        password: str = "",
        logger: Optional[logging.Logger] = None,
    ):
        self.enabled = enabled
        self.url = url.rstrip("/")
        self.topic = topic
        self.username = username
        self._password = password
        self.logger = logger or logging.getLogger("wochenplan.notify")

    def send(self, title: str, message: str, priority: str = "default") -> None:
        if not self.enabled:
            return
        if not _HAS_REQUESTS:
            self.logger.warning("requests not installed — cannot send ntfy notification")
            return
        if not self.topic:
            self.logger.warning("NTFY_TOPIC not set — skipping notification")
            return

        auth = (self.username, self._password) if self.username and self._password else None
        try:
            resp = _requests.post(
                f"{self.url}/{self.topic}",
                data=message.encode("utf-8"),
                headers={"Title": title, "Priority": priority, "Content-Type": "text/plain"},
                auth=auth,
                timeout=10,
            )
            if resp.status_code >= 300:
                self.logger.warning(f"ntfy responded with status {resp.status_code}")
            else:
                self.logger.debug(f"ntfy sent: '{title}'")
        except Exception as e:
            self.logger.warning(f"ntfy notification failed (non-critical): {e}")
