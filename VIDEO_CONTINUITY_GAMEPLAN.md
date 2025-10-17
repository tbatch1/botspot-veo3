# Video Continuity Feature - Game Plan

## 🎯 Project Goal

Build a professional video sequencer that allows users to create **long-form videos** (30s - 2+ minutes) by chaining multiple Veo 3.1 clips with seamless transitions using:
- **First/Last Frame continuity** (Veo 3.1 feature)
- **Video Extension** (extend clips by 7s)
- **Automated scene planning** with AI-assisted prompts
- **Timeline-based editing interface**

---

## 📊 Feature Overview

### What Users Can Do:
1. **Create a Story Arc** - Plan a multi-scene trading bot advertisement
2. **Auto-Generate Sequences** - AI generates prompts for each scene with continuity
3. **Visual Timeline** - Drag-and-drop scenes, preview, reorder
4. **Seamless Transitions** - Veo 3.1 uses last frame of clip N as first frame of clip N+1
5. **Batch Generation** - Generate all clips in sequence automatically
6. **Final Export** - Combine all clips into one downloadable video

### Example Use Case:
```
Scene 1 (8s): "Wide shot of modern trading office, bot powering on..."
Scene 2 (8s): "Camera pushes in, charts appearing, bot analyzing..."
Scene 3 (8s): "Bot executes first trade, green indicators flashing..."
Scene 4 (8s): "Profits accumulating, celebration moment..."
Final: 32-second professional trading bot ad!
```

---

## 🏗️ Technical Architecture

### 1. Backend Components

#### A. Video Sequence Model (MongoDB)
```javascript
{
  _id: ObjectId,
  userId: String,
  title: String, // "Trading Bot Launch Ad"
  description: String,
  totalDuration: Number, // 32
  scenes: [
    {
      sceneNumber: 1,
      prompt: String,
      duration: 8,
      model: 'veo-3.1-generate-preview',
      status: 'completed' | 'generating' | 'pending' | 'failed',
      videoUrl: String,
      lastFrameUrl: String, // Extracted for next scene
      metadata: {
        generatedAt: Date,
        cost: Number
      }
    }
  ],
  status: 'draft' | 'generating' | 'completed' | 'failed',
  finalVideoUrl: String, // Combined video
  createdAt: Date,
  updatedAt: Date
}
```

#### B. New API Endpoints

**Sequence Management:**
```
POST   /api/sequences/create          - Create new sequence
GET    /api/sequences/:id             - Get sequence details
PUT    /api/sequences/:id             - Update sequence
DELETE /api/sequences/:id             - Delete sequence
GET    /api/sequences                 - List user sequences
```

**Scene Operations:**
```
POST   /api/sequences/:id/scenes      - Add scene
PUT    /api/sequences/:id/scenes/:num - Update scene
DELETE /api/sequences/:id/scenes/:num - Remove scene
POST   /api/sequences/:id/reorder     - Reorder scenes
```

**Generation & Export:**
```
POST   /api/sequences/:id/generate    - Generate all scenes
POST   /api/sequences/:id/scenes/:num/generate - Generate single scene
GET    /api/sequences/:id/status      - Get generation progress
POST   /api/sequences/:id/export      - Combine & export final video
```

**AI Assistance:**
```
POST   /api/sequences/suggest-scenes  - AI generates scene breakdown
POST   /api/sequences/optimize-continuity - AI improves transitions
```

#### C. Video Processing Service
```javascript
class VideoSequenceService {
  // Extract last frame from video for continuity
  async extractLastFrame(videoUrl) { }

  // Generate scene with continuity from previous
  async generateSceneWithContinuity(scene, previousScene) { }

  // Combine all scenes into final video
  async combineScenes(scenes) { }

  // AI-powered scene suggestion
  async suggestScenes(concept, duration, sceneCount) { }
}
```

---

### 2. Frontend Components

#### A. Video Sequencer UI (New Main Component)

