#!/usr/bin/env python
"""
Start the OTT Ad Builder FastAPI backend server.
This serves the API on port 8000 for the frontend_new UI.
"""

import uvicorn
import sys
import os

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("Starting OTT Ad Builder API Server")
    print("=" * 60)
    print("API will be available at: http://localhost:8000")
    print("API docs will be at: http://localhost:8000/docs")
    print("Using GEMINI_API_KEY from .env file")
    print("Mock providers enabled for Imagen, Runway, ElevenLabs")
    print("=" * 60)
    print()

    # Import here to show any config errors early
    try:
        from ott_ad_builder.api import app
        print("OTT Ad Builder API loaded successfully")
        print()
    except Exception as e:
        print(f"Failed to load API: {e}")
        print()
        print("Make sure:")
        print("1. GEMINI_API_KEY is set in your .env file")
        print("2. All dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)

    # Start the server
    uvicorn.run(
        "ott_ad_builder.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
