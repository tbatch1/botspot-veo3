# Veo 3.1 Migration Guide

**Migration Date: October 16, 2025**

## Overview

This project has been successfully migrated from Google Veo 3.0 to Veo 3.1, with backward compatibility maintained for existing Veo 3.0 users.

## What Changed

### 1. New Model IDs

**Veo 3.1 Models (Recommended):**
- `veo-3.1-generate-preview` - Latest standard model
- `veo-3.1-fast-generate-preview` - Latest fast model

**Veo 3.0 Models (Legacy, Still Supported):**
- `veo-3.0-generate-001` - Marked as deprecated
- `veo-3.0-fast-generate-001` - Marked as deprecated

### 2. New API Parameters

Veo 3.1 introduces new optional parameters:

```typescript
interface VideoGenerationRequest {
  // Existing parameters (unchanged)
  prompt: string;
  model: string;
  aspectRatio?: '16:9' | '9:16';
  resolution?: '720p' | '1080p';
  duration?: number;

  // NEW Veo 3.1 parameters
  referenceImages?: Array<{ uri?: string; url?: string }>; // Up to 3 images
  video?: { uri?: string; url?: string }; // For video extension
  lastFrame?: { uri?: string; url?: string }; // For interpolation
}
```

### 3. Enhanced Features

**Video Extension:**
- Extend existing Veo videos by up to 7 additional seconds
- Pass the original video via the `video` parameter

**Reference Images:**
- Maintain consistent characters/styles across multiple shots
- Support up to 3 reference images per generation

**Improved Audio:**
- Native audio generation with dialogue support
- Multi-person conversation capability
- Better synchronization with visuals

**Enhanced Prompting:**
- Better understanding of cinematic techniques
- Improved narrative structure comprehension

### 4. Template Updates

All 12 templates have been upgraded with Veo 3.1 optimized prompts following the new formula:
```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

**Before (Veo 3.0):**
```
Show a trading bot executing a perfect breakout strategy during a strong
bull market rally. Display real-time charts with green candlesticks.
```

**After (Veo 3.1):**
```
Smooth camera push in on trading screen. Automated trading bot executing
perfect breakout strategy. Green candlesticks rapidly ascending through
resistance levels while bot enters positions with glowing profit indicators.
Modern tech office with blue ambient lighting. Cinematic style with
electronic trade confirmation sounds.
```

## Migration Steps for Users

### Option 1: Use New Veo 3.1 Models (Recommended)

Update your API calls to use the new model IDs:

```javascript
// Old
const response = await apiClient.generateVideo({
  prompt: "...",
  model: "veo-3.0-fast-generate-001",
  duration: 8
});

// New (recommended)
const response = await apiClient.generateVideo({
  prompt: "...",
  model: "veo-3.1-fast-generate-preview",
  duration: 8
});
```

### Option 2: Continue Using Veo 3.0 (Backward Compatible)

No changes needed! Your existing code will continue to work:

```javascript
const response = await apiClient.generateVideo({
  prompt: "...",
  model: "veo-3.0-fast-generate-001",
  duration: 8
});
```

### Option 3: Use New Veo 3.1 Features

```javascript
const response = await apiClient.generateVideo({
  prompt: "Wide angle shot of trading floor. Traders celebrating...",
  model: "veo-3.1-generate-preview",
  duration: 8,
  // NEW: Add reference images for consistent style
  referenceImages: [
    { url: "https://example.com/style-reference.jpg" }
  ]
});

// Extend an existing video
const extended = await apiClient.generateVideo({
  prompt: "Continue the celebration with fireworks...",
  model: "veo-3.1-generate-preview",
  duration: 5, // Add 5 more seconds
  // NEW: Extend existing video
  video: { url: "https://storage.googleapis.com/previous-video.mp4" }
});
```

## Prompt Optimization Guide

### Veo 3.1 Prompting Best Practices

**1. Cinematography First**
Start with camera movements and composition:
- Camera movements: dolly, tracking, crane, aerial, pan, POV
- Composition: wide shot, close-up, extreme close-up
- Lens effects: shallow depth of field, wide-angle, macro

**2. Subject & Action**
Clearly describe what's happening:
- Trading bot executing strategies
- Charts and indicators appearing
- Real-time data updates

**3. Context & Setting**
Set the scene:
- Modern tech office
- Professional trading floor
- Futuristic interface

**4. Style & Ambiance**
Add mood and audio:
- Cinematic style, dark moody atmosphere
- Electronic beats, keyboard typing sounds
- Alert beeps, trade confirmations

**Example Prompt Structure:**
```
[Camera: Slow dolly shot] + [Subject: AI trading bot] +
[Action: analyzing market indicators] + [Context: modern office setting] +
[Style: professional blue lighting with subtle confirmation sounds]
```

### Audio Direction

Veo 3.1 natively generates audio. Enhance with:

```
SFX: thunder cracks, keyboard typing, alert beeps
Ambient: electronic beats, office chatter, market noise
Dialogue: "Buy signal detected!" or "Position closed successfully!"
```

## Testing Your Migration

### 1. Test Health Endpoint

```bash
curl http://localhost:3000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Veo 3 API",
  "canGenerateVideos": true,
  "message": "Ready to generate videos"
}
```

### 2. Test Models Endpoint

```bash
curl http://localhost:3000/api/models
```

Should return 4 models (2 Veo 3.1, 2 Veo 3.0 legacy).

### 3. Generate Test Video

```bash
curl -X POST http://localhost:3000/api/videos/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Wide shot of trading screen. Bot executing trades with green profit indicators. Modern office. Electronic sounds.",
    "model": "veo-3.1-fast-generate-preview",
    "duration": 4,
    "resolution": "720p",
    "userId": "test-user"
  }'
```

## Breaking Changes

**None!** This migration is fully backward compatible.

- Veo 3.0 models continue to work
- Existing API parameters unchanged
- New parameters are optional
- Templates auto-upgrade to 3.1 but legacy supported

## Environment Variables

No new environment variables required. Existing configuration works:

```env
GEMINI_API_KEY=your_api_key_here
PORT=3000
VEO3_MOCK=false
VEO3_FORCE_FAST=false  # Now uses veo-3.1-fast-generate-preview
VEO3_MAX_COST=5.00
```

## Pricing

Pricing remains the same as Veo 3.0 (estimated):
- **Veo 3.1 Standard**: $0.40/second (~$3.20 for 8s)
- **Veo 3.1 Fast**: $0.15/second (~$1.20 for 8s)

*Note: Pricing is estimated based on Veo 3.0. Check Google's official pricing.*

## Rollback Plan

If you need to rollback to Veo 3.0 only:

1. Update default model in [veo3-service.js:165](backend/veo3-service.js#L165):
```javascript
model: params.model || 'veo-3.0-fast-generate-001',
```

2. Update templates in [templates.ts](app/data/templates.ts) back to:
```typescript
model: 'veo-3.0-generate-001'
```

## Resources

- [Veo 3.1 API Documentation](https://ai.google.dev/gemini-api/docs/video)
- [Veo 3.1 Prompting Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)
- [Google AI Studio](https://aistudio.google.com/)

## Support

For issues or questions:
1. Check the [README.md](README.md) for updated documentation
2. Review API logs in the console
3. Test with mock mode: `VEO3_MOCK=true`

---

**Migration Status**: ✅ Complete

**Last Updated**: October 16, 2025
