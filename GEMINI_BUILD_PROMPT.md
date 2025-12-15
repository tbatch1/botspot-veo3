# COMPLETE BUILD SPECIFICATION FOR APPROVAL WORKFLOW SYSTEM

## PROJECT OVERVIEW

You are building an interactive approval workflow for an OTT (Over-The-Top) commercial video generation system. The system currently generates videos end-to-end with no user control. Your task is to add **approval gates** at each stage so clients can review and approve AI decisions before proceeding.

**Current Flow (Problem):**
```
User fills form → Click Generate → Wait 90 seconds → Get final video
(No visibility, no control, no ability to regenerate)
```

**New Flow (Solution):**
```
User fills form → Click Generate
  ↓
APPROVAL GATE #1: Review AI Strategy (Opus-generated concept)
  → User approves → Start image generation
  ↓
APPROVAL GATE #2: Review Generated Images (see as they appear)
  → User approves → Start video generation
  ↓
APPROVAL GATE #3: Review Generated Videos (see as they appear)
  → User approves → Assemble final video
  ↓
Download final commercial
```

---

## TECHNOLOGY STACK

**Backend:**
- Python 3.13
- FastAPI (REST API)
- Pydantic (data models)
- Background tasks for async generation
- File system for state persistence (JSON files in `output/plan_{id}.json`)

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- React 18
- Zustand (state management)
- Tailwind CSS + Framer Motion
- Axios for API calls

**AI Providers:**
- Anthropic Claude Opus 4.5 (strategy)
- Google Gemini 2.0 Flash (script generation)
- Google Imagen 4 (images)
- Runway Gen-3 / Veo / Kling (video)
- ElevenLabs (audio)

---

## EXISTING CODEBASE STRUCTURE

### Backend Files:
```
ott_ad_builder/
├── api.py                    # FastAPI endpoints
├── pipeline.py               # AdGenerator class (main orchestrator)
├── state.py                  # Pydantic models (ProjectState, Scene, Script)
├── config.py                 # Environment variables
├── parallel_utils.py         # Parallel execution utilities (already exists)
└── providers/
    ├── strategist.py         # Claude Opus (strategy generation)
    ├── gemini.py             # Gemini (script generation)
    ├── imagen.py             # Image generation
    ├── runway.py             # Video generation
    ├── elevenlabs.py         # Audio generation
    └── composer.py           # FFmpeg video assembly
```

### Frontend Files:
```
frontend_new/
├── app/
│   └── ott/
│       └── page.tsx          # Main OTT page
├── components/
│   ├── OTTWorkflowCanvas.tsx # Main UI component
│   ├── PipelineFlow.tsx      # n8n-style node visualization
│   └── TerminalLog.tsx       # Live log display
└── lib/
    ├── store.ts              # Zustand state management
    └── api.ts                # API client functions
```

---

## EXISTING DATA MODELS

### ProjectState (state.py)
```python
class Scene(BaseModel):
    id: int
    visual_prompt: str          # Prompt for image generation
    motion_prompt: str          # Prompt for video animation
    audio_prompt: Optional[str] # Prompt for SFX
    duration: int = 5           # Scene duration in seconds

    # Asset paths (populated during generation)
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    sfx_path: Optional[str] = None

    # Character consistency fields (already exists)
    primary_subject: Optional[str] = None
    subject_description: Optional[str] = None
    subject_reference: Optional[str] = None

class ScriptLine(BaseModel):
    speaker: str                # "VO" or character name
    text: str                   # Voiceover text
    time_range: str             # "0-5s"
    audio_path: Optional[str] = None

class Script(BaseModel):
    lines: List[ScriptLine]
    mood: str                   # "Premium", "Bold", etc.
    scenes: List[Scene]

class ProjectState(BaseModel):
    id: str                     # UUID
    user_input: str             # Original prompt
    status: str                 # "initialized", "planned", "processing", "completed", "failed"
    error: Optional[str] = None
    seed: int                   # For reproducibility

    script: Optional[Script] = None
    strategy: Optional[Dict] = None  # From Opus strategist
    research_brief: Optional[str] = None

    # Asset paths
    final_video_path: Optional[str] = None
    bgm_path: Optional[str] = None

    # Configuration
    video_model: str = "runway"
    image_provider: str = "imagen"
    transition_type: str = "crossfade"
    uploaded_asset: Optional[str] = None

    # Logs
    logs: List[str] = []

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
```

### Strategy Object (from Opus)
```typescript
interface Strategy {
  core_concept: string;           // "Enterprise Control"
  visual_language: string;        // "Shot on Arri Alexa 65..."
  narrative_arc: string;          // 3-sentence story summary
  audience_hook: string;          // Psychological hook
  cinematic_direction: {
    mood_notes: string;
    lighting_notes: string;
    camera_notes: string;
  };
  production_recommendations: {
    visual_engine: "flux" | "imagen";
    video_engine: "runway" | "veo" | "kling";
    voice_vibe: string;
  };
}
```

---

## EXISTING API ENDPOINTS

### Current Endpoints:
```python
POST /api/plan
  Request: { user_input: str, config_overrides: dict }
  Response: ProjectState (with strategy + script, status: "planned")

POST /api/generate
  Request: { project_id: str, script: Script }
  Response: { status: "started", project_id: str }
  Behavior: Runs ENTIRE pipeline in background (images → audio → video → assembly)

GET /api/status/{project_id}
  Response: ProjectState (updated with current progress)

POST /api/upload
  Request: FormData with file
  Response: { status: "success", filename: str }
```

---

## YOUR TASK: IMPLEMENT APPROVAL WORKFLOW

### Part 1: Backend Changes

#### 1.1 Modify `ott_ad_builder/pipeline.py`

