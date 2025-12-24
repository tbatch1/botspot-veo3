from __future__ import annotations

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
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2026", "...")
        .replace("\u00a0", " ")
    )
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class OpenAITTSProvider(AudioProvider):
    """
    OpenAI TTS via `client.audio.speech.create`.
    Pros: more natural ("human") voice than most free TTS.
    Cons: requires OpenAI key; paid usage.
    """

    def __init__(self):
        from openai import OpenAI

        self._client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_speech(self, text: str, voice_id: str, *args, file_prefix: str = "vo", **kwargs) -> str:
        voice = str(voice_id or "").strip()
        if voice.lower().startswith("openai:"):
            voice = voice.split(":", 1)[1].strip()
        if not voice:
            voice = (os.getenv("DEFAULT_OPENAI_VOICE") or "verse").strip()

        text = _sanitize_tts_text(text)
        if not text:
            raise ValueError("Empty TTS text")

        # Tunables
        speed_raw = (os.getenv("OPENAI_TTS_SPEED") or "").strip()
        try:
            speed = float(speed_raw) if speed_raw else 1.0
        except Exception:
            speed = 1.0
        speed = max(0.5, min(speed, 1.25))

        model_pref = (os.getenv("OPENAI_TTS_MODEL") or "gpt-4o-mini-tts").strip()
        model_fallback = (os.getenv("OPENAI_TTS_MODEL_FALLBACK") or "tts-1").strip()

        fmt = (os.getenv("OPENAI_TTS_FORMAT") or "wav").strip().lower()
        if fmt not in ("wav", "flac", "mp3", "aac", "opus"):
            fmt = "wav"

        instructions = (os.getenv("OPENAI_TTS_INSTRUCTIONS") or "").strip()
        if not instructions:
            instructions = (
                "Sound like a real human narrator. Natural cadence, subtle emotion, no robotic delivery. "
                "Avoid over-enunciation; keep it conversational and confident."
            )

        cache_key = f"{model_pref}|{model_fallback}|{voice}|{speed:.2f}|{fmt}|{instructions}|{text}"
        prefix = re.sub(r"[^a-zA-Z0-9_\\-]", "", str(file_prefix or "vo")) or "vo"
        filename = f"{prefix}_openai_{hashlib.md5(cache_key.encode('utf-8', errors='ignore')).hexdigest()}.{fmt}"
        filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            return filepath

        def _synthesize(model_name: str):
            return self._client.audio.speech.create(
                model=model_name,
                voice=voice,
                input=text,
                instructions=instructions,
                response_format=fmt,
                speed=speed,
            )

        try:
            audio = _synthesize(model_pref)
        except Exception:
            audio = _synthesize(model_fallback)

        if hasattr(audio, "write_to_file"):
            audio.write_to_file(filepath)  # type: ignore[attr-defined]
        else:
            # Very defensive fallback.
            content = getattr(audio, "content", None)
            if content:
                with open(filepath, "wb") as f:
                    f.write(content)
            else:
                data = audio.read()  # type: ignore[attr-defined]
                with open(filepath, "wb") as f:
                    f.write(data)

        return filepath

    def generate_sfx(self, text: str, duration: int = 5) -> str:
        return ""
