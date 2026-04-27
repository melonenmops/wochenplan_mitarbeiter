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
        """
        Extract date->names mapping from PDF.
        Returns empty dict if format is not recognized.
        Never raises — all errors are logged and return {}.
        """
        if not _HAS_PDFPLUMBER:
            self.logger.error("pdfplumber not installed — cannot parse PDFs")
            return {}

        try:
            text = self._extract_text(pdf_path)
        except FileNotFoundError:
            self.logger.error(f"PDF file not found: {pdf_path}")
            return {}
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
