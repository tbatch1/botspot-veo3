import unittest
from unittest.mock import MagicMock, patch, mock_open
from ott_ad_builder.providers.runway import RunwayProvider

class TestMotionProviders(unittest.TestCase):
    
    @patch("ott_ad_builder.providers.runway.requests")
    @patch("builtins.open", new_callable=mock_open, read_data=b"image_data")
    def test_runway_animate(self, mock_file, mock_requests):
        # Mock Submit Response
        mock_submit_resp = MagicMock()
        mock_submit_resp.status_code = 200
        mock_submit_resp.json.return_value = {"id": "task_123"}
        
        # Mock Status Response (Success)
        mock_status_resp = MagicMock()
        mock_status_resp.status_code = 200
        mock_status_resp.json.return_value = {
            "status": "SUCCEEDED",
            "output": ["http://example.com/video.mp4"]
        }
        
        # Mock Download Response
        mock_download_resp = MagicMock()
        mock_download_resp.content = b"video_bytes"
        
        # Configure side_effect for requests calls
        # 1. POST submit
        # 2. GET status
        # 3. GET download
        mock_requests.post.return_value = mock_submit_resp
        mock_requests.get.side_effect = [mock_status_resp, mock_download_resp]
        
        provider = RunwayProvider()
        # We patch time.sleep to speed up test
        with patch("time.sleep", return_value=None):
            path = provider.animate("test.png", "Motion Prompt")
            
        self.assertTrue(path.endswith(".mp4"))
        self.assertEqual(mock_requests.post.call_count, 1)

if __name__ == '__main__':
    unittest.main()
