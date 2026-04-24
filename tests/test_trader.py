"""AutoTrader 단위 테스트"""

import pytest
from unittest.mock import MagicMock, patch

from trader.auto_trader import AutoTrader, Position
from strategy.base_strategy import Signal
from kiwoom.constants import ErrorCode, OrderType, OrderPriceType


def _make_candles(closes):
    return [{"date": f"20240101", "open": c, "high": c, "low": c,
             "close": c, "volume": 1000}
            for c in closes]


@pytest.fixture
def mock_kiwoom():
    kiwoom = MagicMock()
    kiwoom.send_order.return_value = ErrorCode.OP_ERR_NONE
    return kiwoom


@pytest.fixture
def mock_strategy():
    return MagicMock()


@pytest.fixture
def trader(mock_kiwoom, mock_strategy):
    return AutoTrader(
        kiwoom=mock_kiwoom,
        strategy=mock_strategy,
        account_no="1234567890",
        target_codes=["005930", "000660"],
        max_buy_amount=1_000_000,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        screen_no="0001",
    )


class TestPosition:
    def test_total_value(self):
        pos = Position("005930", quantity=10, avg_price=70000)
        assert pos.total_value == 700000

    def test_repr(self):
        pos = Position("005930", quantity=5, avg_price=70000)
        assert "005930" in repr(pos)
        assert "5" in repr(pos)


class TestAutoTraderInit:
    def test_attributes(self, trader, mock_kiwoom, mock_strategy):
        assert trader.account_no == "1234567890"
        assert trader.target_codes == ["005930", "000660"]
        assert trader.max_buy_amount == 1_000_000
        assert trader.stop_loss_pct == 0.05
        assert trader.take_profit_pct == 0.10

    def test_no_initial_positions(self, trader):
        assert trader.get_positions() == {}


class TestAutoTraderUpdatePosition:
    def test_add_position(self, trader):
        trader.update_position("005930", 10, 70000)
        positions = trader.get_positions()
        assert "005930" in positions
        assert positions["005930"].quantity == 10

    def test_remove_position_when_zero_quantity(self, trader):
        trader.update_position("005930", 10, 70000)
        trader.update_position("005930", 0, 70000)
        assert "005930" not in trader.get_positions()

    def test_remove_position_when_negative_quantity(self, trader):
        trader.update_position("005930", 10, 70000)
        trader.update_position("005930", -1, 70000)
        assert "005930" not in trader.get_positions()


class TestAutoTraderRunOnce:
    def test_buy_order_on_buy_signal(self, trader, mock_kiwoom, mock_strategy):
        candles = _make_candles([70000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.BUY

        trader.run_once("20240101")

        assert mock_kiwoom.send_order.call_count == 2  # 2 target codes
        call_args = mock_kiwoom.send_order.call_args_list[0]
        assert call_args.kwargs["order_type"] == OrderType.BUY
        assert call_args.kwargs["hoga_type"] == OrderPriceType.MARKET

    def test_no_buy_when_already_holding(self, trader, mock_kiwoom, mock_strategy):
        candles = _make_candles([70000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.BUY

        # Pre-populate positions at the same price as current (no P&L triggers)
        trader.update_position("005930", 10, 70000)
        trader.update_position("000660", 5, 70000)

        trader.run_once("20240101")

        mock_kiwoom.send_order.assert_not_called()

    def test_sell_order_on_sell_signal(self, trader, mock_kiwoom, mock_strategy):
        candles = _make_candles([70000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.SELL

        trader.update_position("005930", 10, 70000)
        trader.update_position("000660", 5, 100000)

        trader.run_once("20240101")

        assert mock_kiwoom.send_order.call_count == 2
        call_args = mock_kiwoom.send_order.call_args_list[0]
        assert call_args.kwargs["order_type"] == OrderType.SELL

    def test_no_sell_when_not_holding(self, trader, mock_kiwoom, mock_strategy):
        candles = _make_candles([70000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.SELL

        trader.run_once("20240101")

        mock_kiwoom.send_order.assert_not_called()

    def test_hold_signal_no_order(self, trader, mock_kiwoom, mock_strategy):
        candles = _make_candles([70000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.HOLD

        trader.run_once("20240101")

        mock_kiwoom.send_order.assert_not_called()

    def test_no_order_when_no_candles(self, trader, mock_kiwoom, mock_strategy):
        mock_kiwoom.get_stock_daily_candle.return_value = []

        trader.run_once("20240101")

        mock_kiwoom.send_order.assert_not_called()
        mock_strategy.generate_signal.assert_not_called()


class TestStopLossTakeProfit:
    def test_stop_loss_triggers_sell(self, trader, mock_kiwoom, mock_strategy):
        # avg price = 100000, current = 94000 → -6% (손절 기준 -5% 초과)
        candles = _make_candles([94000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.HOLD

        trader.update_position("005930", 10, 100000)

        trader._process_code("005930", "20240101")

        mock_kiwoom.send_order.assert_called_once()
        assert mock_kiwoom.send_order.call_args.kwargs["order_type"] == OrderType.SELL

    def test_take_profit_triggers_sell(self, trader, mock_kiwoom, mock_strategy):
        # avg price = 100000, current = 111000 → +11% (익절 기준 +10% 초과)
        candles = _make_candles([111000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.HOLD

        trader.update_position("005930", 10, 100000)

        trader._process_code("005930", "20240101")

        mock_kiwoom.send_order.assert_called_once()
        assert mock_kiwoom.send_order.call_args.kwargs["order_type"] == OrderType.SELL

    def test_no_stop_loss_below_threshold(self, trader, mock_kiwoom, mock_strategy):
        # avg price = 100000, current = 97000 → -3% (손절 기준 미충족)
        candles = _make_candles([97000] * 25)
        mock_kiwoom.get_stock_daily_candle.return_value = candles
        mock_strategy.generate_signal.return_value = Signal.HOLD

        trader.update_position("005930", 10, 100000)

        trader._process_code("005930", "20240101")

        mock_kiwoom.send_order.assert_not_called()


class TestCalcBuyQuantity:
    def test_normal_price(self, trader):
        qty = trader._calc_buy_quantity(100000)
        assert qty == 10  # 1,000,000 // 100,000

    def test_zero_price(self, trader):
        qty = trader._calc_buy_quantity(0)
        assert qty == 0

    def test_fractional(self, trader):
        qty = trader._calc_buy_quantity(300000)
        assert qty == 3  # 1,000,000 // 300,000
