"""
Mock Providers for Testing OTT Ad Builder Without API Keys
Returns placeholder assets to test the full workflow without making real API calls.
"""

import os
import time
from typing import Optional
from .base import ImageProvider, VideoProvider, AudioProvider

class MockImagenProvider(ImageProvider):
    """Mock Imagen 3 provider - returns placeholder images."""

    def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str:
        """Generate a mock image (placeholder)."""
        print(f"[MOCK IMAGEN] Generating image for: {prompt[:50]}...")
        time.sleep(0.5)  # Simulate API delay

        # Create placeholder path
        filename = f"mock_image_{abs(hash(prompt)) % 10000}.png"
        filepath = os.path.join("assets", "images", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Create a simple placeholder file (1x1 pixel PNG)
        # This is a minimal valid PNG file
        placeholder_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        with open(filepath, 'wb') as f:
            f.write(placeholder_png)

        print(f"[MOCK IMAGEN] ✅ Generated: {filepath}")
        return filepath


class MockRunwayProvider(VideoProvider):
    """Mock Runway Gen-3 provider - returns placeholder videos."""

    def animate(self, image_path: str, prompt: str, duration: int = 5) -> str:
        """Generate a mock video from image (placeholder)."""
        print(f"[MOCK RUNWAY] Animating video: {prompt[:50]}...")
        time.sleep(1.0)  # Simulate API delay

        # Create placeholder path
        filename = f"mock_video_{abs(hash(prompt)) % 10000}.mp4"
        filepath = os.path.join("assets", "clips", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Create a minimal valid MP4 file (just header, won't play but exists)
        # For testing, we'll just create an empty file
        with open(filepath, 'wb') as f:
            f.write(b'')  # Empty file as placeholder

        print(f"[MOCK RUNWAY] ✅ Generated: {filepath}")
        return filepath


class MockElevenLabsProvider(AudioProvider):
    """Mock ElevenLabs provider - returns placeholder audio."""

    def generate_speech(self, text: str, voice: str = "Adam") -> str:
        """Generate mock speech audio (placeholder)."""
        print(f"[MOCK ELEVENLABS] Generating speech: {text[:30]}...")
        time.sleep(0.3)  # Simulate API delay

        # Create placeholder path
        filename = f"mock_speech_{abs(hash(text)) % 10000}.mp3"
        filepath = os.path.join("assets", "audio", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Create empty placeholder
        with open(filepath, 'wb') as f:
            f.write(b'')

        print(f"[MOCK ELEVENLABS] ✅ Generated: {filepath}")
        return filepath

    def generate_sfx(self, prompt: str) -> str:
        """Generate mock sound effects (placeholder)."""
        print(f"[MOCK ELEVENLABS] Generating SFX: {prompt[:30]}...")
        time.sleep(0.3)  # Simulate API delay

        # Create placeholder path
        filename = f"mock_sfx_{abs(hash(prompt)) % 10000}.mp3"
        filepath = os.path.join("assets", "audio", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Create empty placeholder
        with open(filepath, 'wb') as f:
            f.write(b'')

        print(f"[MOCK ELEVENLABS] ✅ Generated: {filepath}")
        return filepath
