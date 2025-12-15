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
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        seed: int = None,
        image_input: str = None
    ) -> str:
        """
        Generates an image and returns the local file path.

        Args:
            prompt: Text description of the desired image
            aspect_ratio: Image aspect ratio (default: "16:9")
            seed: Random seed for reproducibility (optional, provider-dependent)
            image_input: Path to input image for image-to-image (optional, provider-dependent)

        Returns:
            str: Path to the generated image file

        Note:
            Not all providers support all parameters. Unsupported parameters
            should be gracefully ignored with appropriate logging.
        """
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
