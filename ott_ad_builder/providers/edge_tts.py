import asyncio
import hashlib
import os
import re
import unicodedata

from ..config import config
from .base import AudioProvider


def _sanitize_tts_text(value: str) -> str:
    s = unicodedata.normalize("NFKC", value or "")
    s = (
        s.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", "\"")
        .replace("\u201d", "\"")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2026", "...")
        .replace("\u00a0", " ")
    )
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _run_coro(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # If we're in an async context, require callers to run this in a thread.
    raise RuntimeError("EdgeTTSProvider.generate_speech must run off the event loop (use a thread).")


class EdgeTTSProvider(AudioProvider):
    """
    Microsoft Edge TTS (edge-tts).
    Pros: huge free voice catalog across locales/accents, decent quality.
    Cons: network-dependent, no SFX/BGM.
    """

    def __init__(self):
        try:
            import edge_tts  # noqa: F401
        except Exception as e:
            raise RuntimeError(f"edge-tts not installed: {e}")

    def generate_speech(self, text: str, voice_id: str, *args, file_prefix: str = "vo", **kwargs) -> str:
        import edge_tts

        voice = str(voice_id or "").strip()
        if voice.lower().startswith("edge:"):
            voice = voice.split(":", 1)[1].strip()
        if not voice:
            raise ValueError("Missing Edge voice name")

        text = _sanitize_tts_text(text)
        if not text:
            raise ValueError("Empty TTS text")

        # Optional tuning (SSML-ish parameters supported by edge-tts).
        rate = str(os.getenv("EDGE_TTS_RATE") or "+0%").strip()
        volume = str(os.getenv("EDGE_TTS_VOLUME") or "+0%").strip()
        pitch = str(os.getenv("EDGE_TTS_PITCH") or "+0Hz").strip()

        cache_key = f"{voice}:{rate}:{volume}:{pitch}:{text}"
        prefix = re.sub(r"[^a-zA-Z0-9_\-]", "", str(file_prefix or "vo")) or "vo"
        filename = f"{prefix}_edge_{hashlib.md5(cache_key.encode()).hexdigest()}.mp3"
        filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            return filepath

        async def _gen():
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume, pitch=pitch)
            await communicate.save(filepath)

        _run_coro(_gen())
        return filepath

    def generate_sfx(self, text: str, duration: int = 5) -> str:
        return ""

