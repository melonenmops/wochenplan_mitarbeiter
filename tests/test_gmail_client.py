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
