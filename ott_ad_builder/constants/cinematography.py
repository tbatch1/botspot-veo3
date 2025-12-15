"""
Cinematography Constants for Hollywood-Grade Video Generation
Professional camera movements, lighting setups, color grading, and technical keywords
"""

# ============================================================================
# CAMERA MOVEMENTS - 100+ Professional Techniques Organized by Scene Purpose
# ============================================================================

CAMERA_MOVEMENTS = {
    "establishing": [
        "Wide crane shot descending from high angle to reveal scene, slow and majestic, cinematic establishing movement",
        "Aerial drone shot slowly pushing forward over landscape, bird's eye perspective, sweeping reveal",
        "Slow dolly back from close detail revealing full environment, gradual contextual reveal",
        "Static wide shot, locked-off tripod, observational documentary perspective, contemplative framing",
        "Crane up from ground level to high vantage point, dramatic vertical reveal, epic scale",
        "Slow 180-degree arc around location, establishing geography and spatial relationships",
        "Wide tracking shot following landscape contours, smooth Steadicam float, environmental immersion"
    ],

    "character_introduction": [
        "Slow dolly push-in from medium to close-up, 35mm lens, intimate emotional approach",
        "Steadicam 360-degree orbit around subject, smooth floating movement, hero introduction",
        "Low angle tracking shot following subject's confident walk, hero framing, powerful presence",
        "Rack focus transition from foreground to subject in background, depth and discovery",
        "Handheld follow shot at subject's eye level, intimate documentary proximity",
        "Slow reveal pan from environment to subject, contextual character introduction",
        "Static medium shot allowing subject to enter frame, measured and deliberate"
    ],

    "emotional_moment": [
        "Handheld close-up with subtle drift, intimate documentary feel, raw authenticity",
        "Slow zoom in on eyes, shallow depth of field, emotional intensity building",
        "Static medium close-up, allowing performance to breathe, contemplative observation",
        "Over-the-shoulder slow push-in during dialogue, drawing viewer deeper into moment",
        "Gentle Steadicam circle around emotional exchange, fluid intimate movement",
        "Slow dolly pull-back revealing emotional context, gradual understanding",
        "Locked-off close-up, no camera movement, letting emotion speak, powerful stillness"
    ],

    "product_hero": [
        "Tabletop 360-degree orbit, macro lens, shallow DOF, luxury product presentation",
        "Slow dolly push-in revealing product details, hero lighting, dramatic unveiling",
        "Low angle hero shot, product framed against clean gradient background, iconic positioning",
        "Overhead bird's eye view, product centered perfectly in frame, symmetrical balance",
        "Slow vertical crane down to product level, majestic reveal, premium positioning",
        "Tracking shot following product line features, smooth gimbal movement, showcase tour",
        "Static locked-off hero shot, product perfectly composed, editorial photography aesthetic",
        "Slow rack focus from environment to product, spotlight reveal, attention shift"
    ],

    "action_energy": [
        "Whip pan transition from subject to environment, dynamic rapid cut",
        "Fast tracking shot following moving subject, gimbal stabilized, urgent pursuit energy",
        "Handheld chase perspective, documentary raw energy, immediate visceral feel",
        "Quick dolly zoom (vertigo effect) for dramatic reveal, psychological tension",
        "Rapid pan across action sequence, motion blur transition, kinetic energy",
        "Dutch angle tilt with forward push, disorienting dynamic movement, tension building",
        "High-speed tracking shot at subject level, speed and momentum, adrenaline rush"
    ],

    "lifestyle_showcase": [
        "Smooth gimbal walk-through following subject's natural movement, authentic lifestyle flow",
        "Slow motion Steadicam glide through environment, dreamy aspirational feel",
        "Natural handheld observation, documentary authenticity, real-life intimacy",
        "Gentle tracking shot parallel to subject, companionable pacing, relatable journey",
        "Crane shot rising above lifestyle scene, aspirational overview, elevated perspective",
        "Static wide allowing lifestyle action to unfold naturally, observational authenticity",
        "Smooth dolly through lifestyle environment, exploratory movement, immersive experience"
    ],

    "closing": [
        "Slow dolly pull back to wide, revealing full context, narrative resolution",
        "Crane up and away with gradual fade to black, elegant ending flourish",
        "Static hold on final composition, letting moment land, contemplative conclusion",
        "Slow rack focus from subject to logo/product, brand resolution and signature",
        "Gentle push-in to final product shot, emphasis and closure, definitive ending",
        "Fade to black with locked-off composition, clean professional finish",
        "Slow pan to reveal final brand message, narrative punctuation"
    ],

    "transition": [
        "Whip pan for scene transition, motion blur connecting moments",
        "Rack focus shift between scenes, depth transition, visual link",
        "Slow push through foreground element to new scene, portal transition",
        "Pan across connecting element between locations, smooth scene bridge"
    ]
}