**Add new stage-based methods to `AdGenerator` class:**

```python
def generate_images_only(self):
    """
    Generate images and audio, then STOP.
    Sets status to 'images_complete' when done.
    Does NOT continue to video generation.
    """
    try:
        self.state.status = "generating_images"
        self.state.add_log("[APPROVAL_GATE] User approved strategy, starting image generation...")
        self.save_state()

        # Import providers
        from .providers.imagen import ImagenProvider
        from .providers.elevenlabs import ElevenLabsProvider
        from .providers.mock import MockElevenLabsProvider
        from .providers.composition import CompositionProvider

        # Initialize providers
        imagen = ImagenProvider()

        try:
            if config.ELEVENLABS_API_KEY and config.ELEVENLABS_API_KEY != "mock_elevenlabs_key":
                eleven = ElevenLabsProvider()
                print("   Using ElevenLabs for audio generation")
            else:
                eleven = MockElevenLabsProvider()
                print("   Using Mock audio provider")
        except Exception as e:
            print(f"   [WARN] ElevenLabs init failed, using mock: {e}")
            eleven = MockElevenLabsProvider()

        composer_tool = CompositionProvider()

        # --- PHASE 3: IMAGE GENERATION (Copy from existing resume() method) ---
        # Lines 216-287 from current pipeline.py
        # This is the EXISTING parallel image generation code

        print(f"\n   [OPTIMIZATION] Using parallel image generation (3x faster)")
        self.state.add_log("[OPTIMIZATION] Parallel image generation enabled")

        # Check for uploaded asset
        uploaded_asset_path = None
        if self.state.uploaded_asset:
            possible_path = os.path.join(config.ASSETS_DIR, "user_uploads", self.state.uploaded_asset)
            if os.path.exists(possible_path):
                uploaded_asset_path = possible_path
                print(f"   [VISUALS] Using Uploaded Reference: {self.state.uploaded_asset}")

        # Handle composition scenes
        composition_scenes = [s for s in self.state.script.scenes if s.composition_sources and not s.image_path]
        for scene in composition_scenes:
            print(f"   [COMPOSE] Composing scene {scene.id}...")
            try:
                scene.image_path = composer_tool.compose(scene.composition_sources, scene.visual_prompt)
                self.state.add_log(f"[VISUALS] Composed Scene {scene.id}")
            except Exception as e:
                print(f"   [ERROR] Composition Failed for Scene {scene.id}: {e}")
                self.state.add_log(f"[ERROR] Composition Failed: {str(e)}")

        # Parallel generation
        try:
            start_time = time.time()
            from .parallel_utils import ParallelImageGenerator, CharacterConsistencyExtractor

            parallel_gen = ParallelImageGenerator(imagen, self.llm, self.state)
            self.state.script.scenes = parallel_gen.generate_parallel(
                self.state.script.scenes,
                uploaded_asset_path=uploaded_asset_path,
                max_workers=3
            )
            elapsed = time.time() - start_time
            print(f"   [PERFORMANCE] Image generation completed in {elapsed:.1f}s")
            self.state.add_log(f"[PERFORMANCE] Parallel image generation: {elapsed:.1f}s")

            # Character consistency
            print(f"\n   [OPTIMIZATION] Extracting character consistency...")
            consistency_extractor = CharacterConsistencyExtractor(self.llm)
            self.state.script.scenes = consistency_extractor.inject_consistency_references(
                self.state.script.scenes
            )
            self.state.add_log("[OPTIMIZATION] Character consistency references injected")

        except Exception as e:
            print(f"   [ERROR] Parallel image generation failed: {e}")
            self.state.add_log(f"[ERROR] Parallel generation failed: {str(e)}")

            # Fallback to sequential
            print(f"   [FALLBACK] Switching to sequential generation...")
            for scene in self.state.script.scenes:
                if not scene.image_path and not scene.composition_sources:
                    try:
                        print(f"   Generating Image for Scene {scene.id}...")
                        scene.image_path = imagen.generate_image(
                            scene.visual_prompt,
                            seed=self.state.seed + scene.id,
                            image_input=uploaded_asset_path
                        )
                        self.state.add_log(f"[VISUALS] Scene {scene.id} created (sequential)")
                    except Exception as e2:
                        print(f"   [ERROR] Scene {scene.id} failed: {e2}")
                        self.state.add_log(f"[ERROR] Scene {scene.id} failed: {str(e2)}")

        # --- PHASE 3.5: AUDIO GENERATION (Copy from existing resume() method) ---
        # Lines 282-341 from current pipeline.py

        print(f"\n   [OPTIMIZATION] Using parallel audio generation (3x faster)")
        self.state.add_log("[OPTIMIZATION] Parallel audio generation enabled")

        # Derive mood from strategy
        mood_prompt = "Cinematic Ambient"
        if self.state.strategy and 'cinematic_direction' in self.state.strategy:
            mood_notes = self.state.strategy['cinematic_direction'].get('mood_notes', '')
            if mood_notes:
                mood_prompt = mood_notes

        # Calculate duration
        total_duration = sum(scene.duration for scene in self.state.script.scenes) + 5

        try:
            start_time = time.time()
            from .parallel_utils import ParallelAudioGenerator

            parallel_audio = ParallelAudioGenerator(eleven, self.state)
            self.state.bgm_path = parallel_audio.generate_all_audio(
                self.state.script,
                bgm_duration=total_duration,
                bgm_mood=mood_prompt
            )
            elapsed = time.time() - start_time
            print(f"   [PERFORMANCE] Audio generation completed in {elapsed:.1f}s")
            self.state.add_log(f"[PERFORMANCE] Parallel audio generation: {elapsed:.1f}s")

        except Exception as e:
            print(f"   [ERROR] Parallel audio generation failed: {e}")
            self.state.add_log(f"[ERROR] Parallel audio failed: {str(e)}")

            # Fallback to sequential
            print(f"   [FALLBACK] Switching to sequential audio generation...")

            for i, line in enumerate(self.state.script.lines):
                if not line.audio_path:
                    try:
                        print(f"   Generating VO for Line {i+1}...")
                        line.audio_path = eleven.generate_speech(line.text)
                    except Exception as e2:
                        print(f"   [ERROR] VO Line {i+1} failed: {e2}")

            for scene in self.state.script.scenes:
                if not scene.sfx_path and scene.audio_prompt:
                    try:
                        print(f"   Generating SFX for Scene {scene.id}...")
                        scene.sfx_path = eleven.generate_sfx(scene.audio_prompt)
                    except Exception as e2:
                        print(f"   [ERROR] SFX Scene {scene.id} failed: {e2}")

            if not self.state.bgm_path:
                try:
                    print(f"   Generating BGM...")
                    self.state.bgm_path = eleven.generate_bgm(mood_prompt, duration=total_duration)
                except Exception as e2:
                    print(f"   [ERROR] BGM failed: {e2}")

        # STOP HERE - Don't continue to video generation
        self.state.status = "images_complete"
        self.state.add_log("[APPROVAL_GATE] Images and audio complete. Waiting for user approval to proceed to videos...")
        self.save_state()

        print(f"\n[STAGE_COMPLETE] Images and audio generated. Status: images_complete")

    except Exception as e:
        error_msg = f"Image generation stage failed: {str(e)}"
        print(f"\n[FATAL ERROR] {error_msg}")
        self.state.status = "failed"
        self.state.error = error_msg
        self.state.add_log(f"[FATAL] {error_msg}")

        import traceback
        self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")
        self.save_state()
        raise


def generate_videos_only(self):
    """
    Generate videos from existing images, then STOP.
    Sets status to 'videos_complete' when done.
    Assumes images already exist in self.state.script.scenes[].image_path
    """
    try:
        self.state.status = "generating_videos"
        self.state.add_log("[APPROVAL_GATE] User approved images, starting video generation...")
        self.save_state()

        # --- PHASE 4: VIDEO GENERATION (Copy from existing resume() method) ---
        # Lines 344-427 from current pipeline.py
        # This is the EXISTING video fallback chain code

        print(f"\n[PHASE 4] Motion Synthesis...")
        self.state.add_log(f"[PHASE 4] Starting Motion Synthesis with fallback chain...")

        from .providers.video_google import GoogleVideoProvider
        from .providers.runway import RunwayProvider
        from .providers.kling import KlingProvider

        runway = RunwayProvider()
        veo = GoogleVideoProvider()
        kling = KlingProvider()

        print(f"   [OPTIMIZATION] Video fallback chain enabled: Runway -> Veo -> Kling")
        self.state.add_log("[OPTIMIZATION] Video provider fallback chain active")

        for i, scene in enumerate(self.state.script.scenes):
            if scene.image_path and not scene.video_path:
                print(f"   Animating Scene {scene.id}...")
                self.state.add_log(f"[VIDEO] Animating Scene {scene.id}...")

                providers = [
                    {
                        "name": "runway",
                        "obj": runway,
                        "method": "animate",
                        "args": (scene.image_path, scene.motion_prompt)
                    },
                    {
                        "name": "veo",
                        "obj": veo,
                        "method": "generate_video",
                        "args": (scene.motion_prompt, scene.image_path)
                    },
                    {
                        "name": "kling",
                        "obj": kling,
                        "method": "animate",
                        "args": (scene.image_path, scene.motion_prompt)
                    }
                ]

                video_generated = False
                for provider in providers:
                    provider_name = provider["name"]
                    provider_obj = provider["obj"]
                    method_name = provider["method"]
                    args = provider["args"]

                    try:
                        print(f"   [VIDEO] Trying {provider_name.upper()}...")
                        self.state.add_log(f"[VIDEO] Attempting {provider_name} for Scene {scene.id}")

                        method = getattr(provider_obj, method_name)
                        scene.video_path = method(*args)

                        if scene.video_path and os.path.exists(scene.video_path):
                            print(f"   [SUCCESS] {provider_name.upper()} completed Scene {scene.id}")
                            self.state.add_log(f"[SUCCESS] {provider_name} generated Scene {scene.id}")
                            video_generated = True
                            break
                        else:
                            print(f"   [WARN] {provider_name.upper()} returned invalid path")

                    except Exception as e:
                        print(f"   [ERROR] {provider_name.upper()} failed: {e}")
                        self.state.add_log(f"[ERROR] {provider_name} failed for Scene {scene.id}: {str(e)}")

                        if provider_name != "kling":
                            print(f"   [FALLBACK] Switching to next provider...")
                            self.state.add_log(f"[FALLBACK] Trying next provider for Scene {scene.id}")

                if not video_generated:
                    print(f"   [FATAL] All video providers failed for Scene {scene.id}")
                    self.state.add_log(f"[FATAL] All providers failed for Scene {scene.id}")

        # STOP HERE - Don't continue to assembly
        self.state.status = "videos_complete"
        self.state.add_log("[APPROVAL_GATE] Videos complete. Waiting for user approval to proceed to assembly...")
        self.save_state()

        print(f"\n[STAGE_COMPLETE] Videos generated. Status: videos_complete")

    except Exception as e:
        error_msg = f"Video generation stage failed: {str(e)}"
        print(f"\n[FATAL ERROR] {error_msg}")
        self.state.status = "failed"
        self.state.error = error_msg
        self.state.add_log(f"[FATAL] {error_msg}")

        import traceback
        self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")
        self.save_state()
        raise


def assemble_final(self):
    """
    Assemble final video from existing videos and audio.
    Sets status to 'completed' when done.
    Assumes videos and audio already exist.
    """
    try:
        self.state.status = "assembling"
        self.state.add_log("[APPROVAL_GATE] User approved videos, starting final assembly...")
        self.save_state()

        # --- PHASE 5: ASSEMBLY (Copy from existing resume() method) ---
        # Lines 429-505 from current pipeline.py

        print("\n[PHASE 5] Final Assembly...")
        self.state.add_log("[PHASE 5] Assembling Final Video...")

        # Validate we have video clips
        video_clips = [s for s in self.state.script.scenes if s.video_path and os.path.exists(s.video_path)]

        if len(video_clips) == 0:
            error_msg = "No video clips available for assembly. All video generation failed."
            print(f"   [FATAL] {error_msg}")
            self.state.add_log(f"[FATAL] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise Exception(error_msg)

        if len(video_clips) < len(self.state.script.scenes):
            missing_count = len(self.state.script.scenes) - len(video_clips)
            print(f"   [WARN] {missing_count} scenes failed, proceeding with {len(video_clips)} clips")
            self.state.add_log(f"[WARN] Partial success: {len(video_clips)}/{len(self.state.script.scenes)} scenes")

        try:
            from .providers.composer import Composer
            composer = Composer()

            print(f"   [ASSEMBLY] Composing {len(video_clips)} video clips...")
            self.state.add_log(f"[ASSEMBLY] Composing with transition: {self.state.transition_type}")

            final_path = composer.compose(self.state, transition_type=self.state.transition_type)

            if final_path and os.path.exists(final_path):
                self.state.final_video_path = final_path
                self.state.status = "completed"
                self.save_state()
                print(f"\n[DONE] Video saved to: {final_path}")
                self.state.add_log(f"[SUCCESS] Final video: {final_path}")
            else:
                raise Exception("Composer returned invalid path")

        except Exception as e:
            error_msg = f"Assembly failed: {str(e)}"
            print(f"   [ERROR] {error_msg}")
            self.state.add_log(f"[ERROR] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise

        # Print performance summary
        print("\n" + "="*80)
        print("PIPELINE COMPLETE - PERFORMANCE SUMMARY")
        print("="*80)

        image_success = len([s for s in self.state.script.scenes if s.image_path])
        video_success = len([s for s in self.state.script.scenes if s.video_path])
        vo_success = len([l for l in self.state.script.lines if l.audio_path])
        sfx_success = len([s for s in self.state.script.scenes if s.sfx_path or not s.audio_prompt])

        print(f"Images:  {image_success}/{len(self.state.script.scenes)} scenes")
        print(f"Videos:  {video_success}/{len(self.state.script.scenes)} scenes")
        print(f"VO:      {vo_success}/{len(self.state.script.lines)} lines")
        print(f"SFX:     {sfx_success}/{len(self.state.script.scenes)} scenes")
        print(f"BGM:     {'Yes' if self.state.bgm_path else 'No'}")
        print(f"Final:   {self.state.final_video_path}")
        print("="*80 + "\n")

        self.state.status = "completed"
        self.save_state()

    except Exception as e:
        error_msg = f"Assembly stage failed: {str(e)}"
        print(f"\n[FATAL ERROR] {error_msg}")
        self.state.status = "failed"
        self.state.error = error_msg
        self.state.add_log(f"[FATAL] {error_msg}")

        import traceback
        self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")
        self.save_state()
        raise
```

