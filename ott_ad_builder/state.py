from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import uuid

class Scene(BaseModel):
    """Represents a single scene in the ad."""
    id: int
    visual_prompt: str = Field(..., description="Prompt for Imagen 3")
    audio_prompt: Optional[str] = Field(None, description="Prompt for SFX")
    motion_prompt: str = Field(..., description="Prompt for Runway Gen-3")
    duration: int = Field(5, description="Duration in seconds")
    
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
    lines: List[ScriptLine]
    mood: str
    scenes: List[Scene]

class ProjectState(BaseModel):
    """The Single Source of Truth for the pipeline."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_input: str
    status: str = "initialized" # initialized, planned, assets_generated, assembled, completed, failed
    error: Optional[str] = None  # Error message if generation fails

    script: Optional[Script] = None

    # Global assets
    final_video_path: Optional[str] = None
    video_model: str = "runway" # "runway" or "veo"
    style_preset: str = "Cinematic" # Default style

    def update_status(self, new_status: str):
        self.status = new_status
