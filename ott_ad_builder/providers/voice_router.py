"""
Voice Router - Smart voice selection for TTS
Maps speaker types, moods, and hints to optimal voices.
Supports both OpenAI and ElevenLabs voices.
"""

# Voice Library - OpenAI voices (prefixed with openai:) + ElevenLabs
# OpenAI voices: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse
VOICE_LIBRARY = {
    # === OPENAI VOICES (Primary - for variety) ===
    # Narrators - Deep, cinematic
    "hype_narrator": "openai:onyx",           # Deep, powerful male
    "movie_trailer": "openai:fable",          # Warm, dramatic
    "epic_male": "openai:echo",               # Strong, authoritative
    
    # Conversational
    "casual_friend": "openai:alloy",          # Natural, friendly
    "casual_female": "openai:nova",           # Warm female
    "storyteller": "openai:sage",             # Calm, wise
    
    # Energy/Young
    "gen_z": "openai:shimmer",                # Bright, energetic
    "energetic": "openai:coral",              # Lively
    
    # Premium/Soft
    "whisper_asmr": "openai:ballad",          # Soft, musical
    "premium_male": "openai:verse",           # Refined
    
    # === ELEVENLABS VOICES (Alternatives) ===
    "eleven_adam": "pNInz6obpgDQGcFmaJgB",    # Adam - Deep
    "eleven_antoni": "ErXwobaYiN019PkySvjV",  # Antoni - Warm
    "eleven_bella": "EXAVITQu4vr4xnSDxMaL",   # Bella - Female
    "eleven_callum": "N2lVS1w4EtoT3dr4eOWO",  # Callum - Tech
    
    # Default - Use OpenAI Onyx for commercials
    "default": "openai:onyx",
}


def select_voice(
    speaker: str = "Narrator",
    voice_hint: str = None,
    mood: str = None,
    style: str = None
) -> str:
    """
    Select the best voice ID based on speaker info and hints.
    
    Args:
        speaker: The speaker name (e.g., "Narrator", "Character")
        voice_hint: Direct hint from script (e.g., "hype_narrator", "gen_z")
        mood: Overall mood of the ad (e.g., "Premium", "Energetic")
        style: Style of the ad (e.g., "Cinematic", "Social")
    
    Returns:
        ElevenLabs voice ID
    """
    
    # Priority 1: Direct voice hint from script
    if voice_hint:
        hint_lower = voice_hint.lower().strip()
        if hint_lower in VOICE_LIBRARY:
            return VOICE_LIBRARY[hint_lower]
        # Handle special cases
        if "silent" in hint_lower:
            return None  # No voice needed
        if "hype" in hint_lower or "trailer" in hint_lower:
            return VOICE_LIBRARY["hype_narrator"]
        if "casual" in hint_lower or "friend" in hint_lower:
            return VOICE_LIBRARY["casual_friend"]
        if "whisper" in hint_lower or "asmr" in hint_lower:
            return VOICE_LIBRARY["whisper_asmr"]
        if "gen_z" in hint_lower or "young" in hint_lower:
            return VOICE_LIBRARY["gen_z"]
    
    # Priority 2: Infer from mood
    if mood:
        mood_lower = mood.lower()
        if "premium" in mood_lower or "luxury" in mood_lower:
            return VOICE_LIBRARY["whisper_asmr"]
        if "hype" in mood_lower or "energy" in mood_lower or "exciting" in mood_lower:
            return VOICE_LIBRARY["hype_narrator"]
        if "casual" in mood_lower or "friendly" in mood_lower:
            return VOICE_LIBRARY["casual_friend"]
        if "tech" in mood_lower or "modern" in mood_lower:
            return VOICE_LIBRARY["tech_expert"]
    
    # Priority 3: Infer from style
    if style:
        style_lower = style.lower()
        if "cinematic" in style_lower or "film" in style_lower:
            return VOICE_LIBRARY["movie_trailer"]
        if "social" in style_lower or "tiktok" in style_lower or "reel" in style_lower:
            return VOICE_LIBRARY["gen_z"]
    
    # Priority 4: Infer from speaker name
    speaker_lower = speaker.lower() if speaker else ""
    if "narrator" in speaker_lower:
        return VOICE_LIBRARY["hype_narrator"]
    
    # Default to hype narrator for commercials
    return VOICE_LIBRARY["hype_narrator"]


def get_voice_settings_for_hint(voice_hint: str) -> dict:
    """
    Get optimal voice settings (stability, style, speed) for a voice hint.
    
    Returns dict compatible with ElevenLabs VoiceSettings.
    """
    hint_lower = (voice_hint or "").lower()
    
    if "hype" in hint_lower or "trailer" in hint_lower:
        return {
            "stability": 0.3,
            "similarity_boost": 0.8,
            "style": 0.7,
            "speed": 0.95  # Slightly slower for drama
        }
    elif "whisper" in hint_lower or "asmr" in hint_lower:
        return {
            "stability": 0.7,
            "similarity_boost": 0.9,
            "style": 0.3,
            "speed": 0.85  # Slow, intimate
        }
    elif "gen_z" in hint_lower or "energy" in hint_lower:
        return {
            "stability": 0.4,
            "similarity_boost": 0.7,
            "style": 0.8,
            "speed": 1.1  # Fast, energetic
        }
    else:
        # Balanced default
        return {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "speed": 1.0
        }
