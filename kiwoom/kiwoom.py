"""키움 증권 자동매매 시스템 - Kiwoom OpenAPI+ 래퍼 모듈

Kiwoom OpenAPI+ OCX 컨트롤을 PyQt5 QAxWidget으로 감싸서 사용합니다.
Windows 환경에서 키움 HTS(영웅문)가 설치되어 있어야 정상 동작합니다.
"""

import sys
import logging
from typing import Callable, Dict, List, Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

from kiwoom.constants import ErrorCode, OrderType, OrderPriceType, TrCode

logger = logging.getLogger(__name__)


class Kiwoom(QAxWidget):
    """Kiwoom OpenAPI+ OCX 컨트롤 래퍼 클래스

    Kiwoom OpenAPI+와 통신하여 시세 조회, 주문 등을 처리합니다.

    Usage:
        app = QApplication(sys.argv)
        kiwoom = Kiwoom()
        kiwoom.comm_connect()
    """

    KIWOOM_OCX_ID = "KHOPENAPI.KHOpenAPICtrl.1"

    def __init__(self) -> None:
        super().__init__()
        self.setControl(self.KIWOOM_OCX_ID)

        self._login_event_loop: Optional[QEventLoop] = None
        self._tr_event_loop: Optional[QEventLoop] = None

        self._tr_data: Dict = {}
        self._real_data_callbacks: Dict[str, List[Callable]] = {}
        self._chejan_callbacks: List[Callable] = []

        self._connect_signals()

    # -------------------------------------------------------------------------
    # 시그널 연결
    # -------------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """OpenAPI 이벤트 시그널과 슬롯을 연결합니다."""
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)

    # -------------------------------------------------------------------------
    # 로그인 / 연결
    # -------------------------------------------------------------------------

    def comm_connect(self) -> int:
        """로그인 창을 띄우고 자동 로그인을 시도합니다.

        Returns:
            0이면 성공, 음수면 실패 (ErrorCode 참고)
        """
        self.dynamicCall("CommConnect()")
        self._login_event_loop = QEventLoop()
        self._login_event_loop.exec_()
        return self.get_connect_state()

    def get_connect_state(self) -> int:
        """현재 연결 상태를 반환합니다.

        Returns:
            1이면 연결됨, 0이면 미연결
        """
        return self.dynamicCall("GetConnectState()")

    def get_login_info(self, tag: str) -> str:
        """로그인 정보를 조회합니다.

        Args:
            tag: 조회할 항목
                - "ACCOUNT_CNT": 보유 계좌수
                - "ACCNO": 전체 계좌 목록 (';' 구분)
                - "USER_ID": 사용자 ID
                - "USER_NAME": 사용자 이름
                - "GetServerGubun": 서버 구분 (1: 모의, 나머지: 실제)

        Returns:
            요청한 로그인 정보 문자열
        """
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    # -------------------------------------------------------------------------
    # TR 요청
    # -------------------------------------------------------------------------

    def set_input_value(self, id: str, value: str) -> None:
        """TR 입력값을 설정합니다.

        Args:
            id: 입력 항목명
            value: 입력 값
        """
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname: str, trcode: str, next: int,
                     screen_no: str) -> int:
        """TR 데이터를 요청합니다.

        Args:
            rqname: 사용자 정의 요청명
            trcode: TR 코드
            next: 연속 조회 여부 (0: 처음, 2: 연속)
            screen_no: 화면번호

        Returns:
            0이면 성공, 음수면 실패
        """
        result = self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rqname, trcode, next, screen_no
        )
        if result == ErrorCode.OP_ERR_NONE:
            self._tr_event_loop = QEventLoop()
            self._tr_event_loop.exec_()
        return result

    def get_comm_data(self, trcode: str, rqname: str, index: int,
                      item_name: str) -> str:
        """TR 수신 데이터를 가져옵니다.

        Args:
            trcode: TR 코드
            rqname: 요청명
            index: 레코드 인덱스
            item_name: 항목명

        Returns:
            요청한 데이터 문자열 (공백 제거됨)
        """
        return self.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, rqname, index, item_name
        ).strip()

    def get_repeat_cnt(self, trcode: str, rqname: str) -> int:
        """TR 수신 데이터 레코드 수를 반환합니다.

        Args:
            trcode: TR 코드
            rqname: 요청명

        Returns:
            수신된 레코드 수
        """
        return self.dynamicCall(
            "GetRepeatCnt(QString, QString)", trcode, rqname
        )

    # -------------------------------------------------------------------------
    # 주문
    # -------------------------------------------------------------------------

    def send_order(
        self,
        rqname: str,
        screen_no: str,
        account_no: str,
        order_type: int,
        code: str,
        quantity: int,
        price: int,
        hoga_type: str,
        origin_order_no: str = ""
    ) -> int:
        """주식 주문을 전송합니다.

        Args:
            rqname: 사용자 정의 요청명
            screen_no: 화면번호
            account_no: 계좌번호
            order_type: 주문유형 (OrderType 참고)
            code: 종목코드
            quantity: 주문 수량
            price: 주문 단가 (시장가이면 0)
            hoga_type: 호가 유형 (OrderPriceType 참고)
            origin_order_no: 원주문번호 (정정/취소 시 사용)

        Returns:
            0이면 성공, 음수면 실패
        """
        return self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString,"
            " int, int, QString, QString)",
            rqname, screen_no, account_no, order_type,
            code, quantity, price, hoga_type, origin_order_no
        )

    # -------------------------------------------------------------------------
    # 시세 조회 (주식 일봉 데이터)
    # -------------------------------------------------------------------------

    def get_stock_daily_candle(
        self,
        code: str,
        base_date: str,
        screen_no: str = "0002",
        adj_price: str = "1"
    ) -> List[Dict]:
        """주식 일봉 데이터를 조회합니다.

        Args:
            code: 종목코드
            base_date: 기준일자 (YYYYMMDD)
            screen_no: 화면번호
            adj_price: 수정주가 구분 (1: 수정주가)

        Returns:
            일봉 데이터 리스트 (최신순)
            각 항목: {"date", "open", "high", "low", "close", "volume"}
        """
        self.set_input_value("종목코드", code)
        self.set_input_value("기준일자", base_date)
        self.set_input_value("수정주가구분", adj_price)
        self.comm_rq_data("주식일봉차트조회", TrCode.STOCK_DAILY, 0, screen_no)

        result = []
        cnt = self.get_repeat_cnt(TrCode.STOCK_DAILY, "주식일봉차트조회")
        for i in range(cnt):
            date = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "일자")
            open_p = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "시가")
            high_p = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "고가")
            low_p = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "저가")
            close_p = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "현재가")
            volume = self.get_comm_data(TrCode.STOCK_DAILY, "주식일봉차트조회", i, "거래량")
            result.append({
                "date": date,
                "open": int(open_p) if open_p else 0,
                "high": int(high_p) if high_p else 0,
                "low": int(low_p) if low_p else 0,
                # Kiwoom API returns negative close price when the stock fell on that day;
                # abs() converts it to the actual traded price.
                "close": abs(int(close_p)) if close_p else 0,
                "volume": int(volume) if volume else 0,
            })
        return result

    # -------------------------------------------------------------------------
    # 계좌 조회
    # -------------------------------------------------------------------------

    def get_account_list(self) -> List[str]:
        """보유 계좌 목록을 반환합니다."""
        raw = self.get_login_info("ACCNO")
        return [acc for acc in raw.split(";") if acc]

    def get_account_balance(
        self, account_no: str, password: str = "0000",
        screen_no: str = "0003"
    ) -> Dict:
        """계좌 평가 잔고 내역을 조회합니다.

        Args:
            account_no: 계좌번호
            password: 비밀번호 (기본 "0000")
            screen_no: 화면번호

        Returns:
            계좌 잔고 딕셔너리
        """
        self.set_input_value("계좌번호", account_no)
        self.set_input_value("비밀번호", password)
        self.set_input_value("비밀번호입력매체구분", "00")
        self.set_input_value("조회구분", "1")
        self.comm_rq_data("계좌평가잔고내역요청", TrCode.ACCOUNT_DETAIL, 0, screen_no)

        balance = {
            "total_purchase": self.get_comm_data(
                TrCode.ACCOUNT_DETAIL, "계좌평가잔고내역요청", 0, "총매입금액"),
            "total_eval": self.get_comm_data(
                TrCode.ACCOUNT_DETAIL, "계좌평가잔고내역요청", 0, "총평가금액"),
            "total_profit_loss": self.get_comm_data(
                TrCode.ACCOUNT_DETAIL, "계좌평가잔고내역요청", 0, "총평가손익금액"),
            "profit_loss_rate": self.get_comm_data(
                TrCode.ACCOUNT_DETAIL, "계좌평가잔고내역요청", 0, "총수익률(%)"),
        }
        return balance

    # -------------------------------------------------------------------------
    # 실시간 데이터 구독
    # -------------------------------------------------------------------------

    def set_real_reg(
        self, screen_no: str, codes: str, fids: str, real_type: str = "0"
    ) -> None:
        """실시간 데이터를 등록합니다.

        Args:
            screen_no: 화면번호
            codes: 종목코드 목록 (';' 구분)
            fids: FID 목록 (';' 구분)
            real_type: 등록 타입 ("0": 교체, "1": 추가)
        """
        self.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no, codes, fids, real_type
        )

    def set_real_remove(self, screen_no: str, code: str) -> None:
        """실시간 데이터 등록을 해제합니다.

        Args:
            screen_no: 화면번호
            code: 종목코드 (전체 해제 시 "ALL")
        """
        self.dynamicCall(
            "SetRealRemove(QString, QString)", screen_no, code
        )

    def register_real_data_callback(
        self, code: str, callback: Callable
    ) -> None:
        """실시간 데이터 콜백을 등록합니다.

        Args:
            code: 종목코드
            callback: 콜백 함수 (code, real_type, data_dict)
        """
        if code not in self._real_data_callbacks:
            self._real_data_callbacks[code] = []
        self._real_data_callbacks[code].append(callback)

    def register_chejan_callback(self, callback: Callable) -> None:
        """체결 콜백을 등록합니다.

        Args:
            callback: 콜백 함수 (gubun, data_dict)
        """
        self._chejan_callbacks.append(callback)

    def get_chejan_data(self, fid: str) -> str:
        """체결 데이터를 가져옵니다.

        Args:
            fid: FID 코드

        Returns:
            FID에 해당하는 데이터 문자열
        """
        return self.dynamicCall("GetChejanData(int)", fid).strip()

    def get_comm_real_data(self, code: str, fid: str) -> str:
        """실시간 데이터를 가져옵니다.

        Args:
            code: 종목코드
            fid: FID 코드

        Returns:
            FID에 해당하는 데이터 문자열
        """
        return self.dynamicCall(
            "GetCommRealData(QString, int)", code, fid
        ).strip()

    # -------------------------------------------------------------------------
    # 이벤트 핸들러 (내부)
    # -------------------------------------------------------------------------

    def _on_event_connect(self, err_code: int) -> None:
        """로그인 이벤트 처리"""
        if err_code == ErrorCode.OP_ERR_NONE:
            logger.info("로그인 성공")
        else:
            logger.error("로그인 실패: %s", ErrorCode.get_message(err_code))
        if self._login_event_loop:
            self._login_event_loop.exit()

    def _on_receive_tr_data(
        self,
        scr_no: str,
        rqname: str,
        trcode: str,
        record_name: str,
        next: str,
        unused1: str,
        unused2: str,
        unused3: str,
        unused4: str,
    ) -> None:
        """TR 데이터 수신 이벤트 처리"""
        logger.debug("TR 수신: rqname=%s, trcode=%s, next=%s", rqname, trcode, next)
        self._tr_data["next"] = next
        if self._tr_event_loop:
            self._tr_event_loop.exit()

    def _on_receive_real_data(
        self, code: str, real_type: str, real_data: str
    ) -> None:
        """실시간 데이터 수신 이벤트 처리"""
        callbacks = self._real_data_callbacks.get(code, [])
        for cb in callbacks:
            try:
                cb(code, real_type, real_data)
            except Exception:
                logger.exception("실시간 데이터 콜백 오류: code=%s", code)

    def _on_receive_chejan_data(
        self, gubun: str, item_cnt: int, fid_list: str
    ) -> None:
        """체결 데이터 수신 이벤트 처리

        Args:
            gubun: 체결구분 ("0": 주문체결, "1": 잔고변동, "3": 특이신호)
        """
        logger.debug("체결 수신: gubun=%s, fids=%s", gubun, fid_list)
        for cb in self._chejan_callbacks:
            try:
                cb(gubun, fid_list)
            except Exception:
                logger.exception("체결 콜백 오류")

    def _on_receive_msg(
        self, scr_no: str, rqname: str, trcode: str, msg: str
    ) -> None:
        """서버 메시지 수신 이벤트 처리"""
        logger.info("서버 메시지: [%s] %s", trcode, msg)