#### 1.2 Modify `ott_ad_builder/api.py`

**Add new endpoints:**

```python
# Add this after the existing /api/generate endpoint (around line 127)

@app.post("/api/generate/images")
async def generate_images_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Step 2a: Generate images only (approval gate).
    User has approved strategy, now generate images and audio.
    """
    print(f"\n[API] Starting image generation for project: {request.project_id}")

    generator = AdGenerator(project_id=request.project_id)

    # Load existing state
    plan_path = generator._get_plan_path()
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate we're in correct state
    if generator.state.status != "planned":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start image generation. Current status: {generator.state.status}"
        )

    # Update status
    generator.state.status = "generating_images"
    generator.save_state()

    # Run in background
    def run_image_generation_with_error_handling():
        try:
            generator.generate_images_only()
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            generator.state.status = "failed"
            generator.state.error = str(e)
            generator.save_state()

    background_tasks.add_task(run_image_generation_with_error_handling)

    return {"status": "started", "project_id": request.project_id}


@app.post("/api/generate/videos")
async def generate_videos_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Step 3a: Generate videos only (approval gate).
    User has approved images, now generate videos.
    """
    print(f"\n[API] Starting video generation for project: {request.project_id}")

    generator = AdGenerator(project_id=request.project_id)

    # Load existing state
    plan_path = generator._get_plan_path()
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate we're in correct state
    if generator.state.status != "images_complete":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start video generation. Current status: {generator.state.status}"
        )

    # Update status
    generator.state.status = "generating_videos"
    generator.save_state()

    # Run in background
    def run_video_generation_with_error_handling():
        try:
            generator.generate_videos_only()
        except Exception as e:
            print(f"[ERROR] Video generation failed: {e}")
            generator.state.status = "failed"
            generator.state.error = str(e)
            generator.save_state()

    background_tasks.add_task(run_video_generation_with_error_handling)

    return {"status": "started", "project_id": request.project_id}


@app.post("/api/generate/assemble")
async def assemble_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Step 4a: Assemble final video (approval gate).
    User has approved videos, now create final commercial.
    """
    print(f"\n[API] Starting assembly for project: {request.project_id}")

    generator = AdGenerator(project_id=request.project_id)

    # Load existing state
    plan_path = generator._get_plan_path()
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate we're in correct state
    if generator.state.status != "videos_complete":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start assembly. Current status: {generator.state.status}"
        )

    # Update status
    generator.state.status = "assembling"
    generator.save_state()

    # Run in background
    def run_assembly_with_error_handling():
        try:
            generator.assemble_final()
        except Exception as e:
            print(f"[ERROR] Assembly failed: {e}")
            generator.state.status = "failed"
            generator.state.error = str(e)
            generator.save_state()

    background_tasks.add_task(run_assembly_with_error_handling)

    return {"status": "started", "project_id": request.project_id}
```

