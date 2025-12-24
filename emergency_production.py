"""
EMERGENCY PRODUCTION VIDEO GENERATOR
Use this when you need REAL production quality TODAY - no AI slop bullshit.

This bypasses the over-engineered GPT prompts and uses clean, simple prompts
that actually work with Veo 3.1.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add project to path
sys.path.append(os.getcwd())

from ott_ad_builder.config import config
from ott_ad_builder.providers.fal_flux import FalFluxProvider
from ott_ad_builder.providers.video_google import GoogleVideoProvider
from ott_ad_builder.providers.composer import Composer
from ott_ad_builder.state import ProjectState, Script, Scene, ScriptLine


class EmergencyProducer:
    """
    Clean, simple video production that ACTUALLY WORKS.
    No GPT-5.2 over-engineering. No AI slop keywords. Just clean prompts.
    """

    def __init__(self):
        self.flux = FalFluxProvider()
        self.veo = GoogleVideoProvider()
        self.seed = int(time.time()) % 1000000

    def create_simple_product_video(self, product_name: str, product_description: str, num_scenes: int = 3):
        """
        Create a clean product video with SIMPLE, WORKING prompts.

        Args:
            product_name: e.g. "iPhone 16 Pro"
            product_description: e.g. "titanium design, 5x telephoto camera, A18 Pro chip"
            num_scenes: 2-4 recommended
        """

        print("\n" + "="*80)
        print("EMERGENCY PRODUCTION MODE - BYPASSING AI SLOP")
        print("="*80)

        # Simple scene templates that ACTUALLY work
        scene_templates = [
            {
                "visual": f"{product_name} on clean white surface, centered, front view, soft shadows, professional product photography",
                "motion": "Slow push in, smooth, product stays centered"
            },
            {
                "visual": f"{product_name} rotating slowly on turntable, clean studio lighting, medium shot, shows key features: {product_description}",
                "motion": "Smooth 180 degree rotation, consistent speed"
            },
            {
                "visual": f"Close-up of {product_name} key feature, dramatic side lighting, shallow depth of field",
                "motion": "Gentle dolly right to left, slow reveal"
            },
            {
                "visual": f"{product_name} in lifestyle context, natural lighting, hero shot, product prominent in frame",
                "motion": "Subtle crane down, smooth settle on product"
            }
        ]

        # Create clean scenes
        scenes = []
        for i in range(min(num_scenes, len(scene_templates))):
            template = scene_templates[i]

            print(f"\n[SCENE {i+1}] Generating with CLEAN prompt...")
            print(f"  Visual: {template['visual'][:80]}...")

            # Generate image with Flux (NO AI SLOP)
            try:
                image_path = self.flux.generate_image(
                    prompt=template['visual'],
                    seed=self.seed + i
                )
                print(f"  ✓ Image generated: {os.path.basename(image_path)}")
            except Exception as e:
                print(f"  ✗ Image failed: {e}")
                continue

            # Generate video with Veo (CLEAN motion prompt)
            try:
                print(f"  [VEO] Animating with clean motion prompt...")
                video_path = self.veo.animate(
                    image_path=image_path,
                    prompt=template['motion'],
                    duration=6  # 6 seconds is the sweet spot
                )
                print(f"  ✓ Video generated: {os.path.basename(video_path)}")
            except Exception as e:
                print(f"  ✗ Video failed: {e}")
                continue

            # Create scene object
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
            raise Exception("All scenes failed! Check your API keys.")

        print(f"\n[SUCCESS] Generated {len(scenes)} clean scenes")

        # Assemble final video
        print(f"\n[ASSEMBLY] Composing final video...")

        state = ProjectState(
            id=f"emergency_{int(time.time())}",
            user_input=f"{product_name} product video",
            seed=self.seed
        )
        state.script = Script(scenes=scenes, lines=[])
        state.status = "assembling"

        composer = Composer()
        final_path = composer.compose(state, transition_type="fade")

        print("\n" + "="*80)
        print("PRODUCTION VIDEO COMPLETE")
        print("="*80)
        print(f"Location: {final_path}")
        print(f"Scenes: {len(scenes)}")
        print(f"Duration: ~{len(scenes) * 6} seconds")
        print("="*80 + "\n")

        return final_path


def main():
    """Run emergency production mode from command line"""

    import argparse
    parser = argparse.ArgumentParser(description="Emergency Production Video Generator - NO AI SLOP")
    parser.add_argument("product_name", help="Product name (e.g. 'iPhone 16 Pro')")
    parser.add_argument("--description", "-d", default="premium design, advanced features",
                       help="Product description for context")
    parser.add_argument("--scenes", "-s", type=int, default=3, choices=[2,3,4],
                       help="Number of scenes (2-4)")

    args = parser.parse_args()

    producer = EmergencyProducer()

    try:
        final_video = producer.create_simple_product_video(
            product_name=args.product_name,
            product_description=args.description,
            num_scenes=args.scenes
        )

        print(f"\n✓ SUCCESS: {final_video}\n")

    except Exception as e:
        print(f"\n✗ FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
