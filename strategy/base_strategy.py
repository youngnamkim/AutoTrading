"""키움 증권 자동매매 시스템 - 전략 기본 클래스"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class Signal:
    """매매 신호"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    """자동매매 전략의 기본 추상 클래스.

    모든 전략은 이 클래스를 상속받아 generate_signal 메서드를 구현해야 합니다.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def generate_signal(
        self, code: str, candles: List[Dict]
    ) -> str:
        """매매 신호를 생성합니다.

        Args:
            code: 종목코드
            candles: 일봉 데이터 리스트 (최신순)
                각 항목: {"date", "open", "high", "low", "close", "volume"}

        Returns:
            Signal.BUY, Signal.SELL, Signal.HOLD 중 하나
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
