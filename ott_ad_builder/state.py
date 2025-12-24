from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import uuid
import random


class UploadedAsset(BaseModel):
    """Represents an uploaded file with its intended usage mode."""
    filename: str
    mode: str = "reference"  # "reference" (I2I style input) or "direct" (use as-is)


class Scene(BaseModel):
    """Represents a single scene in the ad."""
    id: int
    visual_prompt: str = Field(..., description="Prompt for Imagen 3")
    audio_prompt: Optional[str] = Field(None, description="Prompt for SFX")
    motion_prompt: str = Field(..., description="Prompt for Runway Gen-3")
    duration: int = Field(5, description="Duration in seconds")

    # Character/Product Consistency Tracking
    primary_subject: Optional[str] = Field(None, description="Subject identifier (e.g., 'businesswoman', 'sports car')")
    subject_description: Optional[str] = Field(None, description="Detailed appearance for consistency")
    subject_reference: Optional[str] = Field(None, description="Reference to Scene 1's subject for consistency")

    # Asset paths (populated later)
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    sfx_path: Optional[str] = None

    # Image source: "ai" for AI generation, "upload:{filename}" for direct upload
    image_source: Optional[str] = Field(None, description="Image source: 'ai' or 'upload:{filename}'")

    # Composition fields
    composition_sources: Optional[List[str]] = Field(default_factory=list, description="Paths to images to mix")
    composition_prompt: Optional[str] = Field(None, description="Prompt for mixing images")

class ScriptLine(BaseModel):
    """A single line of dialogue."""
    speaker: str
    text: str
    time_range: str = Field(..., description="e.g. '0-5s'")
    voice_id: Optional[str] = Field(
        None,
        description="Optional ElevenLabs voice_id override for this line (UI-selectable).",
    )
    scene_id: Optional[int] = Field(
        None,
        description="Scene id this line should sync to (helps keep dialogue on the correct visual).",
    )
    
    # Asset path
    audio_path: Optional[str] = None

class Script(BaseModel):
    """The generated script and creative direction."""
    lines: List[ScriptLine] = Field(default_factory=list)
    mood: str = "cinematic"  # Default mood
    scenes: List[Scene] = Field(default_factory=list)

class ProjectState(BaseModel):
    """The Single Source of Truth for the pipeline."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_input: str
    status: str = "initialized" # initialized, planned, assets_generated, assembled, completed, failed
    error: Optional[str] = None  # Error message if generation fails
    seed: int = Field(default_factory=lambda: random.randint(0, 2**32 - 1)) # Master seed for consistency


    script: Optional[Script] = None
    strategy: Optional[Dict] = None # The raw output from Strategist (Claude)
    research_brief: Optional[str] = None # The raw output from Researcher
    detected_style: Optional[Dict] = None # Detected aesthetic style profile for adaptive prompting

    # Global assets
    final_video_path: Optional[str] = None
    final_video_path_4k: Optional[str] = None # Path to 4K Master
    bgm_path: Optional[str] = None # Path to generated background music
    video_model: str = "veo" # "veo" (primary) or "runway" (fallback)
    # When true, request Veo native audio generation and preserve clip audio in final assembly.
    # This skips ElevenLabs BGM/SFX mixing by default (demo option; can be noisy/unstable).
    veo_generate_audio: bool = False
    image_provider: str = "flux" # Default to High Fidelity (Flux)
    style_preset: str = "Cinematic" # Default style
    image_provider: str = "flux" # Default to High Fidelity (Flux)
    style_preset: str = "Cinematic" # Default style
    # FFmpeg `xfade` transition name. Use "fade" for a classic crossfade.
    transition_type: str = "fade" # "fade", "wipeleft", "slideleft", "cut"

    # Frontend playback strategy for the final video.
    # - auto: direct MP4 with client-side fallback (recommended)
    # - direct: direct MP4 only (no fallback)
    # - blob: client fetches MP4 and plays via object URL (most reliable for demos)
    player_mode: str = Field(default="auto", description="Final video playback mode (UI).")
    
    # Asset Upload (Image-to-Video)
    uploaded_assets: List[str] = [] # List of filenames (legacy)
    uploaded_asset: Optional[str] = None # Legacy/Primary asset
    uploaded_assets_v2: List[UploadedAsset] = Field(default_factory=list, description="Uploaded files with mode info")

    # Reference image guidance:
    # - none: ignore reference uploads for both prompting + I2I
    # - i2i_only: use reference upload for image-to-image guidance only
    # - prompt_only: analyze reference image for style tokens only
    # - prompt_and_i2i: do both
    image_guidance: str = Field(default="i2i_only", description="How reference images influence prompting and I2I.")
    reference_style_guide: Optional[str] = Field(default=None, description="Derived style guide from reference image (palette/lighting).")

    # Live Logs (Brain Activity)
    logs: List[str] = Field(default_factory=list, description="Real-time thought process")

    def add_log(self, message: str):
        """Add a log entry."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def update_status(self, new_status: str):
        """Update the project status."""
        self.status = new_status
