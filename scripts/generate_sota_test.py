
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config

def main():
    print("==============================================")
    print("   SOTA SYSTEM TEST: 'Cyberpunk Coffee'      ")
    print("==============================================")
    print(f"Goal: Verify Music, Beat Sync, and Visuals.")
    
    # Initialize Generator
    ad_gen = AdGenerator()
    
    # 1. PLAN PHASE
    # We use a prompt that demands rhythm and mood
    topic = "Neon Brew: A cyberpunk coffee brand. Dark, neon, rainy Tokyo streets. High energy visuals."
    
    print(f"\n[1] Planning: {topic}")
    ad_gen.plan(user_input=topic, config_overrides={
        "style": ["Cinematic", "Cyberpunk"],
        "mood": "High Energy",
        "image_provider": "flux", # Force Flux
        "video_model": "runway"   # Force Runway
    })
    
    plan_path = f"output/plan_{ad_gen.state.id}.json"
    print(f"[1] Plan saved to: {plan_path}")
    
    # 2. RESUME (EXECUTION) PHASE
    print("\n[2] Executing Full Production...")
    # This will trigger:
    # - Flux Image Gen
    # - ElevenLabs VO
    # - ElevenLabs BGM (NEW)
    # - Runway Video
    # - Composer with Beat Sync (NEW)
    
    try:
        ad_gen.resume()
        print("\n==============================================")
        print("   TEST COMPLETE: SUCCESS                     ")
        print("==============================================")
        print(f"Final Video: {ad_gen.state.final_video_path}")
        
    except Exception as e:
        print("\n==============================================")
        print("   TEST FAILED                               ")
        print("==============================================")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
