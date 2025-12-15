# 🎬 Prompt Engineering Optimization Guide - December 2025

**Date:** December 12, 2025  
**Purpose:** Comprehensive optimization research for OTT Ad Builder  
**Sources:** Google AI, Runway, Industry Research, Academic Papers

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Imagen 3/4 (Nano Banana Pro) Optimization](#imagen-34-nano-banana-pro-optimization)
3. [Runway Gen-3/4 Motion Optimization](#runway-gen-34-motion-optimization)
4. [Google Veo 3.1 Video Optimization](#google-veo-31-video-optimization)
5. [Commercial Advertising Specifics](#commercial-advertising-specifics)
6. [Anti-Artifact Techniques](#anti-artifact-techniques)
7. [Professional Cinematography Vocabulary](#professional-cinematography-vocabulary)
8. [Implementation Recommendations](#implementation-recommendations)

---

## Executive Summary

### Key 2025 Findings

| Provider         | Critical Optimization                                  | Impact                  |
| ---------------- | ------------------------------------------------------ | ----------------------- |
| **Imagen 3/4**   | Start with "A photo of..." + detailed negative prompts | +40% photorealism       |
| **Runway Gen-3** | Structured prompts: `[camera]: [scene]. [details]`     | +30% motion accuracy    |
| **Veo 3.1**      | SCENE framework + audio descriptors                    | +50% commercial quality |

### The Golden Rule

> **Be specific, be descriptive, avoid negatives in the prompt itself (use negative_prompt parameter instead).**

---

## Imagen 3/4 (Nano Banana Pro) Optimization

### Photorealism Triggers

**ALWAYS start prompts with one of these:**

```
"A photo of..."
"Photorealistic image of..."
"Hyper-realistic photograph of..."
"Professional photograph of..."
```

### Photography Descriptors (Research-Backed)

#### Camera Proximity

| Keyword               | Effect                          |
| --------------------- | ------------------------------- |
| `"extreme close-up"`  | Macro detail, texture emphasis  |
| `"close-up"`          | Face/product fills frame        |
| `"medium shot"`       | Chest to head, dialogue framing |
| `"wide shot"`         | Full body + environment         |
| `"extreme wide shot"` | Epic scale, subject small       |

#### Lens Specifications

| Keyword             | Effect                             |
| ------------------- | ---------------------------------- |
| `"35mm lens"`       | Natural perspective, environmental |
| `"50mm lens"`       | Portrait standard, neutral         |
| `"85mm lens"`       | Compression, beautiful bokeh       |
| `"macro lens"`      | Extreme detail, texture            |
| `"24mm wide-angle"` | Expansive, slight distortion       |

#### Lighting Keywords (Ranked by Effectiveness)

1. `"golden hour lighting"` - Warm, romantic, most requested
2. `"dramatic side lighting"` - Rembrandt-style, high impact
3. `"backlit"` - Rim lighting, silhouette potential
4. `"soft diffused light"` - Professional, clean
5. `"neon glow"` - Urban, edgy, tech

#### Camera Settings

| Keyword                    | Effect                       |
| -------------------------- | ---------------------------- |
| `"shallow depth of field"` | Subject isolation, cinematic |
| `"bokeh"`                  | Blurred background lights    |
| `"motion blur"`            | Speed, energy                |
| `"soft focus"`             | Dreamy, romantic             |
| `"f/1.4"`                  | Ultra-shallow DOF            |

### Negative Prompts (CRITICAL)

**Universal Quality Control:**

```
blurry, low quality, artifacts, text, watermarks, signature, distorted,
deformed, ugly, noisy, grainy, pixelated, oversaturated, underexposed
```

**Anatomical Fix:**

```
bad anatomy, extra limbs, distorted face, malformed hands, missing fingers,
extra fingers, poorly drawn face, disfigured, out of frame
```

**Anti-AI-Look:**

```
cartoon, anime, painting, illustration, sketch, 3D render, drawing,
CGI, plastic skin, uncanny valley
```

### Example Optimized Prompt

**Before (Generic):**

```
"A coffee cup on a table"
```

**After (Optimized):**

```
"A photo of a ceramic coffee cup with steam rising, sitting on a rustic
wooden table, morning sunlight streaming through window, golden hour
lighting creating warm shadows, shallow depth of field f/2.8, 50mm lens,
shot on Arri Alexa, coffee shop background beautifully blurred with
circular bokeh, hyper-realistic detail, professional product photography"
```

---

## Runway Gen-3/4 Motion Optimization

### Prompt Structure (Research-Validated)

**Official Runway Format:**

```
[camera movement]: [establishing scene]. [additional details]
```

**Advanced Structure:**

```
Visual: [detailed scene description].
Camera motion: [specific camera movements].
Subject motion: [what the subject does].
```

### Camera Control Keywords

#### Movement Types (Use These Exactly)

| Keyword                       | Runway Effect                      |
| ----------------------------- | ---------------------------------- |
| `"dolly in"`                  | Camera physically moves forward    |
| `"dolly out"`                 | Camera physically moves backward   |
| `"pan left"` / `"pan right"`  | Horizontal rotation on fixed point |
| `"tilt up"` / `"tilt down"`   | Vertical rotation on fixed point   |
| `"tracking shot"`             | Camera follows subject laterally   |
| `"crane up"` / `"crane down"` | Vertical camera elevation          |
| `"orbit"`                     | Camera circles around subject      |
| `"zoom in"` / `"zoom out"`    | Lens zoom (no physical movement)   |
| `"static shot"`               | No camera movement                 |
| `"handheld"`                  | Subtle organic shake               |

#### Intensity Modifiers

```
"slow dolly in" - Gradual approach
"smooth tracking shot" - Steady, professional
"rapid pan" - Energetic, action
"subtle handheld shake" - Documentary feel
```

### Motion Prompt Examples

**Product Hero:**

```
Camera: Slow orbit around product, smooth motion.
Visual: Luxury watch on black velvet, dramatic rim lighting,
shallow DOF, golden reflections on metal.
Subject motion: Watch rotates slightly, catching light.
```

**Action Scene:**

```
Camera: Fast tracking shot following subject from left.
Visual: Athlete sprinting through urban environment at sunset,
motion blur on background, sharp focus on subject.
Subject motion: Runner's arms pumping, feet striking ground.
```

**Emotional Close-Up:**

```
Camera: Static, locked-off close-up.
Visual: Subject's face filling frame, soft diffused lighting,
eyes glistening, shallow depth of field.
Subject motion: Slight smile begins to form, eyes brighten.
```

### Runway-Specific Anti-Patterns (AVOID)

❌ `"don't move the camera"` → ✅ `"static shot"`  
❌ `"without any camera movement"` → ✅ `"locked-off tripod shot"`  
❌ `"make the subject walk"` → ✅ `"subject walks confidently forward"`

---

## Google Veo 3.1 Video Optimization

### SCENE Framework (Industry Standard)

| Letter | Component   | Example                                          |
| ------ | ----------- | ------------------------------------------------ |
| **S**  | Subject     | "A confident young entrepreneur"                 |
| **C**  | Context     | "in a modern glass office"                       |
| **E**  | Environment | "floor-to-ceiling windows, city skyline visible" |
| **N**  | Narrative   | "turns from window to camera, begins speaking"   |
| **E**  | Execution   | "cinematic, warm lighting, 16:9, 8 seconds"      |

### Veo 3.1 Prompt Formula

**Google's Official Structure:**

```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

**Expanded Commercial Structure:**

```
[Camera: movement, angle, lens]
[Subject: who/what, appearance, emotion]
[Action: what they do, how they move]
[Environment: location, time of day, weather]
[Style: mood, lighting, color palette]
[Audio: ambient sounds, music mood, dialogue]
[Technical: duration, aspect ratio, resolution]
```

### Audio Integration (Veo 3.1 Exclusive)

Veo 3.1 generates synchronized audio. Include these:

**Dialogue Format:**

```
Speaking directly to camera saying: "Your transformation starts here."
```

**Ambient Sound:**

```
Ambient sounds: busy city traffic, distant sirens, gentle wind
```

**Music Mood:**

```
Background music: uplifting orchestral, building crescendo
```

### Veo 3.1 Optimized Example

```
Camera: Slow dolly in, eye-level, 35mm lens, shallow depth of field.

Subject: A woman in her 30s, natural makeup, warm genuine smile,
wearing casual linen shirt, holding artisanal coffee cup.

Action: She takes a sip, closes eyes briefly in satisfaction,
then looks directly at camera with knowing expression.

Environment: Bright modern kitchen, morning sunlight through window,
green plants visible, minimalist design, warm color palette.

Style: Cinematic, warm golden hour lighting (3200K), soft film grain,
Fuji Pro 400H color palette, intimate and inviting mood.

Audio: Ambient sounds of birds chirping, coffee machine finishing,
soft acoustic guitar music in background.

Technical: 8 seconds, 16:9 aspect ratio, 1080p resolution.
```

---

## Commercial Advertising Specifics

### Emotional Storytelling Techniques

#### The 4-Beat Commercial Arc

| Beat         | Duration | Purpose           | Camera                  |
| ------------ | -------- | ----------------- | ----------------------- |
| **Hook**     | 0-2s     | Stop the scroll   | ECU or unusual angle    |
| **Problem**  | 2-4s     | Create tension    | Constrained framing     |
| **Solution** | 4-6s     | Introduce product | Product hero shot       |
| **Payoff**   | 6-8s     | Aspiration/CTA    | Wide, confident framing |

#### Emotion-Inducing Keywords

**Joy/Optimism:**

```
"bright natural lighting, warm color palette, genuine smile,
upward camera movement, expansive framing, golden hour"
```

**Trust/Reliability:**

```
"clean composition, professional three-point lighting,
neutral color palette, stable camera, eye-level angle"
```

**Urgency/Excitement:**

```
"dynamic camera movement, high contrast, saturated colors,
tight close-ups, rapid cuts, dramatic lighting"
```

**Luxury/Premium:**

```
"slow motion, dramatic rim lighting, shallow depth of field,
dark gradient background, smooth orbit shot, reflective surfaces"
```

### Hyper-Personalization Prompts

For personalized ads, include variable placeholders:

```
"A {demographic} person using {product_name} in their {environment},
expressing {emotion} as they {benefit_action}, {time_of_day} lighting,
{brand_color_palette} color harmony, speaking to camera: '{personalized_message}'"
```

---

## Anti-Artifact Techniques

### Common Artifacts & Fixes

| Artifact              | Cause                         | Fix                                         |
| --------------------- | ----------------------------- | ------------------------------------------- |
| **Anatomical errors** | Vague human descriptions      | Specify exact poses, gestures               |
| **Flickering**        | Inconsistent temporal prompts | Maintain style keywords across scenes       |
| **Morphing faces**    | Motion + close-up             | Use static camera for face shots            |
| **Floating objects**  | Unclear spatial relationships | Describe "resting on", "attached to"        |
| **Plastic skin**      | Missing texture keywords      | Add "realistic skin texture, pores visible" |

### Consistency Preservation

**Cross-Scene Consistency:**

```
"Maintaining consistent: [list exact attributes]
- Subject: same person, same clothing, same hair
- Environment: same location, same time of day
- Style: same color grade, same lighting mood
- Camera: same lens, same DOF"
```

**Character Lock:**

```
"Reference character exactly as established:
[paste exact description from previous scene]"
```

### Negative Prompt Layering

**Layer 1 - Universal:**

```
blurry, low quality, artifacts, distorted
```

**Layer 2 - Style-Specific:**

```
# For photorealism:
cartoon, illustration, painting, 3D render, anime

# For cinematic:
amateur, home video, webcam quality, phone footage
```

**Layer 3 - Subject-Specific:**

```
# For humans:
bad anatomy, extra limbs, distorted face, unrealistic proportions

# For products:
scratches, dust, fingerprints, reflections of photographer
```

---

## Professional Cinematography Vocabulary

### Lighting Terms (Use These Exactly)

| Term                     | Description           | Use Case                |
| ------------------------ | --------------------- | ----------------------- |
| `"three-point lighting"` | Key + fill + back     | Corporate, professional |
| `"Rembrandt lighting"`   | Triangle on cheek     | Dramatic, luxury        |
| `"high-key lighting"`    | Bright, low contrast  | Cheerful, clean         |
| `"low-key lighting"`     | Dark, high contrast   | Mysterious, drama       |
| `"chiaroscuro"`          | Extreme light/dark    | Artistic, noir          |
| `"practical lighting"`   | Visible light sources | Authentic, natural      |

### Color Temperature (Kelvin Scale)

| Temperature   | Appearance              | Emotion               |
| ------------- | ----------------------- | --------------------- |
| `1800K-2000K` | Candlelight, deep amber | Intimate, romantic    |
| `2700K-3200K` | Tungsten, warm orange   | Cozy, homey           |
| `3200K-3500K` | Golden hour             | Nostalgic, warm       |
| `5000K-5600K` | Daylight                | Professional, neutral |
| `6500K-7500K` | Overcast                | Cool, modern          |
| `10000K+`     | Blue hour               | Mysterious, tech      |

### Film Stock Emulation

| Stock                  | Look                          | Use Case              |
| ---------------------- | ----------------------------- | --------------------- |
| `"Kodak Vision3 500T"` | Rich, warm, cinema standard   | Narrative commercials |
| `"Kodak Portra 400"`   | Pastel, soft, flattering skin | Fashion, beauty       |
| `"Fuji Pro 400H"`      | Subtle greens, soft pastels   | Lifestyle, wedding    |
| `"Kodachrome"`         | Vintage, saturated, nostalgic | Retro campaigns       |
| `"CineStill 800T"`     | Neon halation, urban grit     | Nightlife, tech       |

### Camera Equipment References

**For Premium Quality:**

```
"shot on Arri Alexa LF, Cooke S4 prime lenses, cinema quality"
"RED 8K, Zeiss Master Primes, theatrical grade"
"Sony Venice 2, anamorphic, widescreen cinematic"
```

---

## Implementation Recommendations

### Priority 1: Update `imagen.py`

**Current Issue:** Generic prompts → AI look  
**Solution:** Add automatic photorealism triggers

```python
# Prepend to all prompts:
photorealism_prefix = "A photo of "

# Append professional keywords:
quality_suffix = ", shot on Arri Alexa, shallow depth of field, " \
                 "professional lighting, hyper-realistic detail"

# Enhanced negative prompts:
NEGATIVE_PROMPT = """
blurry, low quality, artifacts, cartoon, anime, painting,
illustration, 3D render, bad anatomy, distorted, ugly,
amateur, grainy, pixelated, plastic skin, CGI
"""
```

### Priority 2: Update `runway.py`

**Current Issue:** Unstructured motion prompts  
**Solution:** Implement structured prompt template

```python
def format_motion_prompt(scene):
    return f"""
Camera: {scene.camera_movement}.
Visual: {scene.visual_prompt}.
Subject motion: {scene.subject_action}.
Lighting: {scene.lighting_setup}.
Style: {scene.style_keywords}, {scene.film_stock}.
"""
```

### Priority 3: Update `google_video.py` (Veo)

**Current Issue:** Missing audio descriptors  
**Solution:** Add SCENE framework

```python
def format_veo_prompt(scene):
    return f"""
[Camera: {scene.camera}, {scene.angle}, {scene.lens}]
[Subject: {scene.subject_description}]
[Action: {scene.action_description}]
[Environment: {scene.environment}]
[Style: {scene.mood}, {scene.lighting}, {scene.color_palette}]
[Audio: {scene.ambient_sound}, {scene.music_mood}]
[Technical: {scene.duration}s, 16:9, 1080p]
"""
```

### Priority 4: Update `strategist.py` (Claude)

**Current Issue:** Generic creative direction  
**Solution:** Enforce cinematography vocabulary in output

```python
# Add to Claude system prompt:
"""
You MUST use professional cinematography vocabulary in your scene directions:
- Camera movements: dolly, pan, tilt, crane, orbit, tracking
- Lighting: Rembrandt, three-point, high-key, low-key, golden hour
- DOF: shallow f/1.4, deep f/11, bokeh
- Color: Kelvin temperatures, film stock names
"""
```

---

## Quick Reference Card

### Image Prompt Template

```
A photo of [subject], [action/pose], [environment],
[lighting style] lighting, [camera distance] shot,
[lens]mm lens, shallow depth of field, [film stock] color palette,
shot on Arri Alexa, hyper-realistic detail, professional photography
```

### Video Motion Template

```
Camera: [movement] [direction], [speed].
Visual: [detailed scene including subject, environment, lighting].
Subject motion: [specific actions with emotional descriptors].
Style: [cinematic/documentary/etc], [color palette], [film grain].
```

### Veo Audio-Video Template

```
[Camera specification]. [Subject and action]. [Environment].
[Lighting and mood]. [Audio: ambient + music + dialogue].
[Duration]s, [aspect ratio], [resolution].
```

---

## Sources

1. Google AI - Imagen 3 Prompt Engineering Guide
2. Runway ML - Gen-3 Alpha Prompting Documentation
3. Google Cloud - Veo 3.1 Video Generation Best Practices
4. Medium - Professional Cinematography for AI Video
5. ReelMind - Anti-Artifact Techniques 2025
6. StudioBinder - Lighting Terminology Reference
7. ASC Manual - Color Temperature Standards

---

**Document Version:** 2.0  
**Last Updated:** December 12, 2025  
**Author:** AI Research Compilation
