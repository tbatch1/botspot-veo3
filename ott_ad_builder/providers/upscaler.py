
import os
import replicate
import requests
from ..config import config

class VideoUpscaler:
    """
    Upscales video to 4K using Topaz Video AI models on Replicate.
    """
    
    def __init__(self):
        self.client = replicate.Client(api_token=config.REPLICATE_API_TOKEN)
        # Official Topaz Video AI model on Replicate
        # We use the deployment alias
        self.model = "topazlabs/video-upscale:3f23e3c466b721e06f157297e68e42f61882d93e1b782987179044M27850a581" 
        # Actually better to use the owner/name format if version ID is unstable, 
        # but Replicate client likes explicit versions or owner/name.
        # "topazlabs/video-upscale" is the official one.
        self.model_ref = "topazlabs/video-upscale"

    def upscale(self, input_path: str, scale_factor: int = 2) -> str:
        """
        Upscales the input video.
        
        Args:
            input_path: Local path to the 1080p video.
            scale_factor: 2 (for 4K if input is 1080p).
            
        Returns:
            Path to the upscaled 4K video.
        """
        if not os.path.exists(input_path):
            raise Exception(f"Input file not found: {input_path}")
            
        print(f"[UPSCALE] Sending video to Topaz Video AI (Replicate)...")
        print(f"          Input: {input_path}")
        print(f"          Scale: {scale_factor}x")
        
        try:
            # Replicate needs a file handle or URL. We use file handle.
            with open(input_path, "rb") as video_file:
                output = self.client.run(
                    self.model_ref,
                    input={
                        "video": video_file,
                        "scale_factor": scale_factor,
                        "model": "proteus", # 'proteus' is best for general enhancement
                        "output_format": "mp4"
                    }
                )
            
            # Output is a URL
            video_url = str(output)
            print(f"[UPSCALE] Received URL: {video_url[:60]}...")
            
            # Download
            response = requests.get(video_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download upscaled video: {response.status_code}")
                
            filename = f"upscaled_{os.path.basename(input_path)}"
            output_path = os.path.join(config.OUTPUT_DIR, filename)
            
            with open(output_path, "wb") as f:
                f.write(response.content)
                
            print(f"[UPSCALE] Saved 4K Master: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[ERROR] Upscaling failed: {e}")
            return input_path # Fallback to original
