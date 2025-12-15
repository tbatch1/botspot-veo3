import requests
import os

def test_upload_endpoint():
    url = "http://localhost:4000/api/upload"
    filename = "test_upload_image.png"
    file_content = b"fake image content"
    
    # Create dummy file
    with open(filename, "wb") as f:
        f.write(file_content)
        
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "image/png")}
            response = requests.post(url, files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("SUCCESS: Endpoint returned 200 OK")
            # Verify file exists in assets
            assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "user_uploads", filename)
            # Fix path resolution if needed - assuming script runs from tests/ or root
            # Let's check common locations
            if not os.path.exists(assets_path):
                 # Try relative to CWD
                 assets_path = os.path.abspath(os.path.join("assets", "user_uploads", filename))
            
            if os.path.exists(assets_path):
                print(f"SUCCESS: File saved to {assets_path}")
            else:
                print(f"FAILURE: File not found at {assets_path}")
        else:
            print("FAILURE: Endpoint returned non-200 status")
            
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_upload_endpoint()
