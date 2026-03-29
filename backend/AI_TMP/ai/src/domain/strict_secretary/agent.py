from __future__ import annotations

import importlib
import json

from config import get_env, DEFAULT_GEMINI_MODEL
from domain.consumption.ai_insights import _model_candidates, _extract_json
from domain.strict_secretary.models import SecretaryResponse


def _to_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "승인", "approve", "approved"}:
            return True
        if lowered in {"false", "0", "no", "n", "기각", "reject", "rejected"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def _reconcile_approval(approval: bool, comment: str, reasoning: list[str]) -> bool:
    text = f"{comment}\n" + "\n".join(reasoning)

    approve_keywords = ["승인", "구매해", "사도", "합당", "무리 없는", "감당 가능", "필수품"]
    reject_keywords = ["기각", "반려", "사지 마", "무리", "과소비", "감당 불가", "불필요"]

    approve_hit = any(keyword in text for keyword in approve_keywords)
    reject_hit = any(keyword in text for keyword in reject_keywords)

    if approve_hit and not reject_hit:
        return True
    if reject_hit and not approve_hit:
        return False
    return approval


class StrictSecretaryAgent:
    def __init__(self):
        self.api_key = get_env("GEMINI_API_KEY")
        self.model_name = get_env("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self.client = None
        if self.api_key:
            try:
                genai_module = importlib.import_module("google.genai")
                client_factory = getattr(genai_module, "Client", None)
                if client_factory is not None:
                    self.client = client_factory(api_key=self.api_key)
            except Exception:
                self.client = None

    def evaluate_purchase(
        self,
        item_text: str,
        item_link: str,
        user_reason: str,
        page_content: str,
        profile: dict,
        recent_txs: list[dict],
        explain_logs: list[dict],
        ai_report: dict | None,
    ) -> SecretaryResponse:
        """
        Evaluates whether a purchase is justified using the LLM with a strict but friendly persona.
        Returns a SecretaryResponse object.
        """
        if not self.client:
            return SecretaryResponse(
                is_approved=False,
                fact_violence_comment="API Key가 없어서 팩트폭력도 못 해드리겠네요.",
                reasoning=["API Key 누락"],
            )

        context_data = {
            "profile": profile,
            "recent_transactions_summary": recent_txs,  # simplified list
            "past_excuses": explain_logs,
            "latest_ai_report": ai_report,
        }

        context_str = json.dumps(context_data, ensure_ascii=False, indent=2)

        prompt = f"""
You are a "Strict but Friendly AI Secretary/Friend" (깐깐하지만 밉지 않은, 친한 비서/친구).
You must address the user in friendly, informal Korean ("반말", like chatting with a close friend).
Be brutally honest, witty, and somewhat sarcastic but ultimately caring about their finances.

The user wants to buy something. You have:
1. The item name & link.
2. The scraped webpage text from the link (try to find the EXACT price from this text).
3. The user's reason/excuse for buying it.
4. Their financial data, recent spending, past excuses, and AI report.

Your job:
1. Examine the scraped text to figure out the estimated price.
2. Evaluate if they can afford this and if their excuse makes sense.
3. If it's a terrible idea (no money, bad excuse), reject it ("승인 반려") with brutal facts (팩트폭력).
4. If it's justified, approve it ("승인") but still nag them a bit.

Return ONLY strict JSON with the following structure:
{{
  "is_approved": true or false,
  "fact_violence_comment": "Your brutally honest, funny, informal response (반말) to the user. MUST be EXACTLY 3 sentences.",
  "reasoning": ["반말 이유 1 (e.g., 너 이번 달에 벌써 100만원 썼어)", "반말 이유 2", "..."]
}}

-- USER'S PURCHASE REQUEST --
* Item: {item_text}
* Item Link: {item_link}
* User's Excuse: {user_reason}

-- SCRAPED WEBPAGE TEXT (Find the price here) --
{page_content}

-- USER'S FINANCIAL CONTEXT --
{context_str}
""".strip()

        for candidate in _model_candidates(self.model_name):
            try:
                response = self.client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                )
                text = getattr(response, "text", "") or ""
                parsed = _extract_json(text)

                if (
                    "is_approved" in parsed
                    and "fact_violence_comment" in parsed
                    and "reasoning" in parsed
                ):
                    normalized = _to_bool(parsed.get("is_approved"))
                    if normalized is None:
                        continue

                    comment = str(parsed["fact_violence_comment"])
                    reasoning = [str(item) for item in list(parsed["reasoning"])]
                    final_approval = _reconcile_approval(normalized, comment, reasoning)

                    return SecretaryResponse(
                        is_approved=final_approval,
                        fact_violence_comment=comment,
                        reasoning=reasoning,
                    )
            except Exception as e:
                import logging

                logging.warning(
                    f"Error evaluating purchase with model {{candidate}}: {{e}}"
                )
                continue

        return SecretaryResponse(
            is_approved=False,
            fact_violence_comment="답변을 생성하는 중에 문제가 생겼어요. 일단 사지 마세요.",
            reasoning=["AI 오류 발생"],
        )
