"""
Kling AI Video Provider via PiAPI Gateway
Architecture: PiAPI "Host Your Account" ($10/month) + Kling subscription ($6/month)
Uses your Kling subscription credits (660/month) through PiAPI API gateway
"""

import os
import time
import base64
import hashlib
import requests
from typing import Optional
from ..config import config
from .base import VideoProvider


class KlingProvider(VideoProvider):
    """
    Kling AI image-to-video provider using PiAPI gateway.

    Setup:
    1. Kling subscription: $6/month (660 credits)
    2. PiAPI "Host Your Account": $10/month
    3. Connect Kling account in PiAPI dashboard
    4. Get PiAPI API key from dashboard

    Total: $16/month using your own Kling credits
    """

    def __init__(self):
        """Initialize Kling AI provider via PiAPI gateway."""
        self.piapi_key = config.PIAPI_API_KEY
        self.api_url = config.KLING_API_URL  # https://api.piapi.ai
        self.model = config.KLING_MODEL

        if not self.piapi_key:
            print("[WARN]  Warning: PiAPI API key not configured")
            print("   1. Sign up at https://app.piapi.ai")
            print("   2. Subscribe to 'Host Your Account' ($10/month)")
            print("   3. Connect your Kling account in PiAPI dashboard")
            print("   4. Add PIAPI_API_KEY to .env file")
            self.enabled = False
        else:
            self.enabled = True
            print(f"[OK] Kling AI provider initialized via PiAPI (model: {self.model})")

    def _generate_auth_headers(self) -> dict:
        """Generate authentication headers for PiAPI."""
        return {
            "X-API-Key": self.piapi_key,
            "Content-Type": "application/json"
        }

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Convert local image to base64 data URI for API submission."""
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Determine MIME type from file extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')

        return f"data:{mime_type};base64,{image_b64}"

    def _submit_image_to_video_task(self, image_path: str, prompt: str, duration: int = 5) -> Optional[str]:
        """
        Submit image-to-video task to Kling AI API.

        Returns:
            task_id string if successful, None if failed
        """
        print(f"   [Kling] Encoding image to base64...")
        image_data_uri = self._encode_image_to_base64(image_path)

        # Build request payload for image-to-video
        payload = {
            "model_name": self.model,
            "image": image_data_uri,  # Base64 data URI
            "prompt": prompt,
            "duration": str(duration),  # "5" or "10" seconds
            "aspect_ratio": "16:9",  # OTT standard
            "cfg_scale": 0.5,  # Guidance scale (0.0-1.0)
            "mode": "std"  # Standard mode (vs "pro")
        }

        print(f"   [Kling] Submitting image-to-video task...")
        print(f"   [Kling] Prompt: {prompt[:80]}...")
        print(f"   [Kling] Duration: {duration}s")

        try:
            # NOTE: Endpoint path may need adjustment based on actual Kling API docs
            # Common patterns: /api/v1/videos/image2video or /api/tasks/image-to-video
            endpoint = f"{self.api_url}/api/v1/videos/image2video"

            response = requests.post(
                endpoint,
                json=payload,
                headers=self._generate_auth_headers(),
                timeout=30
            )

            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                task_id = result.get("task_id") or result.get("id") or result.get("prediction_id")

                if task_id:
                    print(f"   [Kling] [OK] Task created: {task_id}")
                    return task_id
                else:
                    print(f"   [Kling] ❌ No task_id in response: {result}")
                    return None
            else:
                print(f"   [Kling] ❌ API Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"   [Kling] ❌ Exception during task submission: {e}")
            return None

    def _poll_task_status(self, task_id: str, max_wait_seconds: int = 300, poll_interval: int = 5) -> Optional[dict]:
        """
        Poll Kling AI task status until completion or timeout.

        Returns:
            dict with video_url on success, None on failure
        """
        print(f"   [Kling] Polling task {task_id}...")
        start_time = time.time()
        attempts = 0

        while time.time() - start_time < max_wait_seconds:
            attempts += 1

            try:
                # NOTE: Endpoint path may need adjustment based on actual Kling API docs
                endpoint = f"{self.api_url}/api/v1/tasks/{task_id}"

                response = requests.get(
                    endpoint,
                    headers=self._generate_auth_headers(),
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"   [Kling] [WARN]  Poll attempt {attempts}: Status {response.status_code}")
                    time.sleep(poll_interval)
                    continue

                result = response.json()
                status = result.get("task_status") or result.get("status")

                if status in ["succeed", "completed", "success"]:
                    video_url = result.get("task_result", {}).get("video_url") or result.get("video_url") or result.get("output")

                    if video_url:
                        elapsed = time.time() - start_time
                        print(f"   [Kling] [OK] Video ready after {elapsed:.1f}s ({attempts} polls)")
                        return {"video_url": video_url, "result": result}
                    else:
                        print(f"   [Kling] ❌ Task succeeded but no video_url in response")
                        return None

                elif status in ["failed", "error"]:
                    error_msg = result.get("error") or result.get("message") or "Unknown error"
                    print(f"   [Kling] ❌ Task failed: {error_msg}")
                    return None

                elif status in ["submitted", "processing", "pending", "in_progress"]:
                    print(f"   [Kling] ⏳ Status: {status} (attempt {attempts})")
                    time.sleep(poll_interval)

                else:
                    print(f"   [Kling] [WARN]  Unknown status: {status}")
                    time.sleep(poll_interval)

            except Exception as e:
                print(f"   [Kling] [WARN]  Poll error: {e}")
                time.sleep(poll_interval)

        print(f"   [Kling] ❌ Timeout after {max_wait_seconds}s")
        return None

    def _download_video(self, video_url: str, output_path: str) -> bool:
        """Download video from Kling CDN to local file."""
        print(f"   [Kling] Downloading video...")

        try:
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"   [Kling] [OK] Downloaded: {file_size:.2f} MB")
            return True

        except Exception as e:
            print(f"   [Kling] ❌ Download failed: {e}")
            return False

    def animate(self, image_path: str, prompt: str, duration: int = 5) -> str:
        """
        Main method: Animate an image using Kling AI image-to-video.

        Args:
            image_path: Path to local image file
            prompt: Motion/camera movement description
            duration: Video duration in seconds (5 or 10)

        Returns:
            Path to generated video file
        """
        if not self.enabled:
            raise Exception("Kling AI provider not configured. Check .env for API credentials.")

        print(f"\n[VIDEO] [Kling AI] Starting image-to-video animation...")

        # 1. Submit task
        task_id = self._submit_image_to_video_task(image_path, prompt, duration)
        if not task_id:
            raise Exception("Failed to submit Kling AI task")

        # 2. Poll for completion
        result = self._poll_task_status(task_id, max_wait_seconds=300, poll_interval=5)
        if not result or "video_url" not in result:
            raise Exception("Kling AI task failed or timed out")

        # 3. Download video
        video_url = result["video_url"]

        # Generate filename from prompt hash
        filename = hashlib.md5(prompt.encode()).hexdigest() + ".mp4"
        output_dir = os.path.join(config.ASSETS_DIR, "videos")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        success = self._download_video(video_url, output_path)
        if not success:
            raise Exception("Failed to download video from Kling AI")

        print(f"[OK] [Kling AI] Animation complete: {output_path}\n")
        return output_path