**Location:** `app/components/VideoSequencer/index.tsx`

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  Video Sequencer - "Trading Bot Launch Ad"            │
├────────────────────────────────────────────────────────┤
│  [Timeline View - Horizontal Scrollable]              │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  [+ Add Scene]  │
│  │ Sc1 │→│ Sc2 │→│ Sc3 │→│ Sc4 │                    │
│  │ 8s  │  │ 8s  │  │ 8s  │  │ 8s  │   Total: 32s    │
│  └─────┘  └─────┘  └─────┘  └─────┘                  │
├────────────────────────────────────────────────────────┤
│  [Scene Details Panel - Selected Scene]               │
│  Scene 2: "Camera pushes in..."                       │
│  Prompt: [textarea]                                    │
│  Duration: [8s] Model: [Veo 3.1]                      │
│  Continuity: ✓ Using last frame from Scene 1         │
│  [Generate Scene] [Delete]                            │
├────────────────────────────────────────────────────────┤
│  [Preview Player]                                      │
│  ┌──────────────────────────────────┐                 │
│  │  [Video Preview or Thumbnail]    │                 │
│  │                                  │                 │
│  └──────────────────────────────────┘                 │
│  [◀ Prev] [▶ Play All] [Next ▶]                       │
├────────────────────────────────────────────────────────┤
│  [Action Bar]                                          │
│  [📋 AI Story Assistant] [⚡ Generate All]             │
│  [💾 Save Draft] [📥 Export Final Video]              │
└────────────────────────────────────────────────────────┘
```

#### B. Component Structure

**Main Components:**
```
app/components/VideoSequencer/
  ├── index.tsx                 - Main container
  ├── Timeline.tsx              - Horizontal timeline with drag/drop
  ├── SceneCard.tsx             - Individual scene in timeline
  ├── SceneEditor.tsx           - Edit scene details
  ├── PreviewPlayer.tsx         - Video preview with navigation
  ├── AIStoryAssistant.tsx      - AI-powered scene suggestions
  ├── ExportPanel.tsx           - Final video export
  └── ProgressTracker.tsx       - Generation progress
```

**UI Components (Extend existing):**
```
app/components/ui/
  ├── timeline.tsx              - NEW: Timeline component
  ├── draggable-card.tsx        - NEW: Draggable scene cards
  ├── progress-multi.tsx        - NEW: Multi-step progress
  └── video-player.tsx          - NEW: Enhanced video player
```

---

### 3. User Workflows

#### Workflow 1: AI-Assisted Story Creation
```
1. User clicks "Create Video Sequence"
2. Fills form:
   - Video concept: "Trading bot launch ad"
   - Total duration: 32s
   - Tone: "Exciting, professional, tech-focused"
