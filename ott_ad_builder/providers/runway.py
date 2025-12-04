import os
import requests
import time
import json
from ..config import config
from .base import VideoProvider

class RunwayProvider(VideoProvider):
    """Runway Gen-3 Alpha Turbo implementation."""
    
    def __init__(self):
        self.api_key = config.RUNWAY_API_KEY
        # Official Runway API base URL from docs
        self.base_url = "https://api.dev.runwayml.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",  # Official auth format
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"  # Official API version
        }

    def animate(self, image_path: str, prompt: str, duration: int = 5) -> str:
        """
        Animates an image using Runway Gen-3 Turbo.
        """
        # 1. Upload Image (if not a URL)
        # For simplicity, we assume we need to upload or use a data URI.
        # Gen-3 supports data URIs for small images, or we upload to assets.
        # Let's use Data URI for simplicity if file is small, else upload.
        # But Runway recommends assets for larger files.
        # Let's assume we use a data URI for now as it's easier to implement without extra upload step.
        
        import base64
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        
        data_uri = f"data:image/png;base64,{img_data}"
        
        # 2. Submit Job - Official Runway Gen-3 API payload from docs
        payload = {
            "model": config.RUNWAY_MODEL,  # "gen3a_turbo"
            "promptImage": data_uri,
            "promptText": prompt,
            "ratio": "1280:768",  # Official format - landscape 16:9 (from API: must be 768:1280 or 1280:768)
            "duration": duration  # 2-10 seconds
        }

        # Official endpoint from Runway API docs
        endpoint = f"{self.base_url}/v1/image_to_video"

        print(f"   [RUNWAY] Submitting to: {endpoint}")
        response = requests.post(endpoint, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Runway API Error ({response.status_code}): {response.text}")
            
        task_id = response.json()["id"]
        print(f"   Runway Task ID: {task_id}")
        
        # 3. Poll Status - Official tasks endpoint
        video_url = None
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            time.sleep(5)
            status_resp = requests.get(f"{self.base_url}/v1/tasks/{task_id}", headers=self.headers)
            if status_resp.status_code != 200:
                print(f"   Polling Error: {status_resp.text}")
                continue
                
            status_data = status_resp.json()
            status = status_data.get("status")

            print(f"   [RUNWAY] Status: {status} ({attempt + 1}/{max_attempts})")

            if status == "SUCCEEDED":
                video_url = status_data["output"][0]  # Array of URLs
                break
            elif status == "FAILED":
                error = status_data.get("failureCode", "Unknown error")
                raise Exception(f"Runway generation failed: {error}")
            elif status in ["PENDING", "RUNNING"]:
                continue
            else:
                raise Exception(f"Unknown status: {status}")
        else:
            raise Exception(f"Runway task timed out after {max_attempts * 5} seconds")
        
        # 4. Download Video
        if not video_url:
            raise Exception("No video URL returned")
            
        video_resp = requests.get(video_url)
        
        import hashlib
        filename = hashlib.md5(prompt.encode()).hexdigest() + ".mp4"
        filepath = os.path.join(config.ASSETS_DIR, "videos", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "wb") as f:
            f.write(video_resp.content)
            
        return filepath
