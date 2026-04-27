import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

try:
    import caldav
    _HAS_CALDAV = True
except ImportError:
    _HAS_CALDAV = False


class CalendarClient:
    def __init__(
        self,
        caldav_url: str,
        username: str,
        app_password: str,
        calendar_name: str,
        event_title: str,
        event_prefix: str,
        logger: Optional[logging.Logger] = None,
    ):
        self.caldav_url = caldav_url
        self.username = username
        self._app_password = app_password
        self.calendar_name = calendar_name
        self.event_title = event_title
        self.event_prefix = event_prefix
        self.logger = logger or logging.getLogger("wochenplan.calendar")
        self._calendar = None
        self._dav_client = None

    def connect(self) -> None:
        if not _HAS_CALDAV:
            raise RuntimeError("caldav library not installed — run: pip install caldav")
        self.logger.info(f"Connecting to CalDAV: {self.caldav_url}")
        self._dav_client = caldav.DAVClient(
            url=self.caldav_url,
            username=self.username,
            password=self._app_password,
        )
        principal = self._dav_client.principal()
        calendars = principal.calendars()
        self.logger.info(f"Found {len(calendars)} calendar(s)")
        for cal in calendars:
            if cal.name == self.calendar_name:
                self._calendar = cal
                self.logger.info(f"Using calendar: '{self.calendar_name}'")
                return
        names = [c.name for c in calendars]
        raise ValueError(
            f"Calendar '{self.calendar_name}' not found. Available: {names}"
        )

    def close(self) -> None:
        if self._dav_client:
            try:
                self._dav_client.close()
            except Exception:
                pass
            finally:
                self._dav_client = None
                self._calendar = None

    def upsert_event(
        self,
        event_date: date,
        names: List[str],
        dry_run: bool = True,
    ) -> None:
        if dry_run:
            self.logger.info(
                f"[DRY-RUN] Would upsert {event_date.isoformat()}: "
                f"{len(names)} name(s): {', '.join(names)}"
            )
            return

        if self._calendar is None:
            raise RuntimeError("Not connected. Call connect() first.")

        existing_events = self._find_existing(event_date)
        for ev in existing_events:
            self.logger.info(f"Removing existing event for {event_date.isoformat()}")
            ev.delete()

        ical = self._build_ical(event_date, names)
        self._calendar.add_event(ical)
        self.logger.info(f"Saved event for {event_date.isoformat()} ({len(names)} names)")

    def _find_existing(self, event_date: date) -> list:
        matches = []
        try:
            start = datetime(event_date.year, event_date.month, event_date.day)
            end = start + timedelta(days=1)
            events = self._calendar.search(start=start, end=end, event=True)
            for ev in events:
                try:
                    summary = ev.vobject_instance.vevent.summary.value
                    if summary.startswith(self.event_prefix):
                        matches.append(ev)
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"Error searching calendar for {event_date}: {e}")
        return matches

    @staticmethod
    def _ical_escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")

    @staticmethod
    def _ical_fold(line: str) -> str:
        """Fold iCalendar lines longer than 75 octets per RFC 5545 §3.1."""
        encoded = line.encode("utf-8")
        if len(encoded) <= 75:
            return line + "\r\n"
        result = []
        pos = 0
        first = True
        while pos < len(encoded):
            limit = 75 if first else 74  # 74 because folded lines start with a space
            chunk = encoded[pos:pos + limit]
            # Back off to a valid UTF-8 boundary
            while len(chunk) > 0:
                try:
                    chunk.decode("utf-8")
                    break
                except UnicodeDecodeError:
                    chunk = chunk[:-1]
            result.append(("" if first else " ") + chunk.decode("utf-8"))
            pos += len(chunk)
            first = False
        return "\r\n".join(result) + "\r\n"

    def _build_ical(self, event_date: date, names: List[str]) -> str:
        uid = str(uuid.uuid4())
        d_start = event_date.strftime("%Y%m%d")
        d_end = (event_date + timedelta(days=1)).strftime("%Y%m%d")
        summary = self._ical_escape(f"{self.event_prefix} {self.event_title}")
        escaped_names = [self._ical_escape(n) for n in names]
        description = "Anwesende Kollegen:\\n" + "\\n".join(f"- {n}" for n in escaped_names)
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//weekly-plan-calendar-notes//DE",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{d_start}",
            f"DTEND;VALUE=DATE:{d_end}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "".join(self._ical_fold(line) for line in lines)
