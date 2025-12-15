"""
Nano Banana Provider - Gemini 2.5 Flash Image
Image generation and CONTENT EDITING using Google's Gemini 2.5 Flash Image model.
Code name: "Nano Banana"

IMPORTANT DISTINCTION:
- Nano Banana = CREATIVE EDITOR (can fix content like 6-fingered hands, add snow, change lighting)
  WARNING: May hallucinate/change details! Use for content fixes only.
- Topaz = TECHNICAL UPSCALER (increases resolution without changing content)
  Use for delivery standards (1080p → 4K)

Use Cases:
- Fix anatomical issues (6 fingers → 5 fingers)
- Add effects (add snow, change time of day)
- Content corrections (wrong object, bad composition)

DO NOT USE FOR:
- Simple upscaling (use Topaz instead)
- Quality enhancement without content change (use Topaz)
"""

import os
import base64
import time
from typing import Optional
from ..config import config

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("[NANO_BANANA] google-genai not installed. Run: pip install google-genai")


class NanoBananaProvider:
    """
    Gemini 2.5 Flash Image provider for CONTENT FIXES and CREATIVE EDITS.
    
    ⚠️ WARNING: This model HALLUCINATES. It may add/change details.
    Only use when you need to FIX CONTENT (e.g., wrong fingers, missing objects).
    
    For technical upscaling without content change, use Topaz instead.
    
    Capabilities:
    - Fix anatomical issues (hands, faces)
    - Add/remove elements
    - Change lighting, weather, time of day
    - Content corrections
    """
    
    # Model name for Gemini 2.5 Flash Image
    MODEL_NAME = "gemini-2.5-flash-preview-image"
    
    def __init__(self):
        self.client = None
        
        if not HAS_GENAI:
            print("[NANO_BANANA] google-genai not available. Enhancement disabled.")
            return
        
        if not config.GEMINI_API_KEY:
            print("[NANO_BANANA] No GEMINI_API_KEY configured. Enhancement disabled.")
            return
        
        try:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            print("[NANO_BANANA] Gemini 2.5 Flash Image initialized.")
        except Exception as e:
            print(f"[NANO_BANANA] Initialization failed: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Nano Banana is available."""
        return self.client is not None
    
    def enhance_image(
        self,
        image_path: str,
        enhancement_prompt: str = "Enhance this image: improve quality, fix artifacts, sharpen details",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Enhance an existing image using Gemini 2.5 Flash Image.
        
        Args:
            image_path: Path to the image to enhance
            enhancement_prompt: What to improve about the image
            output_path: Where to save the enhanced image (optional)
        
        Returns:
            Path to enhanced image or None if failed
        """
        if not self.client:
            print("[NANO_BANANA] Not available, skipping enhancement")
            return image_path  # Return original
        
        if not os.path.exists(image_path):
            print(f"[NANO_BANANA] Image not found: {image_path}")
            return image_path
        
        try:
            print(f"[NANO_BANANA] Enhancing image...")
            
            # Load the image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Determine mime type
            extension = os.path.splitext(image_path)[1].lower()
            mime_type = "image/png" if extension == ".png" else "image/jpeg"
            
            # Create image part
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
            
            # Generate enhanced version
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=[
                    enhancement_prompt,
                    image_part
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"]
                )
            )
            
            # Extract generated image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save enhanced image
                        if output_path is None:
                            base, ext = os.path.splitext(image_path)
                            output_path = f"{base}_enhanced{ext}"
                        
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)
                        
                        print(f"[NANO_BANANA] Enhanced image saved: {os.path.basename(output_path)}")
                        return output_path
            
            print("[NANO_BANANA] No image in response, returning original")
            return image_path
            
        except Exception as e:
            print(f"[NANO_BANANA] Enhancement failed: {e}")
            return image_path  # Return original on failure
    
    def fix_image_issues(
        self,
        image_path: str,
        issues: list[str],
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Fix specific issues in an image based on GPT-5.2 feedback.
        
        Args:
            image_path: Path to the image with issues
            issues: List of specific issues to fix (from GPT-5.2 review)
            output_path: Where to save the fixed image
        
        Returns:
            Path to fixed image or original if failed
        """
        if not issues:
            return image_path
        
        # Build a targeted fix prompt
        issues_text = ". ".join(issues[:3])  # Limit to top 3 issues
        fix_prompt = f"Edit this image to fix the following issues: {issues_text}. Keep everything else the same."
        
        return self.enhance_image(image_path, fix_prompt, output_path)
    
    def is_content_issue(self, issues: list[str]) -> bool:
        """
        Determine if the issues require content editing (Nano Banana) 
        vs technical upscaling (Topaz).
        
        Content issues = Nano Banana can fix (hallucinates new content)
        Technical issues = Topaz should fix (upscale without change)
        
        Returns:
            True if Nano Banana should handle, False if Topaz should handle
        """
        content_keywords = [
            "finger", "hand", "face", "eye", "mouth", "nose",
            "wrong", "missing", "extra", "distorted", "anatomy",
            "artifact", "object", "position", "pose", "expression",
            "add", "remove", "change", "fix", "correct"
        ]
        
        technical_keywords = [
            "blur", "resolution", "pixelated", "low quality", "upscale",
            "sharpen", "noise", "grain", "compression"
        ]
        
        issues_lower = " ".join(issues).lower()
        
        content_score = sum(1 for kw in content_keywords if kw in issues_lower)
        technical_score = sum(1 for kw in technical_keywords if kw in issues_lower)
        
        # If content issues, use Nano Banana
        # If mostly technical, skip (wait for Topaz later)
        return content_score > technical_score
    
    def upscale_image(
        self,
        image_path: str,
        scale_factor: str = "2x",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        ⚠️ DEPRECATED: Use Topaz for upscaling instead.
        
        Nano Banana may hallucinate/change content during upscale.
        This method is kept for backwards compatibility but NOT RECOMMENDED.
        
        For clean upscaling, integrate Topaz Video AI instead.
        """
        print("[NANO_BANANA] ⚠️ WARNING: Using Nano Banana for upscale is NOT recommended.")
        print("[NANO_BANANA] Content may be altered. Use Topaz for clean upscaling.")
        
        upscale_prompt = f"Upscale this image to {scale_factor} resolution. Keep the composition and content EXACTLY the same. Do not add or change any details."
        
        return self.enhance_image(image_path, upscale_prompt, output_path)
    
    def generate_image(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        aspect_ratio: str = "16:9"
    ) -> Optional[str]:
        """
        Generate a new image from text prompt.
        
        Args:
            prompt: Text description of the image to generate
            output_path: Where to save the image
            aspect_ratio: Aspect ratio (16:9, 1:1, 9:16, etc.)
        
        Returns:
            Path to generated image or None if failed
        """
        if not self.client:
            print("[NANO_BANANA] Not available")
            return None
        
        try:
            print(f"[NANO_BANANA] Generating image...")
            
            # Enhanced prompt with aspect ratio
            full_prompt = f"{prompt}. Aspect ratio: {aspect_ratio}."
            
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"]
                )
            )
            
            # Extract generated image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Generate output path if not provided
                        if output_path is None:
                            import hashlib
                            hash_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
                            output_path = os.path.join(config.OUTPUT_DIR, f"nano_{hash_id}.png")
                        
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)
                        
                        print(f"[NANO_BANANA] Generated: {os.path.basename(output_path)}")
                        return output_path
            
            print("[NANO_BANANA] No image in response")
            return None
            
        except Exception as e:
            print(f"[NANO_BANANA] Generation failed: {e}")
            return None
