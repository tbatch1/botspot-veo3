import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config

def generate_amazing_ad():
    print("🚀 MISSION: Generate 'Amazing' Ad for $2 Budget")
    print("------------------------------------------------")

    generator = AdGenerator()

    # Budget/Style Constraints
    # 10 seconds of Runway Gen-3 Turbo + Flux Images = ~$1.50
    config_overrides = {
        "url": "https://botspot.trade",
        "style": ["Cinematic", "Raw", "Documentary"], # Triggers Strategist's "Arri Alexa" logic
        "mood": "Intense",
        "duration": "10s", 
        "platform": "Instagram Reels",
        # We let Strategist recommend, but we hint our preference via "style"
        # The prompt engineering we did should force Flux/Runway regardless.
    }

    user_input = """
    Create an Intense, Real-Life ad for Botspot.
    Focus on the PAIN of manual trading (exhaustion, red eyes) vs the RELIEF of automation.
    Visuals MUST look like a Netflix Documentary (Halation, Grain, Imperfect).
    NO "AI Gloss". Make it gritty.
    """

    print("\n🧠 PHASE 1: STRATEGY (Claude Opus)")
    print("   Translating 'Intense' into Technical Camera Specs...")
    plan = generator.plan(user_input, config_overrides)
    
    project_id = plan['id']
    print(f"\n✅ Plan Approved: {project_id}")
    print(f"   Strategy Core: {plan.get('strategy', {}).get('core_concept', 'N/A')}")
    print(f"   Visual Tech: {plan.get('strategy', {}).get('visual_language', 'N/A')}")

    print("\n🎥 PHASE 2: PRODUCTION (Flux + Runway + ElevenLabs)")
    print("   Generating Assets...")
    generator.resume(project_id)

    print("\n✨ FINAL RENDER COMPLETE")
    print(f"   Output: output/{project_id}/final_ad.mp4")

if __name__ == "__main__":
    generate_amazing_ad()
