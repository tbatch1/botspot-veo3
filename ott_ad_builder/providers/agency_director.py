"""
Agency Director Provider (The "Creative Agency" Pipeline)
Released: December 25, 2025

This provider implements a 4-step agentic workflow to generate high-quality,
story-driven commercial concepts. It replaces the monolithic single-prompt approach.

Pipeline:
1. Researcher: Grounds the ad in reality (Brand Bible).
2. Strategist: Develops the core angle and arc (Creative Strategy).
3. Screenwriter: Writes human dialogue and pacing (Screenplay).
4. Director: Translates to technical visual prompts (Production Plan).
"""

import json
import time
from openai import OpenAI, RateLimitError, APIStatusError
from ..config import config
from .base import LLMProvider

class AgencyDirector(LLMProvider):
    """
    Orchestrates the 4-step Creative Agency pipeline.
    """
    
    def __init__(self):
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("[AGENCY] Agency Director initialized.")
        else:
            print("[AGENCY] No OpenAI key found. Agency Director disabled.")
            
    def is_available(self) -> bool:
        return self.client is not None

    def generate_plan(self, user_input: str) -> dict:
        """Satisfy LLMProvider interface."""
        # We don't use this directly in the new pipeline, but ABC requires it.
        # Just map it to a partial pipeline run.
        _, script = self.run_pipeline(user_input, "", {}, 15)
        return script

    def _call_gpt(self, system_prompt: str, user_prompt: str, model: str = None) -> dict:
        """Helper to call GPT with retry logic and JSON enforcement."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        model = model or config.GPT52_MODEL # Default to best model
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                # Default kwargs
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "response_format": {"type": "json_object"}
                }
                
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                return json.loads(content)

            except Exception as e:
                # Handle 400 Unsupported Parameter (likely json_object mode or max_tokens not supported)
                if "unsupported_parameter" in str(e).lower() or "400" in str(e):
                    print(f"[AGENCY] Model {model} rejected params ({e}). Retrying with minimal params...")
                    try:
                        # Retry without potentially unsupported params
                        # O1 models dislike max_tokens (prefer max_completion_tokens) and response_format
                        kwargs.pop("response_format", None)
                        kwargs.pop("max_tokens", None)
                        
                        response = self.client.chat.completions.create(**kwargs)
                        content = response.choices[0].message.content
                        
                        # Strip standard markdown code blocks
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                            
                        return json.loads(content)
                    except Exception as e2:
                        print(f"[AGENCY] Raw retry failed: {e2}")
                        raise e2

                if isinstance(e, (RateLimitError, APIStatusError)):
                    if attempt < max_retries:
                        wait = 2 ** attempt * 2
                        print(f"[AGENCY] API Error: {e}. Retrying in {wait}s...")
                        time.sleep(wait)
                        continue
                
                # Check for JSON decode error
                if "Expecting value" in str(e) or "JSON" in str(e):
                    print(f"[AGENCY] JSON Decode Error ({e}). Retrying...")
                    if attempt < max_retries:
                         continue

                raise e

    # =========================================================================
    # STEP 1: RESEARCHER
    # =========================================================================
    def research_brand(self, topic: str, website_data: str) -> dict:
        print("[AGENCY] Step 1: Researcher is analyzing the brand...")
        
        system = """You are the Senior Researcher at a top ad agency.
Your goal: Analyze the raw input and extracted website data to create a "Brand Bible".
Focus on REALITY. Do not hallucinate features. If you don't know something, say "Unknown".
Identify the exact target audience and the "Killer Feature" that actually matters."""

        prompt = f"""
INPUT TOPIC: {topic}
WEBSITE VISUAL/TEXT DATA:
{website_data[:8000]}

