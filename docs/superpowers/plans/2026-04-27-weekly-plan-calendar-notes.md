# weekly-plan-calendar-notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust Python project that reads weekly plan PDFs from Gmail via IMAP and creates/updates daily all-day events in an iCloud CalDAV calendar listing present colleagues.

**Architecture:** IMAP fetches unprocessed emails → PDF text extracted defensively → CalDAV upserts all-day events per day; state.json prevents duplicate processing; DRY_RUN=true is the safe default; debug text dumped to data/debug/ for parser tuning.

**Tech Stack:** Python 3, imaplib (stdlib), pdfplumber, caldav>=1.3, python-dotenv, requests, pytest, pytest-mock

---

## File Map

| File | Responsibility |
|------|---------------|
| `app/__init__.py` | Package marker |
| `app/config.py` | Load + validate all env vars via python-dotenv |
| `app/logging_setup.py` | Configure rotating file + console handlers |
| `app/state.py` | Read/write state.json, idempotency guard |
| `app/gmail_client.py` | IMAP connect, email search, PDF attachment download |
| `app/pdf_parser.py` | Text extraction, defensive multi-strategy parsing, debug dump |
| `app/calendar_client.py` | CalDAV connect, all-day event upsert with prefix-based dedup |
| `app/notify.py` | Optional ntfy push with graceful failure |
| `app/main.py` | Orchestrates full pipeline, dry-run logic, error handling |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Shared fixtures, env leak prevention |
| `tests/fixtures/` | Sample data for parser tests |
| `tests/test_config.py` | Config loading + validation tests |
| `tests/test_logging_setup.py` | Log file creation tests |
| `tests/test_state.py` | State CRUD + idempotency tests |
| `tests/test_gmail_client.py` | IMAP client tests with mocked imaplib |
| `tests/test_pdf_parser.py` | Parser tests with mocked pdfplumber |
| `tests/test_calendar_client.py` | CalDAV tests with mocked caldav |
| `tests/test_notify.py` | ntfy tests with mocked requests |
| `tests/test_main.py` | Integration test of full pipeline |
| `run.sh` | Entry point: venv activation, .env check, exec |
| `.env.example` | All required vars with safe placeholders |
| `.gitignore` | Python + data dirs, secrets |
| `requirements.txt` | Pinned dependencies |
| `README.md` | Setup, Unraid install, usage, troubleshooting |

---

### Task 1: Git Init + Project Scaffold

**Files:**
- Create: `app/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/` (directory)
- Create: `data/downloads/.gitkeep`
- Create: `data/debug/.gitkeep`
- Create: `data/logs/.gitkeep`
- Create: `data/state.json`
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `.env.example`

- [ ] **Step 1.1: Init git repo and directory structure**

```bash
cd /home/bro/projekt/wochenplan
git init
mkdir -p app data/downloads data/debug data/logs tests tests/fixtures
touch app/__init__.py tests/__init__.py
touch data/downloads/.gitkeep data/debug/.gitkeep data/logs/.gitkeep
```

- [ ] **Step 1.2: Create .gitignore**

Write to `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg-info/
.venv/
venv/
dist/
build/
.pytest_cache/
*.egg

# Environment — never commit secrets
.env

# Data dirs: keep structure, ignore content
data/downloads/*
data/debug/*
data/logs/*
data/state.json
!data/downloads/.gitkeep
!data/debug/.gitkeep
!data/logs/.gitkeep

# IDE
.idea/
.vscode/
*.swp
```

- [ ] **Step 1.3: Create requirements.txt**

Write to `requirements.txt`:
```
python-dotenv>=1.0.0
pdfplumber>=0.10.3
caldav>=1.3.9
requests>=2.31.0
pytest>=7.4.0
pytest-mock>=3.12.0
```

- [ ] **Step 1.4: Create .env.example**

Write to `.env.example`:
```
# Gmail IMAP
GMAIL_IMAP_HOST=imap.gmail.com
GMAIL_IMAP_PORT=993
GMAIL_EMAIL=sanpower1@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# iCloud CalDAV
ICLOUD_CALDAV_URL=https://caldav.icloud.com
ICLOUD_USERNAME=your-apple-id@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ICLOUD_CALENDAR_NAME=Wochenplan

# Calendar event config
CALENDAR_EVENT_TITLE=Kollegen laut Wochenplan
CALENDAR_EVENT_PREFIX=[WEEKLY_PLAN_COLLEAGUES]

# ntfy push notifications (optional)
NTFY_ENABLED=false
NTFY_URL=https://ntfy.sh
NTFY_TOPIC=my-wochenplan
NTFY_USERNAME=
NTFY_PASSWORD=

# Behavior
DRY_RUN=true
DEBUG_PDF_TEXT=true
LOG_LEVEL=INFO

# Paths
STATE_FILE=data/state.json
DOWNLOAD_DIR=data/downloads
DEBUG_DIR=data/debug
LOG_DIR=data/logs
```

- [ ] **Step 1.5: Create initial data/state.json**

Write to `data/state.json`:
```json
{
  "processed": {},
  "version": "1"
}
```

- [ ] **Step 1.6: Create tests/conftest.py**

Write to `tests/conftest.py`:
```python
import pytest


@pytest.fixture(autouse=True)
def no_env_leak(monkeypatch):
    for key in [
        "GMAIL_APP_PASSWORD", "ICLOUD_APP_PASSWORD",
        "NTFY_PASSWORD", "DRY_RUN",
    ]:
        monkeypatch.delenv(key, raising=False)
```

