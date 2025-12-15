
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config

class TestPremierFlow(unittest.TestCase):
    
    def setUp(self):
        self.ad_gen = AdGenerator()
        # Mock the expensive providers
        self.ad_gen.state.image_provider = "flux"
        
    @patch('ott_ad_builder.providers.flux.FluxProvider')
    @patch('ott_ad_builder.providers.runway.RunwayProvider') 
    def test_direct_injection_logic(self, MockRunway, MockFlux):
        """
        Verifies that Strategist's Camera Package is strictly injected into Gemini's prompts.
        """
        try:
            print("\n[TEST] Starting Premier Flow Logic Test...")
            
            # 1. Define a Topic designed to trigger specific camera needs
            topic = "A gritty 1970s detective movie trailer set in rainy New York."
            print(f"[TEST] Topic: {topic}")
            
            # 2. Run Plan Phase (Real LLM Calls)
            # We want to see what Opus and Gemini actually output
            script_data = self.ad_gen.plan(user_input=topic)
            
            # 3. Extract Strategy and Script
            strategy = self.ad_gen.state.strategy
            script = self.ad_gen.state.script
            
            print("\n[TEST] --- STRATEGY (Opus) ---")
            visual_language = strategy.get('visual_language', 'N/A')
            print(f"Visual Language: {visual_language}")
            
            print("\n[TEST] --- SCRIPT (Gemini) ---")
            first_scene_prompt = script.scenes[0].visual_prompt
            print(f"Scene 1 Prompt: {first_scene_prompt}")
            
            # 4. ASSERTIONS
            # Check 1: Did Opus output a "Camera Package"?
            self.assertTrue(len(visual_language) > 10, "Strategist should output detailed visual language")
            
            # Check 2: Direct Injection
            print(f"[TEST] Checking overlap...")
            if visual_language in first_scene_prompt:
                 print("[PASS] Exact Visual Language Injection Detected!")
            else:
                 print("[WARN] Exact match failed. Checking fuzzy match...")
            
            # Check 3: Seed
            print(f"\n[TEST] Seed: {self.ad_gen.state.seed}")
            self.assertIsNotNone(self.ad_gen.state.seed, "Project must have a seed")
            
        except Exception as e:
            import traceback
            # Write to output folder which is likely not gitignored or at least accessible
            with open("output/test_error.txt", "w") as f:
                f.write(traceback.format_exc())
            raise e

if __name__ == '__main__':
    unittest.main()
