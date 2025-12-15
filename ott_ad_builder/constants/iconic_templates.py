"""
Iconic Commercial Templates & Reference Library
Proven ad structures from legendary campaigns for AI video generation
"""

# ============================================================================
# ICONIC COMMERCIAL TEMPLATES - Proven Story Structures
# ============================================================================

ICONIC_TEMPLATES = {
    "mascot_story": {
        "name": "Mascot Story",
        "description": "Character-driven narrative featuring a memorable brand mascot",
        "examples": ["Geico Gecko", "Flo from Progressive", "M&M Characters", "Aflac Duck"],
        "duration_ideal": "15-30s",
        "scenes": [
            {"scene": 1, "purpose": "mascot_intro", "shot_size": "medium", "emotion": "curiosity", "beat": "Meet the mascot in their world"},
            {"scene": 2, "purpose": "problem_encounter", "shot_size": "medium_close_up", "emotion": "problem", "beat": "Mascot encounters relatable challenge"},
            {"scene": 3, "purpose": "mascot_wisdom", "shot_size": "close_up", "emotion": "discovery", "beat": "Mascot delivers insight with humor"},
            {"scene": 4, "purpose": "brand_payoff", "shot_size": "wide", "emotion": "payoff", "beat": "Product solves everything + catchphrase"}
        ],
        "voiceover_style": "playful_character",
        "music_mood": "playful"
    },

    "sensory_metaphor": {
        "name": "Sensory Metaphor",
        "description": "Visual/audio trigger that embodies product benefit - pure sensory experience",
        "examples": ["Coors Light ice mountains", "Coca-Cola fizz pour", "Guinness settling", "Red Bull wings"],
        "duration_ideal": "8-15s",
        "scenes": [
            {"scene": 1, "purpose": "sensory_hook", "shot_size": "extreme_close_up", "emotion": "hook", "beat": "Irresistible sensory detail in macro"},
            {"scene": 2, "purpose": "product_hero", "shot_size": "medium", "emotion": "discovery", "beat": "Reveal the product as source of sensation"},
            {"scene": 3, "purpose": "consumption_moment", "shot_size": "close_up", "emotion": "transformation", "beat": "Human experiencing the sensation"},
            {"scene": 4, "purpose": "brand_seal", "shot_size": "medium", "emotion": "payoff", "beat": "Logo with sensory echo"}
        ],
        "voiceover_style": "luxury_whisper",
        "music_mood": "luxury"
    },

    "emotional_journey": {
        "name": "Emotional Journey",
        "description": "Human story with product as enabler - creates deep emotional connection",
        "examples": ["eBay child commercial", "Google Search ads", "P&G 'Thank You Mom'", "Thai Life Insurance"],
        "duration_ideal": "30-60s",
        "scenes": [
            {"scene": 1, "purpose": "protagonist_intro", "shot_size": "medium", "emotion": "hook", "beat": "Meet relatable human in their world"},
            {"scene": 2, "purpose": "challenge_reveal", "shot_size": "close_up", "emotion": "problem", "beat": "Reveal authentic struggle or longing"},
            {"scene": 3, "purpose": "discovery_moment", "shot_size": "medium_close_up", "emotion": "discovery", "beat": "Product/service enters as possibility"},
            {"scene": 4, "purpose": "transformation", "shot_size": "medium", "emotion": "transformation", "beat": "Visible emotional change"},
            {"scene": 5, "purpose": "brand_connection", "shot_size": "wide", "emotion": "payoff", "beat": "Warm resolution + brand message"}
        ],
        "voiceover_style": "intimate_narrator",
        "music_mood": "nostalgic"
    },

    "catchphrase_comedy": {
        "name": "Catchphrase Comedy",
        "description": "Humor-driven with memorable recurring phrase - highly shareable",
        "examples": ["Bud Light 'Dilly Dilly'", "Budweiser 'Wassup'", "Wendy's 'Where's the beef?'", "Old Spice 'The Man'"],
        "duration_ideal": "15-30s",
        "scenes": [
            {"scene": 1, "purpose": "setup", "shot_size": "wide", "emotion": "hook", "beat": "Establish absurd or unexpected scenario"},
            {"scene": 2, "purpose": "escalation", "shot_size": "medium", "emotion": "problem", "beat": "Situation intensifies comedically"},
            {"scene": 3, "purpose": "punchline", "shot_size": "close_up", "emotion": "discovery", "beat": "Catchphrase delivery moment"},
            {"scene": 4, "purpose": "callback", "shot_size": "medium", "emotion": "payoff", "beat": "Brand + catchphrase echo"}
        ],
        "voiceover_style": "comedic_announcer",
        "music_mood": "playful"
    },

    "problem_solution": {
        "name": "Problem-Solution Demo",
        "description": "Classic before/after format with dramatic product demonstration",
        "examples": ["OxiClean", "Dyson", "Apple iPhone reveals", "Dawn dish soap"],
        "duration_ideal": "15-30s",
        "scenes": [
            {"scene": 1, "purpose": "pain_point", "shot_size": "close_up", "emotion": "problem", "beat": "Show frustrating problem in action"},
            {"scene": 2, "purpose": "failed_attempts", "shot_size": "medium", "emotion": "problem", "beat": "Competitor or old way failing"},
            {"scene": 3, "purpose": "product_intro", "shot_size": "extreme_close_up", "emotion": "discovery", "beat": "Hero product reveal with drama"},
            {"scene": 4, "purpose": "demonstration", "shot_size": "close_up", "emotion": "transformation", "beat": "Satisfying problem being solved"},
            {"scene": 5, "purpose": "result", "shot_size": "wide", "emotion": "payoff", "beat": "Clean result + call to action"}
        ],
        "voiceover_style": "energetic_announcer",
        "music_mood": "urgent"
    },

    "aspirational_lifestyle": {
        "name": "Aspirational Lifestyle",
        "description": "Glamorous world-building that audiences want to inhabit",
        "examples": ["Apple 'Shot on iPhone'", "Nike athlete stories", "BMW driving ads", "Calvin Klein"],
        "duration_ideal": "15-30s",
        "scenes": [
            {"scene": 1, "purpose": "world_establish", "shot_size": "extreme_wide", "emotion": "hook", "beat": "Breathtaking environment/lifestyle shot"},
            {"scene": 2, "purpose": "protagonist_action", "shot_size": "medium", "emotion": "discovery", "beat": "Aspirational person doing enviable thing"},
            {"scene": 3, "purpose": "product_integration", "shot_size": "close_up", "emotion": "transformation", "beat": "Product seamlessly part of this life"},
            {"scene": 4, "purpose": "emotional_peak", "shot_size": "medium_close_up", "emotion": "payoff", "beat": "Moment of triumph/beauty + brand"}
        ],
        "voiceover_style": "cinematic_narrator",
        "music_mood": "epic"
    },

    "tech_reveal": {
        "name": "Tech Product Reveal",
        "description": "Sleek, futuristic product showcase with innovation focus",
        "examples": ["Apple keynotes", "Tesla Cybertruck", "Samsung Galaxy", "PlayStation"],
        "duration_ideal": "15-30s",
        "scenes": [
            {"scene": 1, "purpose": "teaser", "shot_size": "extreme_close_up", "emotion": "hook", "beat": "Mysterious glimpse of form/feature"},
            {"scene": 2, "purpose": "reveal", "shot_size": "medium", "emotion": "discovery", "beat": "Dramatic full product reveal"},
            {"scene": 3, "purpose": "feature_showcase", "shot_size": "close_up", "emotion": "transformation", "beat": "Key innovation in action"},
            {"scene": 4, "purpose": "hero_shot", "shot_size": "medium", "emotion": "payoff", "beat": "Product beauty shot + brand"}
        ],
        "voiceover_style": "tech_futurist",
        "music_mood": "tech"
    }
}


