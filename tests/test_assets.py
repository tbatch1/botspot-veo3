import unittest
import sys
from unittest.mock import MagicMock, patch

# Mock dependencies BEFORE importing providers
sys.modules["elevenlabs"] = MagicMock()
sys.modules["elevenlabs.client"] = MagicMock()
sys.modules["google.auth"] = MagicMock()
sys.modules["google.auth.transport.requests"] = MagicMock()

# Setup specific attributes on mocks
sys.modules["elevenlabs"].save = MagicMock()

# Now import providers
from ott_ad_builder.providers.imagen import ImagenProvider
from ott_ad_builder.providers.elevenlabs import ElevenLabsProvider

class TestAssetProviders(unittest.TestCase):
    
    @patch("ott_ad_builder.providers.imagen.requests.post")
    @patch("ott_ad_builder.providers.imagen.google.auth.default")
    def test_imagen_generate(self, mock_auth, mock_post):
        # Mock Auth
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.token = "test_token"
        mock_auth.return_value = (mock_creds, "test_project")
        
        # Mock API Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Mock base64 of a tiny 1x1 png
        b64_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        mock_response.json.return_value = {
            "predictions": [{"bytesBase64Encoded": b64_img}]
        }
        mock_post.return_value = mock_response
        
        provider = ImagenProvider()
        path = provider.generate_image("Test Prompt")
        
        self.assertTrue(path.endswith(".png"))
        
    @patch("ott_ad_builder.providers.elevenlabs.ElevenLabs")
    @patch("ott_ad_builder.providers.elevenlabs.save")
    def test_elevenlabs_tts(self, mock_save, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = b"audio_data"
        
        provider = ElevenLabsProvider()
        path = provider.generate_speech("Hello world")
        
        self.assertTrue(path.endswith(".mp3"))
        mock_client.generate.assert_called_once()

if __name__ == '__main__':
    unittest.main()
