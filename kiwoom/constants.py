"""키움 증권 자동매매 시스템 - 상수 정의 모듈

Kiwoom OpenAPI+ 에서 사용하는 각종 코드 및 상수를 정의합니다.
"""


class OrderType:
    """주문 유형"""
    BUY = 1    # 신규매수
    SELL = 2   # 신규매도
    BUY_CANCEL = 3   # 매수취소
    SELL_CANCEL = 4  # 매도취소
    BUY_MODIFY = 5   # 매수정정
    SELL_MODIFY = 6  # 매도정정


class OrderPriceType:
    """호가 유형"""
    LIMIT = "00"         # 지정가
    MARKET = "03"        # 시장가
    BEST_LIMIT = "05"    # 최유리지정가
    FIRST_LIMIT = "06"   # 최우선지정가
    PRE_MARKET = "61"    # 장전 시간외
    POST_MARKET = "62"   # 장후 시간외


class Market:
    """시장 구분"""
    KOSPI = "0"   # 코스피
    KOSDAQ = "10" # 코스닥
    ELW = "3"     # ELW
    ETF = "8"     # ETF


class TrCode:
    """TR 코드"""
    STOCK_INFO = "opt10001"       # 주식기본정보요청
    STOCK_DAILY = "opt10081"      # 주식일봉차트조회요청
    ACCOUNT_DETAIL = "opw00018"   # 계좌평가잔고내역요청
    DEPOSIT_DETAIL = "opw00001"   # 예수금상세현황요청
    ORDER_LIST = "opt10076"       # 미체결요청


class RealType:
    """실시간 타입"""
    STOCK_QUOTE = "주식시세"
    STOCK_ORDER = "주식체결"
    CONCLUSION = "체결"
    BALANCE = "잔고"


class ErrorCode:
    """에러 코드"""
    OP_ERR_NONE = 0              # 정상
    OP_ERR_LOGIN = -100          # 로그인 실패
    OP_ERR_CONNECT = -101        # 연결 실패
    OP_ERR_VERSION = -102        # 버전 오류
    OP_ERR_REGIST_FAIL = -103    # 등록 실패
    OP_ERR_EXIST_SESSION = -104  # 이미 세션 존재
    OP_ERR_COMMUNICATION = -105  # 통신 오류
    OP_ERR_NOT_CONNECT = -106    # 미연결
    OP_ERR_SEND_INPUT = -107     # 전송 오류
    OP_ERR_ORDER_OVERFLOW = -108 # 주문 초과
    OP_ERR_RQ_STRUCT_FAIL = -200 # TR 구조 오류
    OP_ERR_RQ_STRING_FAIL = -201 # TR 문자열 오류
    OP_ERR_NO_DATA = -202        # 데이터 없음
    OP_ERR_OVER_MAX_DATA = -203  # 최대 데이터 초과
    OP_ERR_NO_SENDDATA = -300    # 전송 데이터 없음
    OP_ERR_ILLEGAL_SCREEN = -301 # 화면번호 오류

    MESSAGES = {
        0: "정상",
        -100: "로그인 실패",
        -101: "연결 실패",
        -102: "버전 오류",
        -200: "TR 입력값 오류",
        -201: "TR 입력값 오류",
        -202: "TR 데이터 없음",
        -300: "전송 데이터 없음",
        -301: "화면번호 오류",
    }

    @classmethod
    def get_message(cls, code: int) -> str:
        return cls.MESSAGES.get(code, f"알 수 없는 오류 ({code})")


class RealFid:
    """실시간 FID (Field ID) - 주요 항목"""
    CURRENT_PRICE = "10"     # 현재가
    VOLUME = "15"            # 거래량
    OPEN_PRICE = "16"        # 시가
    HIGH_PRICE = "17"        # 고가
    LOW_PRICE = "18"         # 저가
    ASK_PRICE = "27"         # 매도호가
    BID_PRICE = "28"         # 매수호가
    CHANGE = "11"            # 전일대비
    CHANGE_RATE = "12"       # 등락률
