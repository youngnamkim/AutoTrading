"""Kiwoom 상수 및 에러코드 단위 테스트"""

import pytest

from kiwoom.constants import ErrorCode, OrderType, OrderPriceType, Market, TrCode


class TestErrorCode:
    def test_known_error_message(self):
        assert "정상" in ErrorCode.get_message(0)

    def test_unknown_error_code(self):
        msg = ErrorCode.get_message(-999)
        assert "-999" in msg

    def test_login_failure_message(self):
        msg = ErrorCode.get_message(ErrorCode.OP_ERR_LOGIN)
        assert msg  # non-empty string


class TestOrderType:
    def test_buy_is_1(self):
        assert OrderType.BUY == 1

    def test_sell_is_2(self):
        assert OrderType.SELL == 2


class TestOrderPriceType:
    def test_market_order_code(self):
        assert OrderPriceType.MARKET == "03"

    def test_limit_order_code(self):
        assert OrderPriceType.LIMIT == "00"


class TestTrCode:
    def test_stock_daily_code(self):
        assert TrCode.STOCK_DAILY == "opt10081"

    def test_account_detail_code(self):
        assert TrCode.ACCOUNT_DETAIL == "opw00018"
