"""
QUICK VIDEO GENERATOR - GET PRODUCTION QUALITY IN 5 MINUTES

Run this when you need a video TODAY and don't want AI slop.

Usage:
    python quick_video.py "Your product name"

Example:
    python quick_video.py "Tesla Cybertruck"
    python quick_video.py "Luxury Watch Collection"
"""

import os
import sys

sys.path.append(os.getcwd())

from emergency_production import EmergencyProducer


# ============================================================================
# EDIT THESE FOR YOUR VIDEO
# ============================================================================

PRODUCT_NAME = "Strato Frappuccino"

PRODUCT_DESCRIPTION = "blended coffee with cold foam, minimalist cup, premium cafe aesthetic"

NUM_SCENES = 3  # 2, 3, or 4

# Custom scene prompts (OPTIONAL - delete if you want auto-generated)
CUSTOM_SCENES = [
    {
        "visual": "Barista in modern cafe preparing drink, natural light through windows, professional photography, clean composition",
        "motion": "Gentle push in on barista, smooth and steady"
    },
    {
        "visual": "Macro shot of coffee being blended, rich liquid swirling, cream pouring into clear cup, professional food photography",
        "motion": "Slow motion vortex, smooth circular camera movement"
    },
    {
        "visual": "Customer enjoying drink at outdoor cafe table under green umbrella, natural daylight, satisfied expression, lifestyle photography",
        "motion": "Slow lateral drift toward customer, subtle push to product"
    }
]

# ============================================================================


def main():
    print("\n🎬 QUICK VIDEO GENERATOR - BYPASSING AI SLOP\n")

    producer = EmergencyProducer()

    if len(sys.argv) > 1:
        product = sys.argv[1]
        desc = sys.argv[2] if len(sys.argv) > 2 else PRODUCT_DESCRIPTION
    else:
        product = PRODUCT_NAME
        desc = PRODUCT_DESCRIPTION

    print(f"Product: {product}")
    print(f"Description: {desc}")
    print(f"Scenes: {NUM_SCENES}\n")

    # If custom scenes provided, use them
    if CUSTOM_SCENES:
        print(f"Using {len(CUSTOM_SCENES)} custom scenes\n")

        import time
        from ott_ad_builder.state import ProjectState, Script, Scene
        from ott_ad_builder.providers.composer import Composer

        scenes = []
        seed = int(time.time()) % 1000000

        for i, template in enumerate(CUSTOM_SCENES[:NUM_SCENES]):
            print(f"\n[SCENE {i+1}]")
            print(f"  Visual: {template['visual'][:70]}...")

            # Generate image
            try:
                image_path = producer.flux.generate_image(
                    prompt=template['visual'],
                    seed=seed + i
                )
                print(f"  ✓ Image: {os.path.basename(image_path)}")
            except Exception as e:
                print(f"  ✗ Image failed: {e}")
                continue

            # Generate video
            try:
                video_path = producer.veo.animate(
                    image_path=image_path,
                    prompt=template['motion'],
                    duration=6
                )
                print(f"  ✓ Video: {os.path.basename(video_path)}")
            except Exception as e:
                print(f"  ✗ Video failed: {e}")
                continue

            scene = Scene(
                id=i+1,
                visual_prompt=template['visual'],
                motion_prompt=template['motion'],
                duration=6,
                image_path=image_path,
                video_path=video_path
            )
            scenes.append(scene)

        if not scenes:
            print("\n✗ All scenes failed!\n")
            return

        # Assemble
        print(f"\n[ASSEMBLY] Composing {len(scenes)} scenes...")

        state = ProjectState(
            id=f"quick_{int(time.time())}",
            user_input=f"{product} video",
            seed=seed
        )
        state.script = Script(scenes=scenes, lines=[])

        composer = Composer()
        final_path = composer.compose(state, transition_type="fade")

        print("\n" + "="*70)
        print("✓ VIDEO COMPLETE")
        print("="*70)
        print(f"Location: {final_path}")
        print(f"Scenes: {len(scenes)}")
        print(f"Duration: ~{len(scenes) * 6} seconds")
        print("="*70 + "\n")

    else:
        # Use auto-generated scenes
        final_path = producer.create_simple_product_video(
            product_name=product,
            product_description=desc,
            num_scenes=NUM_SCENES
        )

        print(f"\n✓ VIDEO READY: {final_path}\n")


if __name__ == "__main__":
    main()