3. Clicks "Generate Story"
4. AI suggests 4 scenes with prompts following Veo 3.1 formula
5. User reviews, edits prompts if needed
6. Clicks "Generate All Scenes"
7. System generates scenes sequentially with continuity
8. User previews full sequence
9. Clicks "Export Final Video"
10. Downloads combined 32s video
```

#### Workflow 2: Manual Scene Building
```
1. User clicks "Create Video Sequence"
2. Clicks "+ Add Scene" manually
3. Writes custom prompt for Scene 1
4. Clicks "Generate Scene 1"
5. Once complete, adds Scene 2
6. System auto-enables "Use continuity from Scene 1"
7. User writes Scene 2 prompt
8. Generates Scene 2 (uses Scene 1's last frame)
9. Repeats for more scenes
10. Exports final video
```

---

## 🎨 UI/UX Design Details

### Timeline Component
- **Horizontal scrollable** timeline
- **Drag-and-drop** to reorder scenes
- **Color-coded status**:
  - Gray: Pending
  - Blue: Generating (with spinner)
  - Green: Completed
  - Red: Failed
- **Duration labels** on each scene
- **Thumbnail preview** in timeline cards
- **Transition indicators** (→ arrows between scenes)

### Scene Card (Timeline Item)
```
┌─────────────────┐
│  Scene 3        │
│ [Thumbnail]     │
│ ⏱ 8s          │
│ ✓ Completed     │
│ → Continuity    │
└─────────────────┘
```

### AI Story Assistant Modal
```
┌────────────────────────────────────────┐
│  🤖 AI Story Assistant                 │
├────────────────────────────────────────┤
│  What's your video about?              │
│  [Trading bot demonstrating strategy] │
│                                        │
│  Total duration: [32s] ▼               │
│  Number of scenes: [4] ▼               │
│  Tone: [Professional] ▼                │
│                                        │
│  [Generate Scene Breakdown]            │
├────────────────────────────────────────┤
│  Suggested Scenes:                     │
│  ✓ Scene 1 (8s): Wide shot intro...   │
│  ✓ Scene 2 (8s): Camera push in...    │
│  ✓ Scene 3 (8s): Bot executing...     │
│  ✓ Scene 4 (8s): Celebration...       │
│                                        │
│  [Edit] [Accept & Create Sequence]    │
└────────────────────────────────────────┘
```

---

## 🔧 Implementation Plan

### Phase 1: Backend Foundation (Days 1-2)
- [ ] Create VideoSequence MongoDB model
- [ ] Build sequence CRUD API endpoints
- [ ] Implement scene management endpoints
- [ ] Add last frame extraction logic
- [ ] Build continuity-aware generation

### Phase 2: Frontend Structure (Days 3-4)
- [ ] Create VideoSequencer main component
- [ ] Build Timeline component with drag/drop
- [ ] Create SceneCard component
- [ ] Implement SceneEditor panel
- [ ] Add PreviewPlayer component

### Phase 3: AI Integration (Day 5)
- [ ] Build AI story suggestion endpoint
- [ ] Create AIStoryAssistant UI component
- [ ] Implement prompt optimization for continuity
- [ ] Add automatic scene transition suggestions

### Phase 4: Video Processing (Days 6-7)
- [ ] Implement sequential generation with continuity
- [ ] Add batch generation with progress tracking
- [ ] Build video combination/export logic
- [ ] Add download functionality

### Phase 5: Polish & Testing (Days 8-9)
- [ ] Add animations and transitions
- [ ] Implement error handling
- [ ] Create loading states
- [ ] Add keyboard shortcuts
- [ ] Write comprehensive tests

### Phase 6: Documentation (Day 10)
- [ ] User guide for video sequences
- [ ] API documentation
- [ ] Video tutorials/examples
- [ ] Best practices guide

---

## 📐 Technical Specifications

### Veo 3.1 Continuity Implementation

**Scene Generation with Continuity:**
```javascript
// Generate Scene 2 using Scene 1's last frame
const scene2Request = {
  prompt: scene2.prompt,
  model: 'veo-3.1-generate-preview',
  duration: 8,
  lastFrame: {
    url: scene1.lastFrameUrl // Extracted from Scene 1 video
  },
  // Veo 3.1 automatically ensures smooth transition
};
```

**Last Frame Extraction:**
```javascript
// Backend extracts last frame as image
async function extractLastFrame(videoUrl) {
  // Use ffmpeg or similar to extract final frame
  // Upload to storage
  // Return image URL for next scene
  return lastFrameImageUrl;
}
```

### Video Combination Options

**Option A: Client-side (Web-based)**
- Use ffmpeg.wasm in browser
- Combine videos client-side
- Pro: No server load
- Con: Slower, browser limitations

**Option B: Server-side (Recommended)**
- Use ffmpeg on backend
- Combine videos server-side
- Pro: Fast, reliable
- Con: Server processing required

**Option C: Cloud Service**
- Use Cloudinary/AWS MediaConvert
- Pro: Scalable, professional
- Con: Additional cost

---

## 🎬 Continuity Strategy (Veo 3.1 Features Used)

### 1. Last Frame → First Frame
- Extract last frame of Scene N
- Pass as `lastFrame` to Scene N+1
- Veo 3.1 generates Scene N+1 starting from that frame
- Result: Seamless visual transition

### 2. Prompt Continuity
- AI ensures prompts connect logically
- Example:
  - Scene 1: "...bot interface glowing blue"
  - Scene 2: "Blue glowing interface, camera pushing in..."
  - Maintains visual consistency

### 3. Style Consistency
- Use reference images across all scenes
- Same office setting, same bot design
- Veo 3.1's reference images feature ensures consistency

---

## 💰 Pricing Considerations

**Cost Example (32s video, 4 scenes x 8s):**
- Veo 3.1 Fast: 4 × $1.20 = **$4.80**
- Veo 3.1 Standard: 4 × $3.20 = **$12.80**

**Features to Add:**
- Cost calculator showing total sequence cost
- Budget warnings if exceeding limits
- Option to use Fast model for some scenes

---

## 🚀 Future Enhancements (Post-MVP)

1. **Scene Templates Library** - Pre-made sequences for common scenarios
2. **Audio Track** - Add background music/voiceover
3. **Text Overlays** - Add titles, captions, CTAs
4. **Branching Sequences** - Multiple video variations
5. **Collaboration** - Share sequences with team
6. **Version History** - Save different edits
7. **Analytics** - Track which sequences perform best

---

## 📊 Success Metrics

- Users can create 30s+ videos in < 15 minutes
- 90%+ continuity quality (smooth transitions)
- Cost per sequence < $15 on average
- User satisfaction > 4.5/5 stars
- Export success rate > 95%

---

## 🎯 MVP Feature Checklist

### Must Have (MVP):
- ✅ Create sequence with 2-8 scenes
- ✅ Manual scene creation and editing
- ✅ Timeline visualization
- ✅ Sequential generation with continuity
- ✅ Preview individual scenes
- ✅ Export combined video
- ✅ Cost calculator for sequence

### Nice to Have (v1.1):
- 🔄 AI story assistant
- 🔄 Drag-and-drop reordering
- 🔄 Reference images for style consistency
- 🔄 Batch generation progress tracking
- 🔄 Save draft sequences

### Future (v2.0+):
- 🔮 Audio integration
- 🔮 Text overlays
- 🔮 Scene templates library
- 🔮 Collaboration features

---

## 🎨 Visual Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│  🎬 Video Sequencer                          [Save] [Export]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Timeline (32s total)                                           │
│  ┌──────┐ → ┌──────┐ → ┌──────┐ → ┌──────┐    [+ Add Scene]  │
│  │ Sc 1 │   │ Sc 2 │   │ Sc 3 │   │ Sc 4 │                    │
│  │  8s  │   │  8s  │   │  8s  │   │  8s  │    Cost: $4.80    │
│  │  ✓   │   │  ⏳  │   │  📋  │   │  📋  │                    │
│  └──────┘   └──────┘   └──────┘   └──────┘                    │
│     ↑ Currently Editing Scene 2                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Scene 2 Editor                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Prompt:                                                │    │
│  │ Camera push in on glowing blue interface. Trading     │    │
│  │ bot analyzing real-time market data. Charts and       │    │
│  │ indicators appearing. Modern tech aesthetic.           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Duration: [8s ▼]  Model: [Veo 3.1 Fast ▼]                     │
│  ☑ Use continuity from Scene 1                                 │
│  [🎨 Add Reference Images]                                      │
│                                                                  │
│  [Generate This Scene]  [Delete Scene]                         │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Preview                                                        │
│  ┌──────────────────────────────────────┐                      │
│  │                                      │                      │
│  │      [Video Preview Area]            │                      │
│  │                                      │                      │
│  └──────────────────────────────────────┘                      │
│  [◀ Prev] [▶ Play Current] [Next ▶] [▶▶ Play All]             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Ready for Approval?

This game plan provides:
1. ✅ Clear technical architecture
2. ✅ Detailed UI/UX design
3. ✅ Implementation timeline
4. ✅ Veo 3.1 continuity integration
5. ✅ MVP scope and future roadmap
6. ✅ Cost considerations
7. ✅ User workflows

**Next Steps After Approval:**
1. Start with Phase 1 (Backend Foundation)
2. Build MongoDB models
3. Create API endpoints
4. Then move to Frontend components

**Questions for you:**
- Should we start with AI Story Assistant or manual scene creation first?
- Preferred video combination method (server-side recommended)?
- Max scenes per sequence? (Suggest 2-10)
- Should we support branching/alternate scenes in MVP?

Ready to proceed? 🚀
