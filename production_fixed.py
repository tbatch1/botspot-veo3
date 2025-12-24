"""
PRODUCTION-FIXED PIPELINE
Uses the full system but with CLEAN prompts (no AI slop)
"""

import os
import sys
import json
import time

sys.path.append(os.getcwd())

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import Script, Scene, ScriptLine


def create_fixed_video(
    product_name: str,
    product_tagline: str,
    scenes_data: list,
    voiceover_lines: list = None,
    duration_per_scene: int = 6
):
    """
    Create video using the FULL system but bypassing GPT-5.2's over-engineered prompts.

    Args:
        product_name: "iPhone 16 Pro"
        product_tagline: "Titanium. A18 Pro. Camera Control."
        scenes_data: List of dicts with 'visual' and 'motion' keys
        voiceover_lines: Optional list of dicts with 'text' and 'time_range'
        duration_per_scene: Seconds per scene (4, 6, or 8)
    """

    generator = AdGenerator()

    # Create clean script manually (bypass GPT-5.2)
    scenes = []
    for i, scene_data in enumerate(scenes_data):
        scene = Scene(
            id=i+1,
            visual_prompt=scene_data['visual'],
            motion_prompt=scene_data['motion'],
            audio_prompt=scene_data.get('audio', None),
            duration=duration_per_scene,
            primary_subject=product_name,
            subject_description=product_tagline
        )
        scenes.append(scene)

    # Add voiceover if provided
    lines = []
    if voiceover_lines:
        for i, vo in enumerate(voiceover_lines):
            line = ScriptLine(
                text=vo['text'],
                speaker=vo.get('speaker', 'Narrator'),
                time_range=vo.get('time_range', f"0s-{duration_per_scene}s"),
                scene_id=vo.get('scene_id', i+1)
            )
            lines.append(line)

    script = Script(scenes=scenes, lines=lines)

    # Set up state
    generator.state.user_input = f"{product_name} - {product_tagline}"
    generator.state.script = script
    generator.state.strategy = {
        "core_concept": product_tagline,
        "visual_language": "Clean product photography, professional cinematography",
        "product_name": product_name,
        "audio_signature": {
            "bgm_prompt": "minimal electronic, modern, premium",
            "bgm_vibe": "clean, modern"
        }
    }
    generator.state.status = "planned"

    # Save plan
    plan_path = generator._get_plan_path()
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(generator.state.model_dump_json(indent=2))

    print(f"[PLAN] Saved to: {plan_path}")
    print(f"[PLAN] Project ID: {generator.state.id}")

    # Execute pipeline
    print("\n[EXEC] Starting production pipeline...")
    generator.resume(project_id=generator.state.id)

    return generator.state.final_video_path


# ============================================================================
# EDIT YOUR VIDEO DETAILS HERE
# ============================================================================

PRODUCT_NAME = "Strato Frappuccino"
PRODUCT_TAGLINE = "Cold foam bliss"

SCENES = [
    {
        "visual": "Barista preparing drink in bright modern cafe, natural window light, clean composition",
        "motion": "Gentle push in on barista working",
        "audio": "cafe ambience, espresso machine, ice clinking"
    },
    {
        "visual": "Macro shot of blended coffee swirling, cream pouring into clear cup, professional food photography",
        "motion": "Slow motion pour, circular camera movement",
        "audio": "liquid pouring, blender hum, foam swirl"
    },
    {
        "visual": "Customer enjoying drink outdoors, satisfied smile, cup visible with condensation, lifestyle photography",
        "motion": "Slow dolly toward customer and product",
        "audio": "straw sip, ambient outdoor sounds"
    }
]

# Optional voiceover (set to None for music-only)
VOICEOVER = [
    {"text": "Blended to perfection.", "time_range": "0s-2s", "scene_id": 2},
    {"text": "Topped with cold foam.", "time_range": "8s-10s", "scene_id": 2},
    {"text": "Strato Frappuccino. Try it today.", "time_range": "13s-16s", "scene_id": 3}
]

# Or for music-only video:
# VOICEOVER = None


def main():
    print("\n" + "="*80)
    print("PRODUCTION-FIXED PIPELINE")
    print("Using CLEAN prompts + full audio/video system")
    print("="*80 + "\n")

    try:
        final_video = create_fixed_video(
            product_name=PRODUCT_NAME,
            product_tagline=PRODUCT_TAGLINE,
            scenes_data=SCENES,
            voiceover_lines=VOICEOVER,
            duration_per_scene=6
        )

        print("\n" + "="*80)
        print("✓ PRODUCTION COMPLETE")
        print("="*80)
        print(f"Video: {final_video}")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ FAILED: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
