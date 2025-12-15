# FRONTEND APPROVAL WORKFLOW - COMPLETE SPECIFICATION

## 📊 Current State Analysis

### Existing API Endpoints:
```
POST   /api/plan              → Returns: ProjectState (with strategy + script)
POST   /api/generate          → Starts background generation
GET    /api/status/{id}       → Polls for updates (every 3s)
GET    /api/assets/{filename} → Serves images/videos
POST   /api/upload            → Uploads reference images
```

### Current Data Flow:
```
1. User fills form (topic, style, duration, etc.)
   ↓
2. Frontend calls api.createPlan(input, config)
   ↓
3. Backend returns FULL ProjectState:
   {
     id: "abc-123",
     status: "planned",
     strategy: {                    ← FROM OPUS
       core_concept: "...",
       visual_language: "...",
       narrative_arc: "...",
       audience_hook: "...",
       cinematic_direction: {...},
       production_recommendations: {...}
     },
     script: {                      ← FROM GEMINI
       scenes: [
         {
           id: 1,
           visual_prompt: "...",
           motion_prompt: "...",
           audio_prompt: "...",
           duration: 5,
           image_path: null,        ← NOT YET GENERATED
           video_path: null         ← NOT YET GENERATED
         }
       ],
       lines: [
         {
           speaker: "VO",
           text: "What if work just... worked?",
           time_range: "0-5s",
           audio_path: null         ← NOT YET GENERATED
         }
       ],
       mood: "Premium"
     },
     logs: [...]
   }
   ↓
4. Frontend immediately calls api.startGeneration()
   ↓
5. Backend runs in background (images → audio → video → assembly)
   ↓
6. Frontend polls /status every 3s to get updates
   ↓
7. As generation progresses, scene.image_path gets populated
   ↓
8. When complete, final_video_path appears
```

### Current UX:
```
┌─────────────────────────────────────────────────┐
│ [Config Form]                                    │
│   Topic: "Create ad for Botspot AI"            │
│   Style: Cinematic                              │
│   Duration: 15s                                 │
│   [Upload Reference Images]                     │
│                                                 │
│   [GENERATE CAMPAIGN] ←─── One click, no stops │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ [PipelineFlow - n8n style nodes]                │
│   Researcher → Strategist → Gemini → Flux →... │
│   (Nodes light up as they complete)             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ [TerminalLog - Streaming logs]                  │
│   [STRATEGY] Developing creative concept...     │
│   [VISUALS] Generating Scene 1...               │
│   [SUCCESS] Image created.                      │
└─────────────────────────────────────────────────┘
                    ↓
         (90 seconds later...)
                    ↓
┌─────────────────────────────────────────────────┐
│ [Final Video Player]                            │
│   ▶ Download • Share                            │
└─────────────────────────────────────────────────┘
```

**PROBLEM:** No approval gates! User can't review strategy or regenerate images.

---

## 🎯 Desired Workflow (Your Vision)

### Inline Expansion - Recommended Approach:

```
[Input Form - Always visible at top]
┌──────────────────────────────────────┐
│ Topic: [____________]  [Generate →]  │
└──────────────────────────────────────┘

         ↓ (Plan completes, card expands below)

[Strategy Review Card] ← NEW!
┌─────────────────────────────────────────────────┐
│ ⚠️ APPROVAL REQUIRED                             │
│                                                  │
│ 📝 STRATEGIC CONCEPT: "Enterprise Control"      │
│ "Position Botspot as enterprise AI..."          │
│                                                  │
│ 🎬 3 SCENES:                                     │
│ Scene 1: "Professional overwhelmed at desk..."  │
│ Scene 2: "Botspot AI interface materializes..." │
│ Scene 3: "Same professional, now confident..."  │
│                                                  │
│ 💬 VOICEOVER:                                    │
│ "What if work just... worked?"                  │
│ "Meet Botspot. Your AI teammate."               │
│                                                  │
│ [🔄 Regenerate] [✏️ Edit] [✅ Approve]           │
└─────────────────────────────────────────────────┘

         ↓ (User clicks Approve, card expands below)

[Image Generation Panel] ← NEW!
┌─────────────────────────────────────────────────┐
│ 🎨 GENERATING IMAGES (Live Updates)              │
│                                                  │
│ ┌──────┐ ┌──────┐ ┌──────┐                      │
│ │ ✅   │ │ 🔄   │ │ ⏳   │                      │
│ │[IMG1]│ │[...] │ │[...] │                      │
│ │ 8/10 │ │      │ │      │                      │
│ │[🔄]  │ │      │ │      │                      │
│ └──────┘ └──────┘ └──────┘                      │
│                                                  │
│ Progress: 1/3 complete • 5s remaining            │
│                                                  │
│                     [✅ Approve All & Continue]  │
└─────────────────────────────────────────────────┘

         ↓ (User clicks Approve, card expands below)

[Video Generation Panel] ← NEW!
┌─────────────────────────────────────────────────┐
│ 🎬 GENERATING VIDEOS (Live Updates)              │
│                                                  │
│ Scene 1: ✅ Complete (Runway)                    │
│ ┌────────────────────┐                          │
│ │ [▶ Video Player]   │                          │
│ │  8s • 1280x768     │                          │
│ └────────────────────┘                          │
│ [🔄 Regenerate]                                  │
│                                                  │
│ Scene 2: 🔄 Runway Gen-3 (68% complete...)       │
│ Scene 3: ⏳ In Queue                             │
│                                                  │
│                     [✅ Approve All & Continue]  │
└─────────────────────────────────────────────────┘

         ↓ (User clicks Approve, final video assembles)

[Final Result]
┌─────────────────────────────────────────────────┐
│ ✅ COMMERCIAL COMPLETE                           │
│                                                  │
│ ┌────────────────────────────────────┐          │
│ │    [▶ Final Video Player]          │          │
│ │    15s • 1280x768 • Crossfade      │          │
│ └────────────────────────────────────┘          │
│                                                  │
│ [📥 Download] [🔗 Share] [🔄 New Project]        │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- Scroll up to see previous decisions
- Easy to go back and edit
- Clear progression
- Feels like n8n workflow

---

## 🔧 Required API Modifications

### Split Generation into Stages:

```python
# NEW ENDPOINTS NEEDED:

POST /api/regenerate-strategy
# If user doesn't like the strategy, regenerate it
Request: { project_id: string }
Response: { strategy: {...}, script: {...} }

POST /api/generate/images
# Generate ONLY images, then stop
Request: { project_id: string }
Response: { status: "started" }
# Frontend polls /status to see image_path populate

POST /api/regenerate-image
# Regenerate a single image
Request: {
  project_id: string,
  scene_id: number,
  prompt?: string  # Optional: edited prompt
}
Response: { image_path: string }

POST /api/generate/videos
# Generate ONLY videos from existing images
Request: { project_id: string }
Response: { status: "started" }
# Frontend polls /status to see video_path populate

POST /api/regenerate-video
# Regenerate a single video
Request: {
  project_id: string,
  scene_id: number,
  provider?: "runway" | "veo" | "kling"
}
Response: { video_path: string }

POST /api/generate/assemble
# Assemble final video from existing assets
Request: { project_id: string }
Response: { status: "started" }
```

### Backend Pipeline Changes:

**Current pipeline.py:**
```python
def resume(self):
    # Does EVERYTHING in one go:
    # - Generate all images
    # - Generate all audio
    # - Generate all videos
    # - Assemble final video
    # User has NO control during this process
```

**New pipeline.py methods:**
```python
def generate_images_only(self):
    """
    Generate images for all scenes and STOP.
    Returns when all images are complete.
    Saves state so frontend can poll for progress.
    """
    # Phase 3: Image generation (parallel)
    # Phase 3.5: Audio generation (parallel)
    # Save state
    # Return (DON'T continue to video)

def generate_videos_only(self):
    """
    Generate videos from existing images and STOP.
    Assumes images already exist.
    """
    # Phase 4: Video generation (fallback chain)
    # Save state
    # Return (DON'T continue to assembly)

def assemble_final(self):
    """
    Assemble final video from existing videos/audio.
    Assumes all assets already exist.
    """
    # Phase 5: FFmpeg assembly
    # Save state
    # Return

def regenerate_single_image(self, scene_id: int, prompt: str = None):
    """Regenerate image for a specific scene."""
    scene = self.state.script.scenes[scene_id - 1]
    if prompt:
        scene.visual_prompt = prompt

    # Generate image (with critique loop)
    # Update scene.image_path
    # Save state
    return scene.image_path

def regenerate_single_video(self, scene_id: int, provider: str = None):
    """Regenerate video for a specific scene."""
    # Similar to above
```

---

## 📊 Data Flow (With Approval Gates)

```
USER ACTION                  FRONTEND                   BACKEND
─────────────────────────────────────────────────────────────────

1. Fill form
   Click "Generate"          createPlan(input, config)
                                                        ↓
                                                    Opus generates strategy
                                                    Gemini generates script
                                                        ↓
                             ← Returns ProjectState
                             {
                               strategy: {...},
                               script: {...},
                               status: "planned"
                             }