- [ ] **Step 1.7: Commit**

```bash
cd /home/bro/projekt/wochenplan
git add .
git commit -m "chore: project scaffold with directories, gitignore, requirements, env example"
```

---

### Task 2: Configuration Module

**Files:**
- Create: `app/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 2.1: Write failing tests**

Write to `tests/test_config.py`:
```python
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
```

- [ ] **Step 2.2: Run to verify failure**

```bash
cd /home/bro/projekt/wochenplan
python -m pytest tests/test_config.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError` or `ImportError` — `app.config` doesn't exist yet.

- [ ] **Step 2.3: Create app/config.py**

Write to `app/config.py`:
```python
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
    return int(os.getenv(name, str(default)).strip())


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
```

- [ ] **Step 2.4: Run tests**

```bash
python -m pytest tests/test_config.py -v
```

Expected: All 4 PASS

- [ ] **Step 2.5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: config module with env var loading and validation"
```

---

### Task 3: Logging Setup

**Files:**
- Create: `app/logging_setup.py`
- Create: `tests/test_logging_setup.py`

- [ ] **Step 3.1: Write failing tests**

Write to `tests/test_logging_setup.py`:
```python
import logging


def test_setup_logging_creates_log_file(tmp_path):
    from app.logging_setup import setup_logging
    logger = setup_logging(
        log_dir=str(tmp_path / "logs"),
        log_level="DEBUG",
        logger_name="test_wochenplan_log",
    )
    logger.info("hello test")

    log_files = list((tmp_path / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "hello test" in log_files[0].read_text(encoding="utf-8")


def test_setup_logging_has_two_handlers(tmp_path):
    from app.logging_setup import setup_logging
    logger = setup_logging(
        log_dir=str(tmp_path / "logs2"),
        log_level="INFO",
        logger_name="test_wochenplan_handlers",
    )
    assert len(logger.handlers) == 2


def test_setup_logging_respects_level(tmp_path):
    from app.logging_setup import setup_logging
    logger = setup_logging(
        log_dir=str(tmp_path / "logs3"),
        log_level="WARNING",
        logger_name="test_wochenplan_level",
    )
    logger.debug("should not appear")
    logger.warning("should appear")

    log_files = list((tmp_path / "logs3").glob("*.log"))
    content = log_files[0].read_text(encoding="utf-8")
    assert "should not appear" not in content
    assert "should appear" in content
```

- [ ] **Step 3.2: Run to verify failure**

```bash
python -m pytest tests/test_logging_setup.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 3.3: Create app/logging_setup.py**

Write to `app/logging_setup.py`:
```python
import logging
import os
from datetime import datetime


def setup_logging(
    log_dir: str = "data/logs",
    log_level: str = "INFO",
    logger_name: str = "wochenplan",
) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, datetime.now().strftime("%Y-%m-%d") + ".log")

    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.handlers.clear()

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
```

- [ ] **Step 3.4: Run tests**

```bash
python -m pytest tests/test_logging_setup.py -v
```

Expected: All 3 PASS

- [ ] **Step 3.5: Commit**

```bash
git add app/logging_setup.py tests/test_logging_setup.py
git commit -m "feat: logging setup with file and console handlers"
```

---

### Task 4: State Management

**Files:**
- Create: `app/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 4.1: Write failing tests**

Write to `tests/test_state.py`:
```python
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
```

- [ ] **Step 4.2: Run to verify failure**

```bash
python -m pytest tests/test_state.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 4.3: Create app/state.py**

Write to `app/state.py`:
```python
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


VALID_STATUSES = frozenset({"downloaded", "parsed", "calendar_written", "skipped", "failed"})


class StateManager:
    def __init__(self, state_file: str = "data/state.json"):
        self._path = state_file
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "processed" not in data:
                    data["processed"] = {}
                return data
            except (json.JSONDecodeError, OSError):
                return {"processed": {}, "version": "1"}
        os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
        initial = {"processed": {}, "version": "1"}
        self._write(initial)
        return initial

    def _write(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self._path)

    def is_processed(self, message_id: str) -> bool:
        return message_id in self._data["processed"]

    def get(self, message_id: str) -> Optional[Dict[str, Any]]:
        return self._data["processed"].get(message_id)

    def record(
        self,
        message_id: str,
        status: str,
        filename: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}")
        self._data["processed"][message_id] = {
            "status": status,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self._write(self._data)

    def all_entries(self) -> Dict[str, Any]:
        return dict(self._data["processed"])
```

- [ ] **Step 4.4: Run tests**

```bash
python -m pytest tests/test_state.py -v
```

Expected: All 6 PASS

- [ ] **Step 4.5: Commit**

```bash
git add app/state.py tests/test_state.py
git commit -m "feat: state manager with JSON persistence, idempotency guard, status validation"
```

---

### Task 5: Gmail IMAP Client

**Files:**
- Create: `app/gmail_client.py`
- Create: `tests/test_gmail_client.py`

- [ ] **Step 5.1: Write failing tests**

Write to `tests/test_gmail_client.py`:
```python
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from unittest.mock import MagicMock, patch


def _make_raw_email_with_pdf(subject="Wochenplan KW17", filename="wochenplan.pdf"):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["Message-ID"] = f"<test-{subject.replace(' ', '-')}@gmail.com>"
    msg["Date"] = "Mon, 27 Apr 2026 08:00:00 +0000"
    msg.attach(MIMEText("See attached.", "plain"))
    part = MIMEBase("application", "pdf")
    part.set_payload(b"%PDF-1.4 fake content")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)
    return msg.as_bytes()


