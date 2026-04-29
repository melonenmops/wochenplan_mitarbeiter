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
    assert not result.days


def test_parser_returns_empty_on_extraction_error(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    with patch("pdfplumber.open", side_effect=Exception("corrupt PDF")):
        result = parser.parse("corrupt.pdf")
    assert not result.days


def test_parser_handles_missing_file(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    result = parser.parse("/nonexistent/path/plan.pdf")
    assert not result.days
    assert result.location == ""


def test_parser_result_has_correct_types(tmp_path):
    from app.pdf_parser import PDFParser, ParseResult
    from datetime import datetime
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    sample = (
        "Wochenplan KW 17 - 2026\n\n"
        "Montag 27.04.2026\nAlice Muster, Bob Schmidt\n\n"
        "Dienstag 28.04.2026\nCarol Weber\n"
    )
    with patch("pdfplumber.open", return_value=_mock_pdf(sample)):
        result = parser.parse("fake.pdf")
    assert isinstance(result, ParseResult)
    for date_key, names in result.days.items():
        assert isinstance(date_key, str)
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)
        datetime.fromisoformat(date_key)


def test_parser_extracts_location_marschacht(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    text = (
        "Wochenplan Grafisch [wir leben - Apotheke in Marschacht Offizin] Seite: 1 / 1\n"
        "27.04.2026 - 02.05.2026\n"
        "Mo, 27.04. 7 8 9 10\n"
        "Rassel, Maike 07:30-15:00\n"
    )
    with patch("pdfplumber.open", return_value=_mock_pdf(text)):
        result = parser.parse("fake.pdf")
    assert result.location == "Marschacht"


def test_parser_extracts_location_garberscenter(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    text = (
        "Wochenplan Grafisch [wir leben - Apotheke im Garberscenter] Seite: 1 / 1\n"
        "27.04.2026 - 02.05.2026\n"
        "Mo, 27.04. 7 8 9 10\n"
        "Brandt, Sonja 09:00-19:00\n"
    )
    with patch("pdfplumber.open", return_value=_mock_pdf(text)):
        result = parser.parse("fake.pdf")
    assert result.location == "Garberscenter"


def test_parser_names_sorted_alphabetically(tmp_path):
    from app.pdf_parser import PDFParser
    parser = PDFParser(debug_dir=str(tmp_path), debug_mode=False)
    text = (
        "27.04.2026 - 02.05.2026\n"
        "Mo, 27.04. 7 8 9 10\n"
        "Ziegler, Hans 07:30-15:00\n"
        "Ahrens, Christina 08:00-16:00\n"
        "Müller, Tom 09:00-17:00\n"
    )
    with patch("pdfplumber.open", return_value=_mock_pdf(text)):
        result = parser.parse("fake.pdf")
    names = result.days.get("2026-04-27", [])
    assert names == sorted(names)
