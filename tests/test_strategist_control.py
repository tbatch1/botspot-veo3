import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState

class TestStrategistControl(unittest.TestCase):
    def setUp(self):
        self.generator = AdGenerator()
        # Mock dependencies to avoid real API calls
        self.generator.researcher = MagicMock()
        self.generator.llm = MagicMock()
        self.generator.compliance = MagicMock()
        self.generator.compliance.review.return_value = MagicMock()

    @patch('ott_ad_builder.providers.strategist.StrategistProvider.develop_strategy')
    def test_strategist_overrides_defaults(self, mock_develop_strategy):
        """Test that Strategist recommendations override default settings"""
        
        # 1. Setup Mock Strategy with explicit recommendations
        mock_strategy = {
            "core_concept": "Test Concept",
            "production_recommendations": {
                "visual_engine": "flux",      # Should override default (if any)
                "video_engine": "runway",     # Should set video model
                "voice_vibe": "Cinematic"
            }
        }
        mock_develop_strategy.return_value = mock_strategy

        # 2. Run Plan
        # User input does NOT override image_provider, so Strategist should win
        self.generator.plan("Test Topic", config_overrides={})

        # 3. Assertions
        print(f"State Image Provider: {self.generator.state.image_provider}")
        print(f"State Video Model: {self.generator.state.video_model}")

        self.assertEqual(self.generator.state.image_provider, "flux")
        self.assertEqual(self.generator.state.video_model, "runway")
        self.assertEqual(self.generator.state.strategy, mock_strategy)

    @patch('ott_ad_builder.providers.strategist.StrategistProvider.develop_strategy')
    def test_user_config_wins(self, mock_develop_strategy):
        """Test that User Config overrides Strategist"""
        
        # 1. Setup Mock Strategy (Strategist says Flux)
        mock_strategy = {
            "production_recommendations": {
                "visual_engine": "flux" 
            }
        }
        mock_develop_strategy.return_value = mock_strategy

        # 2. Run Plan with User Config Override (User says Imagen)
        overrides = {"image_provider": "imagen"}
        self.generator.plan("Test Topic", config_overrides=overrides)

        # 3. Assertions (User should win)
        print(f"State Image Provider: {self.generator.state.image_provider}")
        self.assertEqual(self.generator.state.image_provider, "imagen")

if __name__ == '__main__':
    unittest.main()
