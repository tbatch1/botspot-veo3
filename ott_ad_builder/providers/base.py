from abc import ABC, abstractmethod
from ..state import Script

class LLMProvider(ABC):
    """Abstract base class for LLM (Brain) providers."""
    @abstractmethod
    def generate_plan(self, user_input: str) -> Script:
        """Analyzes input and returns a structured Script object."""
        pass

class ImageProvider(ABC):
    """Abstract base class for Image Generation providers."""
    @abstractmethod
    def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str:
        """Generates an image and returns the local file path."""
        pass

class VideoProvider(ABC):
    """Abstract base class for Video Generation providers."""
    @abstractmethod
    def animate(self, image_path: str, prompt: str, duration: int = 5) -> str:
        """Animates an image and returns the local video file path."""
        pass

class AudioProvider(ABC):
    """Abstract base class for Audio Generation providers."""
    @abstractmethod
    def generate_speech(self, text: str, voice_id: str) -> str:
        """Generates speech and returns the local audio file path."""
        pass
    
    @abstractmethod
    def generate_sfx(self, text: str, duration: int = 5) -> str:
        """Generates sound effects and returns the local audio file path."""
        pass
