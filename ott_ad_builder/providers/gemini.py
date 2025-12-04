import json
import os
import google.generativeai as genai
from ..config import config
from ..state import Script
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    """Gemini implementation of the Brain."""
    
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Using Gemini 2.5 Flash - latest stable version (Nov 2025)
        # Supports JSON mode for structured output
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )

    def generate_plan(self, user_input: str) -> Script:
        """
        Generates a creative ad plan (Script + Scenes) from user input.
        """
        prompt = f"""
        You are an award-winning Creative Director for broadcast-quality OTT commercials (Netflix, Hulu, Prime Video).

        TASK:
        Create an 8-second BROADCAST-QUALITY commercial for:
        "{user_input}"

        OTT BROADCAST REQUIREMENTS:
        1. Output MUST be valid JSON matching the schema below.
        2. Create EXACTLY 2 scenes, each 4 seconds long (total: 8 seconds, 1080p, 16:9).

        3. SCENE 1 - HERO ESTABLISHMENT:
           - Establish ONE primary character OR hero product shot
           - Be SPECIFIC about character details: age, gender, appearance, clothing
           - OR specific product details: color, material, positioning
           - Use BROADCAST LIGHTING: "cinematic three-point lighting", "golden hour backlight", "soft key light"
           - Frame in SAFE ZONE: Keep faces/products in center 80% of frame
           - Example Character: "A 35-year-old woman with shoulder-length brown hair, wearing a navy blazer,
             holding a smartphone, professional studio lighting, medium close-up, centered"
           - Example Product: "A silver sports car, gleaming metallic paint, parked on wet pavement,
             dramatic backlighting, low-angle hero shot, centered composition"

        4. SCENE 2 - CHARACTER CONSISTENCY:
           - CRITICAL: Use "the same [character/product] from scene 1" to ensure Veo uses same base image
           - Different angle or action, but MUST reference scene 1's subject
           - Example: "The same woman turns toward camera with confident smile, golden hour side lighting,
             slow push-in, face remains centered"
           - Example: "The same silver sports car, camera orbits slowly around driver side,
             revealing sleek profile, maintaining hero framing"

        5. BROADCAST MOTION:
           - Use professional camera language: "Slow dolly push-in", "Subtle Steadicam drift", "Locked-off static"
           - NO jarring movements (OTT compliance)

        6. BROADCAST AUDIO: Subtle, professional ambient sound only.
        7. MOOD: One professional adjective ("Aspirational", "Premium", "Authentic", "Bold").
        8. Each scene duration: 4 seconds (Veo 3.1 requirement).

        JSON SCHEMA:
        {{
            "lines": [
                {{ "speaker": "Narrator", "text": "Short punchy line", "time_range": "0-8s" }}
            ],
            "mood": "...",
            "scenes": [
                {{
                    "id": 1,
                    "visual_prompt": "Brief visual description",
                    "motion_prompt": "Simple camera move",
                    "audio_prompt": "Minimal sound",
                    "duration": 4
                }},
                {{
                    "id": 2,
                    "visual_prompt": "Brief visual description",
                    "motion_prompt": "Simple camera move",
                    "audio_prompt": "Minimal sound",
                    "duration": 4
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown code blocks if the model adds them despite mime_type
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            
            data = json.loads(text)
            return Script(**data)
            
        except Exception as e:
            print(f"Error generating plan with Gemini: {e}")
            # In a real app, we might retry or raise a custom exception
            raise e
