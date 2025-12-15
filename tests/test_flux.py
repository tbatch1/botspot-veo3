import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.providers.flux import FluxProvider
from ott_ad_builder.config import config

def test_flux_generation():
    print("🚀 Starting Flux Pro 1.1 Integration Test...")
    
    # Initialize Provider
    try:
        flux = FluxProvider()
        print("✅ FluxProvider initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize FluxProvider: {e}")
        return

    # Test Prompt
    prompt = "Raw photo, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3, a futuristic electric car driving through a neon-lit forest at night, wet pavement reflections, realistic texture"
    print(f"🎨 Generating image with prompt: '{prompt}'...")
    
    try:
        image_path = flux.generate_image(prompt)
        
        if os.path.exists(image_path):
            print(f"✅ SUCCESS: Image generated at {image_path}")
            print(f"📁 Size: {os.path.getsize(image_path) / 1024:.2f} KB")
        else:
            print(f"❌ ERROR: File reported as generated but not found at {image_path}")
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flux_generation()
