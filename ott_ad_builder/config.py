import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from the root .env file (absolute path)
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_root_dir, ".env")
print(f"[CONFIG] Loading .env from: {_env_path}")
load_dotenv(_env_path, override=True)  # override=True to replace existing env vars
runway_key = os.getenv('RUNWAY_API_KEY')
print(f"[CONFIG] RUNWAY_API_KEY loaded: {'YES' if runway_key else 'NO'}")
if runway_key:
    print(f"[CONFIG] API Key length: {len(runway_key)} chars")

class AppConfig(BaseModel):
    """Application Configuration Validation"""
    GEMINI_API_KEY: str = Field(..., description="Google Cloud Gemini API Key")
    RUNWAY_API_KEY: str = Field(..., description="RunwayML API Key")
    ELEVENLABS_API_KEY: str = Field(..., description="ElevenLabs API Key")
    
    # Model Constants - OTT BROADCAST QUALITY (Nov 2025)
    IMAGEN_MODEL: str = "imagen-4.0-generate-001"  # Imagen 4 GA - Broadcast quality
    LEGACY_IMAGEN_MODEL: str = "imagen-3.0-generate-002"  # Imagen 3 Fallback
    RUNWAY_MODEL: str = "gen3a_turbo"
    ELEVENLABS_MODEL: str = "eleven_turbo_v2_5"
    LUMIERE_MODEL: str = "veo-3.1-generate-preview" # Veo 3.1 - 1080p output, native audio
    COMPOSITION_MODEL: str = "gemini-2.5-flash" # Script generation with OTT guidance
    IMAGE_RESOLUTION: str = "16:9"  # OTT broadcast aspect ratio (Imagen will generate at max quality)
    
    # Paths - use absolute paths for reliability
    ASSETS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

    class Config:
        env_file = ".env"
        extra = "ignore"

def load_config() -> AppConfig:
    """Load and validate configuration."""
    # Get API keys from environment, use dummy values for mock mode
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    runway_key = os.getenv("RUNWAY_API_KEY", "mock_runway_key")
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "mock_elevenlabs_key")

    # Ensure we have at least Gemini API key
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY is required. Set it in your .env file.")

    return AppConfig(
        GEMINI_API_KEY=gemini_key,
        RUNWAY_API_KEY=runway_key,
        ELEVENLABS_API_KEY=eleven_key
    )

# Create directories if they don't exist
config = load_config()
os.makedirs(config.ASSETS_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)
