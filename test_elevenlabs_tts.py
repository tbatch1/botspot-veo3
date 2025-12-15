#!/usr/bin/env python3
"""
Test script for ElevenLabs Text-to-Speech API endpoint
Tests the generate_speech() method with the configured API key
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ott_ad_builder.providers.elevenlabs import ElevenLabsProvider
from ott_ad_builder.config import config

def test_tts():
    """Test Text-to-Speech generation"""
    print("=" * 70)
    print("ELEVENLABS TEXT-TO-SPEECH TEST")
    print("=" * 70)

    # Check API key configuration
    print(f"\n[1] API Key Configuration:")
    print(f"   API Key loaded: {'YES' if config.ELEVENLABS_API_KEY else 'NO'}")
    if config.ELEVENLABS_API_KEY:
        print(f"   API Key length: {len(config.ELEVENLABS_API_KEY)} chars")
        print(f"   API Key prefix: {config.ELEVENLABS_API_KEY[:8]}...")
    print(f"   Model: {config.ELEVENLABS_MODEL}")

    # Initialize provider
    print(f"\n[2] Initializing ElevenLabs Provider...")
    try:
        provider = ElevenLabsProvider()
        if provider.client:
            print(f"   [OK] Provider initialized successfully")
        else:
            print(f"   [FAIL] Provider client is None")
            return False
    except Exception as e:
        print(f"   [FAIL] Provider initialization failed: {e}")
        return False

    # Test text-to-speech generation
    test_text = "Welcome to BotSpot. Your AI video creation platform."
    print(f"\n[3] Testing Text-to-Speech Generation:")
    print(f"   Text: \"{test_text}\"")
    print(f"   Voice: Adam (JBFqnCBsd6RMkjVDRZzb)")
    print(f"   Generating audio...")

    try:
        audio_path = provider.generate_speech(test_text)
        print(f"   [OK] Audio generated successfully!")
        print(f"   Output: {audio_path}")

        # Check file exists and has content
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"   File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")

            if file_size > 10000:  # > 10KB
                print(f"   [OK] File size is valid (> 10KB)")
            else:
                print(f"   [WARN] File size is small (< 10KB) - may be invalid")
                return False
        else:
            print(f"   [FAIL] Audio file not found at: {audio_path}")
            return False

    except Exception as e:
        print(f"   [FAIL] TTS generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print(f"\n{'=' * 70}")
    print(f"[PASS] TEST PASSED - Text-to-Speech endpoint is working correctly!")
    print(f"{'=' * 70}")
    print(f"\nYou can play the audio file at:")
    print(f"{audio_path}")
    return True

if __name__ == "__main__":
    success = test_tts()
    sys.exit(0 if success else 1)
