from __future__ import annotations

import os
import io
import logging
from pathlib import Path
from dotenv import load_dotenv

def _find_env_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parent.parent.parent / ".env"


env_path = _find_env_path()
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

        # 1. 공식 문서 패턴의 호출 방식 (convert 메서드 사용)
        # 여기서 voice_id는 본인이 디자인한 ID로 교체하세요.
        audio_gen = client.text_to_speech.convert(
            text=text,
            voice_id="7N2OPp0g9JRF3evrzZMW", 
            model_id="eleven_multilingual_v2", # 한국어 설정
            output_format="mp3_44100_128",
        )

        # 2. 전송받은 제너레이터 데이터를 바이트로 병합
        # play(audio) 대신 서버 응답을 위해 메모리 버퍼에 저장합니다.
        buffer = io.BytesIO()
        for chunk in audio_gen:
            if chunk:
                buffer.write(chunk)
        
        return buffer.getvalue()

    except Exception as e:
        logging.error(f"ElevenLabs API 실행 오류: {e}")
        return None
