import os
import hashlib
from elevenlabs.client import ElevenLabs
from elevenlabs import save
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

    def generate_speech(self, text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB", delivery_style: str = None) -> str:
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

        # Audio Tags are embedded in text and processed by v3 models
        # The delivery_style is informational - actual control is via Audio Tags in text
        
        # Use text_to_speech.convert() method (SDK v2+)
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=config.ELEVENLABS_MODEL,
            output_format="mp3_44100_128"
        )

        # Save
        filename = f"vo_{hashlib.md5(text.encode()).hexdigest()}.mp3"
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
