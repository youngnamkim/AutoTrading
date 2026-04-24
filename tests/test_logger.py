"""로깅 유틸리티 단위 테스트"""

import logging
import os
import pytest

from utils.logger import setup_logger


class TestSetupLogger:
    def test_returns_logger(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = setup_logger(name="test_logger", log_file=log_file)
        assert isinstance(logger, logging.Logger)

    def test_creates_log_file(self, tmp_path):
        log_file = str(tmp_path / "sub" / "test.log")
        logger = setup_logger(name="test_logger2", log_file=log_file)
        logger.info("test message")
        assert os.path.exists(log_file)

    def test_log_level_respected(self, tmp_path):
        log_file = str(tmp_path / "test_level.log")
        logger = setup_logger(name="test_logger3", level="WARNING", log_file=log_file)
        assert logger.level == logging.WARNING

    def test_idempotent_handlers(self, tmp_path):
        log_file = str(tmp_path / "idempotent.log")
        logger1 = setup_logger(name="test_idempotent", log_file=log_file)
        handler_count = len(logger1.handlers)
        logger2 = setup_logger(name="test_idempotent", log_file=log_file)
        assert len(logger2.handlers) == handler_count
