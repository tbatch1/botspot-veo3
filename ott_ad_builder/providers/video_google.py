import os
import requests
import json
import time
import google.auth
from google.auth.transport.requests import Request
from urllib.parse import quote
from ..config import config
from .base import VideoProvider
from ..constants.style_profiles import VIDEO_ENHANCEMENTS, VIDEO_NEGATIVE_PROMPTS

class GoogleVideoProvider(VideoProvider):
    """Veo 3.1 Ultra implementation - Highest quality video generation for premium clients."""

    def __init__(self):
        # If the env var exists but is blank (e.g. `GOOGLE_APPLICATION_CREDENTIALS=` in .env),
        # google.auth will attempt to load it and fail. Clear it so ADC can be used instead.
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path is not None and not creds_path.strip():
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

        # Use project from google.auth.default() - ensures we use the project user has access to
        self.credentials, self.project = google.auth.default()
        env_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
        self.project_id = env_project or self.project
        if not self.project_id:
            raise RuntimeError("Google project not detected. Set GOOGLE_CLOUD_PROJECT (or GOOGLE_PROJECT_ID) and ensure Application Default Credentials are configured.")
        self.location = "us-central1"
        model_endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{config.LUMIERE_MODEL}"
        # Per Vertex AI Veo docs: use :predictLongRunning then poll via :fetchPredictOperation.
        self.api_endpoint = f"{model_endpoint}:predictLongRunning"
        self.fetch_endpoint = f"{model_endpoint}:fetchPredictOperation"

        self._current_aesthetic = "photorealistic"  # Default aesthetic
        self._seed: int | None = None
        self._use_last_frame = os.getenv("VEO_USE_LAST_FRAME", "").strip().lower() in ("1", "true", "yes", "on")
        self._generate_audio = os.getenv("VEO_GENERATE_AUDIO", "").strip().lower() in ("1", "true", "yes", "on")
        print(f"[VEO 3.1 ULTRA] Using project: {self.project_id}")

    def _get_token(self):
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def set_aesthetic_style(self, aesthetic: str):
        """Set the aesthetic style for next video generation (adaptive prompting)"""
        self._current_aesthetic = aesthetic
        print(f"[VEO 3.1 ULTRA] Aesthetic style set to: {aesthetic}")

    def set_seed(self, seed: int | None):
        """
        Set a deterministic seed for video generation.

        Best practice: keep the same seed across scenes for consistency.
        Docs: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/best-practice#achieve-character-and-voice-consistency
        """
        if seed is None:
            self._seed = None
            return

        try:
            seed_int = int(seed)
        except (TypeError, ValueError):
            return

        # Veo accepts uint32.
        self._seed = max(0, min(seed_int, 4294967295))

    def set_generate_audio(self, enabled: bool) -> None:
        """
        Enable/disable Veo native audio generation.
        If enabled, Veo may produce music/SFX/dialogue embedded in the clip.
        """
        self._generate_audio = bool(enabled)

    @staticmethod
    def _camera_motion_only(prompt: str) -> str:
        """
        For image-to-video, Veo best practice is to prompt for motion only
        (avoid re-describing the scene/lighting already present in the image).

        If prompt follows our "Camera: ... Action: ... Style: ..." format,
        extract only the Camera segment.
        """
        cleaned = " ".join((prompt or "").split())
        if not cleaned:
            return ""

        lower = cleaned.lower()
        camera_key = "camera:"
        start = lower.find(camera_key)
        if start == -1:
            return cleaned

        start += len(camera_key)
        end = len(cleaned)
        for marker in ("action:", "style:", "mood:"):
            idx = lower.find(marker, start)
            if idx != -1:
                end = min(end, idx)

        camera_segment = cleaned[start:end].strip(" .;")
        return camera_segment or cleaned

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

        # Best practices (image-to-video):
        # - Use a high-quality source image (>=720p recommended).
        # - Prompt for motion only; avoid re-describing the scene/lighting already in the image.
        # Docs: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/best-practice#prompt-for-motion-only
        if image_path:
            enhanced_prompt = self._camera_motion_only(prompt)
        else:
            enhanced_prompt = f"{prompt}. {enhancement}"

        if not enhanced_prompt.strip():
            enhanced_prompt = "Slow dolly-in with subtle parallax; gentle ambient light flicker."

        # Suppress common Veo artifacts (especially for UI shots) via negative prompt.
        # Keep this lightweight and generic so it doesn't fight the image prompt too hard.
        artifact_suppression = (
            "unreadable text, garbled text, gibberish, misspelled text, random letters, subtitles, watermark, "
            "flicker, jitter, warping, morphing, distortion, compression artifacts, low quality"
        )
        negative_prompt = f"{negative_prompt}, {artifact_suppression}"

        instances = [{"prompt": enhanced_prompt}]

        if image_path:
            import base64
            with open(image_path, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode("utf-8")
            image_obj = {
                "bytesBase64Encoded": b64_image,
                "mimeType": "image/png"
            }
            instances[0]["image"] = image_obj
            # Optional stabilization: use the same image as last frame to reduce drift.
            # Enable with VEO_USE_LAST_FRAME=1 in .env if desired.
            if self._use_last_frame:
                instances[0]["lastFrame"] = image_obj

        parameters = {
            "sampleCount": 1,
            "durationSeconds": duration,
            "aspectRatio": "16:9",
            "resolution": "1080p",
            # When enabled, Veo generates native audio embedded in the video clip.
            "generateAudio": bool(self._generate_audio),
            "negativePrompt": negative_prompt,
        }
        if self._seed is not None:
            parameters["seed"] = self._seed

        payload = {
            "instances": instances,
            "parameters": parameters,
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

        print(f"   [VEO 3.1 ULTRA] Polling task...")

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

            # Per Vertex AI Veo docs: poll via fetchPredictOperation.
            op_response = requests.post(self.fetch_endpoint, headers=headers, json={"operationName": operation_name})
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

                # New (Veo docs): response.videos[].{bytesBase64Encoded|gcsUri,mimeType}
                videos = result.get("videos")
                if isinstance(videos, list) and videos:
                    first_video = videos[0] or {}
                    if "bytesBase64Encoded" in first_video:
                        import base64
                        video_data = base64.b64decode(first_video["bytesBase64Encoded"])
                    elif "gcsUri" in first_video:
                        gcs_uri = first_video["gcsUri"]
                        if not isinstance(gcs_uri, str) or not gcs_uri.startswith("gs://"):
                            raise Exception(f"Unsupported gcsUri format: {gcs_uri}")
                        bucket_and_path = gcs_uri[len("gs://"):]
                        if "/" not in bucket_and_path:
                            raise Exception(f"Invalid gcsUri: {gcs_uri}")
                        bucket_name, object_path = bucket_and_path.split("/", 1)
                        object_path_escaped = quote(object_path, safe="")
                        download_url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o/{object_path_escaped}?alt=media"
                        print(f"   [VEO 3.1 ULTRA] Downloading from GCS via JSON API: gs://{bucket_name}/{object_path}")
                        download_response = requests.get(download_url, headers={"Authorization": f"Bearer {token}"})
                        if download_response.status_code != 200:
                            raise Exception(f"Failed to download GCS video ({download_response.status_code}): {download_response.text}")
                        video_data = download_response.content
                    else:
                        raise Exception(f"Unknown Veo video object format: {first_video.keys()}")

                # Legacy fallback: response.predictions[] (older Vertex AI style)
                else:
                    predictions = result.get("predictions", [])
                    if not predictions:
                        raise Exception(f"Unexpected Veo response format (no videos/predictions): {result}")
                    first_pred = predictions[0] or {}
                    if "bytesBase64Encoded" in first_pred:
                        import base64
                        video_data = base64.b64decode(first_pred["bytesBase64Encoded"])
                    elif "videoUri" in first_pred:
                        video_uri = first_pred["videoUri"]
                        print(f"   [VEO 3.1 ULTRA] Downloading video: {video_uri}")
                        download_response = requests.get(video_uri, headers={"Authorization": f"Bearer {token}"})
                        if download_response.status_code != 200:
                            raise Exception(f"Failed to download video ({download_response.status_code}): {download_response.text}")
                        video_data = download_response.content
                    else:
                        raise Exception(f"Unknown legacy video format: {first_pred.keys()}")

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
        return self.generate_video(prompt=prompt, image_path=image_path, duration=duration)

    def generate_video(self, prompt: str, image_path: str = None, duration: int = 4) -> str:
        """Generate a video via Veo using predictLongRunning + fetchPredictOperation polling."""
        operation_name = self.submit_async(image_path=image_path, prompt=prompt, duration=duration)
        return self.poll_task(operation_name=operation_name, prompt=prompt)

    def extend_video(self, video_path: str, prompt: str, extension_seconds: int = 7) -> str:
        """
        Extend an existing video by adding more seconds.
        
        Per Veo 3.1 docs:
        - Each extension adds up to 7 seconds
        - Input video can be extended multiple times
        
        Args:
            video_path: Path to existing video
            prompt: Motion/continuation prompt
            extension_seconds: Seconds to add (default 7)
            
        Returns:
            Path to the extended video file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        import base64
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        instances = [{
            "prompt": prompt,
            "video": {
                "bytesBase64Encoded": video_b64,
                "mimeType": "video/mp4"
            }
        }]
        
        parameters = {
            "sampleCount": 1,
            "extensionDurationSeconds": extension_seconds,
            "aspectRatio": "16:9",
            "resolution": "1080p",
            "generateAudio": bool(self._generate_audio),
        }
        if self._seed is not None:
            parameters["seed"] = self._seed
        
        payload = {"instances": instances, "parameters": parameters}
        
        print(f"[VEO EXTEND] Extending video by {extension_seconds}s...")
        
        response = requests.post(self.api_endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Veo Extend Error: {response.text}")
        
        data = response.json()
        operation_name = data.get("name")
        if not operation_name:
            raise Exception(f"No operation in extend response: {data}")
        
        extended_prompt = f"{prompt}_ext_{int(time.time())}"
        return self.poll_task(operation_name=operation_name, prompt=extended_prompt)

    def generate_long_video(self, prompt: str, image_path: str = None, target_duration: int = 15) -> str:
        """
        Generate a long continuous video using Veo Extend.
        
        Strategy: Generate 8s clip, then extend to reach target.
        
        Args:
            prompt: Visual prompt
            image_path: Optional starting image
            target_duration: Desired duration in seconds
            
        Returns:
            Path to final video
        """
        initial = min(8, target_duration)
        print(f"[VEO LONG] Generating {initial}s initial clip...")
        video_path = self.generate_video(prompt=prompt, image_path=image_path, duration=initial)
        
        current = initial
        max_ext = 3
        
        for i in range(max_ext):
            if current >= target_duration:
                break
            remain = min(7, target_duration - current)
            if remain < 2:
                break
            try:
                print(f"[VEO LONG] Extending +{remain}s...")
                video_path = self.extend_video(video_path, f"Continue: {prompt}", remain)
                current += remain
            except Exception as e:
                print(f"[VEO LONG] Extension failed: {e}")
                break
        
        print(f"[VEO LONG] Final: {current}s")
        return video_path
