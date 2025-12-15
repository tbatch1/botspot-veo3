"""
Style Profiles for Adaptive Prompt Engineering
Maps detected styles to specific prompt enhancements and constraints.
"""

# Style-specific prompt enhancements for video generation (Veo 3.1 Ultra)
# ENHANCED with 2025 cinematography research (DOF f-stops, Kelvin temps, motion modifiers)
VIDEO_ENHANCEMENTS = {
    "photorealistic": """Shot on Arri Alexa with Cooke S4 prime lenses, natural film grain texture.
Shallow depth of field f/2.8, 3200K golden hour color temperature, subtle halation on highlights.
Natural skin texture with visible pores, authentic lighting with gentle shadows.
Smooth cinematic camera motion, 35mm depth of field characteristics.""",

    "abstract": """Dreamlike physics, impossible perspectives, surreal geometry, M.C. Escher-inspired composition.
Bold color contrasts, symbolic imagery, conceptual metaphors, non-literal representation.
Speed ramp effect, morphing shapes, unexpected transitions, visual poetry.
Ultra shallow depth of field f/1.4, anamorphic bokeh.""",

    "minimalist": """Clean lines, negative space dominance, breathing room in composition.
Deep depth of field f/11, daylight balanced 5500K color temperature.
Minimal elements, singular focus, zen aesthetics, purity of form.
Smooth glide motion, calm transitions, restrained color palette.""",

    "maximalist": """Rich layered detail, visual abundance, complex textures, ornate elements.
Medium depth of field f/5.6, warm tungsten 2700K lighting.
Dense composition, multiple focal points, baroque aesthetics.
Dynamic motion, bustling energy, overwhelming beauty in complexity.""",

    "noir": """High contrast black and white, dramatic chiaroscuro lighting, deep shadows.
Low-key lighting, 2700K tungsten color temperature, sharp angles.
Film noir aesthetics, venetian blind shadows, smoke effects, mystery.
Slow motion emphasis, dramatic silhouettes, 1940s cinema influence.""",

    "neon": """Neon-lit cyberpunk aesthetics, electric glow, vibrant fluorescent colors.
Shallow depth of field f/1.8, 12000K deep blue color temperature accents.
Blade Runner-inspired, rain-slicked streets, holographic effects.
Speed ramp motion, high contrast neon against darkness, futuristic dystopian atmosphere.""",

    "vintage": """Vintage film aesthetics, aged film grain, nostalgic color grading.
Swirly bokeh effect, 3200K tungsten color temperature, warm tones.
Classic cinema look, 1970s/80s color science, retro vibe.
Organic handheld motion, subtle imperfections, timeless quality.""",

    "documentary": """Authentic documentary style, handheld camera movement, natural lighting.
Medium depth of field f/5.6, daylight balanced 5600K color temperature.
Raw unpolished aesthetics, real-life authenticity, candid moments.
Organic handheld shake, observational approach, photojournalistic quality.""",

    "animated": """Stylized animation aesthetics, exaggerated movements, bold colors.
Deep focus, vibrant saturated palette, graphic design principles.
Non-photorealistic rendering, illustrated quality, cartoon physics.
Dynamic action, playful visuals, expressive character animation.""",

    "epic": """Epic cinematic scope, sweeping vistas, grand scale, heroic framing.
Deep depth of field f/11, golden hour 3500K color temperature.
Slow motion emphasis, crane shot movement, widescreen panoramas.
Lord of the Rings-inspired cinematography, awe-inspiring composition, legendary atmosphere."""
}

# Style-specific negative prompts for Veo 3.1 (supported)
# NOTE: Imagen 4 Ultra does NOT support negative prompts
VIDEO_NEGATIVE_PROMPTS = {
    "photorealistic": "cartoon, illustration, painting, 3d render, cgi, artificial, plastic, fake, stylized",
    "abstract": "photorealistic, mundane, ordinary, literal, documentary, realistic",
    "minimalist": "cluttered, busy, complex, ornate, dense, chaotic, overwhelming",
    "maximalist": "minimal, sparse, empty, simple, plain, bare, understated",
    "noir": "colorful, bright, cheerful, pastel, vibrant, well-lit, flat lighting",
    "neon": "natural lighting, muted colors, dark, monochrome, realistic",
    "vintage": "modern, digital, crisp, clean, contemporary, futuristic",
    "documentary": "staged, posed, artificial, studio lighting, polished",
    "animated": "photorealistic, realistic, live action, authentic",
    "epic": "intimate, small-scale, mundane, ordinary, claustrophobic"
}

# Image generation positive emphasis (Imagen 4 Ultra - no negative prompts supported)
IMAGE_POSITIVE_EMPHASIS = {
    "photorealistic": "Award-winning photography, National Geographic quality, authentic realism, natural imperfections, professional cinematography",
    "abstract": "Abstract art, conceptual composition, symbolic imagery, non-literal representation, artistic vision",
    "minimalist": "Minimalist design, clean composition, negative space, zen aesthetics, simplicity and elegance",
    "maximalist": "Baroque richness, layered complexity, ornate detail, visual abundance, intricate patterns",
    "noir": "Film noir cinematography, dramatic chiaroscuro, high contrast black and white, classic mystery atmosphere",
    "neon": "Cyberpunk neon aesthetics, electric glow, vibrant fluorescent lighting, futuristic atmosphere",
    "vintage": "Vintage photography, nostalgic color grading, timeless classic aesthetics, retro quality",
    "documentary": "Documentary photography, photojournalistic authenticity, candid realism, natural moments",
    "animated": "Stylized illustration, animated art style, bold graphic design, expressive visuals",
    "epic": "Epic fantasy cinematography, grand scale, heroic composition, awe-inspiring, legendary atmosphere"
}

# Emotional beat vocabularies by tone
EMOTIONAL_BEATS_BY_TONE = {
    "mysterious": ["intrigue", "unknown", "discovery", "revelation"],
    "triumphant": ["challenge", "struggle", "breakthrough", "victory"],
    "intimate": ["connection", "vulnerability", "trust", "closeness"],
    "energetic": ["ignition", "momentum", "peak", "exhilaration"],
    "playful": ["curiosity", "surprise", "delight", "joy"],
    "serious": ["awareness", "consideration", "decision", "action"],
    "dramatic": ["tension", "conflict", "climax", "resolution"],
    "serene": ["stillness", "harmony", "peace", "transcendence"]
}

# Duration recommendations by format
FORMAT_DURATIONS = {
    "product_showcase": {"min": 8, "optimal": 15, "max": 20},
    "brand_manifesto": {"min": 30, "optimal": 60, "max": 90},
    "emotional_story": {"min": 15, "optimal": 30, "max": 45},
    "teaser": {"min": 5, "optimal": 10, "max": 15},
    "explainer": {"min": 30, "optimal": 60, "max": 120},
    "testimonial": {"min": 20, "optimal": 30, "max": 45},
    "lifestyle": {"min": 15, "optimal": 30, "max": 60}
}

# Scene count recommendations by format
FORMAT_SCENE_COUNTS = {
    "product_showcase": {"min": 3, "optimal": 5, "max": 7},
    "brand_manifesto": {"min": 6, "optimal": 10, "max": 15},
    "emotional_story": {"min": 4, "optimal": 6, "max": 8},
    "teaser": {"min": 2, "optimal": 3, "max": 4},
    "explainer": {"min": 5, "optimal": 8, "max": 12},
    "testimonial": {"min": 3, "optimal": 5, "max": 7},
    "lifestyle": {"min": 4, "optimal": 6, "max": 10}
}