# ============================================================================
# AUDIO MOOD KEYWORDS - Sound Design Vocabulary
# ============================================================================

AUDIO_MOOD_KEYWORDS = {
    "epic": {
        "description": "Orchestral, triumphant, heroic",
        "music_prompt": "Orchestral crescendo with brass fanfare, timpani rolls, heroic cinematic theme, building intensity",
        "sfx_elements": ["dramatic whoosh", "impact boom", "rising tension", "triumphant swell"]
    },
    "intimate": {
        "description": "Soft, personal, close",
        "music_prompt": "Solo piano with gentle strings, acoustic guitar fingerpicking, soft ambient pads, whispered vocals",
        "sfx_elements": ["soft breath", "fabric rustle", "quiet footsteps", "gentle ambiance"]
    },
    "tech": {
        "description": "Futuristic, clean, innovative",
        "music_prompt": "Clean synth pulses, electronic beeps and tones, futuristic UI sounds, minimal techno underscore",
        "sfx_elements": ["digital interface", "power-up tone", "data stream", "holographic activation"]
    },
    "playful": {
        "description": "Fun, energetic, lighthearted",
        "music_prompt": "Bouncy percussion, pizzicato strings, xylophone melody, upbeat tempo with handclaps",
        "sfx_elements": ["cartoon boing", "cheerful ding", "playful pop", "happy whistle"]
    },
    "luxury": {
        "description": "Premium, sophisticated, indulgent",
        "music_prompt": "Slow jazz with smooth saxophone, champagne glasses clinking, velvet ambient textures, subtle bass",
        "sfx_elements": ["champagne pop", "silk rustle", "luxury car door", "crystal glass"]
    },
    "urgent": {
        "description": "Driving, tense, time-sensitive",
        "music_prompt": "Driving drums with staccato strings, ticking clock motif, building intensity, bass drops",
        "sfx_elements": ["clock tick", "heartbeat pulse", "engine rev", "countdown beep"]
    },
    "nostalgic": {
        "description": "Warm, retro, sentimental",
        "music_prompt": "Vinyl crackle texture, retro synth pads, lo-fi warmth, analog tape hiss, gentle piano",
        "sfx_elements": ["vinyl pop", "film projector", "old radio static", "wind chimes"]
    },
    "dramatic": {
        "description": "Intense, serious, weighty",
        "music_prompt": "Low cello drones, sparse piano notes, building string tension, dramatic silence",
        "sfx_elements": ["deep impact", "thunder rumble", "door slam echo", "suspenseful drone"]
    }
}


