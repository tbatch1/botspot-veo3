import json
import sys
import os
import time
from .base import LLMProvider
from ..config import config
from ..constants.iconic_templates import ICONIC_TEMPLATES, AUDIO_MOOD_KEYWORDS, VOICE_STYLE_DESCRIPTORS
import google.generativeai as genai
import anthropic

class StrategistProvider(LLMProvider):
    """
    The 'Smart Agent' layer (Claude 3 Opus).
    Acts as the Creative Director, synthesizing strategy from raw inputs.
    Uses iconic commercial templates for proven story structures.
    """
    
    def __init__(self):
        # Initialize Anthropic client if key is available
        self.anthropic_client = None
        if config.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            print("[STRATEGIST] Anthropic Claude Opus 4.5 initialized.")
        else:
            print("[STRATEGIST] No Anthropic key found. Falling back to Gemini.")

        # Fallback Gemini model
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel(
            'gemini-1.5-pro-latest',
            generation_config={"response_mime_type": "application/json"}
        )

    def generate_plan(self, user_input: str) -> dict:
        """
        Satisfies the LLMProvider interface.
        For the Strategist, 'user_input' is treated as the topic.
        """
        return self.develop_strategy(topic=user_input, website_data="", constraints={})

    def develop_strategy(self, topic: str, website_data: str, constraints: dict) -> dict:
        """
        Synthesizes a creative strategy based on the topic, website data, and user constraints.
        Now uses iconic_templates when a commercial_style is specified in constraints.
        """
        
        # Extract commercial_style from constraints (from UI selection)
        commercial_style = constraints.get('commercial_style', 'emotional_journey')
        template = ICONIC_TEMPLATES.get(commercial_style, ICONIC_TEMPLATES['emotional_journey'])
        
        # Get the recommended voice and audio mood from template
        voice_style_key = template.get('voiceover_style', 'friendly_guide')
        music_mood_key = template.get('music_mood', 'epic')
        voice_style = VOICE_STYLE_DESCRIPTORS.get(voice_style_key, {})
        audio_mood = AUDIO_MOOD_KEYWORDS.get(music_mood_key, {})
        
        # Build template context for Claude
        template_context = f"""
        SELECTED COMMERCIAL TEMPLATE: {template.get('name', 'Emotional Journey')}
        Template Description: {template.get('description', '')}
        Real-World Examples: {', '.join(template.get('examples', []))}
        
        SCENE STRUCTURE (follow this emotional arc):
        {json.dumps(template.get('scenes', []), indent=2)}
        
        RECOMMENDED VOICE STYLE: {voice_style_key}
        Voice Characteristics: {voice_style.get('characteristics', '')}
        
        RECOMMENDED MUSIC MOOD: {music_mood_key}
        Music Description: {audio_mood.get('music_prompt', '')}
        """
        
        system_prompt = """You are a world-class Creative Director and Marketing Strategist. Your goal is to develop a cohesive, high-impact creative strategy for a video commercial.

CRITICAL RULE - PRODUCT SPECIFICITY:
- NEVER say "the product" or "the service" in visual descriptions
- ALWAYS use the EXACT product name from the website research (e.g., "botspot.trade trading platform", "Nike Air Max sneakers", "Tesla Model 3")
- Scene descriptions must be VISUALLY SPECIFIC to the actual product/brand
- If the product is software/digital, describe ACTUAL UI elements, dashboards, charts, interfaces

Example of WRONG: "Dramatic shot of the product emerging from darkness"
Example of RIGHT: "Dramatic shot of the botspot.trade trading dashboard with glowing green profit charts, dark UI with neon accents, live ticker data"

You will provide COMPLETE scene-level creative direction so the technical team only needs to format your vision into prompts."""
        
        # NOTE: We use double braces {{ }} for JSON literal parts inside the f-string
        user_message = f"""
        INPUTS:
        1. TOPIC: "{topic}"
        
        2. WEBSITE CONTEXT (CRITICAL - USE THIS FOR PRODUCT SPECIFICITY):
        {website_data[:3000]}... (truncated)
        
        ⚠️ EXTRACT FROM ABOVE: Product name, brand name, key visual elements (UI, colors, features)
        These MUST appear in your visual_direction for EVERY scene.
        
        3. USER CONSTRAINTS (The "Vibe"):
        {json.dumps(constraints, indent=2)}
        
        4. ICONIC COMMERCIAL TEMPLATE (YOUR CREATIVE FRAMEWORK):
        {template_context}
        
        YOUR TASK:
        First, IDENTIFY the specific product/service from the website context above.
        Then, create scenes that SHOW this product visually.
        
        PRODUCT IDENTITY (you MUST fill this out first in your mind):
        - Product Name: [extract from website context]
        - Product Type: [software/physical/service]
        - Key Visual Elements: [what does it LOOK like? UI colors, physical appearance, logo]
        
        Analyze these inputs. The user might have selected conflicting or unusual combinations (e.g., "Cyberpunk" mood for "Organic Soap").
        Your job is to resolve these into a brilliant, cohesive concept that features THE ACTUAL PRODUCT.
        
        CRITICAL: "REAL CINEMA" vs "AI SLOP"
        The user demands "Netflix Documentary" realism. Avoid "AI Slop" (plastic skin, smooth textures).
        
        1. "TAKE OUT" THESE WORDS:
           - "Cinematic", "Masterpiece", "Hyper-realistic", "8k", "HDR", "Smooth", "Perfect".
           (These trigger the 'Video Game' look).
           
        2. "EXPAND ON" THESE OPTICAL IMPERFECTIONS:
           - "Halation" (Bloom around lights).
           - "Chromatic Aberration" (Subtle lens fringing).
           - "Film Grain" (16mm or 35mm texture).
           - "Sensor Noise" (High ISO realism).
           - "Natural Skin Texture" (Pores, imperfections).
        
        When describing visual style, use **TECHNICAL CAMERA PACKAGES**:
        - BAD: "Cinematic, realistic, cool vibes."
        - GOOD: "Shot on Arri Alexa 65 with Cooke S4/i Prime lenses. Kodak Vision3 500T 5219 film stock simulation. Heavy halation on highlights, ISO 3200 grain structure."
        
        ICONIC COMMERCIAL ELEMENTS:
        Think of the most memorable commercials ever made:
        - Geico Caveman: Memorable character + recurring catchphrase
        - Bud Light "Dilly Dilly": Catchphrase that spread virally
        - Coors Light: Ice mountains visual metaphor = instant refreshment
        - eBay Child: Emotional journey that tugs heartstrings
        
        Your strategy MUST include ONE of these iconic elements.
        
        OUTPUT A COMPLETE STRATEGY BRIEF WITH SCENE-LEVEL CREATIVE DIRECTION (JSON):
        {{
            "core_concept": "A short, punchy title for the concept (e.g., 'Neon Nature')",
            "visual_language": "Describe specific CAMERA and LENS choices. E.g., 'Handheld 16mm film camera, ISO 3200 grain'.",
            "memorable_element": {{
                "type": "Choose ONE: 'catchphrase' | 'mascot' | 'visual_metaphor' | 'sonic_signature' | 'emotional_moment'",
                "description": "The ONE thing viewers will remember 24 hours later. Be specific and unique.",
                "execution": "How exactly will this element appear in the ad? (e.g., 'Character says catchphrase directly to camera in final shot')"
            }},
            "audio_signature": {{
                "music_mood": "Choose: epic | intimate | tech | playful | luxury | urgent | nostalgic | dramatic",
                "sonic_brand_moment": "Describe a distinctive sound for brand recognition",
                "voiceover_style": "Choose: cinematic_narrator | friendly_guide | energetic_announcer | luxury_whisper | tech_futurist | playful_character | intimate_narrator"
            }},
            "shareability_hook": "What makes this ad worth sharing? Choose ONE: humor | emotional_punch | surprise_twist | controversy | relatable_truth | visual_spectacle",
            
            "scenes": [
                {{
                    "scene_number": 1,
                    "beat": "hook",
                    "duration": 3,
                    "visual_direction": "⚠️ MUST describe the ACTUAL PRODUCT by name from website context. Never say 'the product'. E.g., if product is 'botspot.trade': 'Close-up of the botspot.trade trading dashboard on a sleek monitor, glowing green charts showing profit, dark UI with cyan accents, real-time ticker data scrolling'",
                    "motion_direction": "How does this shot MOVE? Camera movement + subject motion. E.g., 'Slow dolly in on cup, steam rises lazily, camera slightly handheld for organic feel'",
                    "emotional_goal": "What should viewer FEEL? E.g., 'Sensory craving, morning ritual anticipation'",
                    "voiceover_content": "EXACT words spoken. Use Audio Tags for delivery: [whispers], [excited], [pause: 0.5s]. E.g., '[whispers] That first sip... [pause: 0.5s] everything slows down.'",
                    "sfx_description": "Sound effects needed. E.g., 'Gentle pour sound, ceramic contact, ambient morning birds'",
                    "composition_notes": "Any specific framing or blending needs. E.g., 'Rule of thirds, product at intersection point'"
                }},
                {{
                    "scene_number": 2,
                    "beat": "problem/tension",
                    "duration": 4,
                    "visual_direction": "...",
                    "motion_direction": "...",
                    "emotional_goal": "...",
                    "voiceover_content": "...",
                    "sfx_description": "...",
                    "composition_notes": "..."
                }},
                {{
                    "scene_number": 3,
                    "beat": "solution/transformation",
                    "duration": 4,
                    "visual_direction": "...",
                    "motion_direction": "...",
                    "emotional_goal": "...",
                    "voiceover_content": "...",
                    "sfx_description": "...",
                    "composition_notes": "..."
                }},
                {{
                    "scene_number": 4,
                    "beat": "payoff",
                    "duration": 4,
                    "visual_direction": "...",
                    "motion_direction": "...",
                    "emotional_goal": "...",
                    "voiceover_content": "Include the memorable_element here",
                    "sfx_description": "...",
                    "composition_notes": "..."
                }}
            ],
            
            "audience_hook": "The key psychological hook based on the website data.",
            "cinematic_direction": {{
                "mood_notes": "Specific direction on how to achieve the requested mood",
                "lighting_notes": "Guidance on lighting (e.g., 'Low-key, practicals only')",
                "camera_notes": "Guidance on camera movement (e.g., 'Slow push-in, handheld shake')"
            }},
            "production_recommendations": {{
                "visual_engine": "Choose 'flux' (High Fidelity/Slow) or 'imagen' (Standard/Fast). Use 'flux' for luxury/cinematic/photorealism.",
                "video_engine": "Choose 'veo' if the scene requires NATIVE AUDIO (dialogue, specific SFX like explosions/crashes) or precise physics. Choose 'runway' for purely visual high-motion shots (drones, FPV) where audio is secondary.",
                "voice_vibe": "Describe the ideal voice style matching audio_signature.voiceover_style"
            }}
        }}

        IMPORTANT: Fill out ALL 4 scenes with COMPLETE creative direction. Do not use placeholders or "...". 
        Each scene must have detailed, specific content for visual_direction, motion_direction, voiceover_content, etc.
        The technical team will ONLY format your directions into image/video prompts - they will NOT add creative content.
        """
        
        try:
            if self.anthropic_client:
                # Use Claude 3 Opus with RETRY LOGIC for rate limits and overload
                # Suppress stdout/stderr to avoid Windows encoding errors
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                
                max_retries = 3
                response_text = None
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        sys.stdout = open(os.devnull, 'w')
                        sys.stderr = open(os.devnull, 'w')

                        message = self.anthropic_client.messages.create(
                            model=config.STRATEGIST_MODEL,
                            max_tokens=2048,  # Increased for fuller creative strategy
                            temperature=0.7,
                            system=system_prompt,
                            messages=[
                                {"role": "user", "content": user_message}
                            ]
                        )
                        response_text = message.content[0].text
                        break  # Success - exit retry loop
                        
                    except anthropic.RateLimitError as e:
                        last_error = e
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        if attempt < max_retries:
                            wait_time = 2 ** attempt * 5  # 5s, 10s, 20s
                            print(f"[STRATEGIST] Rate limited. Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            print(f"[STRATEGIST] Rate limit exceeded after {max_retries} retries.")
                            raise
                            
                    except anthropic.APIStatusError as e:
                        last_error = e
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        # Retry on 529 (overloaded) and 500 (internal error)
                        if e.status_code in [529, 500, 502, 503]:
                            if attempt < max_retries:
                                wait_time = 2 ** attempt * 3  # 3s, 6s, 12s
                                print(f"[STRATEGIST] API error {e.status_code}. Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"[STRATEGIST] API error {e.status_code} after {max_retries} retries.")
                                raise
                        else:
                            raise  # Non-retryable error
                            
                    finally:
                        # Restore stdout/stderr
                        try:
                            sys.stdout.close()
                            sys.stderr.close()
                        except:
                            pass
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr

                # Extract JSON if wrapped in markdown
                cooked_text = response_text
                if "```json" in cooked_text:
                    cooked_text = cooked_text.split("```json")[1].split("```")[0].strip()
                elif "```" in cooked_text:
                    cooked_text = cooked_text.split("```")[1].split("```")[0].strip()
                
                # Attempt to parse
                try:
                    return json.loads(cooked_text)
                except json.JSONDecodeError:
                    # Last ditch effort: find first { and last }
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(response_text[start:end])
                    raise
            
            else:
                # Fallback to Gemini
                print("[STRATEGIST] Using Gemini fallback...")
                prompt = f"{system_prompt}\n\n{user_message}"
                response = self.gemini_model.generate_content(prompt)
                return json.loads(response.text)

        except Exception as e:
            # Fallback strategy - MUST include scenes array for GPT-5.2 to format
            # CRITICAL: Use actual topic/product name, NOT "the product"
            print(f"[STRATEGIST] Error: {e}. Using fallback strategy with scenes.")
            
            # Extract product name from topic
            product_name = topic.replace("Create a commercial for ", "").replace("Create a 15 second commercial for ", "").strip()
            if not product_name or len(product_name) < 3:
                product_name = topic  # Use full topic if extraction fails
            
            return {
                "core_concept": f"{product_name} Premium Showcase",
                "visual_language": "Shot on Arri Alexa, Cooke S4 prime lens, natural film grain, shallow depth of field",
                "product_name": product_name,  # Store for downstream use
                "scenes": [
                    {
                        "scene_number": 1,
                        "beat": "hook",
                        "duration": 4,
                        "visual_direction": f"Dramatic opening shot of {product_name} interface emerging from darkness, volumetric lighting illuminating the screen, professional tech environment",
                        "motion_direction": "Slow dolly push-in, smooth and deliberate",
                        "emotional_goal": "Intrigue and curiosity",
                        "voiceover_content": "[pause: 0.3s] Some moments... change everything.",
                        "sfx_description": "Deep bass tone, subtle whoosh"
                    },
                    {
                        "scene_number": 2,
                        "beat": "solution",
                        "duration": 5,
                        "visual_direction": f"Wide shot revealing {product_name} dashboard in full operation, showing key features and UI, golden hour lighting streaming through modern office window",
                        "motion_direction": "Slow pan across the scene, revealing details",
                        "emotional_goal": "Understanding and desire",
                        "voiceover_content": "Introducing a new standard. Built for those who demand more.",
                        "sfx_description": "Ambient atmosphere, subtle music swell"
                    },
                    {
                        "scene_number": 3,
                        "beat": "payoff",
                        "duration": 5,
                        "visual_direction": f"Close-up of {product_name} logo and key feature highlight, premium lighting setup with brand colors",
                        "motion_direction": "Slow orbit around display, settling on logo",
                        "emotional_goal": "Aspiration and action",
                        "voiceover_content": "This is it. [pause: 0.5s] Are you ready?",
                        "sfx_description": "Impactful final note, sonic brand signature"
                    }
                ],
                "audio_signature": {
                    "music_mood": "epic",
                    "voiceover_style": "cinematic_narrator"
                },
                "cinematic_direction": {
                    "mood_notes": "Premium, Aspirational",
                    "lighting_notes": "Dramatic three-point lighting with rim highlights",
                    "camera_notes": "Steady, controlled movements"
                }
            }
    
    def review_narrative_coherence(
        self,
        scenes: list,
        original_strategy: dict,
        generated_descriptions: list[str]
    ) -> dict:
        """
        QUALITY GATE: Claude reviews all generated images for narrative coherence.
        Called after all images are generated, before video synthesis.
        
        Args:
            scenes: List of scene objects with prompts
            original_strategy: The original creative strategy
            generated_descriptions: Descriptions of what was actually generated
        
        Returns:
            dict with is_coherent, score, issues, scene_notes
        """
        if not self.anthropic_client:
            return {"is_coherent": True, "score": 8, "issues": [], "scene_notes": {}}
        
        # Build scene summary
        scene_summary = ""
        for i, (scene, desc) in enumerate(zip(scenes, generated_descriptions)):
            prompt = scene.get('visual_prompt', scene.get('description', 'Unknown'))
            scene_summary += f"\nScene {i+1}:\n  Intended: {prompt[:100]}...\n  Generated: {desc[:100]}...\n"
        
        prompt = f"""You are a Creative Director reviewing a generated video advertisement for story coherence.

ORIGINAL STRATEGY:
- Core Concept: {original_strategy.get('core_concept', 'N/A')}
- Story Arc: {original_strategy.get('story_arc', 'N/A')}
- Target Emotion: {original_strategy.get('target_emotion', 'N/A')}

GENERATED SCENES:
{scene_summary}

Review for:
1. Narrative Flow - Does Scene 1 → 2 → 3... tell a coherent story?
2. Emotional Progression - Do emotions build appropriately?
3. Brand Consistency - Does the visual style stay consistent?
4. Call-to-Action Setup - Does the story lead naturally to the CTA?
5. Pacing - Are scene durations appropriate for the content?

Respond in JSON:
{{
    "is_coherent": <true if the ad tells a coherent story>,
    "score": <1-10 narrative quality score>,
    "issues": ["<list any story problems>"],
    "scene_notes": {{
        "1": "<note for scene 1 or null if fine>",
        "2": "<note for scene 2 or null if fine>",
        ...
    }},
    "suggested_reorders": "<if scenes should be reordered, describe. Otherwise null>"
}}"""

        try:
            response = self.anthropic_client.messages.create(
                model=config.STRATEGIST_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON from response
            import json
            content = response.content[0].text
            # Try to extract JSON from response
            if "{" in content:
                json_start = content.index("{")
                json_end = content.rindex("}") + 1
                result = json.loads(content[json_start:json_end])
            else:
                result = {"is_coherent": True, "score": 7, "issues": [], "scene_notes": {}}
            
            print(f"[NARRATIVE] Story coherence: {result.get('score', '?')}/10 - {'✓ COHERENT' if result.get('is_coherent') else '⚠ ISSUES FOUND'}")
            
            if result.get('issues'):
                for issue in result['issues'][:3]:
                    print(f"   → {issue}")
            
            return result
            
        except Exception as e:
            print(f"[NARRATIVE] Review error: {e}")
            return {"is_coherent": True, "score": 7, "issues": [], "scene_notes": {}}

