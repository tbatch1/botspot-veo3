import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from ott_ad_builder.providers.video_google import GoogleVideoProvider

def main():
    print("[START] Starting Google Veo Test Generation...")
    
    try:
        provider = GoogleVideoProvider()
        
        prompt = "A cinematic drone shot of a futuristic city at sunset, 4k, highly detailed"
        print(f"[INFO] Generating video for prompt: '{prompt}'")
        
        # Generate video
        video_path = provider.generate_video(prompt)
        
        print(f"[SUCCESS] Video generated successfully!")
        print(f"[INFO] Saved to: {video_path}")
        
    except Exception as e:
        print(f"[ERROR] Error generating video: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