# ============================================================================
# SHOT SIZES - Professional Framing Templates
# ============================================================================

SHOT_SIZE_PROMPTS = {
    "extreme_wide": "Extreme wide shot (EWS), vast environment visible, subject small in epic space, grand cinematic scale, establishing geography",
    "wide": "Wide shot (WS), subject head-to-toe visible, clear environmental context, balanced composition, establishing perspective",
    "full": "Full shot, subject fills frame head-to-toe, less environmental distraction, focused presentation",
    "medium_wide": "Medium wide shot, waist to head framing, approaching intimacy while maintaining space",
    "medium": "Medium shot (MS), chest to head framing, standard dialogue composition, balanced and relatable, conversational distance",
    "medium_close_up": "Medium close-up (MCU), shoulders to head, intimate conversation distance, emotional connection beginning",
    "close_up": "Close-up (CU), face fills frame, emotional detail and subtle nuance visible, intimate revelation",
    "big_close_up": "Big close-up (BCU), eyes and mouth dominating frame, extreme emotional intensity, powerful impact",
    "extreme_close_up": "Extreme close-up (ECU), minute product detail, surface texture visible, intricate patterns, macro perspective, technical precision"
}


# ============================================================================
# SHOT SEQUENCING - Story Arc Templates
# ============================================================================

# NEW: Emotional beat descriptions for commercial storytelling
EMOTIONAL_BEATS = {
    "hook": "Arresting visual that stops the scroll - high contrast, immediate visceral impact, unexpected framing, demands attention in first 2 seconds",
    "problem": "Visual tension and relatable pain - constrained framing, desaturated or stressed lighting, subject shows struggle or frustration, audience recognition of their own challenge",
    "discovery": "Moment of light and hope - the product/solution enters frame, subtle shift to warmer tones, subject's expression begins to change, curiosity awakened",
    "transformation": "Opening up of frame and relief - wider framing, warmer colors bloom, subject shows genuine relief or satisfaction, the change is visible and emotional",
    "payoff": "Aspirational hero shot - confident subject, premium environment, call to action positioning, the promise fulfilled, audience envisions themselves in this success"
}

SHOT_SEQUENCES = {
    "narrative_story": [
        {"scene": 1, "shot_size": "close_up", "purpose": "hook with arresting visual", "emotion": "hook"},
        {"scene": 2, "shot_size": "medium", "purpose": "establish the problem/tension", "emotion": "problem"},
        {"scene": 3, "shot_size": "medium_close_up", "purpose": "discovery and solution reveal", "emotion": "discovery"},
        {"scene": 4, "shot_size": "wide", "purpose": "transformation and payoff", "emotion": "payoff"}
    ],

    "product_showcase": [
        {"scene": 1, "shot_size": "extreme_close_up", "purpose": "hook with detail intrigue", "emotion": "hook"},
        {"scene": 2, "shot_size": "medium", "purpose": "product solving a moment", "emotion": "discovery"},
        {"scene": 3, "shot_size": "wide", "purpose": "lifestyle aspiration payoff", "emotion": "payoff"}
    ],

    "brand_anthem": [
        {"scene": 1, "shot_size": "extreme_wide", "purpose": "epic hook establishing scale", "emotion": "hook"},
        {"scene": 2, "shot_size": "medium", "purpose": "human connection and relatability", "emotion": "problem"},
        {"scene": 3, "shot_size": "close_up", "purpose": "emotional transformation payoff", "emotion": "payoff"}
    ],

    "tech_reveal": [
        {"scene": 1, "shot_size": "close_up", "purpose": "problem visualization hook", "emotion": "problem"},
        {"scene": 2, "shot_size": "extreme_close_up", "purpose": "technology discovery moment", "emotion": "discovery"},
        {"scene": 3, "shot_size": "medium", "purpose": "transformation in action", "emotion": "transformation"},
        {"scene": 4, "shot_size": "wide", "purpose": "success payoff", "emotion": "payoff"}
    ],
    
    "pain_to_gain": [
        {"scene": 1, "shot_size": "close_up", "purpose": "visceral problem hook", "emotion": "problem"},
        {"scene": 2, "shot_size": "medium", "purpose": "deepening the tension", "emotion": "problem"},
        {"scene": 3, "shot_size": "medium_close_up", "purpose": "discovery of solution", "emotion": "discovery"},
        {"scene": 4, "shot_size": "wide", "purpose": "transformation and relief", "emotion": "transformation"},
        {"scene": 5, "shot_size": "medium", "purpose": "aspirational payoff", "emotion": "payoff"}
    ]
}


