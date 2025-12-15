import os
import replicate
from ..config import config
from .base import ImageProvider

class FluxProvider(ImageProvider):
    """Flux 1.1 Pro implementation for High-Fidelity Visuals."""

    def __init__(self):
        self.client = replicate.Client(api_token=config.REPLICATE_API_TOKEN)
        self.model_id = config.FLUX_MODEL

    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", seed: int = None, image_input: str = None) -> str:
        """
        Generates an image using Flux 1.1 Pro (Text-to-Image) or Flux Dev (Image-to-Image).
        Returns the path to the saved image.
        """
        print(f"[FLUX] Generating image: {prompt[:60]}... Seed: {seed}")
        
        input_args = {
            "prompt": prompt,
            "output_format": "png",
            "output_quality": 100,
            "safety_tolerance": 5  # Allow creative freedom
        }

        # If image input is provided, use Flux Dev for Image-to-Image
        if image_input and os.path.exists(image_input):
            print(f"[FLUX] Using Image Input: {os.path.basename(image_input)} (Switching to flux-dev)")
            # Use Flux Dev for Image-to-Image capability
            # Note: Flux 1.1 Pro is T2I only. Dev supports I2I.
            model_id = "black-forest-labs/flux-dev"
            
            # Open file as binary
            input_args["image"] = open(image_input, "rb")
            input_args["prompt_strength"] = 0.85 # Strong adherence to prompt, but keep structure
            # Flux Dev doesn't strictly use aspect_ratio arg when image is provided, it uses image dimensions
        else:
            # Text-to-Image (Standard)
            print(f"[FLUX] Text-to-Image Mode (Flux 1.1 Pro)")
            model_id = self.model_id # Default to Config's 1.1 Pro
            input_args["aspect_ratio"] = aspect_ratio
        
        if seed is not None:
             input_args["seed"] = seed

        try:
            output = self.client.run(
                model_id,
                input=input_args
            )
            
            # Output is usually a URL or a file object (depending on client version)
            # Replicate python client usually returns a URL or list of URLs
            image_url = str(output)
            
            # Download the image
            import requests
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download Flux image: {response.status_code}")
            
            image_data = response.content

            # Save to file
            import hashlib
            filename = hashlib.md5(prompt.encode()).hexdigest() + ".png"
            filepath = os.path.join(config.ASSETS_DIR, "images", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "wb") as f:
                f.write(image_data)

            print(f"[FLUX PRO] [OK] Generated: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[FLUX PRO] Error: {e}")
            raise e
