from __future__ import annotations

import os
import io
import logging
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def generate_tts_audio(text: str) -> bytes | None:
    """
    ElevenLabs 공식 SDK 패턴을 적용하여 텍스트를 음성 바이트로 변환합니다.
    """
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        logging.error(f"API Key 로드 실패. 경로 확인: {env_path}")
        return None

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        audio_gen = client.text_to_speech.convert(
            text=text,
            voice_id="7N2OPp0g9JRF3evrzZMW",
            model_id="eleven_multilingual_v2", # 한국어 설정
            output_format="mp3_44100_128",
        )

        buffer = io.BytesIO()
        for chunk in audio_gen:
            if chunk:
                buffer.write(chunk)

        return buffer.getvalue()

    except Exception as e:
        logging.error(f"ElevenLabs API 실행 오류: {e}")
        return None