# ============================================================================
# LIGHTING SETUPS - Professional Studio & Natural Techniques
# ============================================================================

LIGHTING_SETUPS = {
    "luxury_product": "Rembrandt lighting with soft box key light positioned at 45 degrees, subtle rim light highlights edges and curves, dark gradient background creates professional depth, high-end studio setup, dramatic shadows define form",

    "energetic_lifestyle": "High-key lighting bright and airy, soft fill light eliminates harsh shadows, colorful practical lights visible in background add life, motivated natural window light creates authentic feel, vibrant energy",

    "dramatic_cinematic": "Low-key chiaroscuro with hard single-source key light, deep dramatic shadows across half the frame casting mystery, film noir aesthetic, 3:1 key-to-fill ratio for high contrast, theatrical mood",

    "natural_authentic": "Golden hour soft sunlight streaming through large window, gentle ambient bounce fill from white walls, warm color temperature 3200K creates inviting glow, shallow depth of field isolates subject beautifully",

    "tech_modern": "Cool color temperature 5600K creates clinical precision, sharp edge lighting defines clean lines and surfaces, cyan and magenta colored gels create futuristic atmosphere, minimal shadows for high-tech aesthetic",

    "fashion_editorial": "Butterfly lighting (Paramount style) from directly above, soft beauty light creates perfect catchlights in eyes, dedicated hair light for separation from background, white seamless backdrop for clean magazine look",

    "automotive": "Dramatic side lighting reveals curves and body lines, rim light highlights metallic paint and reflections, studio black infinity background for complete isolation, hard directional key light sculpts form",

    "food_commercial": "Soft overhead key light mimics natural daylight, white reflector bounces fill light from below to show appetizing details, backlight creates steam and texture glow, warm practical candles add ambiance",

    "cosmetics_beauty": "Even ring light illumination for flawless skin appearance, heavy diffusion softens any texture, perfect catchlights create eye sparkle, minimal shadows for clean beauty shot, white background bounce",

    "outdoor_adventure": "Natural hard sunlight creates strong authentic shadows, lighting motivated by actual sun position in sky, subtle lens flare adds realism, high contrast and vibrant saturation, real location atmosphere",

    "corporate_professional": "Soft three-point lighting setup, balanced key-to-fill ratio 2:1, clean neutral background, professional corporate aesthetic, flattering and polished",

    "moody_atmospheric": "Single motivated source with deep shadows, volumetric haze visible in light beams, dramatic contrast, mysterious and cinematic mood, film-inspired lighting",

    "minimalist_clean": "Soft even lighting with minimal shadows, white or neutral backdrop, clean and simple aesthetic, product-focused with no distraction",

    "warm_inviting": "Soft warm-toned lighting 2700K, practical lamps visible in frame, cozy intimate atmosphere, home environment feel, comforting glow",

    "high_contrast_editorial": "Hard directional light with deep blacks, fashion editorial aesthetic, bold dramatic shadows, striking visual impact, magazine-quality lighting"
}


# ============================================================================
# COLOR GRADING - Film Stock Emulation & Cinematic Looks
# ============================================================================

