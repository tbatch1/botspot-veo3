# 🚀 Quick Start Guide - Botspot Veo3

## ✅ What's Already Working

Your project is **LIVE and READY TO USE** right now!

- **Backend API**: Running on http://localhost:4000
- **Frontend**: Running on http://localhost:3000
- **Google Veo 3**: WORKING - Generated real video successfully!
- **API Key**: Valid and tested

### Use Right Now:
1. Open http://localhost:3000 in your browser
2. Go to the "Studio" tab
3. Write a prompt or select a template
4. Click "Generate Video"
5. Wait 40-60 seconds
6. Your video appears!

---

## 🎯 To Enable Advanced Pipeline (Imagen 3, Multi-Scene Ads)

You need 3 more API keys. Here's exactly where to get them:

###1️⃣ Runway ML (Optional - For Gen-3 video alternative)
1. Go to: **https://dev.runwayml.com/**
2. Sign up for account
3. Create organization
4. Go to Settings → API Keys
5. Click "Create API Key"
6. Copy and paste into `.env` file:
   ```
   RUNWAY_API_KEY=your_key_here
   ```

### 2️⃣ ElevenLabs (For Voice & Sound FX)
1. Go to: **https://elevenlabs.io/**
2. Sign up (free plan works!)
3. Click "Developers" in sidebar
4. Go to "API Keys" tab
5. Click "Create API Key"
6. Copy and paste into `.env` file:
   ```
   ELEVENLABS_API_KEY=your_key_here
   ```

### 3️⃣ Google Cloud Service Account (For Imagen 3 & Vertex AI)
1. Go to: **https://console.cloud.google.com/**
2. Create or select project
3. Enable Vertex AI: **https://console.cloud.google.com/apis/library/aiplatform.googleapis.com**
4. Go to: **https://console.cloud.google.com/iam-admin/serviceaccounts**
5. Click "CREATE SERVICE ACCOUNT"
6. Name it: `botspot-veo3-service`
7. Grant roles:
   - Vertex AI User
   - Service Usage Admin
8. Click on the service account → KEYS tab
9. ADD KEY → Create new key → JSON
10. Save file as `service-account.json` in this folder
11. Update `.env` file:
    ```
    GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
    GOOGLE_CLOUD_PROJECT=your-project-id
    ```

---

## 🧪 Test the Advanced Pipeline

Once you have the keys set up:

```bash
# Test 1: Generate a plan
python main.py "A high-tech trading platform ad" --plan

# Test 2: Execute full pipeline
python main.py --resume
```

This will:
- Generate images with Imagen 3
- Add voiceover with ElevenLabs
- Create video with Veo or Runway
- Combine everything into final ad

---

## 📚 Full Documentation

- **API Links**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Pricing Info**: Included in setup guide
- **Troubleshooting**: Check setup guide

---

## 💡 Quick Tips

**Don't want to set up all keys?**
- Current system works great for simple text-to-video
- Advanced pipeline is optional for complex multi-scene ads

**Want to test without spending money?**
- Mock mode works for development
- Most services have free tiers
- Google Veo Fast model is cheapest ($1.20 per 8s video)

**Need help?**
- Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- All links are clickable and ready to use

---

## 🎉 You're All Set!

The system is working. Add the 3 API keys above whenever you're ready to unlock the full pipeline.

**Current Status:**
- ✅ Simple Video Generation: WORKING
- ⏳ Advanced Multi-Scene Pipeline: Waiting for API keys
- ✅ Backend: Running
- ✅ Frontend: Running
