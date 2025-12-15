import pytest
from unittest.mock import MagicMock, patch
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState

def test_multi_select_inputs_processing():
    """
    Verifies that list inputs from the frontend (Platform, Mood, Camera)
    are correctly processed and stored in the State and passed to prompt generation.
    """
    # 1. Mock inputs
    mock_config = {
        "topic": "Test Car Commercial",
        "style": ["Cinematic", "Cyberpunk"],
        "platform": ["Netflix", "YouTube TV"],
        "mood": ["Premium", "Bold"],
        "camera_style": ["Steadicam", "Drone"],
        "duration": "15s",
        "uploaded_assets": ["image1.png", "image2.png"]
    }

    # 2. Initialize Generator
    generator = AdGenerator()
    
    # 3. Mock the providers to prevent actual API calls
    generator.researcher = MagicMock()
    generator.strategist = MagicMock()
    generator.llm = MagicMock()
    generator.compliance = MagicMock()
    
    # Mock return values
    generator.strategist.develop_strategy.return_value = {
        "core_concept": "Test Concept",
        "production_recommendations": {}
    }
    generator.llm.generate_plan.return_value = MagicMock(scenes=[])
    
    # 4. Run Plan
    # We patch the save file operations to avoid creating junk files
    with patch("builtins.open", MagicMock()):
        generator.plan(user_input=mock_config["topic"], config_overrides=mock_config)

    # 5. Assertions
    
    # Check Pipeline State (uploaded_assets)
    assert generator.state.uploaded_assets == ["image1.png", "image2.png"]
    assert generator.state.uploaded_asset == "image1.png" # Primary fallback
    
    # Check proper keys passed to Strategist
    generator.strategist.develop_strategy.assert_called_once()
    call_args = generator.strategist.develop_strategy.call_args
    assert call_args.kwargs['constraints'] == mock_config
    
    # Check proper formatting in Gemini (Manual check of logic or via mock call inspection)
    # Since we modified Gemini.generate_plan logic, let's test that specifically
    
def test_gemini_prompt_formatting():
    """
    Tests specifically the generate_plan method in GeminiProvider
    to ensure lists are joined into strings.
    """
    from ott_ad_builder.providers.gemini import GeminiProvider
    
    provider = GeminiProvider()
    provider.model = MagicMock()
    provider.model.generate_content.return_value.text = '{"lines": [], "mood": "test", "scenes": []}'
    
    mock_config = {
        "platform": ["Netflix", "Hulu"],
        "mood": ["Dark", "Moody"],
        "camera_style": ["Handheld"]
    }
    
    # We need to spy on the prompt sent to generate_content
    import traceback
    try:
        provider.generate_plan("test input", config_overrides=mock_config)
    except Exception:
        traceback.print_exc()
        raise
    
    call_args = provider.model.generate_content.call_args
    print(f"DEBUG: call_args = {call_args}")
    
    if not call_args:
        pytest.fail("generate_content was never called!")

    sent_prompt = call_args[0][0]
    
    # Assert strings are joined
    assert "Netflix, Hulu" in sent_prompt
    assert "Dark, Moody" in sent_prompt
    # Camera mapping uses the first one, check if it didn't crash
    assert "Handheld" in sent_prompt or "emotional_moment" in sent_prompt # Checking logic flow
