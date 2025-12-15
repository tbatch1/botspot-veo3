import json
import os
import random
import google.generativeai as genai
from ..config import config
from ..state import Script
from .base import LLMProvider
from ..parallel_utils import SmartCritiqueCache
from ..constants.cinematography import (
    CAMERA_MOVEMENTS,
    SHOT_SIZE_PROMPTS,
    SHOT_SEQUENCES,
    LIGHTING_SETUPS,
    COLOR_GRADES,
    CAMERA_EQUIPMENT_KEYWORDS,
    CAMERA_ANGLES,
    EMOTIONAL_BEATS,
    detect_commercial_type,
    calculate_scene_count,
    calculate_scene_durations,
    get_random_equipment
)


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
        # OPTIMIZATION: Smart critique caching (-$0.01 per commercial)
        self.critique_cache = SmartCritiqueCache()

    def generate_plan(self, user_input: str, config_overrides: dict = None, strategy: dict = None) -> Script:
        """
        Generates a cinematic ad plan (Script + Scenes) from user input using professional cinematography.
        
        NEW: If strategy contains 'scenes' array with complete creative direction from Claude,
        Gemini will use a simplified prompt that just formats Claude's content into technical prompts.
        Claude does all creative/marketing decisions, Gemini just formats.

        Args:
            user_input: User's creative brief
            config_overrides: Optional dict with style, duration, platform, mood overrides from UI
            strategy: Optional dict containing the Creative Strategy from the Strategist layer
        """
        # FAST PATH: If Claude provided full scene-level creative direction, use simplified formatting
        if strategy and 'scenes' in strategy and isinstance(strategy['scenes'], list) and len(strategy['scenes']) > 0:
            print("[GEMINI] Using Claude's scene-level creative direction (fast path)")
            return self._format_claude_scenes(user_input, config_overrides, strategy)
        
        # LEGACY PATH: Generate content from scratch (when Claude only provides high-level strategy)
        print("[GEMINI] Generating content from scratch (legacy path)")
        
        # Extract config overrides if provided (from frontend dropdowns)
        user_styles = []
        target_platform = "Netflix"
        mood_override = None
        target_duration = 8
        camera_style_override = None
        lighting_preference = None
        color_grade_override = None
        transition_override = None

        if config_overrides:
            user_styles = config_overrides.get('style', [])
            if isinstance(user_styles, str):
                user_styles = [user_styles]
            
            # Handle Platform (String or List)
            platform_val = config_overrides.get('platform', 'Netflix')
            if isinstance(platform_val, list):
                target_platform = ", ".join(platform_val)
            else:
                target_platform = platform_val

            # Handle Mood (String or List)
            mood_val = config_overrides.get('mood')
            if isinstance(mood_val, list):
                mood_override = ", ".join(mood_val)
            else:
                mood_override = mood_val

            duration_str = config_overrides.get('duration', '8s')
            target_duration = int(duration_str.replace('s', ''))

            # New frontend cinematography controls
            # Handle Camera Style (String or List)
            camera_val = config_overrides.get('camera_style')
            if isinstance(camera_val, list) and len(camera_val) > 0:
                camera_style_override = camera_val[0] # For specific mapping logic, we take the primary/first one
                # But we might want to pass all of them to the prompt? 
                # The current mapping logic maps a SINGLE style to a movement category.
                # Let's keep using the first one for the mapping logic, but maybe use all in prompts?
                # For now, taking the first one is safest for the mapping dicts below.
            else:
                camera_style_override = camera_val
            
            lighting_preference = config_overrides.get('lighting_preference')
            color_grade_override = config_overrides.get('color_grade')
            transition_override = config_overrides.get('transition')

        # Calculate dynamic scene count based on narrative complexity
        scene_count = calculate_scene_count(user_input, target_duration)
        scene_durations = calculate_scene_durations(scene_count, target_duration)
        # Ensure durations are integers for Pydantic validation
        scene_durations = [int(d) for d in scene_durations]

        # Detect commercial type for shot sequencing
        commercial_type = detect_commercial_type(user_input)
        shot_sequence = SHOT_SEQUENCES.get(commercial_type, SHOT_SEQUENCES["product_showcase"])

        # Select cinematic style elements
        # Priority: 1) Exact color_grade from frontend, 2) Style-based, 3) Random
        if color_grade_override:
            # Use exact color grade specified by user (e.g., "Kodak 5219")
            color_grade = color_grade_override
        elif user_styles:
            # Map style to color grade
            if "Cinematic" in user_styles:
                color_grade = COLOR_GRADES["hollywood_blockbuster"]
            elif "Analog Film" in user_styles:
                color_grade = COLOR_GRADES["vintage_analog"]
            elif "Cyberpunk" in user_styles:
                color_grade = COLOR_GRADES["neon_cyberpunk"]
            else:
                color_grade = random.choice(list(COLOR_GRADES.values()))
        else:
            # Default: random selection
            color_grade = random.choice(list(COLOR_GRADES.values()))

        # Build scene guidance with professional cinematography
        scene_guidance_list = []
        for i in range(scene_count):
            scene_num = i + 1
            duration = scene_durations[i]

            # Get shot size from sequence (with fallback)
            if i < len(shot_sequence):
                shot_data = shot_sequence[i]
                shot_size = shot_data["shot_size"]
                purpose = shot_data["purpose"]
                # NEW: Get emotional beat from shot sequence
                emotion_key = shot_data.get("emotion", "discovery")
                emotional_direction = EMOTIONAL_BEATS.get(emotion_key, EMOTIONAL_BEATS["discovery"])
            else:
                shot_size = "medium"
                purpose = "continuation of narrative"
                emotion_key = "discovery"
                emotional_direction = EMOTIONAL_BEATS["discovery"]

            # Determine scene purpose category for camera movement
            if i == 0:
                scene_purpose = "establishing"
            elif i == 1:
                scene_purpose = "character_introduction" if "character" in commercial_type else "product_hero"
            elif i == scene_count - 1:
                scene_purpose = "closing"
            else:
                scene_purpose = "emotional_moment"

            # Select professional camera movement
            # Priority: 1) User's camera_style preference, 2) Scene-appropriate default
            if camera_style_override:
                # Map frontend camera_style to movement categories
                camera_style_map = {
                    "Steadicam": "establishing",  # Smooth, controlled movements
                    "Drone": "establishing",  # Aerial, sweeping movements
                    "Handheld": "emotional_moment",  # Dynamic, intimate movements
                    "Locked": "product_hero",  # Static, focused shots
                    "Gimbal": "establishing",  # Stabilized, cinematic movements
                }
                movement_category = camera_style_map.get(camera_style_override, scene_purpose)
                try:
                    camera_movement = random.choice(CAMERA_MOVEMENTS.get(movement_category, CAMERA_MOVEMENTS["establishing"]))
                except IndexError:
                    print(f"Warning: Empty camera movement list for {movement_category}. Using default.")
                    camera_movement = "Slow dolly push-in"
            else:
                # Use scene-appropriate default
                try:
                    camera_movement = random.choice(CAMERA_MOVEMENTS.get(scene_purpose, CAMERA_MOVEMENTS["establishing"]))
                except IndexError:
                     camera_movement = "Slow dolly push-in"

            # Select lighting setup based on scene
            # Priority: 1) User's lighting preference, 2) Scene-appropriate default
            if lighting_preference:
                # Map frontend lighting_preference to LIGHTING_SETUPS
                lighting_map = {
                    "Dramatic": "dramatic_cinematic",
                    "Natural": "natural_authentic",
                    "High Key": "high_key_commercial",
                    "Low Key": "low_key_moody",
                    "Neon": "neon_accent",
                    "Golden Hour": "golden_hour_warm",
                }
                lighting_key = lighting_map.get(lighting_preference)
                if lighting_key and lighting_key in LIGHTING_SETUPS:
                    lighting = LIGHTING_SETUPS[lighting_key]
                else:
                    # Fallback to random if mapping not found
                    lighting = random.choice(list(LIGHTING_SETUPS.values()))
            elif i == 0:
                # First scene default: dramatic or natural
                lighting = random.choice([LIGHTING_SETUPS["dramatic_cinematic"], LIGHTING_SETUPS["natural_authentic"]])
            else:
                # Other scenes: random selection
                lighting = random.choice(list(LIGHTING_SETUPS.values()))

            # Get professional equipment keywords
            equipment = get_random_equipment()

            # NEW: Enhanced scene guidance with emotional beat
            scene_guidance = f"""
            Scene {scene_num} ({duration}s) - {purpose}:
            - EMOTIONAL BEAT: [{emotion_key.upper()}] {emotional_direction}
            - Shot Size: {SHOT_SIZE_PROMPTS[shot_size]}
            - Camera Movement: {camera_movement}
            - Lighting: {lighting}
            - Color Grade: {color_grade}
            - Equipment: {equipment['camera']}, {equipment['lens']}
            - Format: {equipment['format']}
            """

            scene_guidance_list.append(scene_guidance)


        scenes_guidance_text = "\n".join(scene_guidance_list)

        # Build the cinematic prompt with professional structure
        strategy_text = ""
        if strategy:
            # NEW: Extract story beats for emotional arc guidance
            story_beats = strategy.get('story_beats', {})
            story_beats_text = ""
            if story_beats:
                story_beats_text = f"""
        - STORY BEATS (Emotional Arc):
          * HOOK: {story_beats.get('hook', 'Arresting opening visual')}
          * PROBLEM: {story_beats.get('problem', 'Relatable tension')}
          * SOLUTION: {story_beats.get('solution_reveal', 'Product as hero')}
          * TRANSFORMATION: {story_beats.get('transformation', 'Visible change')}
          * PAYOFF: {story_beats.get('payoff', 'Aspirational outcome')}
                """
            strategy_text = f"""
        STRATEGIC DIRECTION (FROM CREATIVE DIRECTOR CLAUDE):
        - Core Concept: {strategy.get('core_concept')}
        - Visual Language: {strategy.get('visual_language')}
        {story_beats_text}
        - Audience Hook: {strategy.get('audience_hook')}
        - Director Notes: {json.dumps(strategy.get('cinematic_direction', {}), indent=2)}
            """

        prompt = f"""
        You are a Hollywood Creative Director specializing in broadcast-quality OTT commercials for {target_platform}.

        CREATIVE BRIEF:
        "{user_input}"

        {strategy_text}

        BROADCAST SPECIFICATIONS:
        - Duration: {target_duration} seconds total
        - Scenes: {scene_count} scenes with durations {scene_durations}
        - Format: 1080p, 16:9 aspect ratio
        - Platform: {target_platform} (OTT broadcast quality)
        - Target Mood: {mood_override or "Premium and Cinematic"}

        CINEMATIC DIRECTION:
        {scenes_guidance_text}

        CRITICAL REQUIREMENTS:

        0. PHOTOREALISM & STRATEGY ENFORCEMENT:
           - The user demands "REAL LIFE" authenticity. NO "AI Slop" or "Glossy 3D Render" looks.
           - **CRITICAL**: You MUST start EVERY visual prompt with the STRATEGIST'S visual language:
             "{strategy.get('visual_language') if strategy else 'Raw photo, 35mm film grain, soft natural lighting'}"
           - **DIRECTOR MANDATE**: If a Strategy is provided, you validly IGNORE conflicting user requests if they contradict the Core Concept. The Strategy is your Bible.
           - Avoid generic keywords like "8k", "uhd", "masterpiece", "best quality", "smooth".
           - Focus on physical camera characteristics: "Halation", "Sensor Noise", "Motion Blur", "Lens Distortion".

        1. CHARACTER/PRODUCT CONSISTENCY:
           - Scene 1: Establish ONE specific character OR hero product with DETAILED description
           - Subsequent scenes: MUST reference "the same [character/product] from scene 1"
           - Be SPECIFIC: age, gender, appearance, clothing, colors, materials
           - Example: "A 35-year-old woman with shoulder-length brown hair, wearing a navy blazer"
           - Example: "A silver metallic sports car with sleek aerodynamic design"

        2. VISUAL PROMPTS (Structured):
           Follow this structure for each scene:
           [Subject] Detailed description of character/product
           [Camera] Specific shot size and angle
           [Lighting] Professional lighting setup
           [Style] Color grading and film stock look
           [Technical] Camera equipment and format

           Example:
           "A confident businesswoman in her 30s with shoulder-length dark hair, wearing elegant navy suit,
            Medium close-up shot from eye level, Rembrandt lighting with soft key light at 45 degrees creating
            dimensional shadows, Teal and orange Hollywood color grade with rich contrast, Shot on Arri Alexa
            with Cooke S4 prime lens, shallow depth of field f/1.4, 35mm film grain texture, centered in safe zone"

        3. MOTION PROMPTS:
           Use the professional camera movements provided in the guidance above.
           Be specific about speed, direction, and stabilization.
           NO jarring movements (OTT compliance).

        4. AUDIO PROMPTS (LAYERED FOR BROADCAST DEPTH):
           Create THREE audio layers for each scene:
           
           a) AMBIANCE LAYER: Environmental background sound
              Examples: "Soft morning city hum with distant traffic", "Quiet upscale office ambiance", "Nature forest with birdsong"
           
           b) SFX LAYER: Specific action/product sounds (if applicable)
              Examples: "Crisp coffee pour into ceramic cup", "Satisfying package unboxing snap", "Premium car door closing thud"
           
           c) MUSIC MOOD: Reference the strategy's audio_signature.music_mood
              Moods: epic | intimate | tech | playful | luxury | urgent | nostalgic | dramatic
           
           Format each scene's audio_prompt as:
           "AMBIANCE: [description]. SFX: [if applicable]. MUSIC MOOD: [mood keyword]"

        5. VOICEOVER (MULTI-BEAT PROGRESSIVE WITH AUDIO TAGS):
           Create 3-4 SHORT voiceover lines that BUILD with the emotional arc of the visuals.
           Each line should be 5-15 words MAX. The voiceover should PROGRESS emotionally:
           
           - Beat 1 (Hook, 0-3s): A question, provocative statement, or attention-grabber
           - Beat 2 (Tension, 3-7s): Acknowledge the pain/problem the audience feels  
           - Beat 3 (Transformation, 7-12s): Introduce the solution/shift
           - Beat 4 (Payoff, 12-{target_duration}s): Include the memorable_element (catchphrase/emotional moment)
           
           ELEVENLABS AUDIO TAGS (CRITICAL FOR EMOTIONAL DELIVERY):
           Embed these tags DIRECTLY in the voiceover text for emotional control:
           - [whispers] - Soft, intimate, ASMR-like delivery
           - [excited] - High energy, enthusiasm
           - [sad] - Melancholic, empathetic tone
           - [pause: 0.5s] - Dramatic pause for effect
           - [sighs] - Wistful or relieved exhale
           - [laughs] - Light chuckle for humor
           
           Example for 15s ad with Audio Tags:
           [
             {{ "speaker": "Narrator", "text": "[pause: 0.3s] The markets never sleep.", "time_range": "0-3s", "delivery": "gravitas" }},
             {{ "speaker": "Narrator", "text": "[sighs] And neither do you.", "time_range": "3-6s", "delivery": "empathetic" }},
             {{ "speaker": "Narrator", "text": "[excited] Until now.", "time_range": "6-10s", "delivery": "hopeful" }},
             {{ "speaker": "Narrator", "text": "Botspot. Your edge, always on.", "time_range": "10-{target_duration}s", "delivery": "confident" }}
           ]
           
           CRITICAL: Each line MUST have its own time_range. Include 'delivery' field for voice styling.

        6. SAFE ZONES:
           Keep all important subjects in center 80% of frame (title-safe).

        OUTPUT FORMAT (Valid JSON):
        {{
            "lines": [
                {{ "speaker": "Narrator", "text": "[Audio Tag] Hook line - attention grabber", "time_range": "0-3s", "delivery": "style" }},
                {{ "speaker": "Narrator", "text": "[Audio Tag] Problem line - acknowledge pain", "time_range": "3-6s", "delivery": "style" }},
                {{ "speaker": "Narrator", "text": "[Audio Tag] Solution line - introduce shift", "time_range": "6-10s", "delivery": "style" }},
                {{ "speaker": "Narrator", "text": "Payoff line with MEMORABLE ELEMENT", "time_range": "10-{target_duration}s", "delivery": "style" }}
            ],
            "mood": "{mood_override or 'Premium'}",
            "music_mood": "From strategy audio_signature or 'epic'",
            "memorable_element": "From strategy - the ONE thing viewers will remember",
            "scenes": [
                {{
                    "id": 1,
                    "visual_prompt": "Structured visual description following [Subject][Camera][Lighting][Style][Technical] format",
                    "motion_prompt": "Professional camera movement from guidance",
                    "audio_prompt": "AMBIANCE: [env sound]. SFX: [if any]. MUSIC MOOD: [mood]",
                    "duration": {scene_durations[0]}
                }}
                // ... {scene_count} total scenes
            ]
        }}

        SCENE PROGRESSION RULES (CRITICAL FOR ENGAGEMENT):
        - Scene 1 → Scene 2: The emotion must ESCALATE (e.g., tension builds from hook to problem)
        - Scene 2 → Scene 3: The emotion must PIVOT (e.g., problem meets discovery/hope)
        - Scene 3 → Scene 4: The emotion must RESOLVE (e.g., transformation leads to payoff)
        
        Each scene's visual and motion prompt should REFLECT its emotional beat.
        A "problem" scene should feel constrained; a "payoff" scene should feel expansive.
        
        Remember: Scenes 2+ MUST reference "the same character/product from scene 1" for consistency.
        """


        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown code blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]

            data = json.loads(text)

            # Validate scene count matches
            if len(data.get("scenes", [])) != scene_count:
                print(f"Warning: Expected {scene_count} scenes, got {len(data.get('scenes', []))}. Adjusting...")
                # If mismatch, take first N scenes or pad with duplicates
                scenes = data.get("scenes", [])
                if len(scenes) < scene_count:
                    # Pad with last scene duplicated
                    while len(scenes) < scene_count:
                        scenes.append(scenes[-1].copy())
                        scenes[-1]["id"] = len(scenes)
                else:
                    # Truncate to scene_count
                    scenes = scenes[:scene_count]
                data["scenes"] = scenes

            return Script(**data)

        except Exception as e:
            print(f"Error generating cinematic plan with Gemini: {e}")
            print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            raise e

    def critique_image(self, image_path: str, context_prompt: str) -> dict:
        """
        Uses Gemini Vision to critique an image.
        Returns: {"score": int, "reason": str}
        OPTIMIZATION: Uses SmartCritiqueCache to avoid redundant API calls (-$0.01 per commercial)
        """
        # Check cache first
        cached = self.critique_cache.get_cached_critique(context_prompt)
        if cached:
            print(f"[GEMINI VISION] Using cached critique for: {os.path.basename(image_path)}")
            return cached
            
        try:
            print(f"[GEMINI VISION] Critiquing: {os.path.basename(image_path)}...")
            
            # 1. Upload file
            myfile = genai.upload_file(image_path)
            
            # 2. Prompt
            system_prompt = f"""
            You are a strict Broadcast Quality Control Officer.
            Analyze this image generated for the prompt: "{context_prompt}".
            
            Check for:
            1. Text artifacting (gibberish text).
            2. Distorted faces or extra limbs.
            3. "AI Slop" (excessive smoothing).
            
            Rate the image from 1-10.
            - 1-6: FAIL (Re-generate).
            - 7-10: PASS (Broadcast Ready).
            
            Output JSON: {{ "score": int, "reason": "short explanation" }}
            """
            
            # 3. Generate
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            result = model.generate_content([myfile, system_prompt])
            
            # 4. Parse
            response_text = result.text
            
            # Robust JSON extraction
            try:
                if "```json" in response_text:
                     response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                     response_text = response_text.split("```")[1].split("```")[0].strip()
                
                critique_result = json.loads(response_text)
                # Cache the result for future use
                self.critique_cache.cache_critique(context_prompt, critique_result)
                return critique_result
            except json.JSONDecodeError:
                # Last ditch effort: find first { and last }
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(response_text[start:end])
                raise
            
        except Exception as e:
            print(f"[WARN] Critique failed: {e}")
            # Fail open - assume it's okay if critique fails, to avoid blocking flow
            return {"score": 8, "reason": "Critique bypassed due to error"}

    def _format_claude_scenes(self, user_input: str, config_overrides: dict, strategy: dict) -> Script:
        """
        FAST PATH: When Claude provides complete scene-level creative direction,
        Gemini just formats it into technical prompts. No creative generation needed.
        
        Claude's scenes contain: visual_direction, motion_direction, voiceover_content, sfx_description
        Gemini adds: cinematography keywords, equipment specs, prompt structure
        """
        scenes = strategy.get('scenes', [])
        visual_language = strategy.get('visual_language', 'Shot on 35mm film with natural grain')
        audio_signature = strategy.get('audio_signature', {})
        memorable_element = strategy.get('memorable_element', {})
        
        # Build a simplified prompt for Gemini to format Claude's directions
        prompt = f"""
        You are a Technical Prompt Formatter for an AI video generation pipeline.
        
        A Creative Director (Claude) has provided complete scene-level creative direction.
        Your ONLY job is to format their creative vision into technical prompts for image/video AI.
        
        DO NOT add your own creative ideas. DO NOT modify the emotional intent.
        ONLY format into the required technical structure.
        
        CREATIVE DIRECTOR'S VISION:
        - Core Concept: {strategy.get('core_concept')}
        - Visual Language: {visual_language}
        - Memorable Element: {memorable_element.get('description', '')}
        
        SCENES FROM CREATIVE DIRECTOR:
        {json.dumps(scenes, indent=2)}
        
        YOUR TASK:
        For each scene, create:
        1. visual_prompt: Combine the visual_direction with technical camera specs
           Structure: [Subject from visual_direction]. [Camera: shot type from composition_notes]. 
           [Style: {visual_language}]. [Technical: Arri Alexa, Cooke S4 prime, 35mm film grain]
        
        2. motion_prompt: Expand the motion_direction with technical animation keywords
           Add: "smooth camera movement", "natural motion blur", "organic handheld shake" as appropriate
        
        3. audio_prompt: Format as "AMBIANCE: [from sfx_description]. MUSIC MOOD: {audio_signature.get('music_mood', 'epic')}"
        
        4. Keep duration, id from the source scenes
        
        For voiceover lines:
        - Use the voiceover_content EXACTLY as written (including Audio Tags like [whispers], [pause])
        - Create one line per scene with appropriate time_range
        
        OUTPUT FORMAT (Valid JSON):
        {{
            "lines": [
                {{ "speaker": "Narrator", "text": "[exact voiceover_content from scene]", "time_range": "Xs-Ys", "delivery": "from emotional_goal" }}
            ],
            "mood": "{strategy.get('audio_signature', {}).get('music_mood', 'epic')}",
            "music_mood": "{audio_signature.get('music_mood', 'epic')}",
            "memorable_element": "{memorable_element.get('description', '')}",
            "scenes": [
                {{
                    "id": 1,
                    "visual_prompt": "[[Formatted from visual_direction + technical specs]]",
                    "motion_prompt": "[[Formatted from motion_direction + animation keywords]]",
                    "audio_prompt": "AMBIANCE: [[from sfx_description]]. MUSIC MOOD: [[mood]]",
                    "duration": [[from scene duration]]
                }}
            ]
        }}
        
        CRITICAL: Output valid JSON only. No markdown, no explanation.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            
            data = json.loads(text)
            
            print(f"[GEMINI] Formatted {len(data.get('scenes', []))} scenes from Claude's direction")
            return Script(**data)
            
        except Exception as e:
            print(f"[ERROR] Failed to format Claude scenes: {e}")
            print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            raise e

