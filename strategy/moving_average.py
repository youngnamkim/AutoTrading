"""키움 증권 자동매매 시스템 - 이동평균선 교차 전략

단기 이동평균선이 장기 이동평균선을 상향 돌파하면 매수,
하향 돌파하면 매도하는 골든크로스/데드크로스 전략입니다.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from strategy.base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class MovingAverageStrategy(BaseStrategy):
    """이동평균선 교차 전략 (골든크로스/데드크로스).

    Args:
        short_period: 단기 이동평균 기간 (기본 5일)
        long_period: 장기 이동평균 기간 (기본 20일)

    Examples:
        >>> strategy = MovingAverageStrategy(short_period=5, long_period=20)
        >>> signal = strategy.generate_signal("005930", candles)
    """

    def __init__(self, short_period: int = 5, long_period: int = 20) -> None:
        super().__init__("moving_average")
        if short_period >= long_period:
            raise ValueError(
                f"단기 기간({short_period})은 장기 기간({long_period})보다 작아야 합니다."
            )
        self.short_period = short_period
        self.long_period = long_period

    def generate_signal(self, code: str, candles: List[Dict]) -> str:
        """이동평균선 교차를 기반으로 매매 신호를 생성합니다.

        candles 데이터는 최신순(인덱스 0이 가장 최신)으로 전달되어야 합니다.
        최소 long_period + 1개의 데이터가 필요합니다.

        Args:
            code: 종목코드
            candles: 일봉 데이터 리스트 (최신순)

        Returns:
            Signal.BUY, Signal.SELL, Signal.HOLD 중 하나
        """
        required = self.long_period + 1
        if len(candles) < required:
            logger.warning(
                "[%s] 데이터 부족: %d개 필요, %d개 보유",
                code, required, len(candles)
            )
            return Signal.HOLD

        closes = np.array([c["close"] for c in candles[:required]], dtype=float)
        # candles는 최신순이므로 역순으로 만들어 계산
        closes_asc = closes[::-1]

        short_ma_prev = float(np.mean(closes_asc[-(self.short_period + 1):-1]))
        short_ma_curr = float(np.mean(closes_asc[-self.short_period:]))
        long_ma_prev = float(np.mean(closes_asc[-(self.long_period + 1):-1]))
        long_ma_curr = float(np.mean(closes_asc[-self.long_period:]))

        logger.debug(
            "[%s] 단기MA: %.2f→%.2f, 장기MA: %.2f→%.2f",
            code, short_ma_prev, short_ma_curr, long_ma_prev, long_ma_curr
        )

        # 골든크로스: 단기MA가 장기MA를 상향 돌파
        if short_ma_prev <= long_ma_prev and short_ma_curr > long_ma_curr:
            logger.info("[%s] 골든크로스 감지 → 매수 신호", code)
            return Signal.BUY

        # 데드크로스: 단기MA가 장기MA를 하향 돌파
        if short_ma_prev >= long_ma_prev and short_ma_curr < long_ma_curr:
            logger.info("[%s] 데드크로스 감지 → 매도 신호", code)
            return Signal.SELL

        return Signal.HOLD

    def get_moving_averages(self, candles: List[Dict]) -> Dict[str, Optional[float]]:
        """현재 이동평균값을 반환합니다.

        Args:
            candles: 일봉 데이터 리스트 (최신순)

        Returns:
            {"short_ma": float|None, "long_ma": float|None}
        """
        if len(candles) < self.short_period:
            return {"short_ma": None, "long_ma": None}

        closes = np.array([c["close"] for c in candles], dtype=float)

        short_ma = float(np.mean(closes[:self.short_period]))
        long_ma = (
            float(np.mean(closes[:self.long_period]))
            if len(candles) >= self.long_period
            else None
        )
        return {"short_ma": short_ma, "long_ma": long_ma}
