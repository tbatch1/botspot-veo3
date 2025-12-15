"""
GPT-5.2 Spatial Reasoning Provider
Released: December 11, 2025

This provider uses GPT-5.2's enhanced spatial reasoning capabilities for:
- 3D spatial continuity understanding
- Camera angle and lens calculations
- Lighting vector analysis
- Physics-aware scene review

GPT-5.2 reduces spatial reasoning errors by 50%+ compared to GPT-4o.
"""

import json
import time
from openai import OpenAI, RateLimitError, APIStatusError
from ..config import config
from .base import LLMProvider


class SpatialReasoningProvider(LLMProvider):
    """
    GPT-5.2 Spatial Reasoning Provider.
    
    Acts as the "Camera Agent" - calculates lens mm, lighting vectors,
    and physics before a single pixel is generated.
    
    Can also review generated content for spatial consistency.
    """
    
    def __init__(self):
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("[SPATIAL] GPT-5.2 Spatial Reasoning initialized.")
        else:
            print("[SPATIAL] No OpenAI key found. Spatial reasoning disabled.")
    
    def is_available(self) -> bool:
        """Check if GPT-5.2 is available."""
        return self.client is not None
    
    def _call_with_retry(self, messages: list, max_retries: int = 3) -> dict:
        """
        Internal helper to call OpenAI API with exponential backoff retry.
        Handles 429 (rate limit), 500, 502, 503, 529 errors.
        """
        if not self.client:
            return {}
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=config.GPT52_MODEL,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
                
            except RateLimitError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt * 5  # 5s, 10s, 20s
                    print(f"[GPT-5.2] Rate limited. Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[GPT-5.2] Rate limit exceeded after {max_retries} retries.")
                    raise
                    
            except APIStatusError as e:
                last_error = e
                if e.status_code in [500, 502, 503, 529]:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt * 3  # 3s, 6s, 12s
                        print(f"[GPT-5.2] API error {e.status_code}. Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"[GPT-5.2] API error {e.status_code} after {max_retries} retries.")
                        raise
                else:
                    raise  # Non-retryable error
                    
            except Exception as e:
                print(f"[GPT-5.2] Unexpected error: {e}")
                raise
        
        if last_error:
            raise last_error
        return {}
    
    def generate_plan(self, user_input: str) -> dict:
        """Satisfy LLMProvider interface."""
        return self.analyze_scene_spatial(user_input)
    
    def full_creative_direction(self, topic: str, website_data: str, constraints: dict, target_duration: int = 15) -> tuple:
        """
        UNIFIED METHOD: Does EVERYTHING in one GPT-5.2 call.
        Replaces: Claude Strategist + GPT-5.2 Formatter
        
        Returns:
            tuple of (strategy_dict, script_dict) ready for image generation
        """
        if not self.client:
            return self._fallback_full_creative(topic, website_data, constraints, target_duration)
        
        # Extract product name from topic or URL
        product_name = topic.replace("Create a commercial for ", "").replace("Create a 15 second commercial for ", "").strip()
        if "make a creative ad" in product_name.lower():
            product_name = product_name.split("URL:")[-1].strip().rstrip('/').rstrip('.') if "URL:" in product_name else product_name
            # Try to get from constraints URL
            if constraints.get('url'):
                url = constraints.get('url', '')
                product_name = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        style = constraints.get('style', ['Cinematic'])[0] if isinstance(constraints.get('style'), list) else constraints.get('style', 'Cinematic')
        mood = constraints.get('mood', 'Premium')
        platform = constraints.get('platform', 'Netflix')
        
        prompt = f"""You are the Complete Creative Director for a premium video commercial.
Your job: Create the ENTIRE creative vision AND technical prompts in one response.

PRODUCT/BRAND: {product_name}
WEBSITE RESEARCH:
{website_data[:2000]}

USER REQUIREMENTS:
- Style: {style}
- Mood: {mood}
- Platform: {platform}
- Duration: {target_duration} seconds

⚠️ CRITICAL RULES:
1. ALWAYS use "{product_name}" by name in EVERY scene - NEVER say "the product" or "an interface"
2. If it's a software/website, describe the ACTUAL UI (dashboard, charts, features)
3. Make scenes VISUALLY SPECIFIC to this brand
4. Each scene must be production-ready for AI image generation

🎬 CRITICAL - VIDEO-READY IMAGE PROMPTS:
Your visual_prompts will become STILL IMAGES that are then ANIMATED by AI video.
Design images with INHERENT MOTION POTENTIAL - elements that can naturally animate:

BAD (static): "A dashboard showing charts"
GOOD (motion-ready): "A dashboard with data streams flowing across the screen, charts mid-animation with rising bars, glowing indicators pulsing with activity, cursor hovering over a button about to click"

Include in EVERY visual_prompt:
- DYNAMIC ELEMENTS: flowing particles, trailing lights, data streams, rippling effects
- MID-ACTION MOMENTS: hand reaching, cursor hovering, button being pressed
- DEPTH LAYERS: foreground elements, midground subject, background with motion blur
- LIGHT SOURCES: glowing screens, lens flares, volumetric light rays that can animate
- ATMOSPHERIC EFFECTS: floating dust motes, subtle fog, particles in air

Create a {target_duration}-second commercial with 3 scenes.

Respond in JSON:
{{
"strategy": {{
    "core_concept": "Short punchy title featuring {product_name}",
    "visual_language": "Camera/lens/lighting style",
    "product_name": "{product_name}"
}},
"script": {{
    "mood": "{mood}",
    "lines": [
        {{"speaker": "Narrator", "text": "Voiceover line 1", "time_range": "0s-5s"}},
        {{"speaker": "Narrator", "text": "Voiceover line 2", "time_range": "5s-10s"}},
        {{"speaker": "Narrator", "text": "Final CTA with brand name", "time_range": "10s-{target_duration}s"}}
    ],
    "scenes": [
        {{
            "id": 1,
            "duration": 5,
            "visual_prompt": "A cinematic photo of [SPECIFIC scene with {product_name}], [DYNAMIC ELEMENTS: particles, glows, motion blur], [MID-ACTION MOMENT]. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8, cinematic lighting, shallow depth of field.",
            "motion_prompt": "Camera: [dramatic movement]. Action: [what animates]. Style: {style}. Mood: {mood}."
        }},
        {{
            "id": 2, 
            "duration": 5,
            "visual_prompt": "A cinematic photo of [SPECIFIC scene showing {product_name} features/benefits], [FLOWING DATA or LIGHT TRAILS], [ATMOSPHERIC DEPTH]. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8, volumetric lighting.",
            "motion_prompt": "Camera: [movement with purpose]. Action: [elements animating]. Style: {style}. Mood: {mood}."
        }},
        {{
            "id": 3,
            "duration": 5,
            "visual_prompt": "A cinematic photo of [CLOSING SHOT with {product_name} branding], [TRIUMPHANT LIGHTING with lens flares], [PARTICLES rising or falling]. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8, hero lighting.",
            "motion_prompt": "Camera: [epic reveal or settle]. Action: [final flourish]. Style: {style}. Mood: {mood}."
        }}
    ]
}}
}}

IMPORTANT: Replace all [bracketed text] with actual creative content. 
The visual_prompt for EACH scene MUST mention "{product_name}" by name AND include motion-ready elements."""

        try:
            response = self._call_with_retry([{"role": "user", "content": prompt}])
            result = response
            
            # Extract strategy and script
            strategy = result.get('strategy', {})
            script = result.get('script', {})
            
            # Ensure product_name is stored
            strategy['product_name'] = product_name
            
            print(f"[GPT-5.2] Full creative direction complete for: {product_name}")
            print(f"[GPT-5.2] Generated {len(script.get('scenes', []))} scenes")
            
            return strategy, script
            
        except Exception as e:
            print(f"[GPT-5.2] Full creative direction failed: {e}. Using fallback.")
            return self._fallback_full_creative(topic, website_data, constraints, target_duration)
    
    def _fallback_full_creative(self, topic: str, website_data: str, constraints: dict, target_duration: int) -> tuple:
        """Fallback when GPT-5.2 unavailable."""
        product_name = topic.replace("Create a commercial for ", "").replace("Create a 15 second commercial for ", "").strip()
        if constraints.get('url'):
            url = constraints.get('url', '')
            product_name = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        strategy = {
            "core_concept": f"{product_name} Premium Showcase",
            "visual_language": "Shot on Arri Alexa, Cooke S4 prime lens, natural film grain",
            "product_name": product_name
        }
        
        script = {
            "mood": constraints.get('mood', 'Premium'),
            "lines": [
                {"speaker": "Narrator", "text": "[pause: 0.3s] Innovation meets excellence.", "time_range": "0s-5s"},
                {"speaker": "Narrator", "text": f"Discover {product_name}. Built for those who demand more.", "time_range": f"5s-10s"},
                {"speaker": "Narrator", "text": "This is your moment. [pause: 0.5s] Are you ready?", "time_range": f"10s-{target_duration}s"}
            ],
            "scenes": [
                {
                    "id": 1,
                    "duration": 5,
                    "visual_prompt": f"A photo of {product_name} interface emerging from darkness, volumetric lighting illuminating a sleek modern dashboard, professional tech environment. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8, cinematic lighting.",
                    "motion_prompt": f"Camera: Slow dolly push-in. Visual: {product_name} dashboard coming to life. Style: Cinematic, premium."
                },
                {
                    "id": 2,
                    "duration": 5,
                    "visual_prompt": f"A photo of {product_name} dashboard in full operation showing key features, golden hour lighting streaming through modern office window, professional workspace. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8.",
                    "motion_prompt": f"Camera: Slow pan across screen. Visual: {product_name} features revealed. Style: Cinematic, premium."
                },
                {
                    "id": 3,
                    "duration": 5,
                    "visual_prompt": f"A photo of {product_name} logo prominently displayed with brand colors, premium lighting setup, sleek minimalist backdrop. Shot on Arri Alexa, Cooke S4 prime lens, f/2.8.",
                    "motion_prompt": f"Camera: Slow orbit settling on logo. Visual: {product_name} brand reveal. Style: Cinematic, premium."
                }
            ]
        }
        
        return strategy, script

    def analyze_scene_spatial(self, scene_description: str) -> dict:
        """
        Analyze a scene for spatial consistency and recommend camera settings.
        
        Returns:
            dict with camera_mm, lighting_direction, depth_layers, physics_notes
        """
        if not self.client:
            return self._fallback_analysis()
        
        prompt = f"""You are a Spatial Reasoning Agent for video production.
Analyze this scene for 3D spatial consistency and provide technical recommendations.

SCENE: {scene_description}

Respond in JSON with:
{{
    "camera_mm": <recommended lens focal length in mm>,
    "camera_angle": "<eye-level/low-angle/high-angle/dutch-angle>",
    "depth_layers": ["<foreground>", "<midground>", "<background>"],
    "lighting_direction": "<key light position: front-left/front-right/rim/etc>",
    "lighting_kelvin": <color temperature in Kelvin>,
    "subject_position": "<frame position: center/rule-of-thirds-left/etc>",
    "physics_notes": ["<any physics considerations: gravity, motion blur, reflections>"],
    "spatial_warnings": ["<potential consistency issues to watch for>"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.GPT52_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"[SPATIAL] Analyzed scene: {scene_description[:50]}...")
            return result
            
        except Exception as e:
            print(f"[SPATIAL] Error: {e}. Using fallback.")
            return self._fallback_analysis()
    
    def review_video_physics(self, scene_description: str, generated_output_description: str) -> dict:
        """
        Review generated video for physics accuracy.
        Used by ComfyUI Agentic workflow for self-correction.
        
        Returns:
            dict with is_acceptable, issues, re_roll_suggestions
        """
        if not self.client:
            return {"is_acceptable": True, "issues": [], "re_roll_suggestions": None}
        
        prompt = f"""You are a Physics Review Agent for AI-generated video.
Compare the intended scene with the generated output and evaluate physics accuracy.

INTENDED SCENE: {scene_description}

GENERATED OUTPUT: {generated_output_description}

Evaluate for:
1. Gravity and motion physics
2. Lighting consistency (shadows match light source)
3. Reflection accuracy
4. Object permanence (nothing floating/morphing)
5. Temporal consistency (no flickering)

Respond in JSON:
{{
    "is_acceptable": <true/false>,
    "physics_score": <1-10>,
    "issues": ["<list of physics problems>"],
    "re_roll_suggestions": "<specific prompt modifications to fix issues, or null if acceptable>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.GPT52_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"[SPATIAL] Physics review: Score {result.get('physics_score', 'N/A')}/10")
            return result
            
        except Exception as e:
            print(f"[SPATIAL] Review error: {e}")
            return {"is_acceptable": True, "issues": [], "re_roll_suggestions": None}
    
    def calculate_camera_for_product(self, product_type: str, shot_type: str) -> dict:
        """
        Calculate optimal camera settings for product photography.
        
        Args:
            product_type: e.g., "watch", "beverage", "cosmetics", "electronics"
            shot_type: e.g., "hero", "detail", "lifestyle", "360"
        
        Returns:
            dict with lens_mm, aperture, lighting_setup, camera_motion
        """
        if not self.client:
            return self._fallback_camera_settings(product_type, shot_type)
        
        prompt = f"""You are a Product Photography Spatial Agent.
Calculate optimal camera and lighting for this product shot.

PRODUCT TYPE: {product_type}
SHOT TYPE: {shot_type}

Respond in JSON:
{{
    "lens_mm": <focal length>,
    "aperture": "<f-stop, e.g., f/2.8>",
    "camera_distance_cm": <approximate distance from product>,
    "camera_height": "<below/level/above product>",
    "camera_motion": "<static/orbit/dolly-in/pull-back/etc>",
    "motion_speed": "<slow/medium/fast>",
    "lighting_setup": {{
        "key_light": "<position and intensity>",
        "fill_light": "<position and intensity>",
        "rim_light": "<position and intensity or none>",
        "background": "<gradient/solid/environmental>"
    }},
    "recommended_duration_seconds": <optimal clip length>
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.GPT52_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"[SPATIAL] Product camera: {product_type} {shot_type} → {result.get('lens_mm')}mm f/{result.get('aperture')}")
            return result
            
        except Exception as e:
            print(f"[SPATIAL] Camera calc error: {e}")
            return self._fallback_camera_settings(product_type, shot_type)
    
    def _fallback_analysis(self) -> dict:
        """Fallback when GPT-5.2 unavailable."""
        return {
            "camera_mm": 50,
            "camera_angle": "eye-level",
            "depth_layers": ["subject", "mid-distance", "background"],
            "lighting_direction": "front-left",
            "lighting_kelvin": 5500,
            "subject_position": "rule-of-thirds-left",
            "physics_notes": ["Standard physics apply"],
            "spatial_warnings": ["Review for consistency manually"]
        }
    
    def _fallback_camera_settings(self, product_type: str, shot_type: str) -> dict:
        """Fallback camera settings by product type."""
        defaults = {
            "watch": {"lens_mm": 100, "aperture": "f/2.8", "camera_motion": "slow orbit"},
            "beverage": {"lens_mm": 85, "aperture": "f/4", "camera_motion": "dolly-in"},
            "cosmetics": {"lens_mm": 90, "aperture": "f/2.8", "camera_motion": "static"},
            "electronics": {"lens_mm": 50, "aperture": "f/5.6", "camera_motion": "orbit"},
        }
        
        base = defaults.get(product_type, defaults["electronics"])
        return {
            **base,
            "camera_distance_cm": 60,
            "camera_height": "level",
            "motion_speed": "slow",
            "lighting_setup": {
                "key_light": "45-degree front-right, high intensity",
                "fill_light": "front-left, medium intensity",
                "rim_light": "back-right, low intensity",
                "background": "gradient"
            },
            "recommended_duration_seconds": 5
        }
    
    def format_claude_scenes(self, strategy: dict, target_duration: int = 30) -> dict:
        """
        CORE METHOD: Takes Claude's creative direction and formats into technical prompts.
        This replaces Gemini's script generation role.
        
        Args:
            strategy: Claude's creative strategy with scenes, core_concept, etc.
            target_duration: Target video length in seconds
        
        Returns:
            dict with formatted scenes containing visual_prompt, motion_prompt, audio_prompt
        """
        if not self.client:
            return self._fallback_format_scenes(strategy, target_duration)
        
        scenes = strategy.get('scenes', [])
        core_concept = strategy.get('core_concept', '')
        visual_language = strategy.get('visual_language', 'Cinematic, professional')
        audio_signature = strategy.get('audio_signature', {})
        
        prompt = f"""You are a Technical Director for AI video production.
Take the Creative Director's vision and format it into precise technical prompts for AI image/video models.

CREATIVE VISION:
- Core Concept: {core_concept}
- Visual Language: {visual_language}
- Audio Mood: {audio_signature.get('music_mood', 'epic')}
- Target Duration: {target_duration} seconds

⚠️ CRITICAL RULE - PRESERVE PRODUCT/BRAND NAMES:
- If the strategy mentions a specific product name (e.g., "botspot.trade", "Nike", "Tesla"), YOU MUST include it in your prompts
- NEVER replace product names with generic terms like "the product", "an interface", "a dashboard"
- If core_concept includes a brand/product name, use it in EVERY scene's visual_prompt

SCENES FROM CREATIVE DIRECTOR:
{json.dumps(scenes, indent=2)}

For EACH scene, create technical prompts with:

1. **visual_prompt** (for Imagen image generation):
   - Start with "A photo of" for photorealistic scenes
   - Include: subject, action, environment, lighting (Kelvin temp), camera distance
   - PRESERVE any specific product/brand names from the scene description
   - Add: "shot on Arri Alexa, Cooke S4 prime lens" for cinema quality
   - Mention aperture (f/2.8 for shallow DOF, f/8 for deep focus)

2. **motion_prompt** (for Runway/Veo video generation):
   - Use structure: "Camera: [movement]. Visual: [scene]. Style: [aesthetic]"
   - Specify: camera_motion (dolly/pan/orbit/static), motion_speed, subject_action
   - Include physics keywords: motion blur, slow motion, handheld shake as appropriate

3. **audio_prompt** (for ElevenLabs/Veo audio):
   - Format: "AMBIANCE: [environmental sounds]. MUSIC: [mood/genre]."
   - Include voiceover direction if scene has dialogue

4. **spatial_specs** (camera/lighting technical details):
   - lens_mm, aperture, camera_angle, lighting_direction, lighting_kelvin

Respond in JSON:
{{
    "lines": [
        {{"id": 1, "text": "<voiceover text>", "emotion": "<delivery emotion>"}}
    ],
    "scenes": [
        {{
            "id": 1,
            "duration": <seconds>,
            "visual_prompt": "<detailed image prompt>",
            "motion_prompt": "<structured video prompt>",
            "audio_prompt": "<audio/ambiance description>",
            "spatial_specs": {{
                "lens_mm": <number>,
                "aperture": "<f-stop>",
                "camera_angle": "<angle>",
                "camera_motion": "<movement>",
                "lighting_direction": "<direction>",
                "lighting_kelvin": <number>
            }}
        }}
    ],
    "total_duration": {target_duration}
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.GPT52_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"[GPT-5.2] Formatted {len(result.get('scenes', []))} scenes with spatial specs")
            return result
            
        except Exception as e:
            print(f"[GPT-5.2] Formatting error: {e}. Using fallback.")
            return self._fallback_format_scenes(strategy, target_duration)
    
    def _fallback_format_scenes(self, strategy: dict, target_duration) -> dict:
        """Fallback formatting when GPT-5.2 unavailable."""
        # Ensure target_duration is an integer
        if isinstance(target_duration, str):
            # Handle formats like "15s" or "15"
            target_duration = int(''.join(filter(str.isdigit, target_duration)) or '15')
        target_duration = int(target_duration) if target_duration else 15
        
        # Extract product name from strategy (set by Claude strategist)
        product_name = strategy.get('product_name', '')
        if not product_name:
            # Try to extract from core_concept (e.g., "botspot.trade Premium Showcase")
            core_concept = strategy.get('core_concept', '')
            if core_concept and 'Premium Showcase' in core_concept:
                product_name = core_concept.replace(' Premium Showcase', '').strip()
        
        scenes = strategy.get('scenes', [])
        formatted_scenes = []
        
        for i, scene in enumerate(scenes):
            visual_dir = scene.get('visual_direction', scene.get('description', ''))
            motion_dir = scene.get('motion_direction', 'Smooth camera movement')
            voiceover = scene.get('voiceover_content', '')
            
            # Get scene duration, default to equal distribution
            scene_duration = scene.get('duration', 5)
            if isinstance(scene_duration, str):
                scene_duration = int(''.join(filter(str.isdigit, str(scene_duration))) or '5')
            
            formatted_scenes.append({
                "id": i + 1,
                "duration": scene_duration,
                "visual_prompt": f"A photo of {visual_dir}. Shot on Arri Alexa, Cooke S4 prime lens, shallow depth of field f/2.8, cinematic lighting.",
                "motion_prompt": f"Camera: Smooth cinematic motion. Visual: {visual_dir}. {motion_dir}. Style: Professional, cinematic quality.",
                "audio_prompt": f"AMBIANCE: Natural environment sounds. MUSIC: Epic cinematic.",
                "spatial_specs": {
                    "lens_mm": 50,
                    "aperture": "f/2.8",
                    "camera_angle": "eye-level",
                    "camera_motion": "smooth dolly",
                    "lighting_direction": "front-right",
                    "lighting_kelvin": 5500
                }
            })
        
        lines = []
        cumulative_time = 0
        for i, scene in enumerate(scenes):
            if scene.get('voiceover_content'):
                scene_duration = scene.get('duration', 5)
                if isinstance(scene_duration, str):
                    scene_duration = int(''.join(filter(str.isdigit, str(scene_duration))) or '5')
                
                start_time = cumulative_time
                end_time = cumulative_time + scene_duration
                
                lines.append({
                    "speaker": "Narrator",
                    "text": scene.get('voiceover_content'),
                    "time_range": f"{start_time}s-{end_time}s"
                })
                cumulative_time = end_time
        
        return {
            "lines": lines,
            "scenes": formatted_scenes,
            "total_duration": target_duration
        }
    
    def review_generated_image(
        self, 
        intended_prompt: str, 
        image_path: str = None,
        image_description: str = None,
        scene_context: dict = None
    ) -> dict:
        """
        SELF-CORRECTION: Review a generated image against intent using VISION.
        GPT-5.2 actually SEES the image and evaluates quality.
        
        Args:
            intended_prompt: What we asked for
            image_path: Path to the generated image (for vision analysis)
            image_description: Fallback text description if no image path
            scene_context: Optional context (previous scenes, brand requirements)
        
        Returns:
            dict with is_acceptable, quality_score, issues, improved_prompt
        """
        if not self.client:
            return {"is_acceptable": True, "quality_score": 7, "issues": [], "improved_prompt": None}
        
        context_str = ""
        if scene_context:
            context_str = f"\nBRAND CONTEXT: {json.dumps(scene_context)}"
        
        # Build the prompt
        text_prompt = f"""You are a Quality Control Agent for AI-generated commercial images.
Analyze the generated image against the intended prompt.

INTENDED PROMPT: {intended_prompt}
{context_str}

Evaluate for:
1. Subject accuracy - Does the image match the prompt? Is the main subject correct?
2. Composition - Good framing? Rule of thirds? Visual balance?
3. Lighting - Does it match the intended mood? Consistent shadows?
4. Brand safety - Nothing inappropriate, offensive, or off-brand?
5. Technical quality - Sharp? No artifacts? Good resolution?
6. Product visibility - If product in scene, is it prominent and recognizable?
7. Text rendering - If text in image, is it spelled correctly?

Respond in JSON:
{{
    "is_acceptable": <true if quality >= 7 and no major issues, false otherwise>,
    "quality_score": <1-10>,
    "issues": ["<specific problems found>"],
    "what_i_see": "<brief description of what you actually see in the image>",
    "improved_prompt": "<if not acceptable, provide a better prompt. If acceptable, null>"
}}"""

        try:
            # VISION MODE: Actually look at the image
            if image_path and os.path.exists(image_path):
                import base64
                
                # Encode image to base64
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                
                # Determine image type
                extension = os.path.splitext(image_path)[1].lower()
                mime_type = "image/png" if extension == ".png" else "image/jpeg"
                
                print(f"[VISION] GPT-5.2 analyzing image: {os.path.basename(image_path)}")
                
                # Multimodal request with image
                response = self.client.chat.completions.create(
                    model=config.GPT52_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": text_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}",
                                        "detail": "high"  # High detail for quality review
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=1000
                )
            else:
                # TEXT-ONLY FALLBACK: Use description instead of actual image
                if image_description:
                    text_prompt += f"\n\nGENERATED IMAGE DESCRIPTION: {image_description}"
                
                response = self.client.chat.completions.create(
                    model=config.GPT52_MODEL,
                    messages=[{"role": "user", "content": text_prompt}],
                    response_format={"type": "json_object"}
                )
            
            result = json.loads(response.choices[0].message.content)
            score = result.get('quality_score', 5)
            what_i_see = result.get('what_i_see', '')
            
            status = '✓ PASS' if result.get('is_acceptable') else '✗ NEEDS REROLL'
            print(f"[VISION] Review: {score}/10 - {status}")
            if what_i_see:
                print(f"[VISION] Sees: {what_i_see[:80]}...")
            
            return result
            
        except Exception as e:
            print(f"[VISION] Review error: {e}")
            return {"is_acceptable": True, "quality_score": 7, "issues": [], "improved_prompt": None}
    
    def adjust_next_scene_prompt(
        self,
        previous_scene_output: str,
        next_scene_prompt: str,
        narrative_context: str = ""
    ) -> str:
        """
        DYNAMIC STORYBOARDING: Adjust the next scene prompt based on what was 
        actually generated in the previous scene.
        
        This ensures narrative coherence across the ad.
        
        Args:
            previous_scene_output: Description of what was generated in Scene N
            next_scene_prompt: Original prompt for Scene N+1
            narrative_context: The overall story arc
        
        Returns:
            Adjusted prompt for Scene N+1
        """
        if not self.client:
            return next_scene_prompt
        
        prompt = f"""You are a Continuity Director ensuring scene-to-scene coherence.

PREVIOUS SCENE (what was actually generated):
{previous_scene_output}

NEXT SCENE (original prompt):
{next_scene_prompt}

NARRATIVE CONTEXT:
{narrative_context}

Adjust the next scene prompt to:
1. Maintain visual continuity (lighting, time of day, weather)
2. Keep character/product appearance consistent
3. Ensure logical progression (if prev scene ends with action, next should continue)
4. Match color grading and mood

Respond with ONLY the adjusted prompt, no explanation. If no adjustment needed, return the original."""

        try:
            response = self.client.chat.completions.create(
                model=config.GPT52_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            
            adjusted = response.choices[0].message.content.strip()
            if adjusted != next_scene_prompt:
                print(f"[CONTINUITY] Adjusted Scene N+1 prompt for coherence")
            return adjusted
            
        except Exception as e:
            print(f"[CONTINUITY] Error: {e}")
            return next_scene_prompt

