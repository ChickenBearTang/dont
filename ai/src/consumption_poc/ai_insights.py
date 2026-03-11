from __future__ import annotations

import json
from typing import Any

from consumption_poc.config import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_MODEL_FALLBACKS,
    get_env,
)


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
You are a banking financial analyst. Return only JSON with:
- consumption_patterns (list of short Korean sentences)
- anomaly_explanations (list of short Korean sentences)
- actionable_solutions (list of short Korean sentences)
Return strict JSON, no markdown.

IMPORTANT INSTRUCTION:
The provided data may include a 'justifications' list (reasons the user provided via chatbot for specific spending or anomalies).
If 'justifications' are present, you MUST incorporate this context into your analysis.
For example, if they explain a large expense is a long-term investment, or they paid for friends and will be reimbursed, do not scold them for it in 'anomaly_explanations' or 'actionable_solutions', but rather acknowledge it as a positive or expected factor. Re-evaluate their spending based on their given context!

Data:
{compact}
""".strip()


def _model_candidates(raw_model: str | None) -> list[str]:
    configured = []
    if raw_model:
        configured = [m.strip() for m in raw_model.split(",") if m.strip()]

    candidates: list[str] = []
    seen: set[str] = set()

    def add_model(name: str) -> None:
        if not name or name in seen:
            return
        seen.add(name)
        candidates.append(name)

    for name in configured or [DEFAULT_GEMINI_MODEL]:
        add_model(name)
        if not name.startswith("models/"):
            add_model(f"models/{name}")
        else:
            add_model(name.removeprefix("models/"))

    for fallback in DEFAULT_GEMINI_MODEL_FALLBACKS:
        add_model(fallback)
        if not fallback.startswith("models/"):
            add_model(f"models/{fallback}")
        else:
            add_model(fallback.removeprefix("models/"))

    return candidates


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
    except Exception:
        return fallback_analysis, "degraded"

    client = genai.Client(api_key=api_key)
    prompt = _llm_prompt(report_payload)

    for candidate in _model_candidates(model_name):
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=prompt,
            )
            text = getattr(response, "text", "") or ""
            parsed = _extract_json(text)
            ai_analysis = {
                "consumption_patterns": parsed.get("consumption_patterns", []),
                "anomaly_explanations": parsed.get("anomaly_explanations", []),
                "actionable_solutions": parsed.get("actionable_solutions", []),
            }
            if not all(isinstance(value, list) for value in ai_analysis.values()):
                continue
            return ai_analysis, "ok"
        except Exception:
            continue

    return fallback_analysis, "degraded"
