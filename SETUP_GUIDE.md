# Complete Setup Guide for Botspot Veo3 OTT Ad Builder

## Quick Links to Get Your API Keys

### 1. Google Cloud / Vertex AI (For Imagen 3 & Veo)
- **Create Account**: https://console.cloud.google.com/
- **Enable Vertex AI API**: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- **Create Service Account**: https://console.cloud.google.com/iam-admin/serviceaccounts
- **Documentation**: https://cloud.google.com/vertex-ai/docs/authentication

### 2. Runway ML API (For Gen-3 Video)
- **Sign Up**: https://dev.runwayml.com/
- **Get API Key**: https://app.runwayml.com/settings (Organization Settings > API Keys)
- **Documentation**: https://docs.dev.runwayml.com/
- **Pricing**: Separate from web app credits

### 3. ElevenLabs API (For Voice & SFX)
- **Sign Up**: https://elevenlabs.io/
- **Get API Key**: https://elevenlabs.io/app/settings (Developers > API Keys)
- **Documentation**: https://elevenlabs.io/docs/quickstart
- **Free Tier**: Includes API access

### 4. Google Gemini AI (Already Working!)
- **API Key Page**: https://aistudio.google.com/app/apikey
- **Your Current Key**: AIzaSyD5E8Ehrp_nhLA9_33yW3uEawMBZpJG-1U (WORKING)
- **Documentation**: https://ai.google.dev/gemini-api/docs

---

## Step-by-Step Setup Instructions

### Part 1: Google Cloud Setup for Imagen 3 & Veo

#### Option A: Simple API Key (Gemini API) - RECOMMENDED FOR QUICK START
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Select your project or create new one
4. Enable billing on your Google Cloud project
5. Copy the API key

#### Option B: Service Account (Vertex AI) - FOR PRODUCTION
1. **Create Google Cloud Project**:
   - Go to https://console.cloud.google.com/
   - Create new project or select existing one
   - Enable billing

2. **Enable Required APIs**:
   - Vertex AI API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
   - Click "ENABLE"

3. **Create Service Account**:
   - Go to https://console.cloud.google.com/iam-admin/serviceaccounts
   - Click "CREATE SERVICE ACCOUNT"
   - Name: `botspot-veo3-service`
   - Grant these roles:
     - Vertex AI User
     - Service Usage Admin
     - Storage Object Admin (if using Cloud Storage)

4. **Download Service Account Key**:
   - Click on the service account you created
   - Go to "KEYS" tab
   - Click "ADD KEY" > "Create new key"
   - Choose JSON format
   - Save file as `service-account.json` in project root

5. **Set Environment Variable**:
   ```bash
   # Windows (PowerShell)
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\tommy\Desktop\botspot-veo3\service-account.json"

   # Windows (CMD)
   set GOOGLE_APPLICATION_CREDENTIALS=C:\Users\tommy\Desktop\botspot-veo3\service-account.json

   # Or add to .env file
   GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
   ```

### Part 2: Runway ML Setup

1. **Sign Up**:
   - Go to https://dev.runwayml.com/
   - Create account and organization

2. **Get API Key**:
   - Go to Organization Settings > API Keys
   - Click "Create API Key"
   - Copy immediately (won't be shown again!)

3. **Add to .env**:
   ```env
   RUNWAY_API_KEY=your_runway_key_here
   ```

4. **Important**: API credits are separate from web app credits

### Part 3: ElevenLabs Setup

1. **Sign Up**:
   - Go to https://elevenlabs.io/
   - Create free account

2. **Get API Key**:
   - Click "Developers" in sidebar
   - Go to "API Keys" tab
   - Click "Create API Key"
   - Copy the key

3. **Add to .env**:
   ```env
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ```

---

## Environment Configuration

### Create `.env` file in root directory:

```env
# Google Cloud (Choose ONE method)

## Method A: Simple API Key (for Gemini AI SDK)
GEMINI_API_KEY=AIzaSyD5E8Ehrp_nhLA9_33yW3uEawMBZpJG-1U

## Method B: Service Account (for Vertex AI)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_CLOUD_PROJECT=botspot-veo3

# Video Generation
RUNWAY_API_KEY=your_runway_api_key_here

# Voice & Audio
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional Settings
VIDEO_MODEL=runway  # or "veo"
STYLE_PRESET=Cinematic
```

---

## Installation & Testing

### Install Python Dependencies:
```bash
pip install google-auth google-cloud-aiplatform google-generativeai requests pydantic python-dotenv elevenlabs runwayml
```

### Test Google Cloud Auth:
```bash
# Test if credentials work
python -c "import google.auth; creds, project = google.auth.default(); print(f'Authenticated as: {project}')"
```

### Test the Pipeline:
```bash
# Generate a plan
python main.py "A modern cryptocurrency trading platform" --plan

# Execute full pipeline
python main.py --resume
```

---

## Current Status

| Service | Status | Notes |
|---------|--------|-------|
| Google Gemini API | ✅ WORKING | Simple video generation tested |
| Backend API | ✅ RUNNING | Port 4000 |
| Frontend | ✅ RUNNING | Port 3000 |
| Imagen 3 | ⚠️ NEEDS SETUP | Requires Vertex AI or service account |
| Google Veo (Vertex AI) | ⚠️ NEEDS SETUP | Requires service account |
| Runway ML | ⚠️ NEEDS API KEY | Get from dev.runwayml.com |
| ElevenLabs | ⚠️ NEEDS API KEY | Get from elevenlabs.io |

---

## Troubleshooting

### "Default credentials not found"
- Install gcloud CLI: https://cloud.google.com/sdk/docs/install
- Run: `gcloud auth application-default login`
- Or set GOOGLE_APPLICATION_CREDENTIALS

### "API not enabled"
- Enable Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- Enable billing on your project

### "Invalid API key"
- Regenerate key from respective service
- Check for extra spaces in .env file
- Ensure billing is enabled

---

## Cost Estimates (2025 Pricing)

| Service | Cost |
|---------|------|
| Imagen 3 | $0.03 per image |
| Google Veo | $0.15/sec (fast) - $0.40/sec (standard) |
| Runway Gen-3 | Variable (check dev.runwayml.com) |
| ElevenLabs | Free tier available, then paid |
| Gemini API | Varies by model |

---

## Next Steps

1. Get API keys from the links above
2. Add them to your `.env` file
3. For Vertex AI: Download service account JSON
4. Run: `pip install -r requirements.txt` (if exists)
5. Test with: `python main.py "test prompt" --plan`

## Support Resources

- **Google Cloud**: https://cloud.google.com/vertex-ai/docs
- **Runway ML**: https://docs.dev.runwayml.com/
- **ElevenLabs**: https://elevenlabs.io/docs
- **Gemini API**: https://ai.google.dev/gemini-api/docs
