import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator

def generate_botspot_plan():
    generator = AdGenerator()
    
    topic = "Botspot.trade - AI Trading Agents"
    
    # "Premium Cinematic" Config (User Request)
    config = {
        "url": "https://botspot.trade",
        "duration": "15s", 
        "style": ["Cinematic", "3D Render", "Surreal"], # "Amazing creative", "tell a story"
        "mood": "Premium, Aspirational, Mysterious",
        "platform": "Netflix", 
        "camera_style": "Steadicam",
        "video_model": "runway", # Use Gen-3 Alpha for visual quality
        # Strategy Injection for Narrative
        "character_concept": "Metaphorical: A lone trader navigating a chaotic storm, then finding calm precision with Botspot."
    }
    
    print("🧠 Launching Strategist (Claude Opus 4.5)...")
    result = generator.plan(topic, config)
    
    print("\n📜 STRATEGY GENERATED:")
    # Attempt to print strategy if available (it might be hidden in state)
    # The result of generator.plan() is state.model_dump()
    # We can inspect the script lines and scenes.
    
    script = result["script"]
    if hasattr(script, "dict"):
        script = script.dict()
        
    print(f"MOOD: {script.get('mood')}")
    
    print("\n🎬 SCENES:")
    for scene in script["scenes"]:
        print(f"--- Scene {scene['id']} ({scene['duration']}s) ---")
        print(f"VISUAL: {scene['visual_prompt']}")
        print(f"AUDIO: {scene['audio_prompt']}")
        print(f"MOTION: {scene['motion_prompt']}")
        
    print("\n🗣️ VOICEOVER:")
    for line in script["lines"]:
        print(f"[{line['time_range']}] {line['speaker']}: {line['text']}")

    print(f"\n🎬 STARTING PRODUCTION (Runway Gen-3 Turbo + ElevenLabs)...")
    try:
        generator.resume(result["id"])
        print("\n✅ PRODUCTION COMPLETE!")
    except Exception as e:
        print(f"\n❌ PRODUCTION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_botspot_plan()
