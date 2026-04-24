"""이동평균 전략 단위 테스트"""

import pytest

from strategy.moving_average import MovingAverageStrategy
from strategy.base_strategy import Signal


def _make_candles(closes):
    """종가 리스트로 candle 더미 데이터를 생성합니다 (최신순)."""
    return [{"date": f"2024010{i}", "open": c, "high": c, "low": c,
             "close": c, "volume": 1000}
            for i, c in enumerate(closes)]


class TestMovingAverageStrategyInit:
    def test_default_periods(self):
        s = MovingAverageStrategy()
        assert s.short_period == 5
        assert s.long_period == 20

    def test_custom_periods(self):
        s = MovingAverageStrategy(short_period=3, long_period=10)
        assert s.short_period == 3
        assert s.long_period == 10

    def test_invalid_periods_raises(self):
        with pytest.raises(ValueError):
            MovingAverageStrategy(short_period=20, long_period=5)

    def test_equal_periods_raises(self):
        with pytest.raises(ValueError):
            MovingAverageStrategy(short_period=10, long_period=10)


class TestMovingAverageSignal:
    def setup_method(self):
        self.strategy = MovingAverageStrategy(short_period=3, long_period=5)

    def test_hold_when_insufficient_data(self):
        candles = _make_candles([100, 110, 120])
        assert self.strategy.generate_signal("TEST", candles) == Signal.HOLD

    def test_hold_when_no_crossover(self):
        # 단기 MA > 장기 MA 유지 (골든크로스 없음)
        closes = [120, 118, 116, 114, 112, 110]
        candles = _make_candles(closes)
        result = self.strategy.generate_signal("TEST", candles)
        assert result == Signal.HOLD

    def test_golden_cross_generates_buy(self):
        # 최신 2개: 단기MA가 장기MA를 상향 돌파하도록 설계
        # closes는 최신순
        # 이전: 단기MA(100,100,100) = 100, 장기MA(100,100,100,100,100) = 100 → 같음
        # 현재: 단기MA(200,100,100) = 133.3, 장기MA(200,100,100,100,100) = 120 → 골든크로스
        closes = [200, 100, 100, 100, 100, 100]
        candles = _make_candles(closes)
        result = self.strategy.generate_signal("TEST", candles)
        assert result == Signal.BUY

    def test_dead_cross_generates_sell(self):
        # 이전: 단기MA = 100, 장기MA = 100
        # 현재: 단기MA(10,100,100) = 70, 장기MA(10,100,100,100,100) = 82 → 데드크로스
        closes = [10, 100, 100, 100, 100, 100]
        candles = _make_candles(closes)
        result = self.strategy.generate_signal("TEST", candles)
        assert result == Signal.SELL


class TestMovingAverages:
    def setup_method(self):
        self.strategy = MovingAverageStrategy(short_period=3, long_period=5)

    def test_returns_none_when_insufficient(self):
        candles = _make_candles([100, 200])
        result = self.strategy.get_moving_averages(candles)
        assert result["short_ma"] is None
        assert result["long_ma"] is None

    def test_short_ma_only_when_partial(self):
        candles = _make_candles([100, 200, 300])
        result = self.strategy.get_moving_averages(candles)
        assert result["short_ma"] == pytest.approx(200.0)
        assert result["long_ma"] is None

    def test_both_mas_when_sufficient(self):
        candles = _make_candles([100, 200, 300, 400, 500])
        result = self.strategy.get_moving_averages(candles)
        assert result["short_ma"] == pytest.approx(200.0)   # mean(100,200,300)
        assert result["long_ma"] == pytest.approx(300.0)    # mean(100,200,300,400,500)
