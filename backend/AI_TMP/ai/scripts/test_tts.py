import sys
sys.path.insert(0, "src")
from consumption_poc.config import get_env
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=get_env("ELEVEN_API_KEY"))

try:
    audio = client.text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        text="hi",
        model_id="eleven_multilingual_v2",
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR TYPE: {type(e).__name__}")
    print(f"ERROR MSG: {e}")
