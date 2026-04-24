"""키움 증권 자동매매 시스템 - 로깅 유틸리티"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "autotrading",
    level: str = "INFO",
    log_file: str = "logs/autotrading.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """로거를 설정하고 반환합니다.

    콘솔과 파일 양쪽에 로그를 출력합니다.

    Args:
        name: 로거 이름
        level: 로그 레벨 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_file: 로그 파일 경로
        max_bytes: 파일 당 최대 크기
        backup_count: 보관할 백업 파일 수

    Returns:
        설정된 Logger 객체
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger(name)
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        root_logger.addHandler(console_handler)

        # 파일 핸들러
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        root_logger.addHandler(file_handler)

    return root_logger
