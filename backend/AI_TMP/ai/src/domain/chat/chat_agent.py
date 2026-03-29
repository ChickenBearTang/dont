from __future__ import annotations

import importlib
import json
from typing import Any

from config import get_env, DEFAULT_GEMINI_MODEL
from domain.consumption.ai_insights import _model_candidates, _extract_json


class ChatAgent:
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

    def evaluate_justification(
        self, message: str, context: dict, history: list[dict[str, str]]
    ) -> dict[str, Any]:
        """
        Evaluates a user's justification for their spending using the LLM.
        Returns a dictionary with 'is_valid' (bool) and 'response' (str).
        """
        if not self.client:
            return {
                "is_valid": False,
                "response": "앗, 지금은 AI 연결이 원활하지 않아 변명을 들어드릴 수 없어요! (API Key 설정 필요)",
            }

        compact_context = json.dumps(context, ensure_ascii=False, indent=2)
        history_str = json.dumps(history, ensure_ascii=False, indent=2)

        prompt = f"""
You are a friendly, witty, but objective financial advisor chatbot.
The user is providing an excuse or justification for their recent spending patterns, particularly large expenses or anomalies.

Your job is to read their message and their financial context, and decide if their spending is justified (e.g., waiting for reimbursement from friends, long-term investment, reasonable necessary expense).
If it is a valid excuse, set `is_valid: true` and write an empathetic response.
If it is just a clear overspending excuse or not valid, set `is_valid: false` and write a short, witty, somewhat stern (but warm) advice.

Return ONLY strict JSON with the following structure:
{{
  "is_valid": true or false,
  "response": "Your message to the user in Korean"
}}

User's Financial Context for the month:
{compact_context}

Previous Conversation History:
{history_str}

User's Latest Message:
"{message}"
""".strip()

        for candidate in _model_candidates(self.model_name):
            try:
                response = self.client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                )
                text = getattr(response, "text", "") or ""
                parsed = _extract_json(text)

                if "is_valid" in parsed and "response" in parsed:
                    return {
                        "is_valid": bool(parsed["is_valid"]),
                        "response": str(parsed["response"]),
                    }
            except Exception as e:
                import logging

                logging.warning(
                    "Error evaluating justification with model %s: %s", candidate, e
                )
                continue

        return {
            "is_valid": False,
            "response": "죄송해요, 변명을 분석하는 중에 문제가 발생했어요. 다시 한 번 말씀해 주시겠어요?",
        }
