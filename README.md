# AutoTrading - 키움증권 자동매매 시스템

키움증권 OpenAPI+를 활용한 주식 자동매매 시스템입니다.

## 아키텍처

```
AutoTrading/
├── config/
│   └── config.yaml          # 설정 파일
├── kiwoom/
│   ├── kiwoom.py            # Kiwoom OpenAPI+ 래퍼
│   └── constants.py         # API 상수 (주문유형, TR코드 등)
├── strategy/
│   ├── base_strategy.py     # 전략 추상 기본 클래스
│   └── moving_average.py    # 이동평균 교차 전략
├── trader/
│   └── auto_trader.py       # 자동매매 실행 엔진
├── utils/
│   └── logger.py            # 로깅 유틸리티
├── tests/                   # 단위 테스트
├── main.py                  # 진입점
└── requirements.txt
```

## 사전 조건

- **Windows** 운영체제 (Kiwoom OpenAPI+는 Windows 전용)
- [키움증권 영웅문4](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000) 설치 및 로그인
- Python 3.8 이상

## 설치

```bash
pip install -r requirements.txt
```

## 설정

`config/config.yaml`를 편집하여 계좌번호, 대상 종목, 전략 파라미터 등을 설정하세요.

```yaml
kiwoom:
  account: "1234567890"  # 본인 계좌번호 입력

target_stocks:
  - "005930"   # 삼성전자
  - "000660"   # SK하이닉스

trading:
  max_buy_amount: 1000000   # 종목당 최대 매수 금액 (원)
  stop_loss_pct: 0.05       # 손절 비율 (5%)
  take_profit_pct: 0.10     # 익절 비율 (10%)

strategy:
  short_period: 5           # 단기 이동평균 기간
  long_period: 20           # 장기 이동평균 기간
```

## 실행

```bash
python main.py --config config/config.yaml
```

## 전략

현재 구현된 전략: **이동평균 교차 전략 (골든크로스/데드크로스)**

- **매수 신호**: 단기 이동평균선이 장기 이동평균선을 **상향 돌파** (골든크로스)
- **매도 신호**: 단기 이동평균선이 장기 이동평균선을 **하향 돌파** (데드크로스)
- **손절/익절**: 보유 중인 종목이 설정된 비율 이상 손실/이익 발생 시 자동 매도

커스텀 전략을 추가하려면 `strategy/base_strategy.py`의 `BaseStrategy`를 상속하세요.

## 테스트

```bash
pip install pytest pytest-mock numpy
pytest
```

## 주의사항

- 본 소프트웨어는 교육 목적으로 제공됩니다.
- 실제 투자에 사용할 경우 발생하는 손실에 대해 책임지지 않습니다.
- 모의투자 계좌로 충분히 테스트한 후 실제 계좌에서 사용하세요.
