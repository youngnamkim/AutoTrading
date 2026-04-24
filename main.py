"""키움 증권 자동매매 시스템 - 진입점

Usage:
    python main.py [--config config/config.yaml]
"""

import argparse
import sys
import os
import logging

import yaml
from PyQt5.QtWidgets import QApplication

from kiwoom import Kiwoom
from strategy import MovingAverageStrategy
from trader import AutoTrader
from utils import setup_logger


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_strategy(cfg: dict) -> MovingAverageStrategy:
    s = cfg.get("strategy", {})
    return MovingAverageStrategy(
        short_period=s.get("short_period", 5),
        long_period=s.get("long_period", 20),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="키움증권 자동매매 시스템")
    parser.add_argument(
        "--config", default="config/config.yaml", help="설정 파일 경로"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    log_cfg = cfg.get("logging", {})
    setup_logger(
        level=log_cfg.get("level", "INFO"),
        log_file=log_cfg.get("file", "logs/autotrading.log"),
    )
    logger = logging.getLogger("autotrading")

    app = QApplication(sys.argv)

    kiwoom = Kiwoom()
    state = kiwoom.comm_connect()
    if state != 1:
        logger.error("Kiwoom 연결 실패. HTS(영웅문4)가 실행 중인지 확인하세요.")
        sys.exit(1)

    accounts = kiwoom.get_account_list()
    if not accounts:
        logger.error("사용 가능한 계좌가 없습니다.")
        sys.exit(1)

    account_no = cfg.get("kiwoom", {}).get("account") or accounts[0]
    logger.info("사용 계좌: %s", account_no)

    strategy = build_strategy(cfg)
    trading_cfg = cfg.get("trading", {})
    trader = AutoTrader(
        kiwoom=kiwoom,
        strategy=strategy,
        account_no=account_no,
        target_codes=cfg.get("target_stocks", []),
        max_buy_amount=trading_cfg.get("max_buy_amount", 1_000_000),
        stop_loss_pct=trading_cfg.get("stop_loss_pct", 0.05),
        take_profit_pct=trading_cfg.get("take_profit_pct", 0.10),
        screen_no=cfg.get("kiwoom", {}).get("screen_no", "0001"),
    )

    trader.run_once()


if __name__ == "__main__":
    main()
