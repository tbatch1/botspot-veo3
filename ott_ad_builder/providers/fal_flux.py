"""
Fal.ai Flux 1.1 Pro Provider
The premium image generation provider for OTT Ads.

Key Advantages over Replicate:
- LoRA Training API for "Product Lock" (maintain product/brand consistency)
- 2-4 second generation (vs 8-12 on Replicate)
- Better text rendering (no spelling errors)
- Native 16:9 OTT Ad support

Docs: https://docs.fluxapi.ai/
"""

import os
from ..config import config
from .base import ImageProvider

# CRITICAL: Set FAL_KEY before importing fal_client
if config.FAL_API_KEY:
    os.environ["FAL_KEY"] = config.FAL_API_KEY

import fal_client


class FalFluxProvider(ImageProvider):
    """
    Fal.ai Flux 1.1 Pro implementation.
    Premium provider with LoRA support for product consistency.
    """
    
    def __init__(self):
        # Set API key from config
        if config.FAL_API_KEY:
            os.environ["FAL_KEY"] = config.FAL_API_KEY
            print("[FAL.AI] Flux 1.1 Pro initialized (LoRA-capable)")
        else:
            print("[FAL.AI] Warning: FAL_API_KEY not set")
        
        self.model_id = "fal-ai/flux-pro/v1.1"  # Correct model ID per Fal.ai docs
        self._current_lora = None  # For product lock
    
    def set_product_lora(self, lora_path: str, scale: float = 1.0):
        """
        Set a trained LoRA for product consistency.
        Use this to "lock" a client's product/logo.
        
        Args:
            lora_path: URL to the trained LoRA model
            scale: How strongly to apply the LoRA (0.0-1.0)
        """
        self._current_lora = {"path": lora_path, "scale": scale}
        print(f"[FAL.AI] Product LoRA set: {lora_path[:50]}... (scale: {scale})")
    
    def clear_lora(self):
        """Clear the current LoRA."""
        self._current_lora = None
        print("[FAL.AI] Product LoRA cleared")
    
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        seed: int = None,
        image_input: str = None
    ) -> str:
        """
        Generate an image using Fal.ai Flux 1.1 Pro.
        
        Args:
            prompt: The image description
            aspect_ratio: Image dimensions (e.g., "16:9", "1:1", "9:16")
            seed: Optional seed for reproducibility
            image_input: Optional input image for image-to-image
        
        Returns:
            Path to the saved image
        """
        print(f"[FAL.AI] Generating: {prompt[:60]}...")
        
        # Map aspect ratio to Fal format
        aspect_map = {
            "16:9": "landscape_16_9",
            "9:16": "portrait_16_9", 
            "1:1": "square",
            "4:3": "landscape_4_3",
            "3:4": "portrait_4_3"
        }
        fal_aspect = aspect_map.get(aspect_ratio, "landscape_16_9")
        
        # Build arguments
        arguments = {
            "prompt": prompt,
            "image_size": fal_aspect,
            "num_images": 1,
            "safety_tolerance": "2",  # Allow commercially viable creative freedom
            "output_format": "png"
        }
        
        # Add seed if provided
        if seed is not None:
            arguments["seed"] = seed
        
        # Add LoRA if set (Product Lock feature)
        if self._current_lora:
            arguments["loras"] = [self._current_lora]
            print(f"[FAL.AI] Using Product LoRA for consistency")
        
        # Handle image-to-image
        if image_input and os.path.exists(image_input):
            # Fal supports image input via URL or base64
            import base64
            with open(image_input, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            arguments["image"] = f"data:image/png;base64,{image_data}"
            arguments["strength"] = 0.85  # Prompt strength
            print(f"[FAL.AI] Image-to-Image mode: {os.path.basename(image_input)}")
        
        try:
            # Submit and wait for result
            handler = fal_client.submit(self.model_id, arguments=arguments)
            result = handler.get()
            
            # Get the image URL
            image_url = result["images"][0]["url"]
            
            # Download the image
            import requests
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download image: {response.status_code}")
            
            image_data = response.content
            
            # Save to file
            import hashlib
            filename = hashlib.md5(prompt.encode()).hexdigest() + ".png"
            filepath = os.path.join(config.ASSETS_DIR, "images", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            print(f"[FAL.AI] [OK] Generated: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[FAL.AI] Error: {e}")
            raise e
    
    def train_product_lora(
        self,
        images: list[str],
        trigger_word: str,
        product_name: str = None,
        is_style: bool = False,
        steps: int = 1000
    ) -> str:
        """
        Train a LoRA model for a specific product.
        This is the "Product Lock" feature for brand consistency.
        
        Cost: ~$2 per training run (scales with steps)
        Time: ~5 minutes
        
        Args:
            images: List of 5-10 product image paths (high-res recommended)
            trigger_word: Unique word that triggers the product (e.g., "TXCL_BOTTLE")
            product_name: Human-readable product name
            is_style: True for style training, False for product/character
            steps: Training steps (default 1000, more = better but more expensive)
        
        Returns:
            The LoRA path URL to use with set_product_lora()
        """
        import zipfile
        import tempfile
        import requests
        
        print(f"[FAL.AI] Training Product LoRA: {product_name or trigger_word}")
        print(f"[FAL.AI] Using {len(images)} training images (~$2 cost)...")
        
        # Validate images
        valid_images = [img for img in images if os.path.exists(img)]
        if len(valid_images) < 3:
            raise ValueError(f"Need at least 3 product images for LoRA training. Found {len(valid_images)}.")
        
        # Create ZIP file from images
        print(f"[FAL.AI] Creating training ZIP from {len(valid_images)} images...")
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            zip_path = tmp_zip.name
            
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, img_path in enumerate(valid_images):
                # Use consistent naming: image_01.jpg, image_02.jpg, etc.
                ext = os.path.splitext(img_path)[1] or '.jpg'
                zf.write(img_path, f"image_{i+1:02d}{ext}")
        
        # Upload ZIP to Fal's file storage
        print(f"[FAL.AI] Uploading training data...")
        try:
            zip_url = fal_client.upload_file(zip_path)
            print(f"[FAL.AI] Training data uploaded: {zip_url[:60]}...")
        finally:
            # Clean up temp file
            os.unlink(zip_path)
        
        # Submit training job
        print(f"[FAL.AI] Starting LoRA training (trigger: '{trigger_word}', steps: {steps})...")
        try:
            handler = fal_client.submit(
                "fal-ai/flux-lora-fast-training",
                arguments={
                    "images_data_url": zip_url,
                    "trigger_word": trigger_word,
                    "steps": steps,
                    "is_style": is_style
                }
            )
            
            # Wait for training to complete (can take 5-10 minutes)
            print(f"[FAL.AI] Training in progress... (this may take 5-10 minutes)")
            result = handler.get()
            
            # Get the trained LoRA URL
            lora_path = result["diffusers_lora_file"]["url"]
            
            print(f"[FAL.AI] [OK] Product LoRA trained successfully!")
            print(f"[FAL.AI] LoRA URL: {lora_path[:80]}...")
            
            return lora_path
            
        except Exception as e:
            print(f"[FAL.AI] Training error: {e}")
            raise e