# ============================================================================
# VOICE STYLE DESCRIPTORS - ElevenLabs Voiceover Guidance
# ============================================================================

VOICE_STYLE_DESCRIPTORS = {
    "cinematic_narrator": {
        "description": "Deep, authoritative, gravitas",
        "prompt_prefix": "[slow, measured pace] [deep resonant voice]",
        "characteristics": "Deep baritone, measured pacing, gravitas, like Morgan Freeman or Sam Elliott",
        "best_for": ["brand_anthem", "aspirational_lifestyle", "tech_reveal"]
    },
    "friendly_guide": {
        "description": "Warm, conversational, approachable",
        "prompt_prefix": "[warm, friendly tone] [conversational delivery]",
        "characteristics": "Warm mid-range, natural conversational pace, slight smile in voice, trustworthy",
        "best_for": ["problem_solution", "emotional_journey"]
    },
    "energetic_announcer": {
        "description": "Punchy, exciting, call-to-action",
        "prompt_prefix": "[excited] [energetic delivery]",
        "characteristics": "Energetic, punchy staccato delivery, higher energy, excitement building",
        "best_for": ["problem_solution", "tech_reveal", "catchphrase_comedy"]
    },
    "luxury_whisper": {
        "description": "Soft, intimate, seductive",
        "prompt_prefix": "[whispers] [soft, intimate tone]",
        "characteristics": "Soft, intimate ASMR-adjacent quality, seductive, unhurried, breathy",
        "best_for": ["sensory_metaphor", "luxury", "fashion"]
    },
    "tech_futurist": {
        "description": "Clean, precise, modern",
        "prompt_prefix": "[clear, precise enunciation] [confident tone]",
        "characteristics": "Clean enunciation, precise, slightly robotic confidence, modern and minimal",
        "best_for": ["tech_reveal", "product_showcase"]
    },
    "playful_character": {
        "description": "Fun, quirky, memorable",
        "prompt_prefix": "[playful] [character voice]",
        "characteristics": "Fun quirky delivery, character-driven, possibly comedic timing, memorable",
        "best_for": ["mascot_story", "catchphrase_comedy"]
    },
    "intimate_narrator": {
        "description": "Thoughtful, emotional, personal",
        "prompt_prefix": "[thoughtful, emotional] [personal storytelling]",
        "characteristics": "Thoughtful pacing, emotional subtext, personal storytelling quality",
        "best_for": ["emotional_journey", "documentary"]
    },
    "comedic_announcer": {
        "description": "Deadpan, ironic, timing-focused",
        "prompt_prefix": "[deadpan delivery] [comedic timing]",
        "characteristics": "Deadpan or ironic delivery, precise comedic timing, straight-faced humor",
        "best_for": ["catchphrase_comedy", "mascot_story"]
    }
}


