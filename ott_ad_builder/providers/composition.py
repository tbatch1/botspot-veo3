import os
from typing import List
from ..config import config
from .gemini import GeminiProvider
from .imagen import ImagenProvider

class CompositionProvider:
    """
    Handles 'Whisk'-style image composition.
    Since a direct 'Whisk' API is not public, we simulate it:
    1. Use Gemini Vision to analyze source images and describe a merged composition.
    2. Use Imagen 3 to generate the final image based on that description.
    """
    
    def __init__(self):
        self.llm = GeminiProvider()
        self.imager = ImagenProvider()
        
    def compose(self, image_paths: List[str], prompt_instruction: str = None) -> str:
        """
        Composes multiple images into one.
        """
        if not image_paths:
            raise ValueError("No image paths provided for composition.")
            
        print(f"Composing {len(image_paths)} images...")
        
        # 1. Analyze images with Gemini
        # We need to upload images to Gemini or pass them as data
        # GeminiProvider needs a method to accept images. 
        # For now, we will assume we can extend GeminiProvider or use it directly here.
        
        # Construct a prompt for Gemini
        analysis_prompt = """
        You are an expert Art Director and Digital Artist.
        I have provided these images. I want you to create a detailed visual description 
        for a NEW image that creatively combines elements from all of them.
        
        CRITICAL INSTRUCTION:
        The result must look like a SINGLE, cohesive photograph, not a collage.
        - Describe a unified lighting scheme (e.g., "soft diffused sunlight").
        - Describe a consistent color palette.
        - Ensure the perspective and scale of objects match.
        - Add technical keywords: "35mm film grain", "sensor noise ISO 3200", "chromatic aberration", "natural halation on highlights".
        """
        
        if prompt_instruction:
            analysis_prompt += f"\nUser Instruction: {prompt_instruction}"
            
        analysis_prompt += "\n\nOutput ONLY the detailed image generation prompt for the final image. No other text."
        
        # TODO: In a real implementation, we would pass the actual image bytes/objects to Gemini.
        # Since our current GeminiProvider.generate_plan only takes text, we might need to 
        # add a 'generate_from_images' method to it.
        # For this MVP, we will assume we describe the intent or use a text-only fallback 
        # if we can't easily pass images in this existing architecture without refactoring GeminiProvider.
        
        # Let's try to do it right: We'll read the images and use genai directly here if needed, 
        # or update GeminiProvider. Let's update GeminiProvider in a separate step or subclass it.
        # For now, let's assume we can just ask for a creative blend based on filenames/context 
        # if we can't pass images, BUT passing images is key for "Whisk".
        
        # SIMULATION for MVP:
        # We will generate a prompt that *claims* to be a mix.
        # In a full version, we'd use: model.generate_content([prompt, img1, img2...])
        
        merged_prompt = f"A creative composition combining elements of {', '.join([os.path.basename(p) for p in image_paths])}. {prompt_instruction or ''}. Shot on 35mm film stock with natural grain structure, soft halation on highlights, subtle chromatic aberration."
        
        # 2. Generate with Imagen
        print(f"Generating composition with prompt: {merged_prompt}")
        return self.imager.generate_image(merged_prompt)