COLOR_GRADES = {
    "hollywood_blockbuster": "Teal and orange color grade with high contrast, crushed blacks for cinematic depth, warm skin tones against cool backgrounds, blockbuster film aesthetic, theatrical release quality",

    "fuji_film_stock": "Fuji Pro 400H color palette with soft pastel tones, subtle green cast in shadows, gentle magenta highlights, nostalgic analog film emulsion look, wedding photography aesthetic",

    "kodak_5219": "Kodak Vision3 5219 film stock characteristics, deep contrast with rich saturated colors, slight grain texture for organic cinematic feel, professional cinema standard, theatrical release emulation",

    "bleach_bypass": "Desaturated bleach bypass processing, high contrast with intentionally reduced color saturation, gritty action film aesthetic, silver retention look, intense drama",

    "vintage_analog": "35mm analog film grain texture visible, slightly faded colors suggesting age, warm golden highlights, cool blue shadows, nostalgic 1970s Kodachrome aesthetic, retro charm",

    "nordic_minimal": "Muted Scandinavian color palette, soft grays and whites dominate, subtle blue undertones throughout, very low saturation, clean minimalist aesthetic, natural diffused light feel",

    "neon_cyberpunk": "Vibrant neon colors with heavy saturation, dominant cyan and magenta hues, high contrast with deep crushed blacks, futuristic sci-fi atmosphere, dystopian urban aesthetic",

    "natural_documentary": "Natural balanced colors, accurate realistic skin tones, minimal stylistic color grading, authentic documentary representation, clean modern broadcast look, journalistic integrity",

    "warm_golden": "Warm golden hour color palette, enhanced yellows and oranges, lifted shadows with warm tones, sunset glow aesthetic, romantic and nostalgic feel",

    "cool_clinical": "Cool blue and cyan dominant tones, reduced warmth in shadows, clinical precision feel, modern technological aesthetic, sharp and analytical mood",

    "vintage_sepia": "Sepia-toned vintage look, reduced color saturation, warm brown tones, aged photograph aesthetic, historical documentary feel, timeless classic look",

    "high_saturation_pop": "Vibrant highly saturated colors, punchy commercial aesthetic, energetic and youthful feel, social media optimized, attention-grabbing vibrancy"
}


# ============================================================================
# CAMERA EQUIPMENT - Professional Gear References for Quality
# ============================================================================

CAMERA_EQUIPMENT_KEYWORDS = {
    "cinema_camera": [
        "shot on Arri Alexa LF full-frame sensor, 4.5K resolution, professional cinema camera",
        "RED 8K Monstro sensor with 16-bit color depth, ultra-high resolution cinema capture",
        "Panavision DXL2 cinema camera, professional Hollywood production standard",
        "Sony Venice 2 full-frame 8.6K sensor, cutting-edge digital cinema technology",
        "Arri Alexa Mini LF, compact large format cinema camera, Netflix approved"
    ],

    "lenses": [
        "Cooke S4 prime lenses with organic bokeh character, cinema glass",
        "Zeiss Master Prime cinema lenses, clinical sharpness and precision",
        "Canon CN-E anamorphic lens with characteristic horizontal lens flares",
        "35mm f/1.4 prime lens, shallow depth of field, cinematic compression",
        "50mm f/1.2 portrait lens with beautiful subject separation and bokeh",
        "85mm f/1.4 with gorgeous compression and creamy background blur",
        "24mm f/1.4 wide-angle prime, environmental storytelling lens",
        "Sigma Art 40mm f/1.4, sharp cinematic rendering"
    ],

    "format": [
        "35mm film grain texture and organic analog feel",
        "IMAX large format sensor, maximum resolution and clarity",
        "Anamorphic 2.39:1 cinematic scope aspect ratio, theatrical presentation",
        "Super 35mm sensor crop for traditional cinematic look",
        "Full-frame sensor depth and dramatic subject isolation",
        "Vista Vision large format, premium image quality"
    ],

    "quality_enhancers": [
        "8K resolution downscaled to 4K for exceptional sharpness",
        "ProRes 4444 color depth and grading latitude",
        "12-bit RAW color science and wide dynamic range",
        "Shallow depth of field f/1.4 aperture, subject separation",
        "Circular bokeh background blur, lens character and dimension",
        "16-bit color depth, smooth gradient rendering"
    ]
}


# ============================================================================
# CAMERA ANGLES - Psychological Impact Descriptors
# ============================================================================

CAMERA_ANGLES = {
    "eye_level": "Eye level angle, neutral perspective, relatable human viewpoint, no power dynamic, documentary objectivity, conversational framing",

    "high_angle": "High angle looking down at subject, vulnerable positioning, subject appears smaller and less powerful, sympathetic perspective, reduced dominance",

    "low_angle": "Low angle looking up at subject, heroic powerful positioning, subject appears dominant and imposing, authoritative presence, increased stature",

    "dutch_tilt": "Dutch angle tilt 15-25 degrees, psychological tension, visual unease and disorientation, dynamic instability, dramatic stylization",

    "overhead": "Overhead bird's eye view directly above, pattern revelation, isolation emphasis, god's perspective, geographic overview, vulnerability exposure",

    "worms_eye": "Worm's eye view from ground level, extreme upward perspective, exaggerated height and drama, towering intimidation, monumental scale"
}