# ============================================================================
# CATCHPHRASE PATTERNS - Memorable Tagline Structures
# ============================================================================

CATCHPHRASE_PATTERNS = {
    "imperative_action": {
        "pattern": "[Verb] + [Object/Benefit]",
        "examples": ["Just Do It", "Think Different", "Eat Fresh", "Have It Your Way"],
        "psychology": "Commands create urgency and imply control/empowerment"
    },
    "question_hook": {
        "pattern": "[Question about pain/desire]?",
        "examples": ["Got Milk?", "Where's the beef?", "What's in your wallet?", "Can you hear me now?"],
        "psychology": "Questions engage the brain and demand mental response"
    },
    "because_reason": {
        "pattern": "[Brand/Product], because [Reason/Benefit]",
        "examples": ["L'Oréal - Because You're Worth It", "Bounty - The Quicker Picker Upper"],
        "psychology": "Provides logical justification that satisfies rational mind"
    },
    "rhyme_rhythm": {
        "pattern": "[Rhyming or rhythmic phrase]",
        "examples": ["Plop Plop Fizz Fizz", "Snap Crackle Pop", "The Best a Man Can Get"],
        "psychology": "Rhymes are inherently memorable and satisfying"
    },
    "superlative_claim": {
        "pattern": "The [Superlative] [Category]",
        "examples": ["The Ultimate Driving Machine", "The King of Beers", "The Happiest Place on Earth"],
        "psychology": "Bold claims establish category dominance"
    },
    "emotional_promise": {
        "pattern": "[Emotional State/Outcome]",
        "examples": ["Open Happiness", "I'm Lovin' It", "Taste the Feeling"],
        "psychology": "Associates brand with positive emotional state"
    }
}


# ============================================================================
# VISUAL METAPHOR LIBRARY - Iconic Visual Concepts
# ============================================================================

