# Wochenplan Calendar Sync

Reads weekly plan PDFs from Gmail and creates iCloud calendar entries listing which colleagues are in the office.

## Requirements

- Python 3.11+
- A Python virtualenv
- Packages listed in `requirements.txt`
- A Gmail **app password** (not your main Gmail password) — generate one at <https://myaccount.google.com/apppasswords>
- An iCloud **app password** (not your Apple ID password) — generate one at <https://appleid.apple.com/account/manage>

## Setup

1. Clone or copy the project to your server.
2. Create a virtualenv:
   ```bash
   python3 -m venv .venv
   ```
3. Install dependencies:
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in all values:
   ```bash
   cp .env.example .env
   $EDITOR .env
   ```
5. Run with `DRY_RUN=true` first (it is the default — no calendar writes will occur):
   ```bash
   bash run.sh
   ```
6. Verify PDF parsing works: set `DEBUG_PDF_TEXT=true` in `.env`, run once, then inspect `data/debug/` for the extracted text files.
7. Only set `DRY_RUN=false` once you have confirmed that PDF parsing produces correct output.

## Unraid Cron

Add the job via **Unraid User Scripts** or drop a file into `/etc/cron.d/wochenplan`:

```
0 7 * * 1 /path/to/wochenplan/run.sh >> /path/to/wochenplan/data/logs/cron.log 2>&1
```

This runs every Monday at 07:00. Adjust the schedule to match when your office Wochenplan emails arrive.

## Configuration

All configuration is read from the `.env` file in the project root.

| Variable | Description | Default in .env.example |
|---|---|---|
| `GMAIL_IMAP_HOST` | Gmail IMAP hostname | `imap.gmail.com` |
| `GMAIL_IMAP_PORT` | Gmail IMAP port | `993` |
| `GMAIL_EMAIL` | Your Gmail address | — |
| `GMAIL_APP_PASSWORD` | Gmail app password (16-char) | — |
| `ICLOUD_CALDAV_URL` | iCloud CalDAV endpoint | `https://caldav.icloud.com` |
| `ICLOUD_USERNAME` | Your Apple ID email | — |
| `ICLOUD_APP_PASSWORD` | iCloud app password | — |
| `ICLOUD_CALENDAR_NAME` | Name of the iCloud calendar to write to | `Wochenplan` |
| `CALENDAR_EVENT_TITLE` | Title of each calendar event | `Kollegen laut Wochenplan` |
| `CALENDAR_EVENT_PREFIX` | Prefix tag used to identify managed events | `[WEEKLY_PLAN_COLLEAGUES]` |
| `NTFY_ENABLED` | Enable ntfy push notifications | `false` |
| `NTFY_URL` | ntfy server URL | `https://ntfy.sh` |
| `NTFY_TOPIC` | ntfy topic to publish to | `my-wochenplan` |
| `NTFY_USERNAME` | ntfy username (optional) | — |
| `NTFY_PASSWORD` | ntfy password (optional) | — |
| `DRY_RUN` | When `true`, no calendar changes are made | `true` |
| `DEBUG_PDF_TEXT` | When `true`, dumps extracted PDF text to `data/debug/` | `true` |
| `LOG_LEVEL` | Python log level (`DEBUG`, `INFO`, `WARNING`, …) | `INFO` |
| `STATE_FILE` | Path to the idempotency state file | `data/state.json` |
| `DOWNLOAD_DIR` | Directory for downloaded PDF attachments | `data/downloads` |
| `DEBUG_DIR` | Directory for PDF debug text dumps | `data/debug` |
| `LOG_DIR` | Directory for log files | `data/logs` |

## State File

`data/state.json` records every processed email by its RFC 2822 Message-ID. Once an email appears in the state file — regardless of whether its status is `"ok"` or `"failed"` — it will **not** be processed again on the next run.

To retry a failed email: open `data/state.json`, remove the entry whose key matches the Message-ID of the failed email, and re-run the script.

## DRY_RUN Mode

When `DRY_RUN=true` (the default), `calendar.connect()` is never called and `upsert_event()` logs what it *would* write but makes no changes to iCloud. This is the safe default while you are validating PDF parsing.

The comment in `.env.example` says it plainly: **never set `DRY_RUN=false` until PDF parsing is verified.**

Once you have inspected the debug output in `data/debug/` and confirmed that colleagues are being extracted correctly for each weekday, flip the flag to `DRY_RUN=false` and run once more to create the actual calendar events.

## ntfy Notifications

Set `NTFY_ENABLED=true` and fill in `NTFY_TOPIC` (and optionally `NTFY_URL`, `NTFY_USERNAME`, `NTFY_PASSWORD`) to receive a push notification after each run summarising success or failure. The `requests` package required for this is already included in `requirements.txt`.
