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
import os
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

    def rewrite_line_for_slot(
        self,
        *,
        strategy: dict,
        scene: dict | None,
        speaker: str,
        original_text: str,
        slot_seconds: float,
        max_words: int,
        max_sentence_endings: int,
        measured_audio_seconds: float | None = None,
    ) -> str:
        """
        Rewrite a single dialogue line so it fits comfortably in its time slot.

        Keeps meaning and tone, but shortens wording and reduces pauses.
        Returns rewritten text (string) or "" on failure.
        """
        if not self.client:
            return ""

        import re

        brand_card = strategy.get("brand_card") if isinstance(strategy, dict) else {}
        characters = strategy.get("characters") if isinstance(strategy, dict) else None
        if not isinstance(characters, list):
            characters = []

        voice_style = ""
        for ch in characters:
            if not isinstance(ch, dict):
                continue
            name = str(ch.get("name") or "").strip()
            if name and name == speaker:
                voice_style = str(ch.get("voice_style") or "").strip()
                break

        visual_beat = ""
        on_screen = []
        if isinstance(scene, dict):
            visual_beat = str(scene.get("visual_beat") or scene.get("visual_prompt") or "").strip()
            visual_beat = visual_beat.split("\n", 1)[0][:240]
            on_screen = scene.get("on_screen") if isinstance(scene.get("on_screen"), list) else []
        if not on_screen and speaker:
            on_screen = [speaker]

        payload = {
            "brand_card": brand_card if isinstance(brand_card, dict) else {},
            "speaker": speaker,
            "voice_style": voice_style,
            "visual_beat": visual_beat,
            "on_screen": on_screen,
            "slot_seconds": float(slot_seconds),
            "max_words": int(max_words),
            "max_sentence_endings": int(max_sentence_endings),
            "measured_audio_seconds": float(measured_audio_seconds) if measured_audio_seconds is not None else None,
            "original_text": str(original_text or "").strip(),
        }

        prompt = f"""You are a TV commercial dialogue pacing editor.
Rewrite ONE line so it can be spoken naturally within its slot.

CRITICAL RULES:
- Output ONLY JSON: {{\"text\": \"...\"}}
- Keep the same intent/meaning. Keep it human, spoken, and specific.
- Speaker must sound like their voice_style.
- Must fit the slot:
  - max_words: {max_words}
  - sentence-ending punctuation (.,!,?) <= {max_sentence_endings} (prefer commas for rhythm)
  - avoid extra pauses, avoid multiple short sentences in tight slots
- If measured_audio_seconds is provided and it's longer than slot_seconds, shorten more.
- Do NOT mention domains (no .com/.trade/etc).
- No profit guarantees or claims of specific returns. No financial advice language.
- ASCII punctuation only (no smart quotes/em dashes). End the line cleanly with punctuation.
- Do NOT add tags unless absolutely necessary (max 1 tag like [sighs]).

INPUT:
{json.dumps(payload, ensure_ascii=False)}
"""

        try:
            result = self._call_with_retry([{"role": "user", "content": prompt}])
        except Exception:
            return ""

        text = ""
        if isinstance(result, dict):
            text = str(result.get("text") or "").strip()

        if not text:
            return ""

        # Safety normalize: collapse whitespace, strip weird chars, keep ASCII punctuation.
        text = re.sub(r"\s+", " ", text).strip()
        text = (
            text.replace("\u2019", "'")
            .replace("\u2018", "'")
            .replace("\u201c", "\"")
            .replace("\u201d", "\"")
            .replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("\u2026", "...")
        )
        # Hard ASCII fallback (prevents encoding artifacts / odd TTS pronunciation).
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"\s+", " ", text).strip()
        return text
    
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
            raise RuntimeError("GPT-5.2 client not initialized. Set OPENAI_API_KEY.")
        
        def _first_or_default(value, default: str) -> str:
            if isinstance(value, list):
                return str(value[0]).strip() if value else default
            if value is None:
                return default
            s = str(value).strip()
            return s if s else default

        def _join_or_default(value, default: str) -> str:
            if isinstance(value, list):
                parts = [str(v).strip() for v in value if str(v).strip()]
                joined = ", ".join(parts)
                return joined if joined else default
            if value is None:
                return default
            s = str(value).strip()
            return s if s else default

        def _brand_from_website_data(text: str) -> str:
            """
            Try to extract a human brand name from ResearcherProvider output.
            Expected lines include: "OG Title:", "Title:", etc.
            """
            if not text:
                return ""

            for prefix in ("OG Title:", "Title:", "OG Description:", "Description:"):
                for line in str(text).splitlines():
                    if not line.startswith(prefix):
                        continue
                    value = line[len(prefix):].strip()
                    if not value:
                        continue
                    # Common SEO formats: "Brand - Tagline", "Brand | Tagline", "Brand: Tagline"
                    for sep in (" - ", " | ", ": ", " — ", " – "):
                        if sep in value:
                            value = value.split(sep, 1)[0].strip()
                            break
                    return value

            return ""

        def _looks_like_url_or_domain(value: str) -> bool:
            s = (value or "").strip()
            lower = s.lower()
            if not s:
                return False
            if lower.startswith(("http://", "https://")):
                return True
            # Single token containing a dot is usually a domain (e.g. botspot.trade).
            if "." in s and " " not in s:
                return True
            # URL-ish paths/queries.
            if "/" in s or "?" in s or "#" in s:
                return True
            return False
 
        # Prefer UI-provided topic. Users may paste either:
        # - a brand name ("Nike")
        # - a domain ("nike.com")
        # - a full brief sentence ("Make a funny ad for my sneaker brand...")
        # We'll sanitize and, when a URL is present, prefer website metadata for the brand name.
        topic_field = _first_or_default(constraints.get("topic"), "")
        product_name = topic_field

        website_brand = _brand_from_website_data(website_data)

        def _looks_like_brand_candidate(value: str) -> bool:
            s = (value or "").strip()
            if not s:
                return False
            if _looks_like_url_or_domain(s):
                return True
            # Long multi-sentence input is usually a brief, not a clean brand name.
            if len(s) > 40:
                return False
            words = [w for w in s.split() if w]
            if len(words) > 4:
                return False
            return True

        # If the user supplied a URL but typed a long brief into Topic, use the website brand name
        # so VO doesn't try to "say" the entire brief as the product name.
        if website_brand and str(constraints.get("url") or "").strip() and topic_field and not _looks_like_brand_candidate(topic_field):
            product_name = website_brand

        # Fallback: extract product name from the full user prompt string.
        if not product_name:
            cleaned = (topic or "").replace("Create a commercial for ", "").replace("Create a 15 second commercial for ", "")
            # If the prompt includes extra lines like "Style:", strip those.
            cleaned = cleaned.split("\n")[0]
            cleaned = cleaned.split("Style:", 1)[0]
            cleaned = cleaned.strip()
            # If the user appended requirements after a period, strip those.
            if ". " in cleaned and len(cleaned) > 40:
                cleaned = cleaned.split(". ", 1)[0].strip()
            product_name = cleaned or "Your Product"

        # If the user pasted a URL/domain into the prompt, use website metadata to
        # recover the actual brand name (e.g. "BotSpot" instead of "botspot.trade").
        if website_brand:
            product_name_str = str(product_name or "")
            if (
                product_name in ("Your Product", "Product", "Website")
                or _looks_like_url_or_domain(product_name_str)
                or (website_brand.lower() in product_name_str.lower())
            ):
                product_name = website_brand

        # If constraints include a URL and the product name is still generic, use the domain.
        if constraints.get("url") and product_name in ("Your Product", "Product", "Website"):
            url = str(constraints.get("url") or "")
            product_name = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0] or product_name

        # If the user typed a sentence in the Topic field ("Brand is a ..."), keep only the brand name.
        if isinstance(product_name, str):
            candidate = product_name.strip()
            lowered = candidate.lower()
            if " is " in lowered:
                candidate = candidate.split(" is ", 1)[0].strip()
            candidate = candidate.strip(" .")
            if candidate:
                product_name = candidate

        def _domain_to_brand(value: str) -> str:
            """
            Convert a URL/domain-ish string into a human-readable brand token.
            Examples: "https://botspot.trade" -> "Botspot", "store.nike.com" -> "Nike"
            """
            from urllib.parse import urlparse

            raw = (value or "").strip()
            if not raw:
                return ""

            parsed = urlparse(raw if raw.lower().startswith(("http://", "https://")) else f"https://{raw}")
            host = (parsed.hostname or "").strip()
            if not host:
                # Fallback: strip scheme/path manually.
                host = raw.replace("https://", "").replace("http://", "").split("/")[0].strip()

            host = host.lower().lstrip("www.")
            parts = [p for p in host.split(".") if p]
            base = ""
            if len(parts) >= 2:
                # Handle common ccTLD patterns like bbc.co.uk
                if len(parts[-1]) == 2 and parts[-2] in ("co", "com", "net", "org") and len(parts) >= 3:
                    base = parts[-3]
                else:
                    base = parts[-2]
            elif parts:
                base = parts[0]

            base = base.replace("-", " ").replace("_", " ").strip()
            base = " ".join(w for w in base.split() if w)
            return base.title() if base else ""

        # Ensure PRODUCT/BRAND is a human-readable name, not a raw domain.
        if isinstance(product_name, str) and _looks_like_url_or_domain(product_name):
            cleaned_brand = _domain_to_brand(product_name)
            if cleaned_brand:
                product_name = cleaned_brand

        style = _join_or_default(constraints.get("style"), "Cinematic")
        mood = _join_or_default(constraints.get("mood"), "Premium")
        platform = _join_or_default(constraints.get("platform"), "Netflix")
        camera_style = _join_or_default(constraints.get("camera_style"), "")
        lighting_preference = _first_or_default(constraints.get("lighting_preference"), "")
        color_grade = _first_or_default(constraints.get("color_grade"), "")
        commercial_style = _first_or_default(constraints.get("commercial_style"), "")
        source_url = _first_or_default(constraints.get("url"), "")
        image_guidance = _first_or_default(constraints.get("image_guidance"), "")
        reference_style_guide = str(constraints.get("reference_style_guide") or "").strip()

        template_guidance = ""
        if commercial_style:
            try:
                from ..constants.iconic_templates import ICONIC_TEMPLATES

                template = ICONIC_TEMPLATES.get(commercial_style)
                if template:
                    examples = ", ".join(template.get("examples", [])[:3])
                    beats = template.get("scenes", []) or []
                    voiceover_style_key = str(template.get("voiceover_style") or "").strip()
                    music_mood_key = str(template.get("music_mood") or "").strip()
                    template_guidance = (
                        f"- Commercial template: {template.get('name', commercial_style)}\n"
                        f"  - Description: {template.get('description', '')}\n"
                        f"  - Examples: {examples}\n"
                        f"  - Story beats (follow this arc): {json.dumps(beats, ensure_ascii=False)}\n"
                        f"  - Recommended VO style: {voiceover_style_key or 'auto'}\n"
                        f"  - Recommended music mood: {music_mood_key or 'auto'}\n"
                    )
                else:
                    template_guidance = f"- Commercial template: {commercial_style}\n"
            except Exception:
                template_guidance = f"- Commercial template: {commercial_style}\n"

        uploaded_assets_value = constraints.get("uploaded_assets") if isinstance(constraints, dict) else None
        if isinstance(uploaded_assets_value, list):
            uploaded_assets = ", ".join(str(x).strip() for x in uploaded_assets_value if str(x).strip())
        else:
            uploaded_assets = str(uploaded_assets_value or "").strip()
        if not uploaded_assets:
            uploaded_assets = "none"
         
        prompt = f"""You are the Complete Creative Director and senior copywriter for a premium, memorable TV-style commercial.
Your job: Create the ENTIRE creative vision AND production-ready prompts in one response.

TARGET: Make it feel like a real, engaging spot (character-driven like State Farm / emotional like classic eBay / comedic like a catchphrase ad) — not a generic AI montage.

PRODUCT/BRAND: {product_name}
USER BRIEF (verbatim):
{(topic or "")[:2000]}

WEBSITE RESEARCH:
{website_data[:2000]}

         USER REQUIREMENTS:
- Style: {style}
- Mood: {mood}
- Platform: {platform}
- Duration target: {target_duration} seconds
{template_guidance}- Camera style: {camera_style or "auto"}
- Lighting preference: {lighting_preference or "auto"}
         - Color grade: {color_grade or "auto"}
         - Source URL: {source_url or "none"}
         - Uploaded reference assets: {uploaded_assets}
         - Reference image guidance: {image_guidance or "i2i_only"}
         {f"- Reference style guide: {reference_style_guide}" if reference_style_guide else ""}

 CRITICAL RULES:
 0. This is an ad FOR the PRODUCT/BRAND. Never mention being an AI, prompts, models, Flux, Veo, ElevenLabs, or "this tool".
 1. BRAND NAME HYGIENE: Never say/spell a domain (no .com/.trade/etc). Use a human brand name only.
 2. ANTI-META: Do not talk about “making ads/videos” unless the product is literally an ad/video creation tool (and the website/user brief supports that). If it's not, treat that as forbidden.
 3. NO on-screen readable text anywhere: no subtitles/captions/watermarks; no UI labels; no quotes.
    - Screens are allowed ONLY if the product is software/app; if so: over-shoulder shots, blurred/abstract UI, icon-only shapes, NO letters/numbers.
 3b. PROMPT COMPACTNESS: Keep each scene.visual_prompt tight (<= ~650 characters, 2-3 sentences).
     - Do NOT paste huge negative-prompt blocks or repeated "ABSOLUTE REQUIREMENT" paragraphs.
     - Include the "no readable text" constraint once, then focus on the human moment/action.
 4. CHARACTER-FIRST: Include at least 2 characters (or 1 character + narrator) with a consistent “character bible” (name, look, wardrobe, personality, mannerisms). Keep them consistent across scenes.
 5. DIALOGUE-FIRST: Write a mini conversation. Make it human and specific. Do NOT make every line a narrator line.
    - Brand name should be said naturally 1–2 times in a ~15s spot (2–3 times in ~30s+), not in every line.
    - Line count guidance: <=20s → 6–10 lines, 21–40s → 10–16 lines, >40s → 16–26 lines.
    - Timing guidance: prefer 2s slots for quick dialogue, 3–4s slots for emotional beats or CTA.
 6. STORY: Even in short form, include a hook → twist/escalation → payoff/CTA.
 7. VOICEOVER TIMING: Lines MUST NOT overlap. Keep each line short enough to fit its time_range.
    - Allowed: minimal performance tags like [laughs], [sighs], [pause: 0.2s]. Do not overuse.
 7b. SCENE SYNC: Every line MUST include a scene_id that matches one of the scenes below.
     - The speaker must be on-screen in that scene (i.e., that character appears in the scene's primary_subject/visual_prompt), unless speaker is Narrator.
     - Do not let a line cross a scene cut. (time_range can be approximate; it will be snapped to scene windows.)
 7c. SPEAKER NAMES: Each line.speaker MUST be exactly one of strategy.characters[].name or "Narrator".
     - Use SHORT names only (1-2 words). Never put scene descriptions in the speaker field.
 8. IMAGE->VIDEO: Motion prompts must describe MOTION ONLY (camera + subtle actor micro-action + subtle ambience). Do NOT re-describe the entire scene. Keep motion subtle to reduce warping.
 9. BRAND CARD FIRST: Populate strategy.brand_card BEFORE writing scenes/VO, grounded in WEBSITE RESEARCH + USER BRIEF + dropdowns.
   - If a fact isn't supported by the research/brief, set it to null/"unknown" and do NOT claim it.
   - No financial guarantees; avoid profit promises unless explicitly in the research/brief.
   - If USER BRIEF conflicts with WEBSITE RESEARCH, prefer USER BRIEF.
10. SPECIFICITY (fix "AI slop"): The voiceover and scenes MUST reflect brand_card.what_it_is and at least one concrete benefit/feature. Avoid generic phrases and vague adjective piles.
  10b. NO GENERIC AI MONTAGE: Avoid abstract "AI slop" b-roll (floating crystals, glowing geometric objects, generic circuit-board macros, neon oceans, sci-fi city drones) unless the product/brief explicitly calls for it. Prefer grounded live-action situations with real people doing a clear action.
  11. NATURAL SPEECH: Write like a human ad copywriter. Use punctuation and contractions. One clear idea per line.
     - Use simple punctuation only (periods/commas). Avoid em-dashes and other special characters.
  12. SHOT VARIETY (non-negotiable): Do NOT repeat the same framing/lighting/move every scene.
     - Adjacent scenes must differ in shot size (e.g., wide -> medium -> macro -> over-the-shoulder -> overhead).
     - Include at least one: establishing wide/environment, a human performance close/medium, a product/detail macro, and a dynamic move (tracking/handheld/crane) when duration >= 30s.
  13. ENDING VARIETY: The final scene must feel specific to the brand (different CTA phrasing and endcard vibe per brand). Avoid identical "visit us today" closes across projects.

SCENES + DURATIONS:
- Scene durations must be one of: 4, 6, 8 seconds (Veo supported).
- Total duration should land within +/- 2 seconds of {target_duration}.
- Prefer 4s scenes for reliability; use 6/8 only if needed.
- Recommended scene count: <=20s → 3–5 scenes, ~30s → 6–8 scenes, ~60s → 10–14 scenes.

Respond with STRICT JSON (no markdown, no commentary):
{{
"strategy": {{
    "core_concept": "Short punchy title (not generic)",
    "visual_language": "Live-action commercial cinematography notes (lens, lighting, grade, movement)",
    "product_name": "{product_name}",
    "brand_card": {{
        "brand_name": "{product_name}",
        "what_it_is": "Plain-English description grounded in WEBSITE RESEARCH/USER BRIEF",
        "category": "Category (e.g., insurance, ecommerce marketplace, SaaS)",
        "target_audience": "Who it's for (specific)",
        "core_promise": "Primary value proposition (no guarantees)",
        "key_benefits": ["3-5 concrete outcomes"],
        "key_features": ["3-5 concrete features/capabilities (supported)"],
        "differentiators": ["2-4 reasons it's different (supported)"],
        "proof_points": ["Only include facts explicitly supported (or empty array)"],
        "constraints": ["No domain", "No on-screen readable text", "No captions/subtitles/watermarks"],
        "compliance_notes": ["No guaranteed outcomes", "Avoid regulated claims unless supported"],
        "creative_angle": "Big idea / comedic or emotional angle aligned to template",
        "visual_motifs": ["2-5 recurring motifs/props/locations to keep it cohesive"],
        "call_to_action": "Short CTA (no URL unless user provided one explicitly)"
    }},
    "characters": [
        {{
            "name": "Character 1 name",
            "role": "e.g., friendly rep / parent / customer",
            "appearance": "Age range, wardrobe, defining features",
            "personality": "How they speak/act",
            "voice_style": "e.g., deadpan, warm, upbeat"
        }},
        {{
            "name": "Character 2 name",
            "role": "e.g., customer / friend / coworker",
            "appearance": "Age range, wardrobe, defining features",
            "personality": "How they speak/act",
            "voice_style": "e.g., skeptical, excited, heartfelt"
        }}
    ],
    "audio_signature": {{
        "bgm_prompt": "Instrumental music bed that matches the story + template + mood (no vocals, no lyrics).",
        "bgm_vibe": "1-3 words (e.g., warm, playful, tense)",
        "sfx_style": "How the sound design should feel (e.g., crisp, comedic, grounded, cinematic)",
        "mix_notes": "How loud music vs dialogue should be (short)."
    }},
    "brand_summary": "1 sentence: what the brand is, who it's for, why it matters (use WEBSITE RESEARCH if provided)",
    "applied_preferences": {{
        "style": "{style}",
        "mood": "{mood}",
        "platform": "{platform}",
        "commercial_style": "{commercial_style}",
        "camera_style": "{camera_style}",
        "lighting_preference": "{lighting_preference}",
        "color_grade": "{color_grade}",
        "url": "{source_url}"
    }}
}},
"script": {{
    "mood": "{mood}",
    "lines": [
        {{"scene_id": 1, "speaker": "SpeakerName", "text": "Short dialogue line (fit slot)", "time_range": "0s-2s"}},
        {{"scene_id": 1, "speaker": "SpeakerName", "text": "Short dialogue line (fit slot)", "time_range": "2s-4s"}},
        {{"scene_id": 2, "speaker": "SpeakerName", "text": "Short dialogue line (fit slot)", "time_range": "4s-6s"}}
    ],
    "scenes": [
        {{
            "id": 1,
            "duration": 4,
            "primary_subject": "Main on-screen character name (must match strategy.characters[].name) or product name",
            "subject_description": "Wardrobe + appearance + defining traits to keep consistent",
             "visual_prompt": "LIVE-ACTION HOOK: A cinematic still frame showing the relatable problem in a real place with real people. Include character faces, emotion, props, and a clear action beat. Show how this problem feels. NO readable text anywhere. If software must be shown, do over-shoulder blurred UI with icon-only shapes. Shot on pro cinema camera, shallow depth of field, {color_grade} grade.",
             "audio_prompt": "SFX only (no voices): specific diegetic sounds for this moment (2-4 seconds).",
             "motion_prompt": "Camera movement + tiny actor micro-action + ambient motion (no re-description). Vary the camera language across scenes (handheld, push-in, rack-focus, overhead, tracking)."
         }},
        {{
            "id": 2, 
            "duration": 4,
            "primary_subject": "Second on-screen character name (must match strategy.characters[].name) or product name",
            "subject_description": "Wardrobe + appearance + defining traits to keep consistent",
             "visual_prompt": "LIVE-ACTION TWIST/SOLUTION: The product/service enters the scene naturally. Show a tangible, specific benefit in an action beat (not abstract). Keep the world grounded and human. If the product is digital, show it via a real moment (phone call, package, appointment, dashboard glimpse) without readable text. Match {style} vibe. No readable text anywhere.",
             "audio_prompt": "SFX only (no voices): specific diegetic sounds for this moment (2-4 seconds).",
             "motion_prompt": "Camera movement + tiny actor micro-action + ambient motion (no re-description). Choose a different move/framing than the prior scene."
         }},
        {{
            "id": 3,
            "duration": 4,
            "primary_subject": "On-screen character name or product name (must match strategy.characters[].name if character)",
            "subject_description": "Keep continuity with prior scenes",
             "visual_prompt": "LIVE-ACTION PAYOFF/CTA: The emotional/comedic payoff lands. Show the product/service outcome clearly, then a clean brand moment. Avoid generic abstract objects. No readable text/letters anywhere; show brand presence without a wordmark if possible (colors, packaging, icon).",
             "audio_prompt": "SFX only (no voices): specific diegetic sounds for this moment (2-4 seconds).",
             "motion_prompt": "Camera movement + tiny actor micro-action + ambient motion (no re-description). End on a clean, intentional camera settle for the CTA."
         }}
    ]
}}
}}

IMPORTANT: Replace all [bracketed text] with actual creative content. 
Avoid generic filler. Make it feel like a real ad with a human moment and a memorable line."""

        response = self._call_with_retry([{"role": "user", "content": prompt}])
        result = response
            
        # Extract strategy and script
        strategy = result.get('strategy', {})
        script = result.get('script', {})
            
        # Ensure product_name is stored
        strategy['product_name'] = product_name

        # Validate/normalize Brand Card for downstream reliability.
        brand_card = strategy.get("brand_card")
        if not isinstance(brand_card, dict):
            brand_card = {}
        strategy["brand_card"] = brand_card
        brand_card.setdefault("brand_name", product_name)
        brand_name = str(brand_card.get("brand_name") or "").strip()
        if brand_name and _looks_like_url_or_domain(brand_name):
            brand_card["brand_name"] = product_name
            
        print(f"[GPT-5.2] Full creative direction complete for: {product_name}")
        print(f"[GPT-5.2] Generated {len(script.get('scenes', []))} scenes")
            
        return strategy, script

    def polish_dialogue_lines(self, strategy: dict, script, target_duration: int = 15) -> list[dict]:
        """
        Dialogue-only polish pass to fix speaker attribution + tone.

        Why: even strong planners occasionally assign a response to the wrong character or
        use verbose speaker labels. This pass outputs clean, scene-synced dialogue lines:
        - `speaker` is one of strategy.characters[].name or "Narrator"
        - `scene_id` is valid and matches the intended on-screen moment
        - lines are short and performance tags are used sparingly
        """
        if not self.client:
            return []

        import re

        characters = strategy.get("characters") if isinstance(strategy, dict) else None
        if not isinstance(characters, list):
            characters = []

        allowed_names = []
        for ch in characters:
            if isinstance(ch, dict):
                name = str(ch.get("name") or "").strip()
                if name:
                    allowed_names.append(name)

        # Script may be a dict or a Script model. Normalize to dict-ish.
        raw_scenes = None
        raw_lines = None
        if isinstance(script, dict):
            raw_scenes = script.get("scenes")
            raw_lines = script.get("lines")
        else:
            raw_scenes = getattr(script, "scenes", None)
            raw_lines = getattr(script, "lines", None)

        scenes_payload = []
        if raw_scenes:
            for s in list(raw_scenes):
                if isinstance(s, dict):
                    sid = s.get("id")
                    primary = s.get("primary_subject")
                    visual = s.get("visual_prompt")
                    duration = s.get("duration")
                else:
                    sid = getattr(s, "id", None)
                    primary = getattr(s, "primary_subject", None)
                    visual = getattr(s, "visual_prompt", None)
                    duration = getattr(s, "duration", None)

                try:
                    sid_int = int(sid) if sid is not None else None
                except Exception:
                    sid_int = None
                if sid_int is None:
                    continue

                try:
                    dur_int = int(duration) if duration is not None else 4
                except Exception:
                    dur_int = 4

                # Pacing budgets (demo reliability): keep dialogue sparse in short scenes.
                if dur_int <= 4:
                    max_lines = 3
                elif dur_int <= 6:
                    max_lines = 4
                else:
                    max_lines = 5

                beat = str(visual or "").strip()
                beat_first = beat.split("\n", 1)[0][:240]
                searchable = f"{primary or ''} {beat_first}".lower()
                on_screen = []
                for name in allowed_names:
                    if re.search(rf"\\b{re.escape(name.lower())}\\b", searchable):
                        on_screen.append(name)

                scenes_payload.append(
                    {
                        "id": sid_int,
                        "duration": dur_int,
                        "max_lines": max_lines,
                        "primary_subject": str(primary or "").strip(),
                        # Keep small to avoid token bloat; we only need the beat.
                        "visual_beat": beat_first,
                        "on_screen": on_screen,
                    }
                )

        lines_payload = []
        if raw_lines:
            for l in list(raw_lines):
                if isinstance(l, dict):
                    lines_payload.append(
                        {
                            "scene_id": l.get("scene_id"),
                            "speaker": l.get("speaker"),
                            "text": l.get("text"),
                            "time_range": l.get("time_range"),
                        }
                    )
                else:
                    lines_payload.append(
                        {
                            "scene_id": getattr(l, "scene_id", None),
                            "speaker": getattr(l, "speaker", None),
                            "text": getattr(l, "text", None),
                            "time_range": getattr(l, "time_range", None),
                        }
                    )

        payload = {
            "brand_card": strategy.get("brand_card") if isinstance(strategy, dict) else {},
            "characters": characters,
            "scenes": scenes_payload,
            "lines": lines_payload,
        }

        allowed_str = ", ".join(allowed_names) if allowed_names else "(use characters list)"

        prompt = f"""You are a TV commercial dialogue doctor and script supervisor.
Fix speaker attribution, tone, and scene sync for this short spot.

CRITICAL RULES:
- Allowed speakers: {allowed_str}, and Narrator (optional).
- Each line MUST include: scene_id, speaker, text, time_range.
- speaker MUST be exactly one of the allowed names or \"Narrator\" (no descriptions).
 - speaker must be ON-SCREEN for that scene_id based on the scene.on_screen list (or use Narrator).
 - Keep the dialogue coherent: if a line is a response, it must be spoken by the other character.
 - Keep 6-10 lines for a ~{target_duration}s spot.
 - PACING: Respect scene pacing budgets to avoid rushed, unnatural VO.
   - For each scene, do NOT exceed scene.max_lines dialogue lines.
   - If a scene is 4s, prefer 1-2 short lines total.
   - If a scene is 8s, you can fit up to 3-4 short lines.
 - LINE LENGTH: keep each line punchy and speakable. Aim <= 10 words per line; never exceed 16 words. Avoid long product explanations in one line.
 - No profit guarantees or claims of specific returns. No financial advice language.
 - Brand-name hygiene: never say a domain (no .com/.trade/etc).
 - Performance tags: optional and SPARING (<=3 total tags in the whole script). Examples: [sighs], [whispers], [laughs], [pause: 0.2s].
- Punctuation: use simple ASCII punctuation only (straight quotes/apostrophes). Avoid smart quotes, em dashes, and fancy typography.
- Do NOT change the product category; keep facts grounded in the brand_card.

INPUT JSON:
{json.dumps(payload, ensure_ascii=False)}

Respond with STRICT JSON (no markdown, no commentary):
{{
  \"lines\": [
    {{\"scene_id\": 1, \"speaker\": \"Name\", \"text\": \"Line\", \"time_range\": \"0s-2s\"}}
  ]
}}"""

        result = self._call_with_retry([{"role": "user", "content": prompt}])
        lines = result.get("lines") if isinstance(result, dict) else None
        if isinstance(lines, list):
            return [l for l in lines if isinstance(l, dict)]

        # Tolerate nested shapes if the model wraps unexpectedly.
        nested = None
        if isinstance(result, dict):
            nested = (result.get("script") or {}).get("lines") if isinstance(result.get("script"), dict) else None
        if isinstance(nested, list):
            return [l for l in nested if isinstance(l, dict)]

        return []

    def tighten_dialogue_to_time_ranges(self, strategy: dict, script, target_duration: int = 15) -> list[dict]:
        """
        Rewrite ONLY dialogue text to fit existing time slots.

        Goal: reduce rushed/cut VO and "tone mismatch" by ensuring each line is short enough
        to be spoken naturally within its assigned `time_range`.

        This keeps `scene_id`, `speaker`, and `time_range` fixed to preserve sync with visuals.
        """
        if not self.client:
            return []

        import re

        characters = strategy.get("characters") if isinstance(strategy, dict) else None
        if not isinstance(characters, list):
            characters = []

        allowed_names: list[str] = []
        voice_style_by_name: dict[str, str] = {}
        for ch in characters:
            if not isinstance(ch, dict):
                continue
            name = str(ch.get("name") or "").strip()
            if not name:
                continue
            allowed_names.append(name)
            voice_style_by_name[name] = str(ch.get("voice_style") or "").strip()

        # Normalize script to dict-ish.
        raw_scenes = None
        raw_lines = None
        if isinstance(script, dict):
            raw_scenes = script.get("scenes")
            raw_lines = script.get("lines")
        else:
            raw_scenes = getattr(script, "scenes", None)
            raw_lines = getattr(script, "lines", None)

        if not raw_lines:
            return []

        def _parse_time_range_seconds(time_range: str) -> tuple[float | None, float | None]:
            if not time_range:
                return (None, None)
            try:
                parts = str(time_range).replace("s", "").split("-")
                start = float(parts[0]) if parts and parts[0].strip() else None
                end = float(parts[1]) if len(parts) > 1 and parts[1].strip() else None
                return (start, end)
            except Exception:
                return (None, None)

        scenes_payload = []
        if raw_scenes:
            for s in list(raw_scenes):
                if isinstance(s, dict):
                    sid = s.get("id")
                    primary = s.get("primary_subject")
                    visual = s.get("visual_prompt")
                    duration = s.get("duration")
                else:
                    sid = getattr(s, "id", None)
                    primary = getattr(s, "primary_subject", None)
                    visual = getattr(s, "visual_prompt", None)
                    duration = getattr(s, "duration", None)

                try:
                    sid_int = int(sid) if sid is not None else None
                except Exception:
                    sid_int = None
                if sid_int is None:
                    continue

                try:
                    dur_int = int(duration) if duration is not None else 4
                except Exception:
                    dur_int = 4

                beat = str(visual or "").strip()
                beat_first = beat.split("\n", 1)[0][:220]
                searchable = f"{primary or ''} {beat_first}".lower()
                on_screen = []
                for name in allowed_names:
                    if re.search(rf"\\b{re.escape(name.lower())}\\b", searchable):
                        on_screen.append(name)

                scenes_payload.append(
                    {
                        "id": sid_int,
                        "duration": dur_int,
                        "primary_subject": str(primary or "").strip(),
                        "visual_beat": beat_first,
                        "on_screen": on_screen,
                    }
                )

        lines_payload = []
        for idx, l in enumerate(list(raw_lines)):
            if isinstance(l, dict):
                scene_id = l.get("scene_id")
                speaker = l.get("speaker")
                text = l.get("text")
                time_range = l.get("time_range")
                audio_path = l.get("audio_path")
            else:
                scene_id = getattr(l, "scene_id", None)
                speaker = getattr(l, "speaker", None)
                text = getattr(l, "text", None)
                time_range = getattr(l, "time_range", None)
                audio_path = getattr(l, "audio_path", None)

            start, end = _parse_time_range_seconds(str(time_range or ""))
            slot_seconds = None
            if start is not None and end is not None and end > start:
                slot_seconds = float(end - start)

            # Conservative budgets to avoid "machine-gun" VO. Round instead of floor so
            # short slots don't lose critical meaning words (we'll also limit pauses below).
            max_words = 12
            max_sentence_endings = 2  # .,!,? count (controls TTS pause inflation)
            if slot_seconds is not None:
                max_words = int(round(slot_seconds * 2.4 + 1.0))
                max_words = max(1, min(max_words, 16))
                if slot_seconds <= 2.0:
                    max_sentence_endings = 1
                elif slot_seconds <= 3.2:
                    max_sentence_endings = 2
                else:
                    max_sentence_endings = 3

            speaker_name = str(speaker or "").strip()
            voice_style = voice_style_by_name.get(speaker_name, "")

            lines_payload.append(
                {
                    "id": idx,
                    "scene_id": scene_id,
                    "speaker": speaker_name,
                    "time_range": str(time_range or ""),
                    "slot_seconds": slot_seconds,
                    "max_words": max_words,
                    "max_sentence_endings": max_sentence_endings,
                    "voice_style": voice_style,
                    "text": str(text or ""),
                    "audio_path": audio_path,
                }
            )

        payload = {
            "brand_card": strategy.get("brand_card") if isinstance(strategy, dict) else {},
            "characters": characters,
            "scenes": scenes_payload,
            "lines": lines_payload,
        }

        allowed_str = ", ".join(allowed_names) if allowed_names else "(use characters list)"

        prompt = f"""You are a TV commercial dialogue pacing editor and script supervisor.
Rewrite ONLY the dialogue text so each line can be spoken naturally within its assigned time slot.

CRITICAL RULES:
- Allowed speakers: {allowed_str}, and Narrator (optional).
- Do NOT add/remove/reorder lines.
- Do NOT change scene_id, speaker, or time_range.
- Rewrite only `text`.
- Each rewritten line MUST respect the provided `max_words` budget.
- PAUSES: Short slots cannot support lots of sentence breaks. Keep sentence-ending punctuation (.,!,?) <= `max_sentence_endings`.
  Prefer commas for rhythm instead of multiple short sentences.
- Each line must be a complete, natural utterance. Do not end on dangling filler words (e.g., "and", "or", "the", "all").
- End each line with appropriate punctuation (.,!,?) unless it ends with a performance tag like [laughs].
- Make it sound like real spoken dialogue (not narration). Use contractions. Keep it human and specific.
- Tone must match each speaker's `voice_style` and the scene `visual_beat`.
- Brand-name hygiene: never say a domain (no .com/.trade/etc).
- No profit guarantees or claims of specific returns. No financial advice language.
- Punctuation: use simple ASCII punctuation only. Avoid smart quotes, em dashes, and fancy typography.
- Performance tags: optional and VERY SPARING (<=2 total tags across the whole spot). Examples: [sighs], [laughs], [pause: 0.2s].

INPUT JSON:
{json.dumps(payload, ensure_ascii=False)}

Respond with STRICT JSON (no markdown, no commentary):
{{
  "lines": [
    {{"id": 0, "text": "Rewritten text only"}}
  ]
}}"""

        result = self._call_with_retry([{"role": "user", "content": prompt}])
        rewrites = result.get("lines") if isinstance(result, dict) else None
        if not isinstance(rewrites, list):
            return []

        id_to_text: dict[int, str] = {}
        for item in rewrites:
            if not isinstance(item, dict):
                continue
            try:
                idx = int(item.get("id"))
            except Exception:
                continue
            text = str(item.get("text") or "").strip()
            if text:
                id_to_text[idx] = text

        def _normalize_for_slot(text: str, slot_seconds: float | None, max_words: int, max_sentence_endings: int) -> str:
            """
            Deterministic safety net so we don't ship "too many pauses" lines that
            ElevenLabs renders longer than the slot (even if word count is fine).
            """
            t = str(text or "").strip()
            t = re.sub(r"\s+", " ", t).strip()

            # If the slot is tight, remove leading performance tags (they often slow delivery).
            if slot_seconds is not None and slot_seconds <= 1.8:
                t = re.sub(r"^\[[^\]]{1,24}\]\s*", "", t).strip()

            # Limit sentence-ending punctuation by converting earlier endings to commas.
            # Count only real sentence endings: '!'/'?' anywhere, and '.' only when followed by whitespace or end.
            endings = list(re.finditer(r"[!?]|\.(?=\s|$)", t))
            if len(endings) > max_sentence_endings and max_sentence_endings >= 1:
                keep_from = max(len(endings) - max_sentence_endings, 0)
                chars = list(t)
                for m in endings[:keep_from]:
                    chars[m.start()] = ","
                t = "".join(chars)
                t = re.sub(r",\s*", ", ", t)
                t = re.sub(r"\s+", " ", t).strip()

            # Enforce max words (drop trailing clause first; last resort hard truncate).
            words = [w for w in t.split() if w]
            if len(words) > max_words:
                parts = [p.strip() for p in t.split(",") if p.strip()]
                while len(" ".join(parts).split()) > max_words and len(parts) > 1:
                    parts = parts[:-1]
                t2 = ", ".join(parts).strip()
                words2 = [w for w in t2.split() if w]
                if len(words2) > max_words:
                    t2 = " ".join(words2[:max_words]).strip()
                t = t2

            # Remove dangling stopwords at the end (prevents awkward cut-off lines).
            stopwords = {
                "a",
                "an",
                "the",
                "and",
                "or",
                "but",
                "to",
                "of",
                "for",
                "with",
                "at",
                "in",
                "on",
                "all",
                "just",
            }
            words = [w for w in t.split() if w]
            while words and words[-1].strip(".,!?").lower() in stopwords:
                words.pop()
            t = " ".join(words).strip()

            # Ensure the line ends cleanly with punctuation (unless it ends with a tag).
            if t and not re.search(r"[\.\!\?]$", t) and not re.search(r"\]$", t):
                t = f"{t}."

            return t

        # Apply rewrites while preserving timing + routing fields.
        out: list[dict] = []
        for original in lines_payload:
            idx = int(original.get("id"))
            new_text = id_to_text.get(idx)
            if not new_text:
                continue

            new_text = _normalize_for_slot(
                new_text,
                original.get("slot_seconds"),
                int(original.get("max_words") or 12),
                int(original.get("max_sentence_endings") or 2),
            )

            out.append(
                {
                    "scene_id": original.get("scene_id"),
                    "speaker": original.get("speaker"),
                    "text": new_text,
                    "time_range": original.get("time_range"),
                    "audio_path": original.get("audio_path"),
                }
            )

        # Only accept if we preserved line count (prevents accidental drops).
        if len(out) != len(lines_payload):
            return []

        return out

    def polish_scene_prompts(self, strategy: dict, script, target_duration: int = 15) -> list[dict]:
        """
        Scene prompt polish pass to improve framing and dialogue-to-visual alignment.

        Goal: reduce "image montage" failure modes by rewriting each scene into a compact,
        production-friendly shot description with explicit blocking and a single visible action beat
        that matches the dialogue scheduled for that scene.

        Returns a list of scene dicts with updated:
          - visual_prompt (compact, high-signal)
          - motion_prompt (micro-action + camera only)
          - audio_prompt (diegetic SFX only)
        """
        if not self.client:
            return []

        import re

        characters = strategy.get("characters") if isinstance(strategy, dict) else None
        if not isinstance(characters, list):
            characters = []

        allowed_names: list[str] = []
        for ch in characters:
            if isinstance(ch, dict):
                name = str(ch.get("name") or "").strip()
                if name:
                    allowed_names.append(name)

        # Normalize script to dict-ish.
        raw_scenes = None
        raw_lines = None
        if isinstance(script, dict):
            raw_scenes = script.get("scenes")
            raw_lines = script.get("lines")
        else:
            raw_scenes = getattr(script, "scenes", None)
            raw_lines = getattr(script, "lines", None)

        if not raw_scenes:
            return []

        # Group dialogue by scene_id.
        lines_by_scene: dict[int, list[dict]] = {}
        if raw_lines:
            for l in list(raw_lines):
                if isinstance(l, dict):
                    sid = l.get("scene_id")
                    speaker = l.get("speaker")
                    text = l.get("text")
                else:
                    sid = getattr(l, "scene_id", None)
                    speaker = getattr(l, "speaker", None)
                    text = getattr(l, "text", None)

                try:
                    sid_int = int(sid) if sid is not None else None
                except Exception:
                    sid_int = None
                if sid_int is None:
                    continue

                sp = str(speaker or "").strip()
                tx = str(text or "").strip()
                if not sp or not tx:
                    continue

                lines_by_scene.setdefault(sid_int, []).append({"speaker": sp, "text": tx})

        scenes_payload: list[dict] = []
        for s in list(raw_scenes):
            if isinstance(s, dict):
                sid = s.get("id")
                duration = s.get("duration")
                primary = s.get("primary_subject")
                desc = s.get("subject_description")
                visual = s.get("visual_prompt")
                motion = s.get("motion_prompt")
                audio = s.get("audio_prompt")
            else:
                sid = getattr(s, "id", None)
                duration = getattr(s, "duration", None)
                primary = getattr(s, "primary_subject", None)
                desc = getattr(s, "subject_description", None)
                visual = getattr(s, "visual_prompt", None)
                motion = getattr(s, "motion_prompt", None)
                audio = getattr(s, "audio_prompt", None)

            try:
                sid_int = int(sid) if sid is not None else None
            except Exception:
                sid_int = None
            if sid_int is None:
                continue

            try:
                dur_int = int(duration) if duration is not None else 4
            except Exception:
                dur_int = 4

            beat = str(visual or "").strip().replace("\n", " ")
            beat = re.sub(r"\s+", " ", beat).strip()
            beat = beat[:420]

            motion_short = str(motion or "").strip().replace("\n", " ")
            motion_short = re.sub(r"\s+", " ", motion_short).strip()
            motion_short = motion_short[:240]

            audio_short = str(audio or "").strip().replace("\n", " ")
            audio_short = re.sub(r"\s+", " ", audio_short).strip()
            audio_short = audio_short[:200]

            # Who is already on-screen per existing prompt?
            searchable = f"{primary or ''} {desc or ''} {beat}".lower()
            on_screen = []
            for name in allowed_names:
                if re.search(rf"\\b{re.escape(name.lower())}\\b", searchable):
                    on_screen.append(name)

            scenes_payload.append(
                {
                    "id": sid_int,
                    "duration": dur_int,
                    "primary_subject": str(primary or "").strip(),
                    "subject_description": str(desc or "").strip(),
                    "current_visual_prompt": beat,
                    "current_motion_prompt": motion_short,
                    "current_audio_prompt": audio_short,
                    "on_screen_now": on_screen,
                    "dialogue": lines_by_scene.get(sid_int, []),
                }
            )

        payload = {
            "brand_card": strategy.get("brand_card") if isinstance(strategy, dict) else {},
            "characters": characters,
            "scenes": scenes_payload,
        }

        allowed_str = ", ".join(allowed_names) if allowed_names else "(use characters list)"

        prompt = f"""You are a commercial film director and shot designer.
Rewrite each scene prompt to be tight, cinematic, and perfectly aligned with the dialogue in that same scene.

CRITICAL RULES:
- Keep scene ids and durations unchanged.
- Each scene MUST include all speaking characters for that scene ON-SCREEN (unless speaker is Narrator).
- visual_prompt MUST be compact (<= 650 chars, 2-3 sentences) and include:
  1) Shot + framing + lens (e.g., wide 28mm handheld, medium 50mm, close-up 85mm)
  2) Blocking: where each character is in frame
  3) One visible action beat that supports the dialogue (no abstract montage)
  4) Constraint: "No readable text anywhere" (only once; do not add huge negative prompt blocks)
- Avoid generic AI b-roll (floating crystals, glowing geometry, circuit macros, neon oceans) unless the brand/brief explicitly calls for it.
- motion_prompt: micro-action + subtle camera movement ONLY (1 sentence). Do not re-describe the full scene.
- audio_prompt: diegetic SFX only, no voices (1 short sentence).
- Allowed character names: {allowed_str}. Use ONLY these names (or Narrator).
- Brand-name hygiene: never output a domain (no .com/.trade/etc).
- No financial guarantees/returns claims.
- Punctuation: simple ASCII only.

INPUT JSON:
{json.dumps(payload, ensure_ascii=False)}

Respond with STRICT JSON (no markdown, no commentary):
{{
  "scenes": [
    {{"id": 1, "visual_prompt": "…", "motion_prompt": "…", "audio_prompt": "…", "primary_subject": "…", "subject_description": "…"}}
  ]
}}"""

        result = self._call_with_retry([{"role": "user", "content": prompt}])
        scenes = result.get("scenes") if isinstance(result, dict) else None
        if isinstance(scenes, list):
            return [s for s in scenes if isinstance(s, dict)]

        nested = None
        if isinstance(result, dict):
            nested = (result.get("script") or {}).get("scenes") if isinstance(result.get("script"), dict) else None
        if isinstance(nested, list):
            return [s for s in nested if isinstance(s, dict)]

        return []
    
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
                {"speaker": "Narrator", "text": "[pause: 0.2s] Move faster. Stay in control.", "time_range": "0s-4s"},
                {"speaker": "Narrator", "text": f"{product_name} turns data into decisions.", "time_range": "4s-8s"},
                {"speaker": "Narrator", "text": f"Meet {product_name}. Start now.", "time_range": "8s-12s"}
            ],
            "scenes": [
                {
                    "id": 1,
                    "duration": 4,
                    "visual_prompt": f"A photo of {product_name} interface emerging from darkness, volumetric lighting illuminating a sleek modern dashboard, professional tech environment. IMPORTANT: text-free UI (icon-only, abstract shapes; no labels/words). Shot on Arri Alexa, Cooke S4 prime lens, f/2.8, cinematic lighting.",
                    "motion_prompt": "Camera motion only: slow dolly-in with subtle parallax. Environmental animation: gentle dust motes drift + soft light flicker."
                },
                {
                    "id": 2,
                    "duration": 4,
                    "visual_prompt": f"A photo of {product_name} dashboard in full operation showing key features, golden hour lighting streaming through modern office window, professional workspace. IMPORTANT: text-free UI (icon-only, abstract shapes; no labels/words). Shot on Arri Alexa, Cooke S4 prime lens, f/2.8.",
                    "motion_prompt": "Camera motion only: smooth lateral slider move, then a gentle rack focus. Environmental animation: subtle reflections shimmer."
                },
                {
                    "id": 3,
                    "duration": 4,
                    "visual_prompt": f"A photo of {product_name} brand mark displayed in premium lighting, sleek minimalist backdrop. IMPORTANT: show a clean brand mark/symbol only (no wordmark text). Shot on Arri Alexa, Cooke S4 prime lens, f/2.8.",
                    "motion_prompt": "Camera motion only: slow push-in then gentle settle. Environmental animation: lens flare sweep + particles drift."
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
7. Text-free UI - Any readable words/letters on screens are a MAJOR defect (models often output gibberish). Prefer icon-only, text-free interfaces.

Respond in JSON:
{{
    "is_acceptable": <true if quality >= 7 and no major issues, false otherwise>,
    "quality_score": <1-10>,
    "issues": ["<specific problems found (if not acceptable, include at least 1)>"],
    "what_i_see": "<brief description of what you actually see in the image>",
    "improved_prompt": "<REQUIRED if not acceptable: provide a revised prompt that fixes the issues. If acceptable, null>"
}}"""

        try:
            # VISION MODE: Actually look at the image
            if image_path and os.path.exists(image_path):
                import base64
                import io
                from PIL import Image
                
                # Encode image to base64. Downscale large frames for reliability/cost.
                # Some OpenAI endpoints are stricter on payload size; JPEG works well for QC.
                with Image.open(image_path) as im:
                    im = im.convert("RGB")
                    max_width = 1280
                    if im.width > max_width:
                        new_height = max(1, int(im.height * (max_width / float(im.width))))
                        im = im.resize((max_width, new_height), Image.Resampling.LANCZOS)

                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=85, optimize=True)
                    image_data = base64.b64encode(buf.getvalue()).decode("utf-8")

                mime_type = "image/jpeg"
                
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
                    max_completion_tokens=1000
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
            
            status = "PASS" if result.get("is_acceptable") else "NEEDS REROLL"
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