2. [SHOWS STRATEGY CARD]
   ⚠️ APPROVAL GATE #1

   Reviews strategy...

   Option A: Regenerate      POST /regenerate-strategy
                                                        ↓
                                                    Opus tries again
                                                        ↓
                             ← Returns new strategy
                             (Loop back to review)

   Option B: Approve         setState({ step: "images" })
                             POST /generate/images
                                                        ↓
                                                    Generate images in parallel
                                                    Updates scene.image_path
                                                        ↓
3. [SHOWS IMAGE PANEL]       Polls /status every 2s
   Images appear as ready    ← Gets updated state

   ⚠️ APPROVAL GATE #2

   Option A: Regenerate      POST /regenerate-image
   single image              { scene_id: 2 }
                                                        ↓
                                                    Regenerate Scene 2 image
                                                        ↓
                             ← Returns new image_path

   Option B: Approve All     setState({ step: "videos" })
                             POST /generate/videos
                                                        ↓
                                                    Generate videos
                                                    (Runway → Veo → Kling)
                                                    Updates scene.video_path
                                                        ↓
4. [SHOWS VIDEO PANEL]       Polls /status every 3s
   Videos appear as ready    ← Gets updated state

   ⚠️ APPROVAL GATE #3

   Option A: Regenerate      POST /regenerate-video
   single video              { scene_id: 1 }

   Option B: Approve All     POST /generate/assemble
                                                        ↓
                                                    FFmpeg assembly
                                                    Creates final_video_path
                                                        ↓
5. [SHOWS FINAL VIDEO]       ← Gets final state
   Download/Share            { final_video_path: "..." }
```

---

## 🎨 Frontend Components

### 1. StrategyReviewCard.tsx
```typescript
interface StrategyReviewCardProps {
  strategy: {
    core_concept: string;
    visual_language: string;
    narrative_arc: string;
    audience_hook: string;
    cinematic_direction: {...};
    production_recommendations: {...};
  };
  script: {
    scenes: Scene[];
    lines: ScriptLine[];
    mood: string;
  };
  onApprove: () => void;
  onRegenerate: () => void;
  onEdit: (newScript: Script) => void;
  isRegenerating: boolean;
}

// Renders:
// - Strategy summary (collapsible details)
// - Scene breakdown (3-4 scenes with prompts)
// - Voiceover script
// - Action buttons
```

### 2. ImageGenerationPanel.tsx
```typescript
interface ImageGenerationPanelProps {
  scenes: Scene[];
  projectId: string;
  onAllApproved: () => void;
}

// Features:
// - Grid layout (responsive: 3 cols → 2 cols → 1 col)
// - Each scene card shows:
//   - Loading spinner (while generating)
//   - Image preview (when complete)
//   - Prompt (collapsible)
//   - Gemini critique score (8/10)
//   - Regenerate button
//   - Edit prompt button (inline)
// - Progress: "2/3 complete • 5s remaining"
// - Approve All button (only enabled when all complete)
```

### 3. VideoGenerationPanel.tsx
```typescript
interface VideoGenerationPanelProps {
  scenes: Scene[];
  projectId: string;
  onAllApproved: () => void;
}

// Features:
// - Grid layout
// - Each scene card shows:
//   - Loading bar with provider name
//   - Video player (when complete)
//   - Motion prompt
//   - Which provider succeeded
//   - Regenerate button
// - Live provider fallover logs
// - Approve All button
```

### 4. ApprovalWorkflow.tsx (Main Container)
```typescript
type WorkflowStep =
  | "input"           // Config form
  | "strategy"        // Strategy review (waiting for approval)
  | "images"          // Image generation (waiting for approval)
  | "videos"          // Video generation (waiting for approval)
  | "assembly"        // Assembling (no approval needed)
  | "complete";       // Final result

