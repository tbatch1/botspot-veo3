import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.providers.strategist import StrategistProvider

def test_cheap_brain_run():
    print("🧠 STARTING CHEAP BRAIN TEST (Text Only)...")
    
    # Initialize basic provider
    strategist = StrategistProvider()
    
    # Mock inputs - what a user would type in the UI
    test_cases = [
        {
            "topic": "A local coffee shop called 'Bean There'",
            "constraints": {"mood": "Authentic", "style": "Cinematic"}
        },
        {
            "topic": "A futuristic crypto trading bot high tech",
            "constraints": {"mood": "Cyberpunk", "style": "High Tech"}
        }
    ]

    for i, test in enumerate(test_cases):
        print(f"\n🧪 TEST CASE {i+1}: {test['topic']}")
        print(f"   Constraints: {test['constraints']}")
        
        # Run the "Thinking" process
        strategy = strategist.develop_strategy(test['topic'], "", test['constraints'])
        
        # Analyze the output (The "Audit")
        visual_style = strategy.get('visual_language', '')
        direction = strategy.get('cinematic_direction', {})
        
        print("\n   🧐 AUDIT RESULTS:")
        print(f"   > Visual Language: {visual_style}")
        print(f"   > Lighting Notes: {direction.get('lighting_notes')}")
        
        # CHECK 1: Did it use Technical Terms?
        tech_terms = ["Arri", "Alexa", "Grain", "Noise", "Halation", "Aberration", "16mm", "35mm", "Anamorphic"]
        found_terms = [t for t in tech_terms if t.lower() in str(strategy).lower()]
        
        if found_terms:
            print(f"   ✅ PASS: Found Technical Terms: {found_terms}")
        else:
            print("   ❌ FAIL: No technical camera terms found. Still sounds generic?")

        # CHECK 2: Did it use Banned Words?
        banned_words = ["Masterpiece", "Hyper-realistic", "8k", "HDR", "Trending on ArtStation"]
        found_banned = [b for b in banned_words if b.lower() in str(strategy).lower()]
        
        if found_banned:
            print(f"   ❌ FAIL: Found Banned 'AI Slop' Words: {found_banned}")
        else:
            print("   ✅ PASS: Clean of 'AI Slop' keywords.")
            
    print("\n💰 TOTAL COST: ~$0.02 (Text Tokens Only)")

if __name__ == "__main__":
    test_cheap_brain_run()
