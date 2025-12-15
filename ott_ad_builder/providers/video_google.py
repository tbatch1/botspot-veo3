import os
import requests
import json
import time
import google.auth
from google.auth.transport.requests import Request
from ..config import config
from .base import VideoProvider
from ..constants.style_profiles import VIDEO_ENHANCEMENTS, VIDEO_NEGATIVE_PROMPTS

class GoogleVideoProvider(VideoProvider):
    """Veo 3.1 Ultra implementation - Highest quality video generation for premium clients."""

    def __init__(self):
        # Use project from google.auth.default() - ensures we use the project user has access to
        self.credentials, self.project = google.auth.default()
        self.project_id = self.project or "876386907816"  # Fallback to hardcoded if not found
        self.location = "us-central1"
        # Fixed: Use :predictLongRunning for Veo video generation
        self.api_endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{config.LUMIERE_MODEL}:predictLongRunning"

        self._current_aesthetic = "photorealistic"  # Default aesthetic
        print(f"[VEO 3.1 ULTRA] Using project: {self.project_id}")

    def _get_token(self):
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def set_aesthetic_style(self, aesthetic: str):
        """Set the aesthetic style for next video generation (adaptive prompting)"""
        self._current_aesthetic = aesthetic
        print(f"[VEO 3.1 ULTRA] Aesthetic style set to: {aesthetic}")

    def submit_async(self, image_path: str, prompt: str, duration: int = 4) -> str:
        """
        Submit video generation task and return operation_name immediately.
        PREMIUM QUALITY: Enables parallel video generation with Veo 3.1 Ultra.

        Args:
            image_path: Path to input image
            prompt: Motion/action prompt
            duration: Video duration in seconds (4, 6, or 8)

        Returns:
            operation_name for polling
        """
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # ADAPTIVE: Apply style-specific enhancement based on detected aesthetic
        aesthetic_style = self._current_aesthetic
        enhancement = VIDEO_ENHANCEMENTS.get(aesthetic_style, VIDEO_ENHANCEMENTS['photorealistic'])
        negative_prompt = VIDEO_NEGATIVE_PROMPTS.get(aesthetic_style, VIDEO_NEGATIVE_PROMPTS['photorealistic'])

        enhanced_prompt = f"{prompt}. {enhancement}"

        instances = [{"prompt": enhanced_prompt}]

        if image_path:
            import base64
            with open(image_path, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode("utf-8")
            instances[0]["image"] = {
                "bytesBase64Encoded": b64_image,
                "mimeType": "image/png"
            }

        payload = {
            "instances": instances,
            "parameters": {
                "sampleCount": 1,
                "durationSeconds": duration,
                "aspectRatio": "16:9",
                "resolution": "1080p",
                "generateAudio": True,
                "negativePrompt": negative_prompt  # Veo 3.1 supports negative prompts
            }
        }

        print(f"[VEO 3.1 ULTRA] Submitting video ({aesthetic_style} style): {prompt[:50]}...")

        response = requests.post(self.api_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Veo 3.1 Ultra API Error: {response.text}")

        data = response.json()
        operation_name = data.get("name")
        if not operation_name:
            raise Exception(f"No operation name in response: {data}")

        print(f"[VEO 3.1 ULTRA] Task submitted: {operation_name}")
        return operation_name

    def poll_task(self, operation_name: str, prompt: str, timeout_seconds: int = 900) -> str:
        """
        Poll a specific Veo task until completion or timeout.
        PREMIUM QUALITY: Uses exponential backoff to reduce API calls.

        Args:
            operation_name: Operation ID from submit_async()
            prompt: Original prompt (for filename hashing)
            timeout_seconds: Max wait time (default: 600s = 10 minutes)

        Returns:
            Local video file path on success
        """
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Normalize operation name for polling
        if "operations/" in operation_name:
            op_id = operation_name.split("operations/")[-1]
            operation_path = f"projects/{self.project_id}/locations/{self.location}/operations/{op_id}"
            operation_url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_path}"
        else:
            operation_url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_name}"

        print(f"   [VEO 3.1 ULTRA] Polling task: {op_id[:16]}...")

        # Exponential backoff intervals: 5s, 5s, 10s, 10s, 15s, 15s, 20s, 20s, 30s, 30s
        poll_intervals = [5, 5, 10, 10, 15, 15, 20, 20, 30, 30]

        attempt = 0
        elapsed = 0

        while elapsed < timeout_seconds:
            # Get interval (use last interval if we exceed list)
            interval = poll_intervals[min(attempt, len(poll_intervals) - 1)]
            time.sleep(interval)
            elapsed += interval
            attempt += 1

            op_response = requests.get(operation_url, headers=headers)
            if op_response.status_code != 200:
                if op_response.status_code == 404 and attempt < 3:
                    print(f"   [VEO 3.1 ULTRA] Warning: 404 polling operation (attempt {attempt}). Retrying...")
                    continue
                raise Exception(f"Operation polling failed ({op_response.status_code}): {op_response.text}")

            op_data = op_response.json()

            # Check if operation is done
            if op_data.get("done"):
                print(f"   [VEO 3.1 ULTRA] Task completed in {elapsed}s!")

                # Check for errors
                if "error" in op_data:
                    raise Exception(f"Veo operation failed: {op_data['error']}")

                # Extract result
                result = op_data.get("response", {})
                predictions = result.get("predictions", [])

                if not predictions:
                    raise Exception(f"No predictions in completed operation: {result}")

                first_pred = predictions[0]

                # Extract video data
                if "bytesBase64Encoded" in first_pred:
                    import base64
                    video_data = base64.b64decode(first_pred["bytesBase64Encoded"])
                elif "videoUri" in first_pred:
                    video_uri = first_pred["videoUri"]
                    print(f"   [VEO 3.1 ULTRA] Downloading from GCS: {video_uri}")
                    download_response = requests.get(video_uri)
                    if download_response.status_code != 200:
                        raise Exception(f"Failed to download video from GCS: {download_response.status_code}")
                    video_data = download_response.content
                else:
                    raise Exception(f"Unknown video format: {first_pred.keys()}")

                # Save to file
                import hashlib
                filename = hashlib.md5(prompt.encode()).hexdigest() + ".mp4"
                filepath = os.path.join(config.ASSETS_DIR, "videos", filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                with open(filepath, "wb") as f:
                    f.write(video_data)

                print(f"   [VEO 3.1 ULTRA] [OK] Saved video: {filepath}")
                return filepath

        raise Exception(f"Veo task timed out after {elapsed}s")

    def animate(self, image_path: str, prompt: str, duration: int = 4) -> str:
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
        
        # CRITICAL: Apply strategist's "Real Cinema" visual language
        # Avoid AI slop triggers: "4k", "smooth", "photorealistic", "high fidelity"
        # Use authentic film photography vocabulary instead
        enhanced_prompt = f"""
{prompt}. 
Shot on Arri Alexa with Cooke S4 prime lenses, natural film grain texture.
Subtle halation on highlights, organic sensor noise, motivated camera movement.
Natural skin texture with visible pores, authentic lighting with gentle shadows.
Slight chromatic aberration on edges, 35mm depth of field characteristics.
"""
        
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

        print(f"Veo operation started: {operation_name}...")

        # FIX: Normalize operation name for polling
        # Sometimes it returns 'projects/.../models/.../operations/UUID' which is invalid for polling
        # We need 'projects/.../locations/.../operations/UUID'
        if "operations/" in operation_name:
            op_id = operation_name.split("operations/")[-1]
            # Reconstruct standard operations path
            operation_path = f"projects/{self.project_id}/locations/{self.location}/operations/{op_id}"
            operation_url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_path}"
        else:
            # Fallback for standard format
            operation_url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_name}"

        print(f"   [VEO] Polling URL: {operation_url}")

        max_attempts = 120  # increased wait time for Veo (up to 10 mins)
        
        for attempt in range(max_attempts):
            time.sleep(5)  # Wait 5 seconds between polls

            op_response = requests.get(operation_url, headers=headers)
            if op_response.status_code != 200:
                # If 404, try print error but don't crash immediately unless it's persistent
                if op_response.status_code == 404 and attempt < 3:
                     print(f"   [VEO] Warning: 404 polling operation (attempt {attempt}). Retrying...")
                     continue
                raise Exception(f"Operation polling failed ({op_response.status_code}): {op_response.text}")

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
