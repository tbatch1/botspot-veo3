from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import uuid
import random


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

    # Composition fields
    composition_sources: Optional[List[str]] = Field(default_factory=list, description="Paths to images to mix")
    composition_prompt: Optional[str] = Field(None, description="Prompt for mixing images")

class ScriptLine(BaseModel):
    """A single line of dialogue."""
    speaker: str
    text: str
    time_range: str = Field(..., description="e.g. '0-5s'")
    
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
    image_provider: str = "flux" # Default to High Fidelity (Flux)
    style_preset: str = "Cinematic" # Default style
    image_provider: str = "flux" # Default to High Fidelity (Flux)
    style_preset: str = "Cinematic" # Default style
    transition_type: str = "crossfade" # Transition style: "crossfade", "fade", "wipe", "cut"
    
    # Asset Upload (Image-to-Video)
    uploaded_assets: List[str] = [] # List of filenames
    uploaded_asset: Optional[str] = None # Legacy/Primary asset # Filename of user uploaded asset for reference/i2i

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