def test_find_relevant_emails_returns_emails_with_pdfs():
    from app.gmail_client import GmailClient
    mock_imap = MagicMock()
    mock_imap.select.return_value = ("OK", [b"2"])
    mock_imap.search.return_value = ("OK", [b"1 2"])
    mock_imap.fetch.side_effect = [
        ("OK", [(b"1 (RFC822 {500})", _make_raw_email_with_pdf("Wochenplan KW17"))]),
        ("OK", [(b"2 (RFC822 {500})", _make_raw_email_with_pdf("Wochenplan KW18"))]),
    ]

    client = GmailClient.__new__(GmailClient)
    client._imap = mock_imap
    client.logger = MagicMock()

    result = client.find_relevant_emails(subject_filter="Wochenplan")

    assert len(result) == 2
    assert all("message_id" in e for e in result)
    assert all("subject" in e for e in result)
    assert all("raw" in e for e in result)


def test_find_relevant_emails_skips_no_pdf():
    from app.gmail_client import GmailClient
    msg = MIMEMultipart()
    msg["Subject"] = "Wochenplan KW17"
    msg["Message-ID"] = "<no-pdf@gmail.com>"
    msg["Date"] = "Mon, 27 Apr 2026 08:00:00 +0000"
    msg.attach(MIMEText("No attachment here.", "plain"))

    mock_imap = MagicMock()
    mock_imap.select.return_value = ("OK", [b"1"])
    mock_imap.search.return_value = ("OK", [b"1"])
    mock_imap.fetch.return_value = ("OK", [(b"1 (RFC822 {200})", msg.as_bytes())])

    client = GmailClient.__new__(GmailClient)
    client._imap = mock_imap
    client.logger = MagicMock()

    result = client.find_relevant_emails()
    assert result == []


def test_download_email_attachments_saves_pdf(tmp_path):
    from app.gmail_client import GmailClient
    raw = _make_raw_email_with_pdf(filename="kw17.pdf")

    client = GmailClient.__new__(GmailClient)
    client.logger = MagicMock()

    msg = email_lib.message_from_bytes(raw)
    saved = client._save_attachments(msg, str(tmp_path))

    assert len(saved) == 1
    assert saved[0].endswith(".pdf")
    assert (tmp_path / "kw17.pdf").exists()


def test_gmail_client_never_deletes_or_expunges():
    from app.gmail_client import GmailClient
    mock_imap = MagicMock()
    client = GmailClient.__new__(GmailClient)
    client._imap = mock_imap
    client.logger = MagicMock()
    client.close()
    mock_imap.expunge.assert_not_called()
    mock_imap.store.assert_not_called()
```

- [ ] **Step 5.2: Run to verify failure**

```bash
python -m pytest tests/test_gmail_client.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 5.3: Create app/gmail_client.py**

Write to `app/gmail_client.py`:
```python
import email as email_lib
import hashlib
import imaplib
import logging
import os
from typing import Dict, List, Optional


class GmailClient:
    def __init__(
        self,
        host: str,
        port: int,
        email_addr: str,
        app_password: str,
        logger: Optional[logging.Logger] = None,
    ):
        self.host = host
        self.port = port
        self.email_addr = email_addr
        self._app_password = app_password
        self.logger = logger or logging.getLogger("wochenplan.gmail")
        self._imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        self.logger.info(f"Connecting to IMAP {self.host}:{self.port} as {self.email_addr}")
        self._imap = imaplib.IMAP4_SSL(self.host, self.port)
        self._imap.login(self.email_addr, self._app_password)
        self.logger.info("IMAP login successful")

    def close(self) -> None:
        if self._imap:
            try:
                self._imap.logout()
            except Exception:
                pass
            finally:
                self._imap = None

    def find_relevant_emails(
        self,
        subject_filter: str = "Wochenplan",
        mailbox: str = "INBOX",
    ) -> List[Dict]:
        if not self._imap:
            raise RuntimeError("Not connected. Call connect() first.")

        self._imap.select(mailbox)
        status, data = self._imap.search(None, f'SUBJECT "{subject_filter}"')
        if status != "OK":
            self.logger.warning(f"IMAP SEARCH returned status: {status}")
            return []

        nums = data[0].split()
        self.logger.info(f"Found {len(nums)} email(s) matching subject '{subject_filter}'")

        results = []
        for num in nums:
            try:
                status, msg_data = self._imap.fetch(num, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
                msg = email_lib.message_from_bytes(raw)

                has_pdf = any(
                    part.get_content_type() == "application/pdf"
                    or (part.get_filename() or "").lower().endswith(".pdf")
                    for part in msg.walk()
                )
                if not has_pdf:
                    self.logger.debug(f"Skipping '{msg.get('Subject', '')}' — no PDF attachment")
                    continue

                message_id = msg.get("Message-ID", f"unknown-{num.decode()}").strip("<>")
                results.append({
                    "message_id": message_id,
                    "subject": msg.get("Subject", ""),
                    "date": msg.get("Date", ""),
                    "raw": raw,
                })
                self.logger.info(f"Queued: '{msg.get('Subject', '')}' ({message_id})")
            except Exception as e:
                self.logger.error(f"Error fetching email {num}: {e}")

        return results

    def _save_attachments(
        self,
        msg: email_lib.message.Message,
        download_dir: str,
    ) -> List[str]:
        os.makedirs(download_dir, exist_ok=True)
        saved = []

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            if not filename or not filename.lower().endswith(".pdf"):
                if part.get_content_type() != "application/pdf":
                    continue
                filename = filename or "attachment.pdf"

            payload = part.get_payload(decode=True)
            if not payload:
                self.logger.warning(f"Empty payload for: {filename}")
                continue

            safe_name = os.path.basename(filename)
            dest = os.path.join(download_dir, safe_name)
            if os.path.exists(dest):
                suffix = hashlib.md5(payload).hexdigest()[:8]
                base, ext = os.path.splitext(safe_name)
                dest = os.path.join(download_dir, f"{base}_{suffix}{ext}")

            with open(dest, "wb") as f:
                f.write(payload)
            self.logger.info(f"Saved attachment: {dest}")
            saved.append(dest)

        return saved

    def download_email_attachments(
        self,
        email_info: Dict,
        download_dir: str,
    ) -> List[str]:
        msg = email_lib.message_from_bytes(email_info.get("raw", b""))
        return self._save_attachments(msg, download_dir)
```

