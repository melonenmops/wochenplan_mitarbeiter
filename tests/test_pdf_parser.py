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
