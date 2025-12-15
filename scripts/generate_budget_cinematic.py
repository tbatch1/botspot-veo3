import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config

def generate_budget_civilian_ad():
    print("🎬 ACTION: Generating 'Budget Cinematic' Test (Quality + Economy)")

    # 1. Initialize Generator
    generator = AdGenerator()

    # 2. Define Constraints for "Real & Cheap"
    # - Flux: Essential for "Real People" (prevents AI plastic look)
    # - Runway: Good motion
    # - Short Duration: Keeps cost down
    config_overrides = {
        "url": "https://botspot.trade",
        "style": ["Documentary", "Raw Film", "16mm"],
        "mood": "Authentic", 
        "duration": "10s", # Short but enough for a story beat
        "platform": "Instagram",
        "image_provider": "flux", # FLUX PRO IS A MUST for "Real"
        "video_model": "runway",
        "voice_vibe": "Deep, gritty, real person (not announcer)",
        
        # Override Strategy to force "Real Life" concept
        "production_recommendations": {
            "visual_engine": "flux",
            "video_engine": "runway",
            "voice_vibe": "Authentic Interview"
        }
    }

    user_input = """
    Create a 100% realistic documentary-style ad for Botspot.
    SUBJECT: A tired, real human trader at his kitchen table late at night.
    STORY: He looks exhausted, staring at a laptop. Then he closes it, smiles, and walks away to sleep.
    MESSAGE: "Stop watching charts. Let the bots take over."
    VISUALS: Grainy, handheld, low light, warm practical lamps. NO GLOSSY 3D. NO CYBERPUNK.
    It must look like a NETFLIX DOCUMENTARY.
    """

    # 3. Plan
    print("\n🧠 STEP 1: Planning w/ Strategist (Opus)...")
    plan = generator.plan(user_input, config_overrides)
    
    project_id = plan['id']
    print(f"\n✅ Plan ID: {project_id}")

    # 4. Execute (Production)
    print("\n🎥 STEP 2: Production (Flux + Runway + Cinematic Voice)...")
    generator.resume(project_id)

    print("\n✨ DONE! Video saved to output/final_ad.mp4")

if __name__ == "__main__":
    generate_budget_civilian_ad()
