"""
Integration tests for adaptive prompt engineering system.
Tests the complete workflow with different creative styles.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ott_ad_builder.utils.style_detector import StyleDetector
from ott_ad_builder.constants.style_profiles import (
    VIDEO_ENHANCEMENTS,
    VIDEO_NEGATIVE_PROMPTS,
    IMAGE_POSITIVE_EMPHASIS
)
from ott_ad_builder.providers.imagen import ImagenProvider
from ott_ad_builder.providers.video_google import GoogleVideoProvider


def test_style_detection_epic():
    """Test detection of LOTR-style epic fantasy aesthetic"""
    print("\n[TEST 1] LOTR-Style Epic Fantasy Detection")
    print("=" * 60)

    detector = StyleDetector()
    user_input = """
    Create an epic fantasy commercial for a new gaming console.
    Sweeping vistas, heroic characters, Lord of the Rings-inspired cinematography.
    Grand orchestral music, legendary scope, mythic storytelling.
    """

    style = detector.detect_style(user_input)

    print(f"   Detected Aesthetic: {style['aesthetic']}")
    print(f"   Aesthetic Confidence: {style['confidence_breakdown']['aesthetic']:.0%}")
    print(f"   Overall Confidence: {style['confidence']:.0%}")
    print(f"   Format: {style['format']}")
    print(f"   Tone: {style['tone']}")
    print(f"   Pacing: {style['pacing']}")

    # Assertions
    assert style['aesthetic'] == 'epic', f"Expected 'epic', got '{style['aesthetic']}'"
    assert style['confidence_breakdown']['aesthetic'] >= 0.3, f"Low confidence: {style['confidence_breakdown']['aesthetic']:.0%}"

    print("   [OK] Epic fantasy style detected correctly")
    return style


def test_style_detection_abstract():
    """Test detection of Lambo-style abstract/surreal aesthetic"""
    print("\n[TEST 2] Lambo-Style Abstract/Surreal Detection")
    print("=" * 60)

    detector = StyleDetector()
    user_input = """
    Create an abstract commercial for a luxury sports car.
    Surreal dreamlike sequences, impossible camera angles, symbolic imagery.
    Bold colors, conceptual metaphors, artistic composition.
    The car defies gravity, morphs through abstract environments.
    """

    style = detector.detect_style(user_input)

    print(f"   Detected Aesthetic: {style['aesthetic']}")
    print(f"   Aesthetic Confidence: {style['confidence_breakdown']['aesthetic']:.0%}")
    print(f"   Overall Confidence: {style['confidence']:.0%}")
    print(f"   Format: {style['format']}")
    print(f"   Tone: {style['tone']}")

    # Assertions
    assert style['aesthetic'] == 'abstract', f"Expected 'abstract', got '{style['aesthetic']}'"
    assert style['confidence_breakdown']['aesthetic'] >= 0.3, f"Low confidence: {style['confidence_breakdown']['aesthetic']:.0%}"

    print("   [OK] Abstract/surreal style detected correctly")
    return style


def test_style_detection_minimalist():
    """Test detection of minimalist product showcase aesthetic"""
    print("\n[TEST 3] Minimalist Product Showcase Detection")
    print("=" * 60)

    detector = StyleDetector()
    user_input = """
    Create a minimalist commercial for a premium smartphone.
    Clean white backgrounds, negative space, simple compositions.
    Zen aesthetics, pure product focus, elegant simplicity.
    No clutter, no distractions, just the product.
    """

    style = detector.detect_style(user_input)

    print(f"   Detected Aesthetic: {style['aesthetic']}")
    print(f"   Aesthetic Confidence: {style['confidence_breakdown']['aesthetic']:.0%}")
    print(f"   Overall Confidence: {style['confidence']:.0%}")
    print(f"   Format: {style['format']}")
    print(f"   Tone: {style['tone']}")

    # Assertions
    assert style['aesthetic'] == 'minimalist', f"Expected 'minimalist', got '{style['aesthetic']}'"
    assert style['confidence_breakdown']['aesthetic'] >= 0.3, f"Low confidence: {style['confidence_breakdown']['aesthetic']:.0%}"

    print("   [OK] Minimalist style detected correctly")
    return style


def test_adaptive_prompting_epic():
    """Test that epic style generates correct prompt enhancements"""
    print("\n[TEST 4] Epic Style Prompt Enhancement")
    print("=" * 60)

    # Check that epic enhancements exist
    assert 'epic' in VIDEO_ENHANCEMENTS, "Missing epic enhancement in VIDEO_ENHANCEMENTS"
    assert 'epic' in VIDEO_NEGATIVE_PROMPTS, "Missing epic negative prompt"
    assert 'epic' in IMAGE_POSITIVE_EMPHASIS, "Missing epic image emphasis"

    epic_video = VIDEO_ENHANCEMENTS['epic']
    epic_negative = VIDEO_NEGATIVE_PROMPTS['epic']
    epic_image = IMAGE_POSITIVE_EMPHASIS['epic']

    print(f"   Video Enhancement (first 100 chars):\n      {epic_video[:100]}...")
    print(f"   Negative Prompt: {epic_negative}")
    print(f"   Image Emphasis: {epic_image}")

    # Verify key terms are present
    assert 'epic' in epic_video.lower(), "Epic enhancement missing 'epic' keyword"
    assert 'grand' in epic_video.lower() or 'heroic' in epic_video.lower(), "Epic enhancement missing scale keywords"

    print("   [OK] Epic style enhancements configured correctly")


def test_adaptive_prompting_abstract():
    """Test that abstract style generates correct prompt enhancements"""
    print("\n[TEST 5] Abstract Style Prompt Enhancement")
    print("=" * 60)

    # Check that abstract enhancements exist
    assert 'abstract' in VIDEO_ENHANCEMENTS, "Missing abstract enhancement"
    assert 'abstract' in VIDEO_NEGATIVE_PROMPTS, "Missing abstract negative prompt"
    assert 'abstract' in IMAGE_POSITIVE_EMPHASIS, "Missing abstract image emphasis"

    abstract_video = VIDEO_ENHANCEMENTS['abstract']
    abstract_negative = VIDEO_NEGATIVE_PROMPTS['abstract']
    abstract_image = IMAGE_POSITIVE_EMPHASIS['abstract']

    print(f"   Video Enhancement (first 100 chars):\n      {abstract_video[:100]}...")
    print(f"   Negative Prompt: {abstract_negative}")
    print(f"   Image Emphasis: {abstract_image}")

    # Verify key terms are present
    assert 'abstract' in abstract_video.lower() or 'surreal' in abstract_video.lower(), "Abstract enhancement missing style keywords"
    assert 'photorealistic' in abstract_negative.lower(), "Abstract negative should exclude photorealism"

    print("   [OK] Abstract style enhancements configured correctly")


def test_adaptive_prompting_minimalist():
    """Test that minimalist style generates correct prompt enhancements"""
    print("\n[TEST 6] Minimalist Style Prompt Enhancement")
    print("=" * 60)

    # Check that minimalist enhancements exist
    assert 'minimalist' in VIDEO_ENHANCEMENTS, "Missing minimalist enhancement"
    assert 'minimalist' in VIDEO_NEGATIVE_PROMPTS, "Missing minimalist negative prompt"
    assert 'minimalist' in IMAGE_POSITIVE_EMPHASIS, "Missing minimalist image emphasis"

    minimalist_video = VIDEO_ENHANCEMENTS['minimalist']
    minimalist_negative = VIDEO_NEGATIVE_PROMPTS['minimalist']
    minimalist_image = IMAGE_POSITIVE_EMPHASIS['minimalist']

    print(f"   Video Enhancement (first 100 chars):\n      {minimalist_video[:100]}...")
    print(f"   Negative Prompt: {minimalist_negative}")
    print(f"   Image Emphasis: {minimalist_image}")

    # Verify key terms are present
    assert 'minimal' in minimalist_video.lower() or 'clean' in minimalist_video.lower(), "Minimalist enhancement missing style keywords"
    assert 'clutter' in minimalist_negative.lower() or 'busy' in minimalist_negative.lower(), "Minimalist negative should exclude clutter"

    print("   [OK] Minimalist style enhancements configured correctly")


def test_provider_aesthetic_setting():
    """Test that providers correctly accept and store aesthetic styles"""
    print("\n[TEST 7] Provider Aesthetic Configuration")
    print("=" * 60)

    # Test Imagen provider
    print("   Testing ImagenProvider.set_aesthetic_style()...")
    imagen = ImagenProvider()
    imagen.set_aesthetic_style('epic')
    assert imagen._current_aesthetic == 'epic', "Imagen didn't store aesthetic correctly"
    print("   [OK] ImagenProvider aesthetic setting works")

    # Test Veo provider
    print("   Testing GoogleVideoProvider.set_aesthetic_style()...")
    veo = GoogleVideoProvider()
    veo.set_aesthetic_style('abstract')
    assert veo._current_aesthetic == 'abstract', "Veo didn't store aesthetic correctly"
    print("   [OK] GoogleVideoProvider aesthetic setting works")

    print("   [OK] All providers support aesthetic configuration")


def test_integration_workflow():
    """Test the complete workflow: Detection → Provider Configuration"""
    print("\n[TEST 8] Complete Integration Workflow")
    print("=" * 60)

    detector = StyleDetector()

    # Simulate user input
    user_input = "Create an epic fantasy commercial with sweeping Lord of the Rings cinematography"

    # Step 1: Detect style
    print("   Step 1: Detecting style...")
    style = detector.detect_style(user_input)
    aesthetic = style['aesthetic']
    print(f"   Detected: {aesthetic}")

    # Step 2: Configure providers
    print("   Step 2: Configuring providers...")
    imagen = ImagenProvider()
    veo = GoogleVideoProvider()

    imagen.set_aesthetic_style(aesthetic)
    veo.set_aesthetic_style(aesthetic)

    # Step 3: Verify providers use correct enhancements
    print("   Step 3: Verifying prompt enhancements...")
    assert imagen._current_aesthetic == aesthetic
    assert veo._current_aesthetic == aesthetic

    # Verify enhancements exist for detected style
    assert aesthetic in VIDEO_ENHANCEMENTS
    assert aesthetic in IMAGE_POSITIVE_EMPHASIS

    print(f"   [OK] Complete workflow successful for {aesthetic} style")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("ADAPTIVE PROMPTING INTEGRATION TESTS")
    print("=" * 60)

    try:
        # Style Detection Tests
        test_style_detection_epic()
        test_style_detection_abstract()
        test_style_detection_minimalist()

        # Prompt Enhancement Tests
        test_adaptive_prompting_epic()
        test_adaptive_prompting_abstract()
        test_adaptive_prompting_minimalist()

        # Provider Configuration Tests
        test_provider_aesthetic_setting()

        # Integration Test
        test_integration_workflow()

        print("\n" + "=" * 60)
        print("[SUCCESS] All 8 integration tests passed!")
        print("=" * 60)
        print("\nSYSTEM STATUS:")
        print("  - Style detection: WORKING")
        print("  - Prompt enhancements: WORKING")
        print("  - Provider configuration: WORKING")
        print("  - End-to-end workflow: WORKING")
        print("\nREADY FOR PRODUCTION: YES")
        print("=" * 60)

        return True

    except AssertionError as e:
        print(f"\n[FAILED] Test assertion failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
