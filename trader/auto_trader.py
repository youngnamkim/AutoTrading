"""키움 증권 자동매매 시스템 - 자동매매 실행 엔진"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from kiwoom.constants import OrderType, OrderPriceType, ErrorCode
from strategy.base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class Position:
    """보유 포지션 정보"""

    def __init__(self, code: str, quantity: int, avg_price: float) -> None:
        self.code = code
        self.quantity = quantity
        self.avg_price = avg_price

    @property
    def total_value(self) -> float:
        return self.quantity * self.avg_price

    def __repr__(self) -> str:
        return (
            f"Position(code={self.code!r}, qty={self.quantity}, "
            f"avg_price={self.avg_price:.0f})"
        )


class AutoTrader:
    """자동매매 실행 엔진.

    Kiwoom API를 통해 전략 신호에 따라 자동으로 주문을 실행합니다.

    Args:
        kiwoom: Kiwoom API 인스턴스
        strategy: 사용할 전략 인스턴스
        account_no: 거래 계좌번호
        target_codes: 자동매매 대상 종목코드 리스트
        max_buy_amount: 종목당 최대 매수 금액 (KRW)
        stop_loss_pct: 손절 비율 (예: 0.05 → 5%)
        take_profit_pct: 익절 비율 (예: 0.10 → 10%)
        screen_no: 주문용 화면번호
    """

    def __init__(
        self,
        kiwoom,
        strategy: BaseStrategy,
        account_no: str,
        target_codes: List[str],
        max_buy_amount: int = 1_000_000,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
        screen_no: str = "0001",
    ) -> None:
        self.kiwoom = kiwoom
        self.strategy = strategy
        self.account_no = account_no
        self.target_codes = target_codes
        self.max_buy_amount = max_buy_amount
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.screen_no = screen_no

        self._positions: Dict[str, Position] = {}

    # -------------------------------------------------------------------------
    # 공개 메서드
    # -------------------------------------------------------------------------

    def run_once(self, base_date: Optional[str] = None) -> None:
        """전략을 실행하여 모든 대상 종목에 대해 신호를 평가하고 주문합니다.

        Args:
            base_date: 일봉 조회 기준일자 (YYYYMMDD, None이면 오늘)
        """
        if base_date is None:
            base_date = datetime.now().strftime("%Y%m%d")

        logger.info("=== 자동매매 실행 시작: %s ===", base_date)
        for code in self.target_codes:
            try:
                self._process_code(code, base_date)
            except Exception:
                logger.exception("[%s] 처리 중 오류 발생", code)
        logger.info("=== 자동매매 실행 완료 ===")

    def get_positions(self) -> Dict[str, Position]:
        """현재 보유 포지션을 반환합니다."""
        return dict(self._positions)

    def update_position(
        self, code: str, quantity: int, avg_price: float
    ) -> None:
        """보유 포지션을 업데이트합니다.

        Args:
            code: 종목코드
            quantity: 보유 수량 (0이면 포지션 제거)
            avg_price: 평균 단가
        """
        if quantity <= 0:
            self._positions.pop(code, None)
        else:
            self._positions[code] = Position(code, quantity, avg_price)

    # -------------------------------------------------------------------------
    # 내부 로직
    # -------------------------------------------------------------------------

    def _process_code(self, code: str, base_date: str) -> None:
        """단일 종목에 대해 신호 평가 및 주문 처리를 수행합니다."""
        candles = self.kiwoom.get_stock_daily_candle(code, base_date)
        if not candles:
            logger.warning("[%s] 일봉 데이터 없음", code)
            return

        signal = self.strategy.generate_signal(code, candles)
        current_price = candles[0]["close"]

        # 손절/익절 체크 (기존 포지션이 있을 경우)
        if code in self._positions:
            position = self._positions[code]
            pnl_rate = (current_price - position.avg_price) / position.avg_price

            if pnl_rate <= -self.stop_loss_pct:
                logger.info(
                    "[%s] 손절 조건 충족 (수익률: %.2f%%) → 전량 매도",
                    code, pnl_rate * 100
                )
                self._place_sell_order(code, position.quantity, current_price)
                return

            if pnl_rate >= self.take_profit_pct:
                logger.info(
                    "[%s] 익절 조건 충족 (수익률: %.2f%%) → 전량 매도",
                    code, pnl_rate * 100
                )
                self._place_sell_order(code, position.quantity, current_price)
                return

        if signal == Signal.BUY and code not in self._positions:
            quantity = self._calc_buy_quantity(current_price)
            if quantity > 0:
                self._place_buy_order(code, quantity, current_price)
        elif signal == Signal.SELL and code in self._positions:
            position = self._positions[code]
            self._place_sell_order(code, position.quantity, current_price)

    def _calc_buy_quantity(self, price: int) -> int:
        """매수 수량을 계산합니다.

        Args:
            price: 현재가

        Returns:
            매수 가능 수량 (0이면 매수 불가)
        """
        if price <= 0:
            return 0
        return int(self.max_buy_amount // price)

    def _place_buy_order(self, code: str, quantity: int, price: int) -> None:
        """시장가 매수 주문을 전송합니다."""
        logger.info("[%s] 매수 주문: %d주 @ 시장가", code, quantity)
        result = self.kiwoom.send_order(
            rqname="자동매수",
            screen_no=self.screen_no,
            account_no=self.account_no,
            order_type=OrderType.BUY,
            code=code,
            quantity=quantity,
            price=0,
            hoga_type=OrderPriceType.MARKET,
        )
        if result == ErrorCode.OP_ERR_NONE:
            logger.info("[%s] 매수 주문 성공", code)
        else:
            logger.error(
                "[%s] 매수 주문 실패: %s", code, ErrorCode.get_message(result)
            )

    def _place_sell_order(self, code: str, quantity: int, price: int) -> None:
        """시장가 매도 주문을 전송합니다."""
        logger.info("[%s] 매도 주문: %d주 @ 시장가", code, quantity)
        result = self.kiwoom.send_order(
            rqname="자동매도",
            screen_no=self.screen_no,
            account_no=self.account_no,
            order_type=OrderType.SELL,
            code=code,
            quantity=quantity,
            price=0,
            hoga_type=OrderPriceType.MARKET,
        )
        if result == ErrorCode.OP_ERR_NONE:
            logger.info("[%s] 매도 주문 성공", code)
            self._positions.pop(code, None)
        else:
            logger.error(
                "[%s] 매도 주문 실패: %s", code, ErrorCode.get_message(result)
            )
