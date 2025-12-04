import os
import requests
import json
import google.auth
from google.auth.transport.requests import Request
from ..config import config
from .base import ImageProvider

class ImagenProvider(ImageProvider):
    """Nano Banana Pro (Gemini 3 Pro Image) implementation for Visuals."""

    def __init__(self):
        self.project_id = "876386907816"  # Same project as video (gen-lang-client-0590133327)
        self.location = "us-central1"
        # Nano Banana Pro uses different endpoint format
        self.model_id = config.IMAGEN_MODEL  # gemini-3-pro-image-preview
        self.api_endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_id}:predict"

        # Get credentials
        self.credentials, self.project = google.auth.default()
        
    def _get_token(self):
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str:
        """
        Generates an image using Nano Banana Pro (Gemini 3 Pro Image) REST API.
        Supports up to 4K resolution with enhanced text rendering and creative controls.
        Returns the path to the saved image.
        """
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Nano Banana Pro enhanced parameters
        payload = {
            "instances": [
                {
                    "prompt": prompt,
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
                "addWatermark": False,  # Nano Banana Pro supports watermark-free images
                "outputMimeType": "image/png",  # High quality PNG output
                # Nano Banana Pro supports additional creative controls
                "personGeneration": "allow_all",  # Allow person generation
            }
        }

        print(f"[NANO BANANA PRO] Generating image: {prompt[:60]}...")
        response = requests.post(self.api_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Nano Banana Pro API Error: {response.text}")
            
        # Parse response
        data = response.json()
        try:
            # Standard Vertex AI format for Imagen
            predictions = data.get("predictions", [])
            if not predictions:
                raise Exception(f"No predictions returned: {data}")
                
            first_pred = predictions[0]
            
            # Handle different response shapes
            if isinstance(first_pred, str):
                b64_data = first_pred
            elif isinstance(first_pred, dict):
                if "bytesBase64Encoded" in first_pred:
                    b64_data = first_pred["bytesBase64Encoded"]
                elif "image" in first_pred: # Some versions
                    b64_data = first_pred["image"]
                else:
                     raise Exception(f"Unknown prediction format: {first_pred.keys()}")
            else:
                 raise Exception(f"Unexpected prediction type: {type(first_pred)}")

        except Exception as e:
             raise Exception(f"Failed to parse Nano Banana Pro response: {e}. Raw data: {data}")

        # Save to file
        import base64
        image_data = base64.b64decode(b64_data)

        # Create filename hash
        import hashlib
        filename = hashlib.md5(prompt.encode()).hexdigest() + ".png"
        filepath = os.path.join(config.ASSETS_DIR, "images", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(image_data)

        print(f"[NANO BANANA PRO] ✅ Generated: {filepath}")
        return filepath