---

### Part 2: Frontend Changes

#### 2.1 Update `frontend_new/lib/api.ts`

**Add type for strategy:**

```typescript
// Add after Scene interface (around line 14)
export interface Strategy {
  core_concept: string;
  visual_language: string;
  narrative_arc: string;
  audience_hook: string;
  cinematic_direction: {
    mood_notes: string;
    lighting_notes: string;
    camera_notes: string;
  };
  production_recommendations: {
    visual_engine: string;
    video_engine: string;
    voice_vibe: string;
  };
}

// Update ProjectState interface (around line 29)
export interface ProjectState {
  id: string;
  user_input: string;
  status: string;
  script?: Script;
  strategy?: Strategy;  // ADD THIS LINE
  final_video_path?: string;
  logs: string[];
  error?: string;
}

// Add new API functions at the end (around line 64)
export const api = {
  // ... existing functions ...

  generateImages: async (projectId: string): Promise<void> => {
    await axios.post(`${API_URL}/generate/images`, { project_id: projectId, script: {} });
  },

  generateVideos: async (projectId: string): Promise<void> => {
    await axios.post(`${API_URL}/generate/videos`, { project_id: projectId, script: {} });
  },

  assembleVideo: async (projectId: string): Promise<void> => {
    await axios.post(`${API_URL}/generate/assemble`, { project_id: projectId, script: {} });
  },
};
```

