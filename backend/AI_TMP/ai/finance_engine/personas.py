"""20~30대 유형(페르소나)별 합성 재무 데이터 생성기.

기존 synthetic.generate_rows() 는 모든 입력을 서로 무관한 균등분포로 뽑는다
(예: 비상금 0~400만 원 아무 값, 월 지출과도 무관). 현실에 없는 사람이 많이 섞여
있고, 사용자 층(20~30대)을 대표하지 못한다. 여기서는 유형별로 현실적인 모양의
분포를 쓴다.

   - 금액은 정규분포가 아니라 로그정규분포다. 돈은 대부분 작고 일부만 아주 크게
     치우쳐 있고, 정규분포는 음수 잔액을 만든다.
   - 항목끼리 상관이 있다 (월 지출이 큰 사람이 잔액·비상금도 큰 경향). 공통 요인
     하나(소득 수준)를 섞어 가우시안 코퓰러 방식으로 만든다.

!! 파라미터는 가정값이다 !!
    아래 PERSONAS 의 숫자는 통계청 수치에 맞춘 것이 아니라 합리적으로 가정한 값이다.
    (검증된 참고치 하나: 2024년 가계금융복지조사에서 39세 이하 가구의 평균 총자산은
    약 3.16억 원이지만 부동산 등을 포함한 값이라 현금성 잔액에 그대로 쓸 수 없다.)
    실제 분포에 맞추려면 KOSIS 의 가계동향조사(가구주 연령별 소득·소비지출)와
    가계금융복지조사(연령별 금융자산)에서 중앙값과 분산을 읽어 PERSONAS 를 고친다.
    값을 고치면 PERSONA_PARAMS_VERSION 도 올린다.

!! 라벨은 여전히 규칙이 붙인다 !!
    입력 분포를 현실적으로 바꿔도 정답은 synthetic.rule_bucket() 이 정한다.
    그래서 이 데이터의 점수도 '정확도'가 아니라 '규칙을 얼마나 흉내 냈나'다.
    실제 결과 라벨이 아니므로 selection.py 의 10만 건 관문에는 세지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .allowlist import TARGET_NAME
from .features import derive_model_features
from .synthetic import generate_rows, rule_bucket

PERSONA_PARAMS_VERSION = "personas-assumed-v1"

# 월 지출과 공통 요인의 상관 정도. 클수록 잔액·비상금이 월 지출과 함께 움직인다.
_AFFLUENCE_WEIGHT = 0.6


@dataclass(frozen=True)
class Persona:
    name: str
    weight: float  # 전체에서 차지하는 비율(합 1 로 정규화된다)
    monthly_spending_median: float  # 원
    monthly_spending_sigma: float  # 로그 표준편차
    balance_months_median: float  # 현재 잔액 = 월 지출 x 이 값
    balance_sigma: float
    emergency_months_median: float  # 비상자금 = 월 지출 x 이 값
    emergency_sigma: float
    emergency_zero_prob: float  # 비상자금이 아예 없는 사람의 비율
    card_payment_share_range: tuple[float, float]  # 카드 결제 예정액 / 월 지출
    price_median: float  # 사려는 물건 가격
    price_sigma: float


PERSONAS: tuple[Persona, ...] = (
    Persona("사회초년생", 0.25, 1_100_000, 0.45, 0.8, 0.9, 0.5, 1.0, 0.25, (0.15, 0.55), 70_000, 0.9),
    Persona("20대후반_직장인", 0.35, 1_500_000, 0.40, 1.0, 0.8, 1.2, 0.9, 0.15, (0.20, 0.60), 100_000, 0.9),
    Persona("30대초반", 0.25, 2_100_000, 0.40, 1.1, 0.8, 2.0, 0.8, 0.10, (0.20, 0.65), 130_000, 0.9),
    Persona("30대후반_가구", 0.15, 2_800_000, 0.40, 1.3, 0.8, 2.8, 0.8, 0.08, (0.20, 0.70), 160_000, 0.9),
)

PERSONA_NAMES: tuple[str, ...] = tuple(p.name for p in PERSONAS)

_PRICE_BOUNDS = (10_000.0, 3_000_000.0)


def _persona_mix(weights: Mapping[str, float] | None) -> list[tuple[Persona, float]]:
    if weights is None:
        raw = [(p, p.weight) for p in PERSONAS]
    else:
        unknown = sorted(set(weights) - set(PERSONA_NAMES))
        if unknown:
            raise ValueError(f"unknown persona names: {unknown}; choose from {list(PERSONA_NAMES)}")
        raw = [(p, float(weights.get(p.name, 0.0))) for p in PERSONAS]
    total = sum(w for _, w in raw)
    if total <= 0:
        raise ValueError("persona weights must sum to a positive number")
    return [(p, w / total) for p, w in raw if w > 0]


def generate_persona_rows(
    *,
    row_count: int,
    seed: int,
    weights: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    """유형별 합성 행. 같은 (row_count, seed, weights) 는 항상 같은 결과다.

    각 행은 원본 7개 + 파생 3개 + 라벨 + 'persona'(유형 이름)를 가진다.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    mix = _persona_mix(weights)
    personas = [p for p, _ in mix]
    probabilities = [w for _, w in mix]

    rows: list[dict[str, Any]] = []
    for _ in range(max(row_count, 1)):
        persona = personas[int(rng.choice(len(personas), p=probabilities))]

        # 공통 요인 하나 + 항목별 잡음. 월 지출/잔액/비상금이 함께 움직인다.
        affluence = float(rng.standard_normal())

        def latent() -> float:
            noise = float(rng.standard_normal())
            return _AFFLUENCE_WEIGHT * affluence + (1.0 - _AFFLUENCE_WEIGHT**2) ** 0.5 * noise

        monthly = float(persona.monthly_spending_median * np.exp(persona.monthly_spending_sigma * latent()))
        balance = float(monthly * persona.balance_months_median * np.exp(persona.balance_sigma * latent()))
        has_emergency = float(rng.random()) >= persona.emergency_zero_prob
        emergency = (
            float(monthly * persona.emergency_months_median * np.exp(persona.emergency_sigma * latent()))
            if has_emergency
            else 0.0
        )
        savebox = float(emergency * np.exp(0.35 * float(rng.standard_normal())))
        low, high = persona.card_payment_share_range
        card_payment = float(monthly * rng.uniform(low, high))
        days = float(int(rng.integers(1, 31)))
        price = float(persona.price_median * np.exp(persona.price_sigma * float(rng.standard_normal())))
        price = min(max(price, _PRICE_BOUNDS[0]), _PRICE_BOUNDS[1])

        row: dict[str, Any] = {
            "current_balance": balance,
            "emergency_fund_balance": emergency,
            "savebox_balance": savebox,
            "expected_card_payment_amount": card_payment,
            "days_until_card_due": days,
            "monthly_spending_30d": monthly,
            "product_price": price,
        }
        row.update(derive_model_features(row))
        row[TARGET_NAME] = rule_bucket(row)
        row["persona"] = persona.name
        rows.append(row)
    return rows