- [ ] **Step 5.4: Run tests**

```bash
python -m pytest tests/test_gmail_client.py -v
```

Expected: All 4 PASS

- [ ] **Step 5.5: Commit**

```bash
git add app/gmail_client.py tests/test_gmail_client.py
git commit -m "feat: Gmail IMAP client with PDF attachment download, no delete"
```

---

### Task 6: PDF Parser (Defensive MVP)

**Files:**
- Create: `app/pdf_parser.py`
- Create: `tests/test_pdf_parser.py`

**Design note:** The actual PDF format is unknown. This parser:
1. Extracts all text and saves to `data/debug/` when `DEBUG_PDF_TEXT=true`
2. Tries two strategies: day-header pattern and standalone date pattern
3. Returns `{}` (not an error) when no pattern matches — caller decides what to do
4. Never raises — all failures are logged

- [ ] **Step 6.1: Write failing tests**

Write to `tests/test_pdf_parser.py`:
```python
import os
from unittest.mock import MagicMock, patch


def _mock_pdf(text: str):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


def test_parser_saves_debug_text_when_enabled(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path / "debug"), debug_mode=True)
    with patch("pdfplumber.open", return_value=_mock_pdf("Montag 27.04.2026\nAlice")):
        parser.parse("fake.pdf")
    assert any(f.endswith(".txt") for f in os.listdir(tmp_path / "debug"))


def test_parser_does_not_save_debug_text_when_disabled(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path / "debug"), debug_mode=False)
    with patch("pdfplumber.open", return_value=_mock_pdf("Montag 27.04.2026\nAlice")):
        parser.parse("fake.pdf")
    assert not (tmp_path / "debug").exists() or not os.listdir(tmp_path / "debug")


def test_parser_returns_empty_when_no_pattern(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    with patch("pdfplumber.open", return_value=_mock_pdf("Random text with no schedule info.")):
        result = parser.parse("fake.pdf")
    assert result == {}


def test_parser_returns_empty_on_extraction_error(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    with patch("pdfplumber.open", side_effect=Exception("corrupt PDF")):
        result = parser.parse("corrupt.pdf")
    assert result == {}


def test_parser_handles_missing_file(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    result = parser.parse("/nonexistent/path/plan.pdf")
    assert result == {}


def test_parser_result_has_correct_types(tmp_path):
    from app.pdf_parser import PDFParser
    from datetime import datetime
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    sample = (
        "Wochenplan KW 17 - 2026\n\n"
        "Montag 27.04.2026\nAlice Muster, Bob Schmidt\n\n"
        "Dienstag 28.04.2026\nCarol Weber\n"
    )
    with patch("pdfplumber.open", return_value=_mock_pdf(sample)):
        result = parser.parse("fake.pdf")
    for date_key, names in result.items():
        assert isinstance(date_key, str)
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)
        datetime.fromisoformat(date_key)
```

- [ ] **Step 6.2: Run to verify failure**

```bash
python -m pytest tests/test_pdf_parser.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 6.3: Create app/pdf_parser.py**

Write to `app/pdf_parser.py`:
```python
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False