#### 2.2 Update `frontend_new/lib/store.ts`

**Add workflow step state:**

```typescript
// Update AppState interface (around line 4)
interface AppState {
    project: ProjectState | null;
    isLoading: boolean;
    error: string | null;
    pollingInterval: NodeJS.Timeout | null;
    pollRetryCount: number;

    // ADD THESE LINES:
    currentStep: "input" | "strategy" | "images" | "videos" | "complete";

    createPlan: (input: string, config?: any) => Promise<ProjectState | void>;
    startGeneration: () => Promise<void>;

    // ADD THESE ACTIONS:
    approveStrategy: () => Promise<void>;
    approveImages: () => Promise<void>;
    approveVideos: () => Promise<void>;

    pollStatus: () => void;
    stopPolling: () => void;
    reset: () => void;
    updateScript: (script: any) => void;
}

// Update initial state (around line 21)
export const useStore = create<AppState>((set, get) => ({
    project: null,
    isLoading: false,
    error: null,
    pollingInterval: null,
    pollRetryCount: 0,
    currentStep: "input",  // ADD THIS LINE

    createPlan: async (input: string, config?: any) => {
        set({ isLoading: true, error: null });
        try {
            const project = await api.createPlan(input, config);
            set({
                project,
                isLoading: false,
                currentStep: "strategy"  // ADD THIS LINE - Move to strategy review
            });
            return project;
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to create plan';
            set({ error: errorMsg, isLoading: false });
        }
    },

    // ADD NEW ACTIONS:
    approveStrategy: async () => {
        const { project } = get();
        if (!project) return;

        set({ isLoading: true, error: null, pollRetryCount: 0 });
        try {
            await api.generateImages(project.id);
            set({ currentStep: "images" });
            // Start polling to watch image generation
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start image generation';
            set({ error: errorMsg, isLoading: false });
        }
    },

    approveImages: async () => {
        const { project } = get();
        if (!project) return;

        set({ isLoading: true, error: null, pollRetryCount: 0 });
        try {
            await api.generateVideos(project.id);
            set({ currentStep: "videos" });
            // Start polling to watch video generation
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start video generation';
            set({ error: errorMsg, isLoading: false });
        }
    },

    approveVideos: async () => {
        const { project } = get();
        if (!project) return;

        set({ isLoading: true, error: null, pollRetryCount: 0 });
        try {
            await api.assembleVideo(project.id);
            // Keep polling, will move to "complete" when status === "completed"
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start assembly';
            set({ error: errorMsg, isLoading: false });
        }
    },

    // UPDATE pollStatus to handle new statuses:
    pollStatus: () => {
        const { pollingInterval } = get();
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }

        const interval = setInterval(async () => {
            const { project, pollRetryCount } = get();
            if (!project) {
                get().stopPolling();
                return;
            }

            try {
                const updated = await api.getStatus(project.id);
                set({ project: updated, pollRetryCount: 0 });

                // Handle status changes
                if (updated.status === 'completed') {
                    get().stopPolling();
                    set({ isLoading: false, error: null, currentStep: "complete" });
                } else if (updated.status === 'failed') {
                    get().stopPolling();
                    const errorMsg = (updated as any).error || 'Generation failed';
                    set({ isLoading: false, error: errorMsg });
                } else if (updated.status === 'images_complete') {
                    // Images done, stop polling, wait for user approval
                    get().stopPolling();
                    set({ isLoading: false });
                } else if (updated.status === 'videos_complete') {
                    // Videos done, stop polling, wait for user approval
                    get().stopPolling();
                    set({ isLoading: false });
                }
            } catch (err: any) {
                console.error('Polling error', err);
                const newRetryCount = pollRetryCount + 1;
                if (newRetryCount >= 20) {
                    get().stopPolling();
                    const errorMsg = err.response?.status === 404
                        ? 'Project not found'
                        : 'Failed to check status - server may be down';
                    set({ isLoading: false, error: errorMsg, pollRetryCount: 0 });
                } else {
                    set({ pollRetryCount: newRetryCount });
                }
            }
        }, 3000); // Poll every 3 seconds

        set({ pollingInterval: interval });
    },

    // ... rest of existing code (stopPolling, reset, updateScript) ...
}));
```

