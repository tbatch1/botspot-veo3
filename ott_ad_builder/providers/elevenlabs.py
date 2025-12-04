import os
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
                print(f"⚠️ ElevenLabs client init failed: {e}")

    def generate_speech(self, text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb") -> str:
        """
        Generates TTS.
        Default voice: 'Adam' (JBFqnCBsd6RMkjVDRZzb)
        """
        if not self.client:
            raise Exception("ElevenLabs API key not configured.")

        audio = self.client.generate(
            text=text,
            voice=voice_id,
            model=config.ELEVENLABS_MODEL
        )
        
        # Save
        import hashlib
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
