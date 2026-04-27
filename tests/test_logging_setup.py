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