#### 2.3 Create `frontend_new/components/StrategyReviewCard.tsx`

**New file:**

```typescript
'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, RefreshCw, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Strategy, Script } from '@/lib/api';
import clsx from 'clsx';

interface StrategyReviewCardProps {
  strategy: Strategy;
  script: Script;
  onApprove: () => void;
  isVisible: boolean;
}

export default function StrategyReviewCard({
  strategy,
  script,
  onApprove,
  isVisible
}: StrategyReviewCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto mb-8"
    >
      {/* Header with approval gate warning */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-t-2xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-amber-400 animate-pulse" />
          <span className="text-amber-300 font-bold text-sm tracking-wider uppercase">
            Approval Required - Review AI Strategy
          </span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-amber-400 hover:text-amber-300 transition-colors"
        >
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Card content */}
      <div className={clsx(
        "bg-slate-900/90 backdrop-blur-xl border-x border-b border-slate-700 rounded-b-2xl shadow-2xl overflow-hidden transition-all",
        isExpanded ? "max-h-[2000px]" : "max-h-0"
      )}>
        <div className="p-6 space-y-6">
          {/* Core Concept */}
          <div>
            <h3 className="text-cyan-400 font-bold text-sm uppercase tracking-wider mb-2">
              Strategic Concept
            </h3>
            <p className="text-white text-xl font-bold mb-2">
              "{strategy.core_concept}"
            </p>
            <p className="text-slate-300 text-sm leading-relaxed">
              {strategy.narrative_arc}
            </p>
          </div>

          {/* Visual Language */}
          <div>
            <h3 className="text-purple-400 font-bold text-sm uppercase tracking-wider mb-2">
              Visual Language
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed font-mono bg-slate-800/50 p-3 rounded-lg border border-slate-700">
              {strategy.visual_language}
            </p>
          </div>

          {/* Scenes */}
          <div>
            <h3 className="text-green-400 font-bold text-sm uppercase tracking-wider mb-3">
              {script.scenes.length}-Scene Breakdown
            </h3>
            <div className="space-y-3">
              {script.scenes.map((scene, idx) => (
                <div
                  key={scene.id}
                  className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 hover:border-cyan-500/30 transition-all"
                >
                  <div className="flex items-start gap-3">
                    <div className="bg-cyan-500/20 text-cyan-400 font-bold text-xs px-2 py-1 rounded">
                      SCENE {idx + 1}
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-200 text-sm leading-relaxed">
                        {scene.visual_prompt.length > 150
                          ? scene.visual_prompt.substring(0, 150) + '...'
                          : scene.visual_prompt}
                      </p>
                      <p className="text-slate-500 text-xs mt-1">
                        Duration: {scene.duration}s
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Voiceover Script */}
          {script.lines && script.lines.length > 0 && (
            <div>
              <h3 className="text-pink-400 font-bold text-sm uppercase tracking-wider mb-3">
                Voiceover Script
              </h3>
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-2">
                {script.lines.map((line, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="text-slate-600 font-mono text-xs shrink-0">
                      {line.time_range}
                    </span>
                    <p className="text-slate-200 text-sm italic">
                      "{line.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cinematic Direction */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-3">
              <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-1">Mood</h4>
              <p className="text-slate-200 text-sm">
                {strategy.cinematic_direction?.mood_notes || script.mood}
              </p>
            </div>
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-3">
              <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-1">Lighting</h4>
              <p className="text-slate-200 text-sm">
                {strategy.cinematic_direction?.lighting_notes || 'Dramatic'}
              </p>
            </div>
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-3">
              <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-1">Camera</h4>
              <p className="text-slate-200 text-sm">
                {strategy.cinematic_direction?.camera_notes || 'Steadicam'}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-700">
            {/* Regenerate button (future feature) */}
            <button
              disabled
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-600 rounded-lg text-sm font-bold cursor-not-allowed"
            >
              <RefreshCw className="w-4 h-4" />
              Regenerate
            </button>

            {/* Approve button */}
            <button
              onClick={onApprove}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-lg font-bold shadow-lg hover:shadow-green-500/25 transition-all"
            >
              <Check className="w-5 h-5" />
              Approve & Start Image Generation
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
```

#### 2.4 Create `frontend_new/components/ImageGenerationPanel.tsx`

**New file:**

