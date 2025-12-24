import hashlib
import json
import os
import re
import subprocess
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


def list_sapi_voices() -> list[dict]:
    script = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $s.GetInstalledVoices() | ForEach-Object {
  [PSCustomObject]@{
    name = $_.VoiceInfo.Name
    gender = $_.VoiceInfo.Gender.ToString()
    locale = $_.VoiceInfo.Culture.Name
  }
}
$voices | ConvertTo-Json
"""
    raw = subprocess.check_output(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [v for v in parsed if isinstance(v, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except Exception:
        return []
    return []


class SapiTTSProvider(AudioProvider):
    """
    Windows System.Speech (SAPI) TTS.
    Pros: offline, reliable.
    Cons: limited voice variety unless extra voice packs installed.
    """

    def generate_speech(self, text: str, voice_id: str, *args, file_prefix: str = "vo", **kwargs) -> str:
        voice = str(voice_id or "").strip()
        if voice.lower().startswith("sapi:"):
            voice = voice.split(":", 1)[1].strip()
        if not voice:
            raise ValueError("Missing SAPI voice name")

        text = _sanitize_tts_text(text)
        if not text:
            raise ValueError("Empty TTS text")

        rate = int(float(os.getenv("SAPI_TTS_RATE") or "2"))
        cache_key = f"{voice}:{rate}:{text}"
        prefix = re.sub(r"[^a-zA-Z0-9_\-]", "", str(file_prefix or "vo")) or "vo"
        filename = f"{prefix}_sapi_{hashlib.md5(cache_key.encode()).hexdigest()}.wav"
        filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            return filepath

        ps = rf"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('{voice}')
$synth.Rate = {rate}
$synth.Volume = 100
$synth.SetOutputToWaveFile('{filepath}')
$synth.Speak(@'
{text}
'@)
$synth.Dispose()
"""
        subprocess.check_call(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps])
        return filepath

    def generate_sfx(self, text: str, duration: int = 5) -> str:
        return ""

