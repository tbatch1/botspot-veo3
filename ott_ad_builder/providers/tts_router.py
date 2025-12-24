from __future__ import annotations

from dataclasses import dataclass

from .base import AudioProvider
from .openai_tts import OpenAITTSProvider
from .sapi_tts import SapiTTSProvider


@dataclass(frozen=True)
class RoutedVoice:
    provider: str
    voice: str


def parse_voice_id(voice_id: str | None) -> RoutedVoice:
    raw = str(voice_id or "").strip()
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        p = prefix.strip().lower()
        v = rest.strip()
        if p in ("sapi", "openai", "eleven", "11l", "elevenlabs"):
            return RoutedVoice(provider=p, voice=v)
    return RoutedVoice(provider="eleven", voice=raw)


class TTSRouterProvider(AudioProvider):
    """
    Routes `generate_speech()` by voice_id prefix:
      - `sapi:<Name>`      -> SapiTTSProvider
      - `openai:<voice>`   -> OpenAITTSProvider
      - `eleven:<id>` or bare `<id>` -> ElevenLabsProvider (passed in)
    """

    def __init__(self, *, eleven: AudioProvider | None):
        self._eleven = eleven
        self._sapi = None
        self._openai = None

    def _get_sapi(self) -> SapiTTSProvider:
        if self._sapi is None:
            self._sapi = SapiTTSProvider()
        return self._sapi

    def _get_openai(self) -> OpenAITTSProvider:
        if self._openai is None:
            self._openai = OpenAITTSProvider()
        return self._openai

    def generate_speech(self, text: str, voice_id: str, *args, **kwargs) -> str:
        routed = parse_voice_id(voice_id)
        if routed.provider == "sapi":
            return self._get_sapi().generate_speech(text, f"sapi:{routed.voice}", *args, **kwargs)
        if routed.provider == "openai":
            return self._get_openai().generate_speech(text, f"openai:{routed.voice}", *args, **kwargs)

        if routed.provider in ("eleven", "11l", "elevenlabs"):
            if not self._eleven:
                raise RuntimeError("ElevenLabs provider not configured")
            # Use the raw voice id (no prefix) for ElevenLabs calls.
            return self._eleven.generate_speech(text, routed.voice, *args, **kwargs)

        if not self._eleven:
            raise RuntimeError("No default TTS provider configured")
        return self._eleven.generate_speech(text, voice_id, *args, **kwargs)

    def generate_sfx(self, text: str, duration: int = 5) -> str:
        # SFX stays ElevenLabs-only for now.
        if hasattr(self._eleven, "generate_sfx") and self._eleven:
            return self._eleven.generate_sfx(text, duration=duration)  # type: ignore[attr-defined]
        return ""