const ApprovalWorkflow = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>("input");
  const { project } = useStore();

  return (
    <div className="space-y-8">
      {/* Input form - always visible */}
      <InputForm onGenerate={() => setCurrentStep("strategy")} />

      {/* Strategy Card - shows when plan completes */}
      {currentStep !== "input" && (
        <StrategyReviewCard
          strategy={project.strategy}
          script={project.script}
          onApprove={() => setCurrentStep("images")}
          onRegenerate={handleRegenerateStrategy}
          onEdit={handleEditScript}
        />
      )}

      {/* Image Panel - shows after strategy approval */}
      {["images", "videos", "assembly", "complete"].includes(currentStep) && (
        <ImageGenerationPanel
          scenes={project.script.scenes}
          projectId={project.id}
          onAllApproved={() => setCurrentStep("videos")}
        />
      )}

      {/* Video Panel - shows after image approval */}
      {["videos", "assembly", "complete"].includes(currentStep) && (
        <VideoGenerationPanel
          scenes={project.script.scenes}
          projectId={project.id}
          onAllApproved={() => setCurrentStep("assembly")}
        />
      )}

      {/* Final Result - shows after assembly */}
      {currentStep === "complete" && (
        <FinalResultCard
          videoPath={project.final_video_path}
          onNewProject={handleReset}
        />
      )}
    </div>
  );
};
```

---

## 🤔 Design Decisions Needed

Before I start building, please choose:

### 1. Auto-Advance or Manual?
**Option A (Recommended):** Auto-advance
- Click "Approve" → automatically starts next step
- Less clicking, smoother flow
- User sees next panel expand immediately

**Option B:** Manual advance
- Click "Approve" → button changes to "Start Image Generation"
- More control, but extra click

**Your choice:** ________

---

### 2. Regeneration Limits?
**Option A (Recommended):** Unlimited
- User can regenerate as many times as they want
- Better for quality
- Cost: ~$0.10 per image regeneration

**Option B:** Limited (3 per scene)
- Prevents excessive API costs
- Forces user to think before regenerating
- Could frustrate users

**Your choice:** ________

---

### 3. Edit Prompts?
**Option A (Recommended):** Allow editing
- Click "Edit Prompt" → inline textarea appears
- User modifies prompt → regenerates with new prompt
- More flexibility

**Option B:** View-only (regenerate with same prompt)
- Simpler, less risky
- User can't break prompts
- Less control

**Your choice:** ________

---

### 4. Polling Frequency?
**Current:** Poll /status every 3 seconds

**Options:**
- **Fast (1-2s):** More responsive, more server load
- **Medium (3s):** Current setting, good balance
- **Slow (5s):** Less load, slightly delayed updates

**Your choice:** ________

---

### 5. Skip Approvals?
**Option A:** Force approvals (safer)
- User MUST approve at each step
- Prevents wasting API calls on bad results

**Option B:** Add "Skip Approvals" toggle (power users)
- Toggle in UI: "Auto-approve all steps"
- Runs like current pipeline (no stops)
- Risky but faster

**Your choice:** ________

---

## 🚀 Implementation Checklist

### Backend (Python)
- [ ] Add `generate_images_only()` method to pipeline.py
- [ ] Add `generate_videos_only()` method to pipeline.py
- [ ] Add `assemble_final()` method to pipeline.py
- [ ] Add `regenerate_single_image()` method
- [ ] Add `regenerate_single_video()` method
- [ ] Create `/api/regenerate-strategy` endpoint
- [ ] Create `/api/generate/images` endpoint
- [ ] Create `/api/generate/videos` endpoint
- [ ] Create `/api/generate/assemble` endpoint
- [ ] Create `/api/regenerate-image` endpoint
- [ ] Create `/api/regenerate-video` endpoint

### Frontend (TypeScript/React)
- [ ] Create `StrategyReviewCard.tsx` component
- [ ] Create `ImageGenerationPanel.tsx` component
- [ ] Create `VideoGenerationPanel.tsx` component
- [ ] Create `FinalResultCard.tsx` component
- [ ] Create `ApprovalWorkflow.tsx` orchestrator
- [ ] Update store.ts with new actions
- [ ] Add polling logic for each stage
- [ ] Add animations (cards expand, images fade in)
- [ ] Add responsive grid layouts
- [ ] Update OTTWorkflowCanvas to use new workflow

### Testing
- [ ] Test full approval workflow
- [ ] Test regeneration flows
- [ ] Test error handling
- [ ] Test responsive layouts
- [ ] Test polling/live updates

**Estimated Time:** 8-12 hours total

---

## ✅ Summary

**Current:** One-click → wait 90s → get video (no control)

**New:** Multi-step approval workflow with full control:
1. Generate strategy → Review → Approve
2. Generate images → Review → Regenerate if needed → Approve
3. Generate videos → Review → Regenerate if needed → Approve
4. Assemble → Download

**Your Decisions Needed:**
1. Auto-advance? (A/B)
2. Regeneration limits? (A/B)
3. Edit prompts? (A/B)
4. Polling frequency? (1-5s)
5. Skip approvals toggle? (A/B)

**Once you decide, I'll start building!** 🎯