_DAY_DATE_RE = re.compile(
    r"(?:montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|"
    r"mo|di|mi|do|fr|sa|so)[.,\s]+(\d{1,2})[.\s/](\d{1,2})[.\s/]?(\d{4})?",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")

_HEADER_WORDS = frozenset(["wochenplan", "kw", "datum", "name", "tag", "kalenderwoche"])


class PDFParser:
    def __init__(
        self,
        debug_dir: str = "data/debug",
        debug_mode: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        self.debug_dir = debug_dir
        self.debug_mode = debug_mode
        self.logger = logger or logging.getLogger("wochenplan.pdf_parser")

    def parse(self, pdf_path: str) -> Dict[str, List[str]]:
        if not _HAS_PDFPLUMBER:
            self.logger.error("pdfplumber not installed — cannot parse PDFs")
            return {}
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return {}

        try:
            text = self._extract_text(pdf_path)
        except Exception as e:
            self.logger.error(f"Text extraction failed for {pdf_path}: {e}")
            return {}

        if not text or not text.strip():
            self.logger.warning(
                f"No text extracted from {pdf_path} — possibly a scanned/image PDF"
            )
            return {}

        if self.debug_mode:
            self._save_debug(pdf_path, text)

        self.logger.debug(f"Extracted {len(text)} chars from {pdf_path}")

        result = self._run_strategies(text, pdf_path)
        if result:
            total = sum(len(v) for v in result.values())
            self.logger.info(f"Parsed {len(result)} day(s), {total} name(s) from {pdf_path}")
        else:
            self.logger.warning(
                f"No date/name pairs found in {pdf_path}. "
                "Enable DEBUG_PDF_TEXT=true and check data/debug/ to tune the parser."
            )
        return result

    def _extract_text(self, pdf_path: str) -> str:
        with pdfplumber.open(pdf_path) as pdf:
            parts = []
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    parts.append(t)
                else:
                    self.logger.debug(f"Page {i+1}: no text layer")
            return "\n".join(parts)

    def _save_debug(self, pdf_path: str, text: str) -> None:
        os.makedirs(self.debug_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(self.debug_dir, f"{base}_{ts}.txt")
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(f"Source: {pdf_path}\nExtracted: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(text)
            self.logger.info(f"Debug text saved: {dest}")
        except OSError as e:
            self.logger.warning(f"Could not save debug text: {e}")

    def _run_strategies(self, text: str, pdf_path: str) -> Dict[str, List[str]]:
        for fn in [self._strategy_day_headers, self._strategy_standalone_dates]:
            try:
                result = fn(text)
                if result:
                    self.logger.info(f"Strategy '{fn.__name__}' matched for {pdf_path}")
                    return result
                self.logger.debug(f"Strategy '{fn.__name__}' found nothing")
            except Exception as e:
                self.logger.debug(f"Strategy '{fn.__name__}' raised: {e}")
        return {}

    def _strategy_day_headers(self, text: str) -> Dict[str, List[str]]:
        """Parses blocks like:
            Montag 27.04.2026
            Alice Muster, Bob Schmidt
        """
        result: Dict[str, List[str]] = {}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            m = _DAY_DATE_RE.search(lines[i])
            if m:
                day, month, year = m.group(1), m.group(2), m.group(3)
                if not year:
                    i += 1
                    continue
                try:
                    d = datetime(int(year), int(month), int(day)).date()
                except ValueError:
                    i += 1
                    continue
                names, j = [], i + 1
                while j < len(lines) and not _DAY_DATE_RE.search(lines[j]):
                    names.extend(self._names_from_line(lines[j]))
                    j += 1
                if names:
                    result[d.isoformat()] = names
                i = j
            else:
                i += 1
        return result

    def _strategy_standalone_dates(self, text: str) -> Dict[str, List[str]]:
        """Parses DD.MM.YYYY followed by name lines."""
        result: Dict[str, List[str]] = {}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = _DATE_RE.search(line)
            if m:
                try:
                    d = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
                except ValueError:
                    continue
                names = []
                for j in range(i + 1, min(i + 4, len(lines))):
                    if _DATE_RE.search(lines[j]):
                        break
                    names.extend(self._names_from_line(lines[j]))
                if names:
                    result[d.isoformat()] = names
        return result

    def _names_from_line(self, line: str) -> List[str]:
        if _DATE_RE.search(line) or _DAY_DATE_RE.search(line):
            return []
        if any(w in line.lower() for w in _HEADER_WORDS):
            return []
        candidates = re.split(r"[,;]+", line)
        names = []
        for c in candidates:
            c = c.strip()
            if 2 <= len(c) <= 60 and re.match(r"^[A-ZÄÖÜa-zäöüß\s\-\.]+$", c):
                names.append(c)
        return names
```

- [ ] **Step 6.4: Run tests**

```bash
python -m pytest tests/test_pdf_parser.py -v
```

Expected: All 6 PASS

- [ ] **Step 6.5: Commit**

```bash
git add app/pdf_parser.py tests/test_pdf_parser.py
git commit -m "feat: defensive PDF parser with debug dump and multi-strategy parsing"
```

---

### Task 7: CalDAV Calendar Client

**Files:**
- Create: `app/calendar_client.py`
- Create: `tests/test_calendar_client.py`

- [ ] **Step 7.1: Write failing tests**

Write to `tests/test_calendar_client.py`:
```python
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
```

- [ ] **Step 7.2: Run to verify failure**

```bash
python -m pytest tests/test_calendar_client.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 7.3: Create app/calendar_client.py**

Write to `app/calendar_client.py`:
```python
import logging
import uuid
from datetime import date, datetime, timedelta
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

    def connect(self) -> None:
        if not _HAS_CALDAV:
            raise RuntimeError("caldav library not installed — run: pip install caldav")
        self.logger.info(f"Connecting to CalDAV: {self.caldav_url}")
        with caldav.DAVClient(
            url=self.caldav_url,
            username=self.username,
            password=self._app_password,
        ) as client:
            principal = client.principal()
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

        existing = self._find_existing(event_date)
        if existing:
            self.logger.info(f"Replacing existing event for {event_date.isoformat()}")
            existing.delete()

        ical = self._build_ical(event_date, names)
        self._calendar.save_event(ical)
        self.logger.info(f"Saved event for {event_date.isoformat()} ({len(names)} names)")

    def _find_existing(self, event_date: date):
        try:
            start = datetime(event_date.year, event_date.month, event_date.day)
            end = start + timedelta(days=1)
            events = self._calendar.search(start=start, end=end, event=True)
            for ev in events:
                try:
                    summary = ev.vobject_instance.vevent.summary.value
                    if summary.startswith(self.event_prefix):
                        return ev
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"Error searching calendar for {event_date}: {e}")
        return None

    def _build_ical(self, event_date: date, names: List[str]) -> str:
        uid = str(uuid.uuid4())
        d_start = event_date.strftime("%Y%m%d")
        d_end = (event_date + timedelta(days=1)).strftime("%Y%m%d")
        summary = f"{self.event_prefix} {self.event_title}"
        description = "Anwesende Kollegen:\\n" + "\\n".join(f"- {n}" for n in names)
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//weekly-plan-calendar-notes//DE\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{uid}\r\n"
            f"DTSTAMP:{now}\r\n"
            f"DTSTART;VALUE=DATE:{d_start}\r\n"
            f"DTEND;VALUE=DATE:{d_end}\r\n"
            f"SUMMARY:{summary}\r\n"
            f"DESCRIPTION:{description}\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
```

- [ ] **Step 7.4: Run tests**

```bash
python -m pytest tests/test_calendar_client.py -v
```

Expected: All 5 PASS

- [ ] **Step 7.5: Commit**

```bash
git add app/calendar_client.py tests/test_calendar_client.py
git commit -m "feat: CalDAV calendar client with iCloud support and prefix-based dedup"
```

---

### Task 8: ntfy Notification Module

**Files:**
- Create: `app/notify.py`
- Create: `tests/test_notify.py`

- [ ] **Step 8.1: Write failing tests**

Write to `tests/test_notify.py`:
```python
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
```

- [ ] **Step 8.2: Run to verify failure**

```bash
python -m pytest tests/test_notify.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 8.3: Create app/notify.py**

Write to `app/notify.py`:
```python
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
```

- [ ] **Step 8.4: Run tests**

```bash
python -m pytest tests/test_notify.py -v
```

Expected: All 4 PASS

- [ ] **Step 8.5: Commit**

```bash
git add app/notify.py tests/test_notify.py
git commit -m "feat: ntfy notification module with graceful failure"
```

---

### Task 9: Main Orchestrator

**Files:**
- Create: `app/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 9.1: Write failing test**

Write to `tests/test_main.py`:
```python
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
    assert exit_code == 0


def test_already_processed_message_skipped(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path)
    import json
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
```

- [ ] **Step 9.2: Run to verify failure**

```bash
python -m pytest tests/test_main.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 9.3: Create app/main.py**

Write to `app/main.py`:
```python
import logging
import os
import sys
from datetime import date

from app.calendar_client import CalendarClient
from app.config import Config
from app.gmail_client import GmailClient
from app.logging_setup import setup_logging
from app.notify import Notifier
from app.pdf_parser import PDFParser
from app.state import StateManager


def run() -> int:
    cfg = Config()

    logger = setup_logging(
        log_dir=cfg.log_dir,
        log_level=cfg.log_level,
        logger_name="wochenplan",
    )
    logger.info(f"Starting | {repr(cfg)}")

    state = StateManager(cfg.state_file)
    notifier = Notifier(
        enabled=cfg.ntfy_enabled,
        url=cfg.ntfy_url,
        topic=cfg.ntfy_topic,
        username=cfg.ntfy_username,
        password=cfg.ntfy_password,
        logger=logger,
    )
    gmail = GmailClient(
        host=cfg.gmail_imap_host,
        port=cfg.gmail_imap_port,
        email_addr=cfg.gmail_email,
        app_password=cfg.gmail_app_password,
        logger=logger,
    )
    parser = PDFParser(
        debug_dir=cfg.debug_dir,
        debug_mode=cfg.debug_pdf_text,
        logger=logger,
    )
    calendar = CalendarClient(
        caldav_url=cfg.icloud_caldav_url,
        username=cfg.icloud_username,
        app_password=cfg.icloud_app_password,
        calendar_name=cfg.icloud_calendar_name,
        event_title=cfg.calendar_event_title,
        event_prefix=cfg.calendar_event_prefix,
        logger=logger,
    )

    try:
        gmail.connect()
    except Exception as e:
        logger.error(f"Gmail connection failed: {e}")
        notifier.send("Wochenplan Fehler", f"Gmail: {e}", priority="high")
        return 1

    if not cfg.dry_run:
        try:
            calendar.connect()
        except Exception as e:
            logger.error(f"CalDAV connection failed: {e}")
            notifier.send("Wochenplan Fehler", f"Kalender: {e}", priority="high")
            gmail.close()
            return 1

    processed_ok = 0
    processed_fail = 0

    try:
        emails = gmail.find_relevant_emails(subject_filter="Wochenplan")
        logger.info(f"Found {len(emails)} relevant email(s)")

        for email_info in emails:
            msg_id = email_info["message_id"]

            if state.is_processed(msg_id):
                logger.info(f"Already processed, skipping: {msg_id}")
                continue

            try:
                pdf_paths = gmail.download_email_attachments(email_info, cfg.download_dir)
            except Exception as e:
                logger.error(f"Download failed for {msg_id}: {e}")
                state.record(msg_id, "failed", details={"error": f"download: {e}"})
                processed_fail += 1
                continue

            if not pdf_paths:
                logger.warning(f"No PDFs in email {msg_id}")
                state.record(msg_id, "skipped", details={"reason": "no pdf attachments"})
                continue

            state.record(msg_id, "downloaded", filename=pdf_paths[0])

            for pdf_path in pdf_paths:
                schedule = parser.parse(pdf_path)

                if not schedule:
                    logger.warning(f"Parser returned no data for {pdf_path}")
                    state.record(
                        msg_id, "failed", filename=pdf_path,
                        details={"error": "parser returned empty result"},
                    )
                    notifier.send(
                        "Wochenplan Parse-Fehler",
                        f"Keine Daten aus {os.path.basename(pdf_path)}. "
                        "Prüfe data/debug/ für den extrahierten Text.",
                    )
                    processed_fail += 1
                    continue

                state.record(
                    msg_id, "parsed", filename=pdf_path,
                    details={"dates_found": list(schedule.keys())},
                )

                cal_errors = []
                for date_str, names in sorted(schedule.items()):
                    try:
                        calendar.upsert_event(
                            event_date=date.fromisoformat(date_str),
                            names=names,
                            dry_run=cfg.dry_run,
                        )
                    except Exception as e:
                        logger.error(f"Calendar write failed for {date_str}: {e}")
                        cal_errors.append(f"{date_str}: {e}")
                        notifier.send("Wochenplan Kalender-Fehler", f"{date_str}: {e}", priority="high")

                if cal_errors:
                    state.record(
                        msg_id, "failed", filename=pdf_path,
                        details={"calendar_errors": cal_errors},
                    )
                    processed_fail += 1
                else:
                    state.record(
                        msg_id, "calendar_written", filename=pdf_path,
                        details={"dates_written": list(schedule.keys())},
                    )
                    processed_ok += 1
                    notifier.send(
                        "Wochenplan OK",
                        f"{len(schedule)} Tag(e) eingetragen aus {os.path.basename(pdf_path)}",
                    )
    finally:
        gmail.close()

    logger.info(f"Done. OK={processed_ok} FAIL={processed_fail}")
    return 0 if processed_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
```

- [ ] **Step 9.4: Run tests**

```bash
python -m pytest tests/test_main.py -v
```

Expected: All 3 PASS

- [ ] **Step 9.5: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 9.6: Commit**

```bash
git add app/main.py tests/test_main.py
git commit -m "feat: main orchestrator with dry-run, state tracking, full pipeline"
```

---

### Task 10: run.sh + README

**Files:**
- Create: `run.sh`
- Create: `README.md`

- [ ] **Step 10.1: Create run.sh**

Write to `run.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ".env" ]; then
    echo "ERROR: .env not found in $SCRIPT_DIR"
    echo "       cp .env.example .env  — then fill in your credentials."
    exit 1
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "WARNING: No venv found at .venv/ or venv/ — using system Python."
fi

mkdir -p data/downloads data/debug data/logs

exec python -m app.main "$@"
```

Make executable:
```bash
chmod +x run.sh
```

- [ ] **Step 10.2: Create README.md**

Write to `README.md`:
```markdown
# weekly-plan-calendar-notes

Liest Wochenplan-PDFs aus Gmail (IMAP) und erstellt pro Tag einen ganztägigen Kalendereintrag in einem iCloud-Kalender (CalDAV).

## Projektziel

Aus einer E-Mail mit Wochenplan-PDF werden automatisch Kalendereinträge erstellt, die festhalten, welche Kollegen/Kolleginnen an welchem Tag laut Plan anwesend sind. Das Projekt läuft auf einem Unraid-Server, wird per Cron oder User Script gestartet und ist standardmäßig im Dry-Run-Modus — schreibt also nichts, bis du es aktiv freischaltest.

## Voraussetzungen

- Python 3.10+
- Unraid oder ein beliebiger Linux-Server
- Gmail-Konto mit aktiviertem IMAP
- iCloud-Konto mit App-spezifischem Passwort

## Installation auf Unraid

```bash
# Projektordner anlegen (oder clone das Repo)
mkdir -p /mnt/user/appdata/weekly-plan-calendar-notes
cd /mnt/user/appdata/weekly-plan-calendar-notes

# Python venv erstellen
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# .env anlegen
cp .env.example .env
nano .env   # oder vi .env
```

## .env konfigurieren

Öffne `.env` und trage ein:

| Variable | Beschreibung |
|---|---|
| `GMAIL_EMAIL` | Deine Gmail-Adresse |
| `GMAIL_APP_PASSWORD` | App-Passwort (nicht dein normales Passwort!) |
| `ICLOUD_USERNAME` | Deine Apple-ID (z. B. `name@icloud.com`) |
| `ICLOUD_APP_PASSWORD` | iCloud App-Passwort |
| `ICLOUD_CALENDAR_NAME` | Exakter Kalendernamem z. B. `Wochenplan` |
| `DRY_RUN` | `true` zum Testen, `false` zum echten Schreiben |
| `DEBUG_PDF_TEXT` | `true` → extrahierten Text unter `data/debug/` speichern |

### Gmail App-Passwort erstellen

1. Gehe zu [myaccount.google.com/security](https://myaccount.google.com/security)
2. Aktiviere 2-Faktor-Authentifizierung (falls noch nicht aktiv)
3. Suche nach „App-Passwörter"
4. Erstelle ein neues Passwort für „Mail" / „Anderes Gerät"
5. Das 16-stellige Passwort in `GMAIL_APP_PASSWORD` eintragen

### iCloud App-Passwort erstellen

1. Gehe zu [appleid.apple.com](https://appleid.apple.com)
2. Abschnitt „Anmelden und Sicherheit" → „App-spezifische Passwörter"
3. Neues Passwort generieren (Name z. B. „wochenplan-server")
4. In `ICLOUD_APP_PASSWORD` eintragen

## Erster Testlauf (Dry-Run)

```bash
# Stelle sicher, dass DRY_RUN=true in .env steht
./run.sh
```

Das Skript:
- verbindet sich mit Gmail
- sucht E-Mails mit „Wochenplan" im Betreff
- lädt PDF-Anhänge in `data/downloads/` herunter
- extrahiert Text (wenn `DEBUG_PDF_TEXT=true`) nach `data/debug/`
- zeigt, welche Kalendereinträge es *würde* erstellen
- schreibt **nichts** in den Kalender

## PDF-Debug-Text prüfen

Nach dem ersten Dry-Run:

```bash
ls data/debug/
cat data/debug/wochenplan_kw17_*.txt
```

Prüfe, ob der extrahierte Text Datumszeilen und Namenszeilen enthält.
Der Parser sucht nach Mustern wie:
```
Montag 27.04.2026
Alice Muster, Bob Schmidt

Dienstag 28.04.2026
Carol Weber
```

Falls dein PDF anders strukturiert ist, kannst du `app/pdf_parser.py` anpassen — die Methoden `_strategy_day_headers` und `_strategy_standalone_dates` sind die Einstiegspunkte.

## Echten Lauf aktivieren

```bash
# .env öffnen und setzen:
# DRY_RUN=false
./run.sh
```

## Unraid User Scripts

Im Unraid-Webinterface unter **User Scripts**:

- Name: `Wochenplan Kalender`
- Script:
  ```bash
  #!/bin/bash
  cd /mnt/user/appdata/weekly-plan-calendar-notes
  ./run.sh
  ```
- Zeitplan: z. B. täglich um 07:00 Uhr

## Cron-Beispiel (direkt auf Unraid)

```bash
# crontab -e
0 7 * * 1-5 cd /mnt/user/appdata/weekly-plan-calendar-notes && ./run.sh >> /tmp/wochenplan-cron.log 2>&1
```

## Status prüfen

```bash
# Verarbeitete E-Mails anzeigen
cat data/state.json | python3 -m json.tool

# Logs anzeigen
ls data/logs/
tail -50 data/logs/$(date +%Y-%m-%d).log
```

## Troubleshooting

| Problem | Lösung |
|---|---|
| `EnvironmentError: GMAIL_APP_PASSWORD` | `.env` fehlt oder Variable nicht gesetzt |
| IMAP-Login fehlgeschlagen | App-Passwort prüfen; IMAP in Gmail aktiviert? |
| `Calendar 'X' not found` | `ICLOUD_CALENDAR_NAME` exakt wie im Kalender schreiben |
| Parser findet keine Daten | `DEBUG_PDF_TEXT=true` setzen, `data/debug/` prüfen |
| Doppelte Einträge | Prefix `[WEEKLY_PLAN_COLLEAGUES]` muss im Eintrag stehen |
| Keine neuen E-Mails gefunden | Betreff enthält "Wochenplan"? IMAP-Suche prüfen |

## Sicherheitshinweise

- Secrets nur in `.env` — nie ins Git-Repo
- `.env` ist in `.gitignore` eingetragen
- `DRY_RUN=true` ist der Standard — immer zuerst testen
- Keine E-Mails werden gelöscht oder verändert
- Kalendereinträge werden nur geschrieben wenn `DRY_RUN=false`
```

- [ ] **Step 10.3: Mark run.sh executable and commit**

```bash
chmod +x run.sh
git add run.sh README.md
git commit -m "feat: run.sh entrypoint with venv support and README with Unraid instructions"
```

- [ ] **Step 10.4: Final full test run**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: All tests PASS, no failures.

---

## Self-Review

**Spec Coverage:**
- [x] IMAP Gmail → Task 5 (`gmail_client.py`)
- [x] PDF Anhänge herunterladen → Task 5
- [x] Message-ID, Betreff, Datum erfassen → Task 5
- [x] Keine E-Mails löschen → Task 5 (test + impl)
- [x] PDF-Text extrahieren → Task 6 (`pdf_parser.py`)
- [x] Debug-Text in `data/debug/` → Task 6
- [x] Defensiver Parser, klare Logs → Task 6
- [x] Ergebnisformat `{date: [names]}` → Task 6
- [x] CalDAV iCloud → Task 7 (`calendar_client.py`)
- [x] Kalender per Name auswählen → Task 7
- [x] Ganztägige Einträge → Task 7 (`DTSTART;VALUE=DATE`)
- [x] Keine Duplikate → Task 7 (prefix-based search + delete)
- [x] Bestehende Einträge erkennen per PREFIX → Task 7
- [x] DRY_RUN → Task 7 + 9
- [x] State JSON → Task 4 (`state.py`)
- [x] Status: downloaded/parsed/calendar_written/skipped/failed → Task 4
- [x] Logging file + console → Task 3
- [x] Keine Secrets im Log → Task 2 (`__repr__` ohne Passwörter)
- [x] ntfy optional → Task 8 (`notify.py`)
- [x] Config via .env → Task 2 (`config.py`)
- [x] .env.example vollständig → Task 1
- [x] .gitignore → Task 1
- [x] requirements.txt → Task 1
- [x] run.sh mit venv → Task 10
- [x] README mit Unraid-Anleitung → Task 10
- [x] `data/` Verzeichnisstruktur → Task 1

**Placeholder-Scan:** Keine gefunden. Alle Steps enthalten vollständigen Code.

**Type-Konsistenz:**
- `StateManager.record(message_id, status, filename, details)` — in allen call sites gleich
- `CalendarClient.upsert_event(event_date, names, dry_run)` — konsistent
- `Config` Feldnamen — durchgehend snake_case, konsistent in `main.py`
