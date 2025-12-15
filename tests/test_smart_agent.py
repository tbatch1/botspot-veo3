import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config

def test_smart_agent_flow():
    print("🚀 Starting Smart Agent Integration Test...")
    
    # Initialize Generator
    generator = AdGenerator()
    
    # Test Inputs
    topic = "Rivian R2"
    url = "https://rivian.com/r2" # Real URL, but Researcher might just get basic text
    config_overrides = {
        "mood": "Cyberpunk",
        "camera_style": "Drone",
        "lighting_preference": "Neon",
        "url": url
    }
    
    print(f"📋 Input Topic: {topic}")
    print(f"🔗 Input URL: {url}")
    print(f"⚙️ Config: {config_overrides}")
    print(f"🧠 Strategist Model: {config.STRATEGIST_MODEL}")
    
    # Run the Plan Phase
    # This triggers: Researcher -> Strategist (Claude) -> Gemini
    try:
        result = generator.plan(topic, config_overrides)
        
        # Verify Strategy was used (indirectly via logs, but we can check the script content)
        script = result.get("script", {})
        scenes = script.get("scenes", [])
        
        print("\n✅ Plan Generated Successfully!")
        print(f"📜 Script contains {len(scenes)} scenes.")
        
        # Check for evidence of the strategy in the generated scenes
        # (e.g., if we asked for Cyberpunk, do we see neon/tech keywords?)
        cyberpunk_keywords = ["neon", "cyber", "tech", "digital", "futuristic", "blue", "pink"]
        found_keywords = []
        
        print("\n🔍 Analyzing Scenes for Strategic Alignment (Cyberpunk)...")
        for scene in scenes:
            visual = scene.get("visual_prompt", "").lower()
            for kw in cyberpunk_keywords:
                if kw in visual:
                    found_keywords.append(kw)
                    
        if found_keywords:
            print(f"✅ SUCCESS: Found strategic keywords in script: {list(set(found_keywords))}")
        else:
            print("⚠️ WARNING: Script generated, but specific strategic keywords were not explicitly found. Check logs for Strategist output.")
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smart_agent_flow()
