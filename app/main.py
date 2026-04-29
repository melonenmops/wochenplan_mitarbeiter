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
                if cfg.force_reprocess:
                    logger.info(f"FORCE_REPROCESS active — reprocessing: {msg_id}")
                else:
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
                result = parser.parse(pdf_path)

                if not result.days:
                    logger.warning(f"Parser returned no data for {pdf_path}")
                    state.record(
                        msg_id, "failed", filename=pdf_path,
                        details={"error": "parser returned empty result"},
                    )
                    notifier.send(
                        "Wochenplan Parse-Fehler",
                        f"Keine Daten aus {os.path.basename(pdf_path)}. "
                        f"Prüfe {cfg.debug_dir}/ für den extrahierten Text.",
                    )
                    processed_fail += 1
                    continue

                state.record(
                    msg_id, "parsed", filename=pdf_path,
                    details={"dates_found": list(result.days.keys()), "location": result.location},
                )

                cal_errors = []
                for date_str, names in sorted(result.days.items()):
                    try:
                        calendar.upsert_event(
                            event_date=date.fromisoformat(date_str),
                            names=names,
                            location=result.location,
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
                        details={"dates_written": list(result.days.keys())},
                    )
                    processed_ok += 1
                    notifier.send(
                        "Wochenplan OK",
                        f"{len(result.days)} Tag(e) eingetragen aus {os.path.basename(pdf_path)}"
                        + (f" [{result.location}]" if result.location else ""),
                    )
    finally:
        gmail.close()
        if not cfg.dry_run:
            calendar.close()

    logger.info(f"Done. OK={processed_ok} FAIL={processed_fail}")
    return 0 if processed_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