OUTPUT JSON "BrandBible":
{{
    "brand_name": "Exact brand name",
    "brand_url": "The official website URL (e.g. www.brand.com) or null if not found",
    "product_category": "e.g. SaaS, Footwear, Beverage",
    "target_audience_avatar": {{
        "description": "Specific persona, e.g. 'Overworked 30s dad who loves grilling'",
        "pain_points": ["List 3 real problems they have"],
        "desires": ["List 3 things they deeply want"]
    }},
    "killer_feature": "The ONE thing this product does better than anything else (grounded in extraction)",
    "brand_voice": "Adjectives describing the tone (e.g. Witty, Serious, Premium)",
    "key_benefits": ["List 3 concrete benefits"],
    "visual_identity_clues": "Any colors, logos, or styles found in the website data"
}}
"""
        return self._call_gpt(system, prompt)

    # =========================================================================
    # STEP 2: STRATEGIST
    # =========================================================================
    def develop_strategy(self, brand_bible: dict, constraints: dict) -> dict:
        print("[AGENCY] Step 2: Strategist is developing the concept...")
        
        mood = constraints.get("mood", "General")
        style = constraints.get("style", "Cinematic")
        
        system = f"""You are the Creative Strategist.
Your goal: Develop a high-level creative concept based on the Brand Bible and Client Constraints.
You represent the "Big Idea".
Client Mood: {mood}
Client Style: {style}"""

        prompt = f"""
BRAND BIBLE:
{json.dumps(brand_bible, indent=2)}

TASK: Create a Creative Strategy.
1. Choose an "Angle" that fits the mood ({mood}).
2. Define a 3-act structure (Hook, Agitation/Journey, Payoff).
3. Define the Visual Style.

OUTPUT JSON "CreativeStrategy":
{{
    "concept_name": "Punchy title",
    "core_angle": "The 'what if' or core insight",
    "emotional_arc": "How the viewer feels Start -> Middle -> End",
    "visual_style_guide": {{
        "lighting": "e.g. Moody, High-Key, Neon",
        "camera": "e.g. Handheld, Steadycam, Macro",
        "color_palette": "List of colors"
    }},
    "audio_vibe": "Description of music and SFX style",
    "music_direction": {{
        "genre": "e.g. electronic_cinematic, trap_hype, ambient_chill, orchestral_epic",
        "energy_curve": "e.g. build -> drop -> sustain OR slow_burn -> climax OR steady_pulse",
        "bpm_feel": "slow (60-80), medium (90-110), fast (120-140), hype (140+)",
        "drop_timing": "When should the energy peak? e.g. '8 seconds' for hero shot reveal",
        "vibe_keywords": "3-5 words describing the sound: dark, punchy, ethereal, aggressive, smooth"
    }},
    "structure": {{
        "hook_beat": "What happens in first 3s?",
        "body_beat": "What happens in middle?",
        "payoff_beat": "What happens at end?"
    }},
    "visual_anchor": "DETAILED description of the primary visual element (e.g. the specific phone model, or the main character) that appears in every shot to ensure flow.",
    "brand_card": {{
        "brand_name": "Copy from Brand Bible",
        "url": "Copy 'brand_url' from Brand Bible EXACTLY. Do not fake it."
    }}
}}
"""
        return self._call_gpt(system, prompt)

    # =========================================================================
    # STEP 3: SCREENWRITER
    # =========================================================================
    def write_screenplay(self, brand_bible: dict, strategy: dict, duration: int) -> dict:
        print("[AGENCY] Step 3: Screenwriter is writing the script...")
        
        system = """You are a VIRAL CONTENT WRITER, not a corporate copywriter.

STYLE RULES:
1. Write like TikTok/Reels, not like TV ads.
2. REACTIONS over descriptions:
   - BAD: "This phone is incredibly fast."
   - GOOD: "Wait... it just did that?"
3. Max 6 words per line.
4. AT LEAST 1 scene MUST have dialogue for voiceover impact.
   Use the HERO SHOT scene for your best punchy line.

BANNED WORDS (instant fail - rewrite if you use these):
Experience, Discover, Revolutionary, Seamless, Innovative, 
Game-changing, Cutting-edge, Elevate, Unleash, Delve, 
Unprecedented, Transform, Empower, Synergy, Leverage

