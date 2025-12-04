import unittest
import sys
from unittest.mock import MagicMock, patch

# Mock ffmpeg before import
sys.modules["ffmpeg"] = MagicMock()

from ott_ad_builder.providers.composer import Composer
from ott_ad_builder.state import ProjectState, Script, Scene, ScriptLine

class TestComposer(unittest.TestCase):
    
    @patch("ott_ad_builder.providers.composer.ffmpeg")
    @patch("os.path.exists", return_value=True)
    def test_compose(self, mock_exists, mock_ffmpeg):
        # Setup State
        scene = Scene(id=1, visual_prompt="p", motion_prompt="m", video_path="clip1.mp4")
        line = ScriptLine(speaker="N", text="t", time_range="0-5s", audio_path="vo1.mp3")
        script = Script(lines=[line], mood="Happy", scenes=[scene])
        state = ProjectState(user_input="Test", script=script)
        
        # Mock ffmpeg chain
        mock_input = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_concat = MagicMock()
        mock_ffmpeg.concat.return_value = mock_concat
        mock_concat.node = [MagicMock()] # video node
        
        mock_output = MagicMock()
        mock_ffmpeg.output.return_value = mock_output
        
        composer = Composer()
        path = composer.compose(state)
        
        self.assertTrue(path.endswith("final_ad.mp4"))
        mock_ffmpeg.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
