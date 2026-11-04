"""반사실 제안을 사람이 읽을 문장으로 다듬는다.

원칙: 문장을 다듬을 뿐 제안의 사실(금액, 판단 변화)은 바꾸지 않는다.
  - 금액은 한국어로 읽기 쉽게 (1,110,000원 -> 111만 원). 반올림되면 '약'을 붙인다.
  - 지금 판단에서 어디로 바뀌는지를 말한다.
  - 월 지출/원래 가격에 비해 얼마나 큰 변화인지 감을 준다.
  - 목표를 이뤄도 남는 걸림돌(카드 결제일 임박)을 숨기지 않는다.
  - 확인되지 않은 제안(validated 가 아님)은 원문 그대로 둔다.
템플릿 기반이라 같은 입력은 항상 같은 문장이고 테스트할 수 있다. LLM 을 쓰지 않으므로
온프레미스에서도 그대로 동작한다.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

DECISION_LABEL_KO: dict[str, str] = {
    "BUY_NOW": "바로 구매",
    "WAIT": "관망",
    "REVIEW": "추가 검토",
    "NOT_RECOMMENDED": "구매 비추천",
}

_DUE_SOON_DAYS = 8  # 규칙 엔진이 결제일 임박으로 보는 기준(days/30 < 0.25)과 같은 범위
_HEAVY_RATIO = 2.0  # 월 지출의 2배를 넘으면 단기간 마련이 어렵다고 말한다


def friendly_won(amount: float) -> str:
    """원화 금액을 읽기 쉬운 한국어로. 반올림되면 '약 '을 붙인다."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return "0원"
    if not math.isfinite(value) or value <= 0:
        return "0원"

    original = int(round(value))
    unit = 10_000 if original >= 100_000 else 1_000 if original >= 10_000 else 100 if original >= 1_000 else 1
    rounded = int(round(original / unit)) * unit
    prefix = "약 " if rounded != original else ""

    if rounded < 1_000:
        return f"{prefix}{rounded:,}원"

    eok, rest = divmod(rounded, 100_000_000)
    man, rest = divmod(rest, 10_000)
    cheon, rest = divmod(rest, 1_000)
    baek = rest // 100
    parts: list[str] = []
    if eok:
        parts.append(f"{eok:,}억")
    if man:
        parts.append(f"{man:,}만")
    if cheon:
        parts.append(f"{cheon}천")
    if baek:
        parts.append(f"{baek}백")
    return f"{prefix}{' '.join(parts)} 원"


_SUBJECT = {
    # 변수 -> (이름+목적격 조사 포함 동사구 앞부분)
    "emergency_fund_balance": "비상자금을",
    "savebox_balance": "세이브박스 잔액을",
    "current_balance": "계좌 잔액을",
}


def _label(decision: str) -> str:
    return DECISION_LABEL_KO.get(decision, decision)


def render_counterfactual(
    suggestion: Mapping[str, Any],
    *,
    current_decision: str,
    monthly_spending: float,
    days_until_card_due: int | float,
    price: float,
) -> str:
    variable = str(suggestion.get("variable", ""))
    delta = max(float(suggestion.get("suggested_change") or 0), 0.0)
    threshold = float(suggestion.get("threshold") or 0)
    target = str(suggestion.get("target_decision", ""))
    monthly = max(float(monthly_spending or 0), 0.0)

    move = f"구매 판단이 '{_label(current_decision)}'에서 '{_label(target)}'{_josa_ro(_label(target))}"

    if delta <= 0:
        return f"지금 조건에서 {move} 나아질 수 있습니다." if target else "지금 조건을 다시 확인해 보세요."

    scale = ""
    if variable == "product_price":
        head = f"가격이 {friendly_won(delta)} 내려 {friendly_won(threshold)} 이하가 되면"
        if price > 0:
            scale = f"이는 현재 가격의 약 {round(delta / price * 100)}% 할인에 해당합니다."
    elif variable in _SUBJECT:
        head = f"{_SUBJECT[variable]} {friendly_won(delta)} 더 늘려 {friendly_won(threshold)}이 되면"
        if monthly > 0:
            scale = f"이는 월 지출의 약 {round(delta / monthly * 100)}%에 해당하는 금액입니다."
    else:
        head = f"{friendly_won(delta)}만큼 조건이 나아지면"

    sentence = f"{head} {move} 나아집니다."

    extras: list[str] = [scale] if scale else []
    if variable != "product_price" and monthly > 0 and delta > monthly * _HEAVY_RATIO:
        extras.append("목표 금액이 커서 단기간에 마련하기는 어려울 수 있습니다.")
    if target == "WAIT":
        due = float(days_until_card_due) if days_until_card_due is not None else 99
        if due < _DUE_SOON_DAYS:
            extras.append(f"다만 카드 결제일이 {int(due)}일 남아 있어, 결제가 끝난 뒤 다시 확인하는 것이 좋습니다.")
        else:
            extras.append("여유가 더 생기면 다시 확인해 보세요.")
    elif target == "REVIEW":
        extras.append("구매 전에 한 번 더 확인해 보세요.")
    return " ".join([sentence, *extras])


def _josa_ro(word: str) -> str:
    """'로' / '으로' 선택. 받침이 있으면(ㄹ 받침 제외) '으로'."""
    if not word:
        return "(으)로"
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return "(으)로"
    jong = (ord(last) - 0xAC00) % 28
    return "로" if jong in (0, 8) else "으로"


def polish_counterfactuals(
    suggestions: Sequence[Mapping[str, Any]],
    *,
    current_decision: str,
    monthly_spending: float,
    days_until_card_due: int | float,
    price: float,
) -> list[dict[str, Any]]:
    """message 만 다듬은 복사본을 돌려준다. 확인되지 않은 제안은 그대로 둔다."""
    out: list[dict[str, Any]] = []
    for suggestion in suggestions:
        item = dict(suggestion)
        if item.get("validated") is True:
            item["message"] = render_counterfactual(
                item,
                current_decision=current_decision,
                monthly_spending=monthly_spending,
                days_until_card_due=days_until_card_due,
                price=price,
            )
        out.append(item)
    return out