# ============================================================================
# ASPECT RATIOS - Platform-Specific Formats
# ============================================================================

ASPECT_RATIOS = {
    "standard_hd": "16:9 (1920x1080) standard HD broadcast format, television compatible",
    "cinematic_scope": "2.39:1 anamorphic cinematic scope, theatrical widescreen presentation",
    "theatrical": "1.85:1 theatrical standard, cinema exhibition format",
    "social_square": "1:1 square format, Instagram and social media optimized",
    "vertical_mobile": "9:16 vertical format, TikTok and mobile story optimized",
    "imax": "1.43:1 IMAX aspect ratio, premium large format presentation"
}


# ============================================================================
# MOTION MODIFIERS - Speed & Timing Effects (2025 Research)
# Sources: ReelMind, Runway Gen-4, Google Veo 3.1 Best Practices
# ============================================================================

MOTION_MODIFIERS = {
    # Slow Motion Effects
    "slow_motion": "Dramatic slow motion, 120fps capture, emphasizes beauty and detail, time dilation effect, cinematic emphasis",
    "extreme_slow_motion": "Extreme slow motion, 240fps+ capture, ultra-slow detail, particles visible, high-speed camera aesthetic",
    "subtle_slow_motion": "Subtle slow motion, 60fps capture, gentle time stretch, elegant pacing, refined movement",
    
    # Speed Variations
    "time_lapse": "Time-lapse effect, compressed time passage, accelerated movement, environmental change visible, hours to seconds",
    "hyperlapse": "Hyperlapse effect, moving time-lapse, smooth motion through time compression, dynamic progression",
    "normal_speed": "Normal real-time speed, natural motion, 24fps cinematic timing, authentic pacing",
    "fast_motion": "Fast motion, time compression, energetic pacing, dynamic movement emphasis, undercranked feel",
    "speed_ramp": "Speed ramp effect, variable frame rate, slow to fast transition, dramatic impact moment",
    
    # Motion Character
    "smooth_glide": "Smooth floating glide, ultra-stabilized movement, effortless elegance, Steadicam aesthetic",
    "organic_handheld": "Organic handheld shake, documentary realism, subtle natural movement, human POV feel",
    "mechanical_precision": "Mechanical precision movement, robotic smooth tracking, industrial accuracy, motion control rig"
}


# ============================================================================
# DEPTH OF FIELD STYLES - Focus & Bokeh Techniques (2025 Research)
# Sources: Any-to-Bokeh arXiv, ReelMind AI, Runway Gen-3/4 Guides
# ============================================================================

DEPTH_OF_FIELD_STYLES = {
    # Shallow DOF (Cinematic Isolation)
    "ultra_shallow": "Ultra shallow depth of field (f/1.2-f/1.4), extreme subject isolation, creamy smooth bokeh, cinematic separation, background melt, dreamy atmosphere",
    "shallow": "Shallow depth of field (f/1.8-f/2.8), subject in sharp focus, background beautifully blurred, cinematic bokeh circles, portrait aesthetic",
    "medium_shallow": "Medium shallow depth of field (f/4-f/5.6), subject sharp with gentle background blur, balanced isolation, commercial standard",
    
    # Medium DOF (Balanced)
    "medium": "Medium depth of field (f/5.6-f/8), subject and immediate environment sharp, natural balanced look, versatile framing",
    
    # Deep DOF (Environmental Context)
    "deep": "Deep depth of field (f/11-f/16), everything sharp from foreground to background, maximum information, landscape aesthetic",
    "extreme_deep": "Extreme deep depth of field (f/16-f/22), infinite focus, architectural precision, maximum environmental context, zone focus",
    
    # Bokeh Styles
    "circular_bokeh": "Beautiful circular bokeh balls, smooth round out-of-focus lights, f/1.4 wide aperture, creamy background separation, premium lens aesthetic",
    "hexagonal_bokeh": "Hexagonal bokeh pattern, 6-blade aperture characteristic, geometric light orbs, vintage lens aesthetic",
    "swirly_bokeh": "Swirly bokeh effect, circular blur pattern, vintage Helios lens aesthetic, dreamy romantic background, classic film look",
    "anamorphic_bokeh": "Oval anamorphic bokeh, horizontal lens flares, cinematic widescreen aesthetic, theatrical film quality"
}