```typescript
'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Loader2, Image as ImageIcon, ChevronDown, ChevronUp } from 'lucide-react';
import { Scene, api } from '@/lib/api';
import clsx from 'clsx';

interface ImageGenerationPanelProps {
  scenes: Scene[];
  onAllComplete: () => void;
  isVisible: boolean;
  status: string;
}

export default function ImageGenerationPanel({
  scenes,
  onAllComplete,
  isVisible,
  status
}: ImageGenerationPanelProps) {
  const [expandedScene, setExpandedScene] = useState<number | null>(null);

  if (!isVisible) return null;

  const scenesWithImages = scenes.filter(s => s.image_path).length;
  const totalScenes = scenes.length;
  const allComplete = scenesWithImages === totalScenes && status === 'images_complete';
  const isGenerating = status === 'generating_images';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-6xl mx-auto mb-8"
    >
      {/* Header */}
      <div className={clsx(
        "border rounded-t-2xl px-6 py-3 flex items-center justify-between",
        allComplete
          ? "bg-green-500/10 border-green-500/30"
          : "bg-cyan-500/10 border-cyan-500/30"
      )}>
        <div className="flex items-center gap-3">
          {isGenerating ? (
            <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
          ) : (
            <Check className="w-5 h-5 text-green-400" />
          )}
          <span className={clsx(
            "font-bold text-sm tracking-wider uppercase",
            allComplete ? "text-green-300" : "text-cyan-300"
          )}>
            Image Generation - {scenesWithImages}/{totalScenes} Complete
          </span>
        </div>
        <div className="text-slate-400 text-xs font-mono">
          {allComplete ? 'Ready for approval' : 'Generating in parallel...'}
        </div>
      </div>

      {/* Scene Grid */}
      <div className="bg-slate-900/90 backdrop-blur-xl border-x border-b border-slate-700 rounded-b-2xl p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {scenes.map((scene, idx) => {
            const hasImage = !!scene.image_path;
            const isExpanded = expandedScene === scene.id;

            return (
              <motion.div
                key={scene.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className={clsx(
                  "border rounded-xl overflow-hidden transition-all",
                  hasImage
                    ? "border-green-500/30 bg-green-900/10"
                    : "border-cyan-500/30 bg-cyan-900/10 animate-pulse"
                )}
              >
                {/* Image preview or loading state */}
                <div className="aspect-video bg-slate-800 relative">
                  {hasImage ? (
                    <img
                      src={api.getAssetUrl(scene.image_path)}
                      alt={`Scene ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                    </div>
                  )}

                  {/* Scene number badge */}
                  <div className="absolute top-2 left-2 bg-black/70 px-2 py-1 rounded text-white text-xs font-bold">
                    SCENE {idx + 1}
                  </div>

                  {/* Status badge */}
                  {hasImage && (
                    <div className="absolute top-2 right-2 bg-green-500/90 px-2 py-1 rounded flex items-center gap-1 text-xs font-bold">
                      <Check className="w-3 h-3" />
                      Complete
                    </div>
                  )}
                </div>

                {/* Prompt (collapsible) */}
                <div className="p-3 bg-slate-800/50">
                  <button
                    onClick={() => setExpandedScene(isExpanded ? null : scene.id)}
                    className="w-full flex items-center justify-between text-left"
                  >
                    <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                      Prompt
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>

                  {isExpanded && (
                    <motion.p
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="text-slate-300 text-xs mt-2 leading-relaxed"
                    >
                      {scene.visual_prompt}
                    </motion.p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-sm">Overall Progress</span>
            <span className="text-cyan-400 text-sm font-bold">
              {Math.round((scenesWithImages / totalScenes) * 100)}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(scenesWithImages / totalScenes) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-600"
            />
          </div>
        </div>

        {/* Approve button */}
        {allComplete && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-end"
          >
            <button
              onClick={onAllComplete}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-lg font-bold shadow-lg hover:shadow-green-500/25 transition-all"
            >
              <Check className="w-5 h-5" />
              Approve All & Start Video Generation
            </button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
```

#### 2.5 Update `frontend_new/components/OTTWorkflowCanvas.tsx`

**Modify to integrate approval workflow:**

```typescript
// Add imports at top (around line 10)
import StrategyReviewCard from './StrategyReviewCard';
import ImageGenerationPanel from './ImageGenerationPanel';

// Inside the component (around line 14)
export default function OTTWorkflowCanvas() {
    const { startGeneration, isLoading, project, currentStep, approveStrategy, approveImages, approveVideos } = useStore();

    // ... existing state ...

    // MODIFY handleLaunch to NOT auto-start generation
    const handleLaunch = async () => {
        if (!config.topic.trim()) return;

        // ... existing code to build prompt and config ...

        const fullConfig = {
            ...config,
            uploaded_assets: uploadedFiles,
            uploaded_asset: uploadedFiles[0]
        };

        // Create plan (this will set currentStep to "strategy")
        const project = await useStore.getState().createPlan(prompt, fullConfig);

        // DON'T call startGeneration() anymore!
        // User must approve strategy first
    };

    return (
        <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 pt-8 pb-32">
            {/* Existing header and form ... */}

            {/* ... all existing config form code ... */}

            {/* STRATEGY REVIEW CARD - Shows after plan completes */}
            {project && currentStep !== "input" && (
                <StrategyReviewCard
                    strategy={project.strategy}
                    script={project.script}
                    onApprove={approveStrategy}
                    isVisible={currentStep === "strategy"}
                />
            )}

            {/* IMAGE GENERATION PANEL - Shows after strategy approved */}
            {project && ["images", "videos", "complete"].includes(currentStep) && (
                <ImageGenerationPanel
                    scenes={project.script?.scenes || []}
                    onAllComplete={approveImages}
                    isVisible={true}
                    status={project.status}
                />
            )}

            {/* VIDEO GENERATION PANEL - Can add similar component later */}
            {/* For demo, just show message */}
            {project && currentStep === "videos" && project.status === "videos_complete" && (
                <div className="w-full max-w-4xl mx-auto mb-8 bg-slate-900 border border-cyan-500/30 rounded-2xl p-6">
                    <h3 className="text-cyan-400 font-bold mb-4">Videos Complete!</h3>
                    <button
                        onClick={approveVideos}
                        className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-bold"
                    >
                        Approve & Assemble Final Video
                    </button>
                </div>
            )}

            {/* FINAL RESULT */}
            {project && currentStep === "complete" && project.final_video_path && (
                <div className="w-full max-w-4xl mx-auto mb-8 bg-slate-900 border border-green-500/30 rounded-2xl p-6">
                    <h3 className="text-green-400 font-bold mb-4">Commercial Complete!</h3>
                    <video
                        controls
                        className="w-full rounded-lg"
                        src={api.getAssetUrl(project.final_video_path)}
                    />
                    <div className="mt-4 flex gap-3">
                        <a
                            href={api.getAssetUrl(project.final_video_path)}
                            download
                            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-bold"
                        >
                            Download
                        </a>
                    </div>
                </div>
            )}

            {/* Existing PipelineFlow and TerminalLog ... */}
        </div>
    );
}
```

---

## TESTING REQUIREMENTS

Create test file `tests/test_approval_workflow.py`:

```python
import pytest
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState

def test_stage_based_generation():
    """Test that stage methods stop at correct points"""
    gen = AdGenerator()

    # Step 1: Plan
    result = gen.plan("Test commercial for Botspot AI", config_overrides={})
    assert gen.state.status == "planned"
    assert gen.state.strategy is not None
    assert gen.state.script is not None

    # Step 2: Generate images only
    gen.generate_images_only()
    assert gen.state.status == "images_complete"
    assert all(s.image_path for s in gen.state.script.scenes)
    assert not any(s.video_path for s in gen.state.script.scenes)  # Should NOT have videos yet

    # Step 3: Generate videos only
    gen.generate_videos_only()
    assert gen.state.status == "videos_complete"
    assert all(s.video_path for s in gen.state.script.scenes if s.image_path)
    assert gen.state.final_video_path is None  # Should NOT have final video yet

    # Step 4: Assemble
    gen.assemble_final()
    assert gen.state.status == "completed"
    assert gen.state.final_video_path is not None

def test_error_handling_in_stages():
    """Ensure errors don't crash pipeline"""
    gen = AdGenerator()
    gen.plan("Test ad")

    # Simulate error
    try:
        # This should catch and log errors gracefully
        gen.generate_images_only()
    except Exception as e:
        # Should have error in state
        assert gen.state.status == "failed"
        assert gen.state.error is not None

def test_approval_gate_status_transitions():
    """Test that status values update correctly"""
    gen = AdGenerator()

    assert gen.state.status == "initialized"

    gen.plan("Test")
    assert gen.state.status == "planned"

    gen.generate_images_only()
    assert gen.state.status == "images_complete"

    gen.generate_videos_only()
    assert gen.state.status == "videos_complete"

    gen.assemble_final()
    assert gen.state.status == "completed"
```

---

## CLIENT DEMO SCRIPT

**What to show (2 minute demo):**

1. **Fill Form (10s)**
   - "This is our OTT ad builder"
   - Type: "Commercial for Botspot AI"
   - Show controls: Style=Cinematic, Duration=15s
   - Click "Generate Campaign"

2. **Strategy Review (30s)**
   - Card expands below
   - "Our AI strategist analyzed your request"
   - Read the concept: "Enterprise Control"
   - "Notice the 3-scene breakdown"
   - "See the voiceover script"
   - "This is Claude Opus creating the strategy"
   - Click "Approve"

3. **Image Generation (30s)**
   - Panel expands, images start generating
   - "Watch as images generate in parallel"
   - "See Scene 1... Scene 2... Scene 3"
   - "Progress bar shows 33%... 66%... 100%"
   - Click "Approve All"

4. **Video Generation (30s)**
   - "Now converting images to video"
   - "See the fallback chain: Trying Runway... Success!"
   - Wait for completion
   - Click "Approve"

5. **Final Result (20s)**
   - "Here's your broadcast-ready commercial"
   - Play video
   - "Download or share"

**Total: ~2 minutes**

---

## SUCCESS CRITERIA

After implementation:

✅ User can see AI strategy before any generation starts
✅ User can approve strategy to start image generation
✅ Images appear live as they generate (3x concurrent)
✅ User can approve images to start video generation
✅ Videos generate with fallback chain (Runway→Veo→Kling)
✅ User can approve videos to assemble final commercial
✅ Comprehensive logging at every step
✅ Error handling prevents crashes
✅ Status values transition correctly (planned → generating_images → images_complete → generating_videos → videos_complete → assembling → completed)
✅ Demo takes ~2 minutes with real APIs

---

## DELIVERABLES

1. ✅ Modified `ott_ad_builder/pipeline.py` with 3 new methods
2. ✅ Modified `ott_ad_builder/api.py` with 3 new endpoints
3. ✅ Updated `frontend_new/lib/api.ts` with new types and functions
4. ✅ Updated `frontend_new/lib/store.ts` with workflow state
5. ✅ New `frontend_new/components/StrategyReviewCard.tsx`
6. ✅ New `frontend_new/components/ImageGenerationPanel.tsx`
7. ✅ Updated `frontend_new/components/OTTWorkflowCanvas.tsx`
8. ✅ Test file `tests/test_approval_workflow.py`

---

## IMPORTANT NOTES

- Keep ALL existing code intact
- Only ADD new methods, don't modify existing `resume()` method
- Copy exact code from existing `resume()` into new stage methods
- Use existing `parallel_utils.py` for parallel generation
- Maintain all error handling and logging patterns
- Status values are critical for workflow progression
- Frontend polls `/status` every 3 seconds to get updates
- Background tasks run async, frontend must poll to see progress

---

## START HERE

Begin with backend:
1. Add 3 methods to `pipeline.py`
2. Add 3 endpoints to `api.py`
3. Test with curl/Postman to verify stages work

Then frontend:
4. Update store.ts with workflow state
5. Create StrategyReviewCard component
6. Create ImageGenerationPanel component
7. Update OTTWorkflowCanvas to show components

Finally:
8. Test end-to-end
9. Practice demo script
10. Polish animations

**Estimated time: 3-4 hours total**

Good luck! 🚀
