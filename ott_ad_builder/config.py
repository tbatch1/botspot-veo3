import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from the root .env file (absolute path)
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_root_dir, ".env")
print(f"[CONFIG] Loading .env from: {_env_path}")
load_dotenv(_env_path, override=True)  # override=True to replace existing env vars
print(f"[CONFIG] OPENAI_API_KEY loaded: {'YES' if os.getenv('OPENAI_API_KEY') else 'NO'}")
print(f"[CONFIG] FAL_API_KEY loaded: {'YES' if os.getenv('FAL_API_KEY') else 'NO'}")
print(f"[CONFIG] ELEVENLABS_API_KEY loaded: {'YES' if os.getenv('ELEVENLABS_API_KEY') else 'NO'}")

class AppConfig(BaseModel):
    """Application Configuration Validation"""
    # Demo foundation: single-provider mode (no fallbacks)
    OPENAI_API_KEY: str = Field(..., description="OpenAI API Key (GPT-5.2)")
    FAL_API_KEY: str = Field(..., description="Fal.ai API Key (Flux)")
    ELEVENLABS_API_KEY: str = Field(..., description="ElevenLabs API Key (Voice)")

    # Optional/legacy keys kept for compatibility with unused modules
    GEMINI_API_KEY: str = Field(default="", description="Google Cloud Gemini API Key (unused in strict mode)")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key (unused in strict mode)")
    REPLICATE_API_TOKEN: str = Field(default="", description="Replicate API Token (unused in strict mode)")
    RUNWAY_API_KEY: str = Field(default="", description="RunwayML API Key (unused in strict mode)")

    # Model Constants - PREMIUM QUALITY (Dec 2025 - Upgraded for quality-first clients)
    IMAGEN_MODEL: str = "imagen-4.0-ultra-generate-001"  # Imagen 4 Ultra - Highest Quality
    LEGACY_IMAGEN_MODEL: str = "imagen-4.0-generate-001"  # Imagen 4 Standard Fallback
    FLUX_MODEL: str = "black-forest-labs/flux-1.1-pro" # Replicate fallback
    FAL_FLUX_MODEL: str = "fal-ai/flux-pro/v1.1"  # Fal.ai Flux 1.1 Pro (Primary)
    RUNWAY_MODEL: str = "gen3a_turbo"
    # Higher quality (less "AI-sounding") than turbo; slower but better for demos.
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
    LUMIERE_MODEL: str = "veo-3.1-generate-preview" # Veo 3.1 - 1080p output, native audio
    COMPOSITION_MODEL: str = "gemini-2.5-flash" # Script generation with OTT guidance
    STRATEGIST_MODEL: str = "claude-opus-4-5-20251101" # Claude Opus 4.5 (Nov 2025)
    GPT52_MODEL: str = "gpt-5.2"  # GPT-5.2 Spatial Reasoning (Dec 11, 2025)
    IMAGE_RESOLUTION: str = "16:9"  # OTT broadcast aspect ratio
    
    # Paths - use absolute paths for reliability
    ASSETS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

    class Config:
        env_file = ".env"
        extra = "ignore"

def load_config() -> AppConfig:
    """Load and validate configuration."""
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    fal_key = os.getenv("FAL_API_KEY", "").strip()
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "").strip()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    replicate_key = os.getenv("REPLICATE_API_TOKEN", "").strip()
    runway_key = os.getenv("RUNWAY_API_KEY", "").strip()

    missing = []
    if not openai_key:
        missing.append("OPENAI_API_KEY")
    if not fal_key:
        missing.append("FAL_API_KEY")
    if not eleven_key:
        missing.append("ELEVENLABS_API_KEY")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}. Set them in your root .env file.")

    return AppConfig(
        OPENAI_API_KEY=openai_key,
        FAL_API_KEY=fal_key,
        ELEVENLABS_API_KEY=eleven_key,
        GEMINI_API_KEY=gemini_key,
        ANTHROPIC_API_KEY=anthropic_key,
        REPLICATE_API_TOKEN=replicate_key,
        RUNWAY_API_KEY=runway_key,
    )

# Create directories if they don't exist
config = load_config()
os.makedirs(config.ASSETS_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)
