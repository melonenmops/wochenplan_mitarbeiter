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
