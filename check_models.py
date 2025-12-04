import os
import sys
# from google.cloud import aiplatform # Not installed/configured in this env properly maybe

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def list_models():
    print("🔍 Checking available Vertex AI models...")
    
    try:
        print("\nChecking specific Veo availability...")
        # We'll try to instantiate the model class which usually validates existence
        from ott_ad_builder.providers.video_google import GoogleVideoProvider
        provider = GoogleVideoProvider()
        print(f"✅ Provider initialized for model: {provider.api_endpoint}")
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_models()