VISUAL_METAPHORS = {
    "ice_cold_refresh": {
        "visual": "Ice crystals forming, frost spreading, condensation droplets",
        "feeling": "Instant refreshment, cooling relief, thirst quenching",
        "brands_used": ["Coors Light", "Coca-Cola", "Gatorade", "Mentos"]
    },
    "mountain_peak": {
        "visual": "Summit achievement, panoramic vista, conquering heights",
        "feeling": "Achievement, aspiration, freedom, peak performance",
        "brands_used": ["Coors", "Patagonia", "The North Face", "Jeep"]
    },
    "transformation_morph": {
        "visual": "Before/after transition, caterpillar to butterfly, clay to sculpture",
        "feeling": "Change, improvement, potential realized",
        "brands_used": ["Weight Watchers", "Dyson", "Renovation shows"]
    },
    "speed_blur": {
        "visual": "Motion blur, wind streaks, time compression",
        "feeling": "Efficiency, excitement, living fast, no waiting",
        "brands_used": ["FedEx", "Uber", "sports cars", "5G ads"]
    },
    "family_moment": {
        "visual": "Multigenerational gathering, shared meal, childhood memory",
        "feeling": "Nostalgia, belonging, tradition, love",
        "brands_used": ["Hallmark", "Folgers", "Campbell's", "Johnson & Johnson"]
    },
    "sunrise_new_day": {
        "visual": "Dawn light, fresh start, morning routine, first rays",
        "feeling": "Hope, new beginnings, energy, optimism",
        "brands_used": ["Tropicana", "Morning routines", "Insurance", "Health brands"]
    },
    "precision_engineering": {
        "visual": "Gears interlocking, circuits activating, mechanisms in motion",
        "feeling": "Quality, precision, reliability, engineering excellence",
        "brands_used": ["Tag Heuer", "Intel", "German cars", "Tech products"]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_template_for_style(style: str) -> dict:
    """Get iconic template based on style keyword/commercial type."""
    style_lower = style.lower()
    
    if any(kw in style_lower for kw in ["mascot", "character", "funny"]):
        return ICONIC_TEMPLATES["mascot_story"]
    elif any(kw in style_lower for kw in ["sensory", "luxury", "premium", "drink", "food"]):
        return ICONIC_TEMPLATES["sensory_metaphor"]
    elif any(kw in style_lower for kw in ["emotional", "story", "journey", "human"]):
        return ICONIC_TEMPLATES["emotional_journey"]
    elif any(kw in style_lower for kw in ["catchphrase", "comedy", "humor", "viral"]):
        return ICONIC_TEMPLATES["catchphrase_comedy"]
    elif any(kw in style_lower for kw in ["problem", "solution", "demo", "before"]):
        return ICONIC_TEMPLATES["problem_solution"]
    elif any(kw in style_lower for kw in ["lifestyle", "aspir", "fashion", "sport"]):
        return ICONIC_TEMPLATES["aspirational_lifestyle"]
    elif any(kw in style_lower for kw in ["tech", "product", "reveal", "innovation"]):
        return ICONIC_TEMPLATES["tech_reveal"]
    else:
        return ICONIC_TEMPLATES["problem_solution"]  # Safe default


def get_audio_mood(mood: str) -> dict:
    """Get audio mood keywords for a given mood."""
    mood_lower = mood.lower()
    
    for key, value in AUDIO_MOOD_KEYWORDS.items():
        if key in mood_lower or mood_lower in value["description"].lower():
            return value
    
    return AUDIO_MOOD_KEYWORDS["epic"]  # Default


def get_voice_style(template_name: str) -> dict:
    """Get recommended voice style for a template."""
    template = ICONIC_TEMPLATES.get(template_name, {})
    voice_key = template.get("voiceover_style", "friendly_guide")
    return VOICE_STYLE_DESCRIPTORS.get(voice_key, VOICE_STYLE_DESCRIPTORS["friendly_guide"])


def generate_catchphrase_prompt(brand_name: str, benefit: str, pattern: str = None) -> str:
    """Generate a prompt for creating catchphrases."""
    pattern_info = CATCHPHRASE_PATTERNS.get(pattern, CATCHPHRASE_PATTERNS["imperative_action"])
    
    return f"""
    Create a memorable catchphrase/tagline for:
    Brand: {brand_name}
    Key Benefit: {benefit}
    
    Pattern to use: {pattern_info['pattern']}
    Examples of this pattern: {', '.join(pattern_info['examples'])}
    Why this works: {pattern_info['psychology']}
    
    Requirements:
    - Maximum 6 words
    - Easy to remember and repeat
    - Evokes emotion, not just information
    - Unique and ownable by this brand
    """
