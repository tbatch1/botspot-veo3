import os
import requests
import json
import time
import google.auth
from google.auth.transport.requests import Request
from ..config import config
from .base import VideoProvider

class GoogleVideoProvider(VideoProvider):
    """Google Veo (Lumiere) implementation for Video."""
    
    def __init__(self):
        self.project_id = "876386907816"
        self.location = "us-central1"
        # Fixed: Use :predictLongRunning for Veo video generation
        self.api_endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{config.LUMIERE_MODEL}:predictLongRunning"

        self.credentials, self.project = google.auth.default()
        
    def _get_token(self):
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def animate(self, image_path: str, prompt: str, duration: int = 5) -> str:
        """Satisfy VideoProvider interface."""
        return self.generate_video(prompt, image_path)

    def generate_video(self, prompt: str, image_path: str = None) -> str:
        """
        Generates a video using Google Veo (via Vertex AI).
        """
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Construct payload for Veo
        # Note: Actual schema may vary as it's in preview, using standard generative video schema
        
        # Enhance prompt for cinematic quality
        enhanced_prompt = f"{prompt}, cinematic motion, 4k, high fidelity, stabilized, smooth movement, photorealistic"
        
        instances = [
            { "prompt": enhanced_prompt }
        ]
        
        if image_path:
            # If image-to-video is supported
            import base64
            with open(image_path, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode("utf-8")
            # Fixed: Add required mimeType field
            instances[0]["image"] = {
                "bytesBase64Encoded": b64_image,
                "mimeType": "image/png"
            }

        payload = {
            "instances": instances,
            "parameters": {
                "sampleCount": 1,
                "durationSeconds": 4,  # Fixed: Veo 3 requires 4, 6, or 8 seconds
                "aspectRatio": "16:9",
                "resolution": "1080p",  # OTT broadcast quality
                "generateAudio": True  # Fixed: Required for Veo 3 models
            }
        }
        
        print(f"Generating video with Google Veo: {prompt[:50]}...")
        
        response = requests.post(self.api_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Google Veo API Error: {response.text}")

        data = response.json()

        # Veo uses long-running operations - poll until complete
        operation_name = data.get("name")
        if not operation_name:
            raise Exception(f"No operation name in response: {data}")

        print(f"Veo operation started: {operation_name.split('/')[-1][:16]}...")

        # Poll operation until complete (max 5 minutes)
        operation_url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_name}"
        max_attempts = 60  # 5 minutes (5 second intervals)

        for attempt in range(max_attempts):
            time.sleep(5)  # Wait 5 seconds between polls

            op_response = requests.get(operation_url, headers=headers)
            if op_response.status_code != 200:
                raise Exception(f"Operation polling failed: {op_response.text}")

            op_data = op_response.json()

            # Check if operation is done
            if op_data.get("done"):
                print(f"Veo operation completed!")

                # Check for errors
                if "error" in op_data:
                    raise Exception(f"Veo operation failed: {op_data['error']}")

                # Extract result
                result = op_data.get("response", {})
                predictions = result.get("predictions", [])

                if not predictions:
                    raise Exception(f"No predictions in completed operation: {result}")

                first_pred = predictions[0]
                break
        else:
            raise Exception(f"Operation timed out after {max_attempts * 5} seconds")

        # Continue with existing video extraction logic
        try:
            
            # Check for video bytes or URI
            if "bytesBase64Encoded" in first_pred:
                b64_data = first_pred["bytesBase64Encoded"]
                import base64
                video_data = base64.b64decode(b64_data)
            elif "videoUri" in first_pred:
                # Download from GCS URI
                video_uri = first_pred["videoUri"]
                print(f"Downloading video from GCS: {video_uri}")

                # Download video from GCS URI
                download_response = requests.get(video_uri)
                if download_response.status_code != 200:
                    raise Exception(f"Failed to download video from GCS: {download_response.status_code}")

                video_data = download_response.content
            else:
                 # Fallback for now if we can't guess the schema
                 raise Exception(f"Unknown video format: {first_pred.keys()}")

            # Save to file
            import hashlib
            filename = hashlib.md5(prompt.encode()).hexdigest() + ".mp4"
            filepath = os.path.join(config.ASSETS_DIR, "videos", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(video_data)
                
            return filepath

        except Exception as e:
             raise Exception(f"Failed to parse Veo response: {e}. Raw data: {data}")