VIBE CHECK:
- Would a 22-year-old say this unironically? If not, rewrite.
- Could this be a meme caption? If yes, perfect.
- Is this something a real person would text their friend? That's the energy.

TIMING: Use 6s or 8s scenes. Avoid 4s unless it's a quick cut.
FLOW: 2-3 long scenes > 5 short choppy scenes.

CRITICAL - CTA SCENE (MANDATORY):
Your FINAL scene MUST be a Brand Card / CTA with:
- action_description: "Brand logo appears. QR code graphic. Clean dark background."
- dialogue_line: "Visit [brand_url] today." or just null for silent logo.
- This scene is NON-NEGOTIABLE. Every ad ends with CTA.
"""

        prompt = f"""
BRAND BIBLE: {json.dumps(brand_bible)}
STRATEGY: {json.dumps(strategy)}
TARGET DURATION: {duration} seconds

OUTPUT JSON "Screenplay":
{{
    "story_outline": "Write a punchy 2-sentence hook describing the vibe and energy. Think movie trailer logline.",
    "scenes": [
        {{
            "id": 1,
            "duration": 6,
            "action_description": "What we SEE. Visual-first. No people unless necessary.",
            "dialogue_line": "Short punchy line or null. Max 6 words.",
            "speaker": "Narrator or Character",
            "voice_hint": "hype_narrator | casual_friend | whisper_asmr | gen_z | silent",
            "visual_notes": "Setting, mood, camera move"
        }},
        ...
    ]
}}
"""
        return self._call_gpt(system, prompt)

    # =========================================================================
    # STEP 4: DIRECTOR
    # =========================================================================
    def direct_production(self, brand_bible: dict, strategy: dict, screenplay: dict) -> dict:
        print("[AGENCY] Step 4: Director is creating the shot list...")
        
        system = """You are the Director of Photography and Visual Director.
Your goal: Translate the screenplay into technical prompts for Veo/Runway.
Use professional terminology: 'Anamorphic', 'Bokeh', 'Dolly Zoom', 'Volumetric Light'.
Ensure CONSISTENCY of characters/branding across shots."""

        prompt = f"""
BRAND BIBLE: {json.dumps(brand_bible)}
STRATEGY: {json.dumps(strategy)}
SCREENPLAY: {json.dumps(screenplay)}

TASK: Create the final Production Plan.
1. START every `visual_prompt` with the VISUAL ANCHOR description from the strategy.
2. Use "Match Cut" or similar transition language to ensure FLOW between scenes.
3. Ensure the lighting/color matches the `visual_style_guide`.
4. The FINAL SCENE is a Brand Card. Visual Prompt must be: "Official logo of [Brand Name] on a clean, premium background. Text overlay 'Scan to Learn More'. High resolution graphic design."

