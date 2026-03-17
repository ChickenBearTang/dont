from __future__ import annotations

import os
import io
from consumption_poc.config import get_env

def generate_tts_audio(text: str) -> bytes | None:
    """
    ElevenLabs TTS로 텍스트를 음성으로 변환합니다.
    ELEVEN_API_KEY가 없으면 None을 반환합니다.
    """
    api_key = get_env("ELEVEN_API_KEY")
    if not api_key:
        return None

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        # 사용자가 지정한 Voice ID
        VOICE_ID = "TRO4gatqxbbwLXHLDLSk"

        audio_gen = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2",  # 한국어는 v2 필수
        )

        # generator → bytes 변환
        buffer = io.BytesIO()
        for chunk in audio_gen:
            if chunk:
                buffer.write(chunk)
        return buffer.getvalue()

    except Exception as e:
        import logging
        logging.warning(f"TTS 생성 실패: {e}")
        return None