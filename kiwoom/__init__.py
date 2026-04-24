"""키움 증권 자동매매 시스템 - kiwoom 패키지

Kiwoom 클래스는 PyQt5(Windows) 환경에서만 임포트 가능합니다.
상수 클래스는 플랫폼에 관계없이 임포트할 수 있습니다.
"""

from kiwoom.constants import OrderType, OrderPriceType, Market, TrCode, ErrorCode

__all__ = ["OrderType", "OrderPriceType", "Market", "TrCode", "ErrorCode"]

try:
    from kiwoom.kiwoom import Kiwoom
    __all__.append("Kiwoom")
except ImportError:
    pass