OUTPUT JSON "ProductionPlan":
{{
    "scenes": [
        {{
            "id": 1,
            "visual_prompt": "[ANCHOR DESCRIPTION] ... rest of scene details. Cinematic lighting. 35mm film.",
            "audio_prompt": "Detailed audio description (SFX + Ambience).",
            "motion_prompt": "Description of camera movement and subject movement."
        }}
        ... (match all scenes in screenplay)
    ]
}}
"""
        return self._call_gpt(system, prompt)

    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================
    def run_pipeline(self, topic: str, website_data: str, constraints: dict, target_duration: int = 15) -> tuple:
        """
        Runs the full 4-step pipeline.
        Returns (strategy_dict, script_dict) compatible with the main backend.
        """
        if not self.client:
            raise RuntimeError("Agency Director not initialized")

        # Step 1: Research
        brand_bible = self.research_brand(topic, website_data)
        
        # Step 2: Strategy
        strategy_doc = self.develop_strategy(brand_bible, constraints)
        
        # Step 3: Writing
        screenplay = self.write_screenplay(brand_bible, strategy_doc, target_duration)
        
        # Step 4: Directing
        production_plan = self.direct_production(brand_bible, strategy_doc, screenplay)
        
        # =====================================================================
        # ADAPTER: Convert to Legacy Format (state.py / pipeline.py expectations)
        # =====================================================================
        
        # 1. Build Legacy Strategy Object
        # We merge the new "BrandBible" and "CreativeStrategy" into the old big dict structure
        
        # [CTA FIX] Use the brand_card from the Strategist if available (contains the URL)
        strat_card = strategy_doc.get("brand_card", {})
        
        final_strategy = {
            "core_concept": strategy_doc.get("concept_name"),
            "visual_language": json.dumps(strategy_doc.get("visual_style_guide")),
            "product_name": brand_bible.get("brand_name"),
            "brand_card": {
                "brand_name": brand_bible.get("brand_name"),
                "what_it_is": brand_bible.get("product_category") + " - " + brand_bible.get("killer_feature"),
                "category": brand_bible.get("product_category"),
                "target_audience": brand_bible.get("target_audience_avatar", {}).get("description"),
                "key_benefits": brand_bible.get("key_benefits", []),
                "voice": brand_bible.get("brand_voice"),
                "url": strat_card.get("url") or brand_bible.get("brand_url") # Ensure URL passes through
            },
            "applied_preferences": {
                "url": strat_card.get("url") or brand_bible.get("brand_url") # Redundant safety
            },
            "audio_signature": {
                "bgm_prompt": strategy_doc.get("audio_vibe"),
                "sfx_style": "Cinematic"
            }
        }
        
        # 3. Populate Characters for Better TTS
        # Scan screenplay for speakers and create character profiles
        unique_speakers = set()
        if screenplay and "scenes" in screenplay:
            for s in screenplay["scenes"]:
                spk = s.get("speaker")
                if spk and spk not in ["Narrator", ""]:
                    unique_speakers.add(spk)
        
        chars_list = []
        for spk in unique_speakers:
            chars_list.append({
                "name": spk,
                "description": f"Main character, {brand_bible.get('brand_voice', 'Authentic')} voice",
                "voice_style": "Expressive, American, Professional" 
            })
            
        # Add Narrator if script has narration logic (implied or explicit)
        chars_list.append({
            "name": "Narrator",
            "description": "Professional Voiceover Artist",
            "voice_style": "Deep, Cinematic, Trailer-style"
        })
        
        final_strategy["characters"] = chars_list
        
        # 2. Build Legacy Script Object
        final_scenes = []
        final_lines = []
        
        # Merge Screenplay and Production Plan
        # They should have matching IDs and order
        sp_scenes = screenplay.get("scenes", [])
        pp_scenes = production_plan.get("scenes", [])
        
        # Create a map for production plan scenes by ID
        pp_map = {s.get("id"): s for s in pp_scenes}
        
        current_time = 0.0
        
        for sp_scene in sp_scenes:
            sid = sp_scene.get("id")
            pp_scene = pp_map.get(sid, {})
            
            dur = float(sp_scene.get("duration", 4))
            
            # Create Scene Object
            scene_obj = {
                "id": sid,
                "duration": dur,
                "primary_subject": brand_bible.get("brand_name"), # Default
                "subject_description": sp_scene.get("action_description"),
                "visual_prompt": pp_scene.get("visual_prompt", sp_scene.get("action_description")),
                "audio_prompt": pp_scene.get("audio_prompt", ""),
                "motion_prompt": pp_scene.get("motion_prompt", "")
            }
            final_scenes.append(scene_obj)
            
            # Create ScriptLine Object (if dialogue exists)
            dialogue = sp_scene.get("dialogue_line")
            speaker = sp_scene.get("speaker")
            if dialogue and speaker:
                final_lines.append({
                    "scene_id": sid,
                    "speaker": speaker,
                    "text": dialogue,
                    "time_range": f"{current_time}s-{current_time + dur}s"
                })
                
            current_time += dur
            
        final_script = {
            "mood": constraints.get("mood", "General"),
            "scenes": final_scenes,
            "lines": final_lines
        }
        
        print("[AGENCY] Pipeline complete. Returning legacy-compatible objects.")
        return final_strategy, final_script