# ============================================================================
# COLOR TEMPERATURE KELVIN - Mood through Light Color (2025 Research)
# Sources: Google Veo 3.1 Guide, Superprompt Best Practices
# ============================================================================

COLOR_TEMPERATURE_KELVIN = {
    # Warm Tones (Emotional, Cozy, Intimate)
    "candlelight": "1800K-2000K candlelight color temperature, deep warm amber glow, intimate romantic mood, flickering warmth",
    "tungsten": "2700K-3200K tungsten lighting, warm incandescent tone, cozy homey atmosphere, classic indoor tungsten",
    "golden_hour": "3200K-3500K golden hour temperature, warm sunset tone, nostalgic romantic atmosphere, magic hour glow",
    
    # Neutral Tones (Professional, Balanced)
    "daylight_balanced": "5000K-5600K daylight balanced, neutral white, professional accurate colors, natural outdoor look",
    "flash_neutral": "5500K flash color temperature, clean neutral white, studio photography standard, balanced illumination",
    
    # Cool Tones (Tech, Modern, Mysterious)
    "overcast_cool": "6500K-7500K overcast sky temperature, slightly cool tone, modern professional aesthetic, diffused daylight",
    "blue_hour": "10000K-12000K blue hour temperature, deep cool blue tone, mysterious cinematic twilight, atmospheric dusk",
    "deep_blue": "12000K+ deep blue color temperature, extreme cool tone, tech and sci-fi aesthetic, futuristic cold"
}


# ============================================================================
# MACRO SHOT TEMPLATES - Close-Up & Product Detail (2025 Research)
# Sources: Google Veo 3, InVideo Best Practices, Skywork.ai Examples
# ============================================================================

MACRO_SHOT_TEMPLATES = {
    "food_beverage": "Macro close-up of {subject}, slow motion detail visible, effervescent texture, backlit amber highlights, condensation beads, shallow depth of field f/2.8, studio lighting, appetizing presentation",
    
    "product_texture": "Extreme close-up of {subject} surface texture, grain detail visible, warm side lighting emphasizing ridges, macro lens 100mm, shallow depth of field, premium craftsmanship visible, material quality",
    
    "liquid_pour": "Macro shot of {subject} being poured, slow motion liquid dynamics, droplets and splash visible, backlit translucent glow, studio dramatic lighting, shallow DOF, beverage commercial aesthetic",
    
    "tech_detail": "Extreme close-up of {subject} precision engineering, light reflecting off surfaces, macro detail showing construction, matte finish visible, dramatic side lighting, shallow DOF, premium tech aesthetic",
    
    "nature_detail": "Macro close-up of {subject}, morning dew detail, soft diffused natural light, ultra shallow depth of field, organic texture visible, 100mm macro lens aesthetic, nature documentary quality",
    
    "cosmetics_texture": "Extreme close-up of {subject} texture and pigment, creamy product visible, beautiful bokeh background, ring light catchlights, shallow DOF f/2.0, beauty photography aesthetic, luxurious detail",
    
    "fabric_material": "Macro shot of {subject} weave pattern, fiber detail visible, soft directional lighting, shallow depth of field, textile quality visible, fashion photography aesthetic, material close-up",
    
    "droplet_splash": "Ultra slow motion macro of {subject} droplet impact, water crown formation visible, backlit dramatic lighting, shallow DOF, high-speed camera aesthetic, physics beauty captured"
}


# ============================================================================
# SCENE COMPLEXITY KEYWORDS - For Dynamic Scene Count Detection
# ============================================================================

SCENE_COMPLEXITY_KEYWORDS = {
    "story_driven": ["story", "journey", "transformation", "before and after", "narrative", "arc", "evolution", "progression"],
    "simple_minimal": ["product", "logo", "simple", "clean", "minimal", "single", "straightforward", "focus"],
    "complex_varied": ["multiple", "various", "several", "collection", "range", "series", "lineup", "variety", "showcase"]
}


# ============================================================================
# NEGATIVE PROMPTS - Quality Control (For Future Imagen API Support)
# ============================================================================

