import os
import hashlib
import re
import unicodedata
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from elevenlabs.types import VoiceSettings
from ..config import config
from .base import AudioProvider

class ElevenLabsProvider(AudioProvider):
    """ElevenLabs implementation for Audio."""
    
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.client = None
        if self.api_key and self.api_key != "dummy_key_for_test":
            try:
                self.client = ElevenLabs(api_key=self.api_key)
            except Exception as e:
                print(f"[WARN] ElevenLabs client init failed: {e}")

    def generate_speech(
        self,
        text: str,
        voice_id: str | None = None,
        delivery_style: str = None,
        *,
        file_prefix: str = "vo",
    ) -> str:
        """
        Generates TTS with optional delivery style.
        
        ElevenLabs v3 Audio Tags are embedded directly in text:
        - [whispers], [excited], [sad], [pause: 0.5s], [sighs], [laughs]
        
        delivery_style affects voice settings:
        - "gravitas": slower, deeper, more measured
        - "energetic": faster, higher energy
        - "intimate": softer, closer feel
        - "confident": strong, assured delivery
        
        Default voice: 'Adam' (pNInz6obpgDQGcFmaJgB) - Standard American Male
        """
        if not self.client:
            raise Exception("ElevenLabs API key not configured.")

        def _sanitize_tts_text(value: str) -> str:
            """
            Make VO text stable across TTS engines and Windows encodings.
            Avoid smart quotes/em-dashes that can produce odd pronunciations.
            """
            s = unicodedata.normalize("NFKC", value or "")
            replacements = {
                "“": "\"",
                "”": "\"",
                "„": "\"",
                "’": "'",
                "‘": "'",
                "—": ". ",
                "–": "-",
                "…": "...",
                "\u00a0": " ",  # non-breaking space
            }
            for src, dst in replacements.items():
                s = s.replace(src, dst)

            # Normalize common “smart punctuation” to ASCII so TTS doesn't lose characters.
            s = (
                s.replace("\u2019", "'")
                .replace("\u2018", "'")
                .replace("\u201c", "\"")
                .replace("\u201d", "\"")
                .replace("\u2014", "-")
                .replace("\u2013", "-")
                .replace("\u2026", "...")
            )

            # Strip control chars, collapse whitespace.
            s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)

            # Drop any remaining non-ASCII characters to avoid Windows mojibake
            # and weird TTS pronunciations (common when a file was mis-decoded once).
            s = s.encode("ascii", "ignore").decode("ascii")

            s = re.sub(r"\s+", " ", s).strip()
            return s

        text = _sanitize_tts_text(text)

        def _env_float(key: str) -> float | None:
            value = os.getenv(key)
            if value is None:
                return None
            value = value.strip()
            if not value:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        def _env_bool(key: str) -> bool | None:
            value = os.getenv(key)
            if value is None:
                return None
            value = value.strip().lower()
            if value in ("1", "true", "yes", "on"):
                return True
            if value in ("0", "false", "no", "off"):
                return False
            return None

        # Allow demo-day tuning via env vars (no code changes required).
        # Recommended for "less AI-sounding" voice: use a higher-quality model + broadcaster voice.
        resolved_voice_id = (voice_id or os.getenv("ELEVENLABS_VOICE_ID") or "onwK4e9ZLuTAKqWW03F9").strip()
        resolved_model_id = (os.getenv("ELEVENLABS_MODEL") or config.ELEVENLABS_MODEL).strip()
        # NOTE: Higher bitrate formats (e.g. mp3_44100_192) require higher ElevenLabs tiers.
        # Default to a broadly-allowed format and fall back automatically if an override isn't permitted.
        resolved_output_format = (os.getenv("ELEVENLABS_OUTPUT_FORMAT") or "mp3_44100_128").strip()

        # Optional voice tuning
        stability = _env_float("ELEVENLABS_STABILITY")
        similarity_boost = _env_float("ELEVENLABS_SIMILARITY_BOOST")
        style = _env_float("ELEVENLABS_STYLE")
        speed = _env_float("ELEVENLABS_SPEED")
        use_speaker_boost = _env_bool("ELEVENLABS_SPEAKER_BOOST")

        voice_settings = None
        if any(v is not None for v in (stability, similarity_boost, style, speed, use_speaker_boost)):
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                speed=speed,
                use_speaker_boost=use_speaker_boost,
            )

        # Audio Tags are embedded in text and processed by v3 models
        # The delivery_style is informational - actual control is via Audio Tags in text
        
        # Use text_to_speech.convert() method (SDK v2+)
        convert_kwargs = {
            "text": text,
            "voice_id": resolved_voice_id,
            "model_id": resolved_model_id,
            "output_format": resolved_output_format,
        }
        if voice_settings is not None:
            convert_kwargs["voice_settings"] = voice_settings

        try:
            audio = self.client.text_to_speech.convert(**convert_kwargs)
        except Exception as e:
            # If the chosen output format isn't allowed for this account tier, retry with a safe default.
            message = str(e)
            if (
                resolved_output_format != "mp3_44100_128"
                and ("output_format_not_allowed" in message or "Requested output format" in message)
            ):
                convert_kwargs["output_format"] = "mp3_44100_128"
                audio = self.client.text_to_speech.convert(**convert_kwargs)
            else:
                raise

        # Save
        # Include voice + model in the cache key so the same line can be regenerated
        # with different voices without overwriting / reusing the wrong file.
        cache_key = f"{resolved_voice_id}:{resolved_model_id}:{text}"
        prefix = re.sub(r"[^a-zA-Z0-9_\\-]", "", str(file_prefix or "vo")) or "vo"
        filename = f"{prefix}_{hashlib.md5(cache_key.encode()).hexdigest()}.mp3"
        filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        save(audio, filepath)
        return filepath

    def generate_sfx(self, text: str, duration: int = 5) -> str:
        """
        Generates SFX.
        """
        # Note: ElevenLabs SFX API might be different or require specific endpoint
        # Using the text_to_sound_effects endpoint if available in SDK
        # If not, we might need requests. 
        # SDK usually has `text_to_sound_effects`
        
        try:
            result = self.client.text_to_sound_effects.convert(
                text=text,
                duration_seconds=duration,
                prompt_influence=0.5
            )
            
            # Result is a generator or bytes?
            # Usually generator.
            
            filename = f"sfx_{hashlib.md5(text.encode()).hexdigest()}.mp3"
            filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            save(result, filepath)
            return filepath
            
        except Exception as e:
            print(f"SFX Generation failed: {e}")
            return ""

    def generate_bgm(self, prompt: str, duration: int = 15) -> str:
        """
        Generates Background Music (BGM).
        Uses text-to-sound-effects with a musical prompt.
        """
        if not self.client:
            print("ElevenLabs API key missing for BGM.")
            return ""

        print(f"[ELEVENLABS] Generating BGM ({duration}s): {prompt}...")
        try:
            # We append 'instrumental music track, high quality' to ensure musicality
            enhanced_prompt = f"Music track, {prompt}, high quality instrumental, cinematic score"
            
            result = self.client.text_to_sound_effects.convert(
                text=enhanced_prompt,
                duration_seconds=duration,
                prompt_influence=0.7 # Higher influence for music
            )
            
            filename = f"bgm_{hashlib.md5(prompt.encode()).hexdigest()}.mp3"
            filepath = os.path.join(config.ASSETS_DIR, "audio", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            save(result, filepath)
            print(f"[ELEVENLABS] BGM Saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] BGM Generation failed: {e}")
            return ""
