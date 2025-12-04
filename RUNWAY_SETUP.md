# Runway Gen-3 Setup Guide

## Quick Setup (5 Minutes)

### 1. Sign Up for Runway API
Go to: https://dev.runwayml.com/

- Click "Sign Up" or "Get Started"
- Create account with email
- Verify email

### 2. Create Organization
After signing in:
- Click "Create Organization" when prompted
- Enter organization name (e.g., "My Company")
- Your API key will be displayed

### 3. Copy API Key
- Copy the API key shown (format: `rw_...`)
- Keep it secure - you won't see it again!

### 4. Add to Environment
Edit `.env` file in project root:
```bash
RUNWAY_API_KEY=rw_your_key_here_abc123...
```

### 5. Restart Backend
```bash
# Kill existing backend
# Then restart:
python start_ott.py
```

### 6. Test Generation
- Go to http://localhost:4000/ott
- Create a plan
- Click "Start Production"
- Videos will generate with Runway!

## Pricing

**Free Tier:**
- 125 one-time credits
- ~25 seconds of video

**Standard Plan:** $12/month
- 625 monthly credits
- ~125 seconds of video with Gen-3 Turbo

**Pro Plan:** $28/month
- 2,250 monthly credits
- ~450 seconds of video

**Unlimited Plan:** $76-95/month
- Unlimited Gen-3 Turbo & Gen-4 generations
- Relaxed rate (slower queue)

## Cost Calculator

**Current Config:** 2 scenes × 4 seconds = 8 seconds

**Cost per test:**
- Gen-3 Turbo: ~5 credits/second × 8s = **40 credits** (~$0.40)
- Gen-4: ~12 credits/second × 8s = **96 credits** (~$0.96)

**Free tier gives you:** 125 ÷ 40 = **3 free test videos!**

## How It Works

When you have `RUNWAY_API_KEY` configured:
1. Backend detects Runway is available
2. Uses Runway for video generation instead of Veo
3. Imagen 4 still generates images (free)
4. Runway animates those images into videos
5. Composer assembles final video

## Switching Between Veo and Runway

**Use Veo (Free):**
- Remove or comment out `RUNWAY_API_KEY` in `.env`
- Requires Veo quota approval
- Free within quota limits

**Use Runway (Paid but Immediate):**
- Add `RUNWAY_API_KEY` to `.env`
- Works immediately
- Costs $0.40-$0.96 per 8-second test

## Support

- API Docs: https://docs.dev.runwayml.com/
- Pricing: https://docs.dev.runwayml.com/guides/pricing/
- Support: https://runwayml.com/contact

## Status

**Current:**
- ✅ Imagen 4 working (images)
- ✅ Veo 3.1 code fixed (async polling implemented)
- ⏳ Veo quota: Need approval or testing async flow
- ⏳ Runway: Need API key

**Recommendation:**
Get Runway key NOW for immediate testing while Veo async completes.