NEGATIVE_PROMPTS = {
    "default": "blurry, low quality, amateur photography, grainy noise, pixelated, distorted proportions, watermark, text overlay, logo, signature, amateur lighting, cluttered composition, out of focus, soft focus, poor framing",

    "professional_product": "blurry edges, low resolution, bad lighting, cluttered background, distracting elements, watermark, copyright text, poor composition, unwanted shadows on product, dust particles, scratches, defects",

    "people_portraits": "deformed faces, extra limbs, missing fingers, amateur photography, bad skin texture, unnatural poses, awkward expressions, blurry eyes, weird hands, distorted features, uncanny valley",

    "automotive": "scratches, dents, dirt, poor lighting, cluttered background, distorted reflections, low quality render, unrealistic materials, bad perspective, crooked wheels, panel gaps",

    "food": "unappetizing presentation, overexposed highlights, poor plating, cluttered table setting, artificial colors, plastic-looking texture, unnatural food appearance, burned, undercooked, messy"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_random_camera_movement(scene_purpose: str = "establishing") -> str:
    """Get a random professional camera movement for the specified scene purpose"""
    import random
    if scene_purpose in CAMERA_MOVEMENTS:
        return random.choice(CAMERA_MOVEMENTS[scene_purpose])
    return random.choice(CAMERA_MOVEMENTS["establishing"])


def get_random_equipment() -> dict:
    """Get random professional camera equipment keywords"""
    import random
    return {
        "camera": random.choice(CAMERA_EQUIPMENT_KEYWORDS["cinema_camera"]),
        "lens": random.choice(CAMERA_EQUIPMENT_KEYWORDS["lenses"]),
        "format": random.choice(CAMERA_EQUIPMENT_KEYWORDS["format"])
    }


def detect_commercial_type(user_input: str) -> str:
    """Detect the type of commercial from user input for shot sequencing"""
    input_lower = user_input.lower()

    if any(kw in input_lower for kw in ["story", "narrative", "journey", "transformation"]):
        return "narrative_story"
    elif any(kw in input_lower for kw in ["product", "showcase", "reveal", "feature"]):
        return "product_showcase"
    elif any(kw in input_lower for kw in ["brand", "anthem", "mission", "values"]):
        return "brand_anthem"
    elif any(kw in input_lower for kw in ["tech", "technology", "digital", "innovation"]):
        return "tech_reveal"
    else:
        return "product_showcase"  # Default


def calculate_scene_count(user_input: str, target_duration: int = 8) -> int:
    """Determine optimal scene count based on narrative complexity"""
    input_lower = user_input.lower()

    # Story-driven: needs more scenes for narrative arc
    if any(kw in input_lower for kw in SCENE_COMPLEXITY_KEYWORDS["story_driven"]):
        return 4  # 4 scenes × 2s each = 8s

    # Complex showcase: medium scene count
    elif any(kw in input_lower for kw in SCENE_COMPLEXITY_KEYWORDS["complex_varied"]):
        return 3  # 3 scenes × 2.67s each ≈ 8s

    # Simple/minimal: fewer scenes, longer holds
    elif any(kw in input_lower for kw in SCENE_COMPLEXITY_KEYWORDS["simple_minimal"]):
        return 2  # 2 scenes × 4s each = 8s

    # Default balanced
    else:
        return 3


def calculate_scene_durations(scene_count: int, total_duration: int = 8) -> list:
    """Calculate strategic scene duration distribution"""
    if scene_count == 2:
        return [4, 4]
    elif scene_count == 3:
        return [3, 3, 2]  # Build tension, quick resolution
    elif scene_count == 4:
        return [2, 2, 2, 2]  # Even rhythmic beats
    else:
        base = total_duration // scene_count
        return [base] * scene_count


def get_cinematography_enhancement(
    camera_movement: str = None,
    camera_angle: str = None,
    lighting: str = None,
    depth_of_field: str = None,
    motion_modifier: str = None,
    color_temperature: str = None
) -> str:
    """
    Combine cinematography elements into a cohesive enhancement string.
    Based on 2025 research from Runway Gen-4, Google Veo 3.1, and industry standards.
    
    Args:
        camera_movement: Key from CAMERA_MOVEMENTS (scene purpose like "product_hero")
        camera_angle: Key from CAMERA_ANGLES
        lighting: Key from LIGHTING_SETUPS
        depth_of_field: Key from DEPTH_OF_FIELD_STYLES
        motion_modifier: Key from MOTION_MODIFIERS
        color_temperature: Key from COLOR_TEMPERATURE_KELVIN
    
    Returns:
        Combined cinematography enhancement string for prompt engineering
    """
    import random
    elements = []
    
    if camera_movement and camera_movement in CAMERA_MOVEMENTS:
        elements.append(random.choice(CAMERA_MOVEMENTS[camera_movement]))
    
    if camera_angle and camera_angle in CAMERA_ANGLES:
        elements.append(CAMERA_ANGLES[camera_angle])
    
    if lighting and lighting in LIGHTING_SETUPS:
        elements.append(LIGHTING_SETUPS[lighting])
    
    if depth_of_field and depth_of_field in DEPTH_OF_FIELD_STYLES:
        elements.append(DEPTH_OF_FIELD_STYLES[depth_of_field])
    
    if motion_modifier and motion_modifier in MOTION_MODIFIERS:
        elements.append(MOTION_MODIFIERS[motion_modifier])
    
    if color_temperature and color_temperature in COLOR_TEMPERATURE_KELVIN:
        elements.append(COLOR_TEMPERATURE_KELVIN[color_temperature])
    
    return ". ".join(elements) if elements else ""


def get_macro_template(template_type: str, subject: str) -> str:
    """
    Get a formatted macro shot prompt template for the specified type and subject.
    
    Args:
        template_type: Key from MACRO_SHOT_TEMPLATES (e.g., "food_beverage", "tech_detail")
        subject: The subject to insert into the template (e.g., "luxury watch", "cold beer")
    
    Returns:
        Formatted macro shot prompt string
    """
    if template_type in MACRO_SHOT_TEMPLATES:
        return MACRO_SHOT_TEMPLATES[template_type].format(subject=subject)
    # Default to product_texture if type not found
    return MACRO_SHOT_TEMPLATES["product_texture"].format(subject=subject)


def get_style_cinematography_recommendations(aesthetic_style: str) -> dict:
    """
    Get recommended cinematography settings for a given aesthetic style.
    Based on 2025 AI video generation research.
    
    Args:
        aesthetic_style: The detected aesthetic (photorealistic, epic, abstract, etc.)
    
    Returns:
        Dictionary with recommended camera_movement, lighting, depth_of_field, motion
    """
    style_recommendations = {
        "photorealistic": {
            "camera_purpose": "product_hero",
            "lighting": "natural_authentic",
            "depth_of_field": "shallow",
            "motion_modifier": "smooth_glide",
            "color_temperature": "daylight_balanced"
        },
        "epic": {
            "camera_purpose": "establishing",
            "lighting": "dramatic_cinematic",
            "depth_of_field": "deep",
            "motion_modifier": "slow_motion",
            "color_temperature": "golden_hour"
        },
        "abstract": {
            "camera_purpose": "emotional_moment",
            "lighting": "tech_modern",
            "depth_of_field": "ultra_shallow",
            "motion_modifier": "speed_ramp",
            "color_temperature": "deep_blue"
        },
        "minimalist": {
            "camera_purpose": "product_hero",
            "lighting": "minimalist_clean",
            "depth_of_field": "medium",
            "motion_modifier": "normal_speed",
            "color_temperature": "daylight_balanced"
        },
        "retro": {
            "camera_purpose": "lifestyle_showcase",
            "lighting": "warm_inviting",
            "depth_of_field": "medium_shallow",
            "motion_modifier": "organic_handheld",
            "color_temperature": "tungsten"
        },
        "tech": {
            "camera_purpose": "product_hero",
            "lighting": "tech_modern",
            "depth_of_field": "shallow",
            "motion_modifier": "mechanical_precision",
            "color_temperature": "overcast_cool"
        },
        "neon": {
            "camera_purpose": "action_energy",
            "lighting": "tech_modern",
            "depth_of_field": "shallow",
            "motion_modifier": "slow_motion",
            "color_temperature": "deep_blue"
        },
        "luxury": {
            "camera_purpose": "product_hero",
            "lighting": "luxury_product",
            "depth_of_field": "ultra_shallow",
            "motion_modifier": "slow_motion",
            "color_temperature": "golden_hour"
        },
        "documentary": {
            "camera_purpose": "lifestyle_showcase",
            "lighting": "natural_authentic",
            "depth_of_field": "medium",
            "motion_modifier": "organic_handheld",
            "color_temperature": "daylight_balanced"
        },
        "cinematic": {
            "camera_purpose": "emotional_moment",
            "lighting": "dramatic_cinematic",
            "depth_of_field": "shallow",
            "motion_modifier": "slow_motion",
            "color_temperature": "golden_hour"
        }
    }
    
    return style_recommendations.get(aesthetic_style, style_recommendations["photorealistic"])
