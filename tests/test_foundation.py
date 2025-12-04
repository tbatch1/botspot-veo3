import unittest
import os
import shutil
from ott_ad_builder.config import load_config, AppConfig
from ott_ad_builder.state import ProjectState, Script, Scene, ScriptLine

class TestFoundation(unittest.TestCase):
    
    def setUp(self):
        # Ensure we have a clean environment
        self.test_assets_dir = "test_assets"
        os.makedirs(self.test_assets_dir, exist_ok=True)
        
    def tearDown(self):
        if os.path.exists(self.test_assets_dir):
            shutil.rmtree(self.test_assets_dir)

    def test_config_loading(self):
        """Test that configuration loads correctly."""
        config = load_config()
        self.assertIsInstance(config, AppConfig)
        self.assertTrue(hasattr(config, "GEMINI_API_KEY"))
        self.assertTrue(hasattr(config, "RUNWAY_API_KEY"))
        self.assertEqual(config.IMAGEN_MODEL, "imagegeneration@006")

    def test_state_management(self):
        """Test ProjectState initialization and updates."""
        state = ProjectState(user_input="Test Product")
        self.assertEqual(state.status, "initialized")
        self.assertIsNotNone(state.id)
        
        # Test updating status
        state.update_status("planned")
        self.assertEqual(state.status, "planned")
        
        # Test adding a script
        scene = Scene(
            id=1, 
            visual_prompt="A test scene", 
            motion_prompt="Pan right"
        )
        line = ScriptLine(
            speaker="Narrator", 
            text="Hello world", 
            time_range="0-5s"
        )
        script = Script(
            lines=[line], 
            mood="Happy", 
            scenes=[scene]
        )
        
        state.script = script
        self.assertEqual(state.script.mood, "Happy")
        self.assertEqual(len(state.script.scenes), 1)

if __name__ == '__main__':
    unittest.main()
