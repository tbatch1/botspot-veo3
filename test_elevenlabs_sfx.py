#!/usr/bin/env python3
"""
Test script for ElevenLabs Sound Effects API endpoint
Tests the generate_sfx() method with the configured API key
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ott_ad_builder.providers.elevenlabs import ElevenLabsProvider
from ott_ad_builder.config import config

def test_sfx():
    """Test Sound Effects generation"""
    print("=" * 70)
    print("ELEVENLABS SOUND EFFECTS TEST")
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

    # Test sound effects generation
    test_prompt = "dramatic swoosh sound effect"
    test_duration = 3
    print(f"\n[3] Testing Sound Effects Generation:")
    print(f"   Prompt: \"{test_prompt}\"")
    print(f"   Duration: {test_duration} seconds")
    print(f"   Generating sound effect...")

    try:
        sfx_path = provider.generate_sfx(test_prompt, duration=test_duration)

        if not sfx_path:
            print(f"   [FAIL] SFX generation returned empty path")
            return False

        print(f"   [OK] Sound effect generated successfully!")
        print(f"   Output: {sfx_path}")

        # Check file exists and has content
        if os.path.exists(sfx_path):
            file_size = os.path.getsize(sfx_path)
            print(f"   File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")

            if file_size > 5000:  # > 5KB
                print(f"   [OK] File size is valid (> 5KB)")
            else:
                print(f"   [WARN] File size is small (< 5KB) - may be invalid")
                return False
        else:
            print(f"   [FAIL] Sound effect file not found at: {sfx_path}")
            return False

    except Exception as e:
        print(f"   [FAIL] SFX generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print(f"\n{'=' * 70}")
    print(f"[PASS] TEST PASSED - Sound Effects endpoint is working correctly!")
    print(f"{'=' * 70}")
    print(f"\nYou can play the audio file at:")
    print(f"{sfx_path}")
    return True

if __name__ == "__main__":
    success = test_sfx()
    sys.exit(0 if success else 1)
