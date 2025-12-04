import unittest
from unittest.mock import MagicMock, patch
from ott_ad_builder.providers.gemini import GeminiProvider
from ott_ad_builder.state import Script

class TestGeminiProvider(unittest.TestCase):
    
    @patch("google.generativeai.GenerativeModel")
    def test_generate_plan(self, mock_model_cls):
        # Mock the response
        mock_instance = mock_model_cls.return_value
        mock_response = MagicMock()
        mock_response.text = """
        {
            "lines": [
                { "speaker": "Narrator", "text": "Test line", "time_range": "0-5s" }
            ],
            "mood": "Excited",
            "scenes": [
                {
                    "id": 1,
                    "visual_prompt": "A test image",
                    "motion_prompt": "Pan left",
                    "audio_prompt": "Silence",
                    "duration": 5
                }
            ]
        }
        """
        mock_instance.generate_content.return_value = mock_response
        
        provider = GeminiProvider()
        script = provider.generate_plan("Test Product")
        
        self.assertIsInstance(script, Script)
        self.assertEqual(script.mood, "Excited")
        self.assertEqual(len(script.scenes), 1)
        self.assertEqual(script.scenes[0].visual_prompt, "A test image")

if __name__ == '__main__':
    unittest.main()