# 학습 데이터 분포.
#   uniform : 옛 방식(입력이 서로 무관한 균등분포). 현실에 없는 사람이 많이 섞인다.
#   persona : 20~30대 유형별 분포. 유형 분포로만 학습하면 그 밖의 사람에게 크게 틀린다
#             (균등 테스트 macro-F1 0.962 -> 0.897).
#   mixed   : 둘을 절반씩. 유형 분포에서 0.948 -> 0.967 로 오르고 균등 분포에서는
#             0.962 -> 0.956 으로 조금만 내려가서 운영 학습 기본값으로 쓴다.
TRAIN_POPULATIONS: tuple[str, ...] = ("uniform", "persona", "mixed")
DEFAULT_TRAIN_POPULATION = "mixed"


def generate_training_rows(population: str, *, row_count: int, seed: int) -> list[dict[str, Any]]:
    if population == "uniform":
        return generate_rows(row_count=row_count, seed=seed)
    if population == "persona":
        return generate_persona_rows(row_count=row_count, seed=seed)
    if population == "mixed":
        half = row_count // 2
        return generate_rows(row_count=half, seed=seed) + generate_persona_rows(
            row_count=row_count - half, seed=seed + 10_000
        )
    raise ValueError(f"unknown population {population!r}; choose from {list(TRAIN_POPULATIONS)}")
