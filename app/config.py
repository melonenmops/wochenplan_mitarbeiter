import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise EnvironmentError(f"Required environment variable not set: {name}")
    return val


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("true", "1", "yes")


def _int_env(name: str, default: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Environment variable {name!r} must be an integer, got: {raw!r}")


@dataclass
class Config:
    # Gmail
    gmail_imap_host: str = field(default_factory=lambda: _optional("GMAIL_IMAP_HOST", "imap.gmail.com"))
    gmail_imap_port: int = field(default_factory=lambda: _int_env("GMAIL_IMAP_PORT", 993))
    gmail_email: str = field(default_factory=lambda: _require("GMAIL_EMAIL"))
    gmail_app_password: str = field(default_factory=lambda: _require("GMAIL_APP_PASSWORD"))

    # iCloud CalDAV
    icloud_caldav_url: str = field(default_factory=lambda: _optional("ICLOUD_CALDAV_URL", "https://caldav.icloud.com"))
    icloud_username: str = field(default_factory=lambda: _require("ICLOUD_USERNAME"))
    icloud_app_password: str = field(default_factory=lambda: _require("ICLOUD_APP_PASSWORD"))
    icloud_calendar_name: str = field(default_factory=lambda: _require("ICLOUD_CALENDAR_NAME"))

    # Calendar event
    calendar_event_title: str = field(default_factory=lambda: _optional("CALENDAR_EVENT_TITLE", "Kollegen laut Wochenplan"))
    calendar_event_prefix: str = field(default_factory=lambda: _optional("CALENDAR_EVENT_PREFIX", "[WEEKLY_PLAN_COLLEAGUES]"))

    # ntfy
    ntfy_enabled: bool = field(default_factory=lambda: _bool_env("NTFY_ENABLED", False))
    ntfy_url: str = field(default_factory=lambda: _optional("NTFY_URL", "https://ntfy.sh"))
    ntfy_topic: str = field(default_factory=lambda: _optional("NTFY_TOPIC"))
    ntfy_username: str = field(default_factory=lambda: _optional("NTFY_USERNAME"))
    ntfy_password: str = field(default_factory=lambda: _optional("NTFY_PASSWORD"))

    # Behavior
    dry_run: bool = field(default_factory=lambda: _bool_env("DRY_RUN", True))
    debug_pdf_text: bool = field(default_factory=lambda: _bool_env("DEBUG_PDF_TEXT", True))
    log_level: str = field(default_factory=lambda: _optional("LOG_LEVEL", "INFO"))

    # Paths
    state_file: str = field(default_factory=lambda: _optional("STATE_FILE", "data/state.json"))
    download_dir: str = field(default_factory=lambda: _optional("DOWNLOAD_DIR", "data/downloads"))
    debug_dir: str = field(default_factory=lambda: _optional("DEBUG_DIR", "data/debug"))
    log_dir: str = field(default_factory=lambda: _optional("LOG_DIR", "data/logs"))

    def __repr__(self) -> str:
        return (
            f"Config(gmail_email={self.gmail_email!r}, "
            f"icloud_username={self.icloud_username!r}, "
            f"dry_run={self.dry_run}, "
            f"debug_pdf_text={self.debug_pdf_text}, "
            f"log_level={self.log_level!r})"
        )
