from __future__ import annotations

import json
from typing import Any

from consumption_poc.config import DEFAULT_GEMINI_MODEL, get_env


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)


def _llm_prompt(report_payload: dict) -> str:
    compact = json.dumps(report_payload, ensure_ascii=False, indent=2)
    return f"""
다음 소비리포트 데이터를 바탕으로 JSON만 반환하세요.
키는 반드시 consumption_patterns, anomaly_explanations, actionable_solutions 세 개만 사용하세요.
각 값은 한국어 문자열 배열이어야 합니다.
추가 설명 없이 JSON만 출력하세요.

데이터:
{compact}
""".strip()


def generate_ai_analysis(
    report_payload: dict,
    fallback_analysis: dict[str, list[str]],
    include_ai: bool = True,
) -> tuple[dict[str, list[str]], str]:
    if not include_ai:
        return fallback_analysis, "skipped"

    api_key = get_env("GEMINI_API_KEY")
    model_name = get_env("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    if not api_key:
        return fallback_analysis, "degraded"

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=_llm_prompt(report_payload),
        )
        text = getattr(response, "text", "") or ""
        parsed = _extract_json(text)
        ai_analysis = {
            "consumption_patterns": parsed.get("consumption_patterns", []),
            "anomaly_explanations": parsed.get("anomaly_explanations", []),
            "actionable_solutions": parsed.get("actionable_solutions", []),
        }
        if not all(isinstance(value, list) for value in ai_analysis.values()):
            return fallback_analysis, "degraded"
        return ai_analysis, "ok"
    except Exception:
        return fallback_analysis, "degraded"
