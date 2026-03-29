from __future__ import annotations

import io
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

_resolved_file = Path(__file__).resolve()
_env_candidates: list[Path] = []
for parent in _resolved_file.parents:
    candidate = parent / ".env"
    if candidate.exists():
        _env_candidates.append(candidate)

for env_file in reversed(_env_candidates):
    load_dotenv(dotenv_path=env_file, override=False)


def generate_tts_audio(text: str) -> bytes | None:
    """
    ElevenLabs SDK를 사용해 텍스트를 MP3 바이트로 변환한다.
    """
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        logging.error(
            "API Key 로드 실패. 탐색 경로: %s",
            ", ".join(str(path) for path in _env_candidates) if _env_candidates else "(없음)",
        )
        return None

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)
        audio_gen = client.text_to_speech.convert(
            text=text,
            voice_id="7N2OPp0g9JRF3evrzZMW",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        buffer = io.BytesIO()
        for chunk in audio_gen:
            if chunk:
                buffer.write(chunk)

        return buffer.getvalue()
    except Exception as exc:
        logging.error("ElevenLabs API 실행 오류: %s", exc)
        return None
