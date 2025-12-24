from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .pipeline import AdGenerator
from .state import ProjectState, Script
import os
import sys
import json
import time
from .config import config
from pathlib import Path
import requests
from fastapi import Query

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except Exception:
        pass  # Silently fail if unable to set encoding

app = FastAPI(title="OTT Ad Builder API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    user_input: str
    config_overrides: Optional[dict] = None  # UI config: {style, duration, platform, mood}

class GenerateRequest(BaseModel):
    project_id: str
    script: Script # User might have edited the script

class RegenerateSceneRequest(BaseModel):
    project_id: str
    scene_id: int
    new_prompt: Optional[str] = None


class RemixVoiceoverRequest(BaseModel):
    project_id: str
    script: Script
    regenerate_all: bool = False
    include_sfx: bool = False
    include_bgm: bool = False
    bgm_prompt: Optional[str] = None
    speaker_voice_map: Optional[Dict[str, str]] = None


class VoiceLibraryAddRequest(BaseModel):
    public_owner_id: str
    voice_id: str
    new_name: str


class ElevenLabsPreviewRequest(BaseModel):
    voice_id: str
    text: str
    model_id: Optional[str] = None


class TtsPreviewRequest(BaseModel):
    voice_id: str
    text: str

def run_generation_with_error_handling(generator: AdGenerator):
    """Wrapper to catch and store errors from background generation tasks."""
    try:
        generator.resume()
    except Exception as e:
        # Update state to failed and save error message
        error_msg = f"Generation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        generator.state.status = "failed"
        generator.state.error = error_msg
        generator.save_state()


def run_audio_remix_with_error_handling(generator: AdGenerator, request: RemixVoiceoverRequest):
    """Wrapper for audio-only remix (VO + optional SFX/BGM + optional re-assembly) with error handling."""
    try:
        generator.remix_audio_only(
            script=request.script,
            regenerate_all=bool(request.regenerate_all),
            include_sfx=bool(request.include_sfx),
            include_bgm=bool(request.include_bgm),
            bgm_prompt=(request.bgm_prompt or "").strip() or None,
            speaker_voice_map=request.speaker_voice_map,
        )
    except Exception as e:
        error_msg = f"Audio remix failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        generator.state.status = "failed"
        generator.state.error = error_msg
        generator.save_state()

from fastapi import File, UploadFile, Form
import shutil

@app.post("/api/upload")
async def upload_asset(
    file: UploadFile = File(...),
    mode: str = Form("reference")  # "reference" or "direct"
):
    """Handle file uploads for the asset drop zone.

    Args:
        file: The uploaded file
        mode: "reference" (use as I2I style input) or "direct" (use as scene image directly)
    """
    try:
        # Create user_uploads directory if it doesn't exist
        upload_dir = os.path.join(config.ASSETS_DIR, "user_uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # Save the file
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        return {
            "status": "success",
            "filename": file.filename,
            "mode": mode,
            "url": f"/api/assets/user_uploads/{file.filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateSceneSourceRequest(BaseModel):
    project_id: str
    scene_id: int
    image_source: str  # "ai" or "upload:{filename}"


@app.post("/api/scene/source")
async def update_scene_source(request: UpdateSceneSourceRequest):
    """Update a scene's image source (AI or uploaded file)."""
    try:
        # Load project state
        plan_path = os.path.join(config.OUTPUT_DIR, request.project_id, "plan.json")
        if not os.path.exists(plan_path):
            raise HTTPException(status_code=404, detail="Project not found")

        with open(plan_path, "r") as f:
            state_data = json.load(f)

        state = ProjectState(**state_data)

        # Find and update the scene
        scene_found = False
        for scene in state.script.scenes:
            if scene.id == request.scene_id:
                scene.image_source = request.image_source
                scene_found = True

                # If switching to uploaded file, copy it to image_path
                if request.image_source.startswith("upload:"):
                    filename = request.image_source.replace("upload:", "")
                    source_path = os.path.join(config.ASSETS_DIR, "user_uploads", filename)
                    if os.path.exists(source_path):
                        dest_path = os.path.join(config.ASSETS_DIR, "images", f"scene_{scene.id}_{filename}")
                        shutil.copy2(source_path, dest_path)
                        scene.image_path = dest_path
                break

        if not scene_found:
            raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")

        # Save updated state
        with open(plan_path, "w") as f:
            json.dump(state.model_dump(), f, indent=2)

        return {"status": "success", "scene_id": request.scene_id, "image_source": request.image_source}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/uploads/{project_id}")
async def list_uploads(project_id: str):
    """List uploaded files for a project."""
    try:
        # Load project state
        plan_path = os.path.join(config.OUTPUT_DIR, project_id, "plan.json")
        if not os.path.exists(plan_path):
            raise HTTPException(status_code=404, detail="Project not found")

        with open(plan_path, "r") as f:
            state_data = json.load(f)

        state = ProjectState(**state_data)

        # Return v2 uploads if available, otherwise convert legacy
        if state.uploaded_assets_v2:
            uploads = [{"filename": a.filename, "mode": a.mode} for a in state.uploaded_assets_v2]
        elif state.uploaded_assets:
            uploads = [{"filename": f, "mode": "reference"} for f in state.uploaded_assets]
        else:
            uploads = []

        return {"status": "success", "uploads": uploads}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """
    Step 1: Generate the cinematic plan.

    Accepts config_overrides from UI with professional cinematography options:
    - style: List of visual styles ["Cinematic", "Analog Film", "Cyberpunk", "3D Render"]
    - duration: Video duration "8s", "15s", "30s"
    - platform: Target platform "Netflix", "Hulu", "YouTube", "Instagram"
    - mood: Creative mood "Premium", "Authentic", "Bold", "Aspirational"
    """
    print(f"\\n[API] Received Plan Request: {request.user_input}")
    print(f"[API] Config Overrides: {request.config_overrides}")
    try:
        generator = AdGenerator()
        state_dict = generator.plan(request.user_input, config_overrides=request.config_overrides)
        print("[API] Plan Generation Successful")
        return state_dict
    except Exception as e:
        # Safe error handling for Windows encoding issues
        try:
            error_msg = str(e)
        except (UnicodeEncodeError, UnicodeDecodeError):
            error_msg = "Planning failed due to encoding error"
        print(f"[API] Plan Generation Failed: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Step 2: Start asset generation and assembly (Async)."""
    print(f"\\n[API] Received Generation Request for Project: {request.project_id}")
    
    # 1. Update state with user edits
    generator = AdGenerator(project_id=request.project_id)
    
    # Load existing state to preserve other fields
    plan_path = generator._get_plan_path()
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            generator.state = ProjectState(**data)
    
    # Apply updates
    generator.state.script = request.script
    generator.state.status = "processing"
    generator.save_state()
    
    # 2. Run in background with error handling
    background_tasks.add_task(run_generation_with_error_handling, generator)

    return {"status": "started", "project_id": request.project_id}

# ========================================================================================
# APPROVAL WORKFLOW: Stage-Based API Endpoints for Client Demo
# ========================================================================================
# These endpoints allow the frontend to control generation in stages with approval gates
# ========================================================================================

def run_image_generation_with_error_handling(generator: AdGenerator):
    """Wrapper for image generation stage with error handling."""
    try:
        generator.generate_images_only()
    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        generator.state.status = "failed"
        generator.state.error = error_msg
        generator.save_state()

def run_video_generation_with_error_handling(generator: AdGenerator):
    """Wrapper for video generation stage with error handling."""
    try:
        generator.generate_videos_only()
    except Exception as e:
        error_msg = f"Video generation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        generator.state.status = "failed"
        generator.state.error = error_msg
        generator.save_state()

def run_assembly_with_error_handling(generator: AdGenerator):
    """Wrapper for final assembly stage with error handling."""
    try:
        generator.assemble_final()
    except Exception as e:
        error_msg = f"Assembly failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        generator.state.status = "failed"
        generator.state.error = error_msg
        generator.save_state()

@app.post("/api/generate/images")
async def generate_images_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    APPROVAL GATE 1: Generate images and audio, then STOP.
    Status will be set to 'images_complete' when done.
    Frontend should poll /api/status and show approval UI.
    """
    print(f"\n[API] APPROVAL_GATE_1: Starting image generation for Project: {request.project_id}")

    # Load existing state
    generator = AdGenerator(project_id=request.project_id)
    plan_path = generator._get_plan_path()

    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate status
    if generator.state.status not in ["planned", "images_complete"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status for image generation. Expected 'planned', got '{generator.state.status}'"
        )

    # Apply any script edits from frontend
    generator.state.script = request.script
    generator.state.status = "generating_images"
    generator.save_state()

    # Run in background
    background_tasks.add_task(run_image_generation_with_error_handling, generator)

    return {"status": "started", "project_id": request.project_id, "stage": "images"}

@app.post("/api/generate/videos")
async def generate_videos_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    APPROVAL GATE 2: Generate videos from existing images, then STOP.
    Status will be set to 'videos_complete' when done.
    Frontend should poll /api/status and show approval UI.
    """
    print(f"\n[API] APPROVAL_GATE_2: Starting video generation for Project: {request.project_id}")

    # Load existing state
    generator = AdGenerator(project_id=request.project_id)
    plan_path = generator._get_plan_path()

    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate status
    if generator.state.status not in ["images_complete", "videos_complete"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status for video generation. Expected 'images_complete', got '{generator.state.status}'"
        )

    # Apply any script edits (user might have regenerated specific images)
    generator.state.script = request.script
    generator.state.status = "generating_videos"
    generator.save_state()

    # Run in background
    background_tasks.add_task(run_video_generation_with_error_handling, generator)

    return {"status": "started", "project_id": request.project_id, "stage": "videos"}

@app.post("/api/generate/assemble")
async def assemble_final_stage(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    APPROVAL GATE 3: Assemble final video from existing clips.
    Status will be set to 'completed' when done.
    """
    print(f"\n[API] APPROVAL_GATE_3: Starting final assembly for Project: {request.project_id}")

    # Load existing state
    generator = AdGenerator(project_id=request.project_id)
    plan_path = generator._get_plan_path()

    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Validate status
    if generator.state.status not in ["videos_complete", "assembling", "completed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status for assembly. Expected 'videos_complete', got '{generator.state.status}'"
        )

    # Apply any final edits
    generator.state.script = request.script
    generator.state.status = "assembling"
    generator.save_state()

    # Run in background
    background_tasks.add_task(run_assembly_with_error_handling, generator)

    return {"status": "started", "project_id": request.project_id, "stage": "assembly"}


class RegenerateSceneRequest(BaseModel):
    project_id: str
    scene_id: int
    new_prompt: Optional[str] = None


@app.post("/api/regenerate/scene")
async def regenerate_scene(request: RegenerateSceneRequest, background_tasks: BackgroundTasks):
    """
    Regenerate a single scene's image with optional new prompt.
    Useful when one image doesn't look right and user wants to retry.
    """
    print(f"\n[API] Regenerating Scene {request.scene_id} for Project: {request.project_id}")

    # Load existing state
    generator = AdGenerator(project_id=request.project_id)
    plan_path = generator._get_plan_path()

    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    # Find the scene
    scene_idx = None
    for i, scene in enumerate(generator.state.script.scenes):
        if scene.id == request.scene_id:
            scene_idx = i
            break

    if scene_idx is None:
        raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")

    # Update prompt if provided
    if request.new_prompt:
        generator.state.script.scenes[scene_idx].visual_prompt = request.new_prompt
        generator.state.add_log(f"[REGENERATE] Scene {request.scene_id} prompt updated")

    # Clear the existing image path to trigger regeneration
    generator.state.script.scenes[scene_idx].image_path = None
    generator.state.add_log(f"[REGENERATE] Scene {request.scene_id} image regeneration started")
    generator.save_state()

    async def regenerate_single_scene():
        try:
            from .providers.fal_flux import FalFluxProvider
            
            scene = generator.state.script.scenes[scene_idx]
            flux = FalFluxProvider()
            
            print(f"   [REGENERATE] Generating new image for Scene {scene.id}...")
            image_path = flux.generate_image(scene.visual_prompt)
            
            if image_path:
                generator.state.script.scenes[scene_idx].image_path = image_path
                generator.state.add_log(f"[REGENERATE] Scene {scene.id} new image generated")
            else:
                generator.state.add_log(f"[ERROR] Scene {scene.id} regeneration failed")
            
            generator.save_state()
        except Exception as e:
            generator.state.add_log(f"[ERROR] Regeneration failed: {str(e)[:50]}")
            generator.save_state()

    # Run in background
    background_tasks.add_task(regenerate_single_scene)

    return {"status": "regenerating", "project_id": request.project_id, "scene_id": request.scene_id}


@app.get("/api/elevenlabs/voices")
async def list_elevenlabs_voices():
    """
    Return available ElevenLabs voices for the configured account.
    Used by the UI for voice dropdowns.
    """
    api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")

    try:
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse ElevenLabs voices: {str(e)}")

    voices = data.get("voices", []) if isinstance(data, dict) else []
    cleaned: list[dict[str, Any]] = []
    for v in voices if isinstance(voices, list) else []:
        if not isinstance(v, dict):
            continue
        cleaned.append(
            {
                "voice_id": v.get("voice_id"),
                "name": v.get("name"),
                "category": v.get("category"),
                "description": v.get("description"),
                "labels": v.get("labels") if isinstance(v.get("labels"), dict) else {},
                "preview_url": v.get("preview_url"),
            }
        )

    return {"voices": cleaned}


@app.get("/api/elevenlabs/voice_library")
async def search_elevenlabs_voice_library(
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    age: Optional[str] = Query(default=None),
    accent: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    locale: Optional[str] = Query(default=None),
    use_case: Optional[str] = Query(default=None),
    featured: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
):
    """
    Search/browse ElevenLabs Voice Library (shared voices) so users can add many accents/tones.
    """
    api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)
        resp = client.voices.get_shared(
            page_size=page_size,
            category=category,
            gender=gender,
            age=age,
            accent=accent,
            language=language,
            locale=locale,
            search=search,
            use_cases=use_case,
            featured=featured,
            page=page,
        )

        payload = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()  # type: ignore[no-any-return]
        voices = payload.get("voices") if isinstance(payload, dict) else None
        if not isinstance(voices, list):
            raise RuntimeError("Unexpected voice library response format")

        cleaned = []
        for v in voices:
            if not isinstance(v, dict):
                continue
            cleaned.append(
                {
                    "public_owner_id": v.get("public_owner_id"),
                    "voice_id": v.get("voice_id"),
                    "name": v.get("name"),
                    "accent": v.get("accent"),
                    "gender": v.get("gender"),
                    "age": v.get("age"),
                    "descriptive": v.get("descriptive"),
                    "use_case": v.get("use_case"),
                    "category": v.get("category"),
                    "language": v.get("language"),
                    "locale": v.get("locale"),
                    "description": v.get("description"),
                    "preview_url": v.get("preview_url"),
                    "free_users_allowed": v.get("free_users_allowed"),
                    "featured": v.get("featured"),
                    "is_added_by_user": v.get("is_added_by_user"),
                }
            )

        return {
            "voices": cleaned,
            "has_more": bool(payload.get("has_more")) if isinstance(payload, dict) else False,
            "last_sort_id": payload.get("last_sort_id") if isinstance(payload, dict) else None,
            "page": page,
            "page_size": page_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs voice library failed: {str(e)}")


@app.post("/api/elevenlabs/voice_library/add")
async def add_elevenlabs_voice_from_library(request: VoiceLibraryAddRequest):
    """
    Add a shared Voice Library voice to this account (so it appears in /api/elevenlabs/voices).
    """
    api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")

    public_owner_id = str(request.public_owner_id or "").strip()
    voice_id = str(request.voice_id or "").strip()
    new_name = str(request.new_name or "").strip()
    if not public_owner_id or not voice_id or not new_name:
        raise HTTPException(status_code=400, detail="public_owner_id, voice_id, and new_name are required")

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)
        added = client.voices.share(public_user_id=public_owner_id, voice_id=voice_id, new_name=new_name)
        voice_id_out = getattr(added, "voice_id", None)
        return {"status": "success", "voice_id": voice_id_out or voice_id}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs add voice failed: {str(e)}")


@app.post("/api/elevenlabs/tts_preview")
async def elevenlabs_tts_preview(request: ElevenLabsPreviewRequest):
    """
    Generate a short TTS preview clip for a given voice_id and text.
    Used by UI to audition voices with *your actual line*, not just ElevenLabs' preview samples.
    """
    voice_id = str(request.voice_id or "").strip()
    text = str(request.text or "").strip()
    if not voice_id or not text:
        raise HTTPException(status_code=400, detail="voice_id and text are required")

    # Optional per-request model override.
    model_id = (request.model_id or "").strip()
    old_model = os.getenv("ELEVENLABS_MODEL")
    if model_id:
        os.environ["ELEVENLABS_MODEL"] = model_id

    try:
        # Accept ElevenLabs voices, `openai:` and `sapi:` prefixes
        # so the frontend can audition different voices.
        from starlette.concurrency import run_in_threadpool
        from .providers.elevenlabs import ElevenLabsProvider
        from .providers.tts_router import TTSRouterProvider

        eleven = ElevenLabsProvider()
        tts = TTSRouterProvider(eleven=eleven)
        audio_path = await run_in_threadpool(tts.generate_speech, text, voice_id, file_prefix="preview")
        # Return as a bare filename so frontend `getAssetUrl()` keeps working.
        filename = os.path.basename(audio_path)
        return {"audio_path": filename}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS preview failed: {str(e)}")
    finally:
        # Restore env to avoid cross-request bleed.
        if model_id:
            if old_model is None:
                os.environ.pop("ELEVENLABS_MODEL", None)
            else:
                os.environ["ELEVENLABS_MODEL"] = old_model


_SAPI_VOICE_CACHE: dict[str, Any] = {"ts": 0.0, "voices": []}


@app.get("/api/voices")
async def list_all_voices(
    provider: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    locale: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    limit: int = Query(default=300, ge=1, le=2000),
):
    """
    Unified voice catalog for the Studio:
    - ElevenLabs account voices (if configured)
    - Windows SAPI voices (offline) via System.Speech
    - OpenAI TTS voices (high quality)

    Returns: { voices: [{ provider, voice_id, name, labels, category, preview_url }] }
    """
    wanted = (provider or "").strip().lower()
    query = (q or "").strip().lower()
    locale_q = (locale or "").strip().lower()
    gender_q = (gender or "").strip().lower()

    results: list[dict[str, Any]] = []

    def _matches(name: str, labels: dict[str, Any]) -> bool:
        if query and query not in (name or "").lower():
            # allow search by locale/gender keywords too
            hay = " ".join([name or "", str(labels.get("locale") or ""), str(labels.get("gender") or "")]).lower()
            if query not in hay:
                return False
        if locale_q and str(labels.get("locale") or "").lower() != locale_q:
            return False
        if gender_q and str(labels.get("gender") or "").lower() != gender_q:
            return False
        return True

    # ElevenLabs voices (account-scoped).
    if not wanted or wanted in ("eleven", "elevenlabs", "11l"):
        api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
        if api_key:
            try:
                resp = requests.get(
                    "https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": api_key},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                voices = data.get("voices", []) if isinstance(data, dict) else []
                for v in voices if isinstance(voices, list) else []:
                    if not isinstance(v, dict):
                        continue
                    vid = str(v.get("voice_id") or "").strip()
                    name = str(v.get("name") or "").strip()
                    labels = v.get("labels") if isinstance(v.get("labels"), dict) else {}
                    payload = {
                        "provider": "elevenlabs",
                        "voice_id": vid,
                        "name": name,
                        "category": v.get("category"),
                        "description": v.get("description"),
                        "labels": labels,
                        "preview_url": v.get("preview_url"),
                    }
                    if _matches(name, {"locale": labels.get("language"), "gender": labels.get("gender")}):
                        results.append(payload)
            except Exception:
                pass

    # Windows SAPI voices (offline, small).
    if not wanted or wanted in ("sapi", "windows", "system.speech"):
        try:
            from .providers.sapi_tts import list_sapi_voices

            now = time.time()
            if (now - float(_SAPI_VOICE_CACHE.get("ts") or 0.0)) > 3600 or not _SAPI_VOICE_CACHE.get("voices"):
                voices = list_sapi_voices()
                _SAPI_VOICE_CACHE["voices"] = voices
                _SAPI_VOICE_CACHE["ts"] = now

            voices = _SAPI_VOICE_CACHE.get("voices") or []
            for v in voices if isinstance(voices, list) else []:
                name = str(v.get("name") or "").strip()
                if not name:
                    continue
                labels = {"gender": str(v.get("gender") or "").lower(), "locale": str(v.get("locale") or "")}
                if not _matches(name, labels):
                    continue
                results.append(
                    {
                        "provider": "sapi",
                        "voice_id": f"sapi:{name}",
                        "name": name,
                        "category": "windows",
                        "description": "",
                        "labels": labels,
                        "preview_url": None,
                    }
                )
        except Exception:
            pass

    # OpenAI TTS voices (high quality).
    if not wanted or wanted in ("openai", "oa"):
        try:
            # Current OpenAI speech voices (SDK-level): alloy, ash, ballad, coral, echo, sage, shimmer, verse, marin, cedar.
            for v in ["marin", "verse", "shimmer", "alloy", "sage", "coral", "ash", "echo", "ballad", "cedar"]:
                name = f"{v} (OpenAI)"
                labels = {"gender": "", "locale": ""}
                if _matches(name, labels):
                    results.append(
                        {
                            "provider": "openai",
                            "voice_id": f"openai:{v}",
                            "name": name,
                            "category": "openai-tts",
                            "description": "High-quality neural TTS (paid).",
                            "labels": labels,
                            "preview_url": None,
                        }
                    )
        except Exception:
            pass

    # Cap output size for UI stability.
    return {"voices": results[: int(limit)]}


@app.post("/api/tts_preview")
async def tts_preview(request: TtsPreviewRequest):
    """
    Provider-agnostic audition endpoint.
    Supports `openai:*`, `sapi:*`, or ElevenLabs voice IDs.
    """
    voice_id = str(request.voice_id or "").strip()
    text = str(request.text or "").strip()
    if not voice_id or not text:
        raise HTTPException(status_code=400, detail="voice_id and text are required")

    try:
        from starlette.concurrency import run_in_threadpool
        from .providers.elevenlabs import ElevenLabsProvider
        from .providers.tts_router import TTSRouterProvider

        eleven = ElevenLabsProvider()
        tts = TTSRouterProvider(eleven=eleven)
        audio_path = await run_in_threadpool(tts.generate_speech, text, voice_id, file_prefix="preview")
        return {"audio_path": os.path.basename(audio_path)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS preview failed: {str(e)}")


@app.post("/api/remix/voiceover")
async def remix_voiceover(request: RemixVoiceoverRequest, background_tasks: BackgroundTasks):
    """
    Regenerate VO (and optionally SFX/BGM) and re-assemble the final MP4 without regenerating visuals.

    Works best after videos are generated (videos_complete/completed), but can also be used earlier to
    regenerate VO audio files for preview.
    """
    print(f"\n[API] Remixing voiceover for Project: {request.project_id}")

    generator = AdGenerator(project_id=request.project_id)
    plan_path = generator._get_plan_path()
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")

    # Load existing state so we preserve generated images/videos, BGM, etc.
    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        generator.state = ProjectState(**data)

    generator.state.script = request.script
    generator.state.status = "remixing_audio"
    generator.state.add_log("[AUDIO] Remix started (VO/SFX/BGM + optional re-assembly)")
    generator.save_state()

    background_tasks.add_task(run_audio_remix_with_error_handling, generator, request)
    return {"status": "started", "project_id": request.project_id, "stage": "remix_audio"}

@app.get("/api/status/{project_id}")
async def get_status(project_id: str):
    """Check progress."""
    generator = AdGenerator(project_id=project_id)
    plan_path = generator._get_plan_path()
    
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")
        
    def _safe_run_id(pid: str) -> str:
        import re

        run_id = str(pid or "").strip() or "run"
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", run_id).strip("_-")[:24] or "run"

    def _maybe_repair_final_video_path(data: dict) -> dict:
        import glob

        # Back-compat: old plan files won't have this (frontend can still default).
        if not str(data.get("player_mode") or "").strip():
            data["player_mode"] = "auto"

        final_path = str(data.get("final_video_path") or "").strip()
        base = os.path.basename(final_path) if final_path else ""
        exists = bool(final_path and os.path.exists(final_path))

        # Avoid the global filename (historically overwritten/corrupted by concurrent runs).
        needs_repair = (base.lower() == "final_ad.mp4") or (final_path and not exists)
        if not needs_repair:
            return data

        safe = _safe_run_id(str(data.get("id") or project_id))
        candidates = []
        # Prefer the new per-project output naming.
        direct = os.path.join(config.OUTPUT_DIR, f"final_ad_{safe}.mp4")
        if os.path.exists(direct):
            candidates.append(direct)
        candidates.extend(sorted(glob.glob(os.path.join(config.OUTPUT_DIR, f"final_ad_{safe}*.mp4")), reverse=True))

        # Heuristic fallback: any mp4 that includes the project id prefix.
        pid_prefix = str(data.get("id") or project_id)[:8]
        if pid_prefix:
            candidates.extend(sorted(glob.glob(os.path.join(config.OUTPUT_DIR, f"*{pid_prefix}*.mp4")), reverse=True))

        for cand in candidates:
            if os.path.basename(cand).lower() == "final_ad.mp4":
                continue
            if os.path.exists(cand):
                data["final_video_path"] = cand
                return data

        return data

    with open(plan_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
        if isinstance(data, dict):
            if not str(data.get("player_mode") or "").strip():
                data["player_mode"] = "auto"
            data = _maybe_repair_final_video_path(data)
        return data

@app.api_route("/api/assets/{filepath:path}", methods=["GET", "HEAD"])
async def get_asset(filepath: str, request: Request):
    # Serve static files (simple implementation)
    # In production, use Nginx or a proper static file server
    from fastapi.responses import FileResponse, Response

    def _resolve(rel: str) -> str | None:
        # 1) If a subpath is provided (e.g. audio/..., user_uploads/...), try ASSETS_DIR directly.
        direct_asset = os.path.join(config.ASSETS_DIR, *Path(rel).parts)
        if os.path.exists(direct_asset):
            return direct_asset

        # 2) Back-compat: allow callers to pass only a filename; probe known subfolders.
        name_only = Path(rel).name
        for subdir in ("images", "clips", "audio", "user_uploads"):
            candidate = os.path.join(config.ASSETS_DIR, subdir, name_only)
            if os.path.exists(candidate):
                return candidate

        # 3) Output directory (final renders, intermediates, etc).
        direct_out = os.path.join(config.OUTPUT_DIR, *Path(rel).parts)
        if os.path.exists(direct_out):
            return direct_out

        out_candidate = os.path.join(config.OUTPUT_DIR, name_only)
        if os.path.exists(out_candidate):
            return out_candidate

        return None

    rel = str(filepath or "").replace("\\", "/").lstrip("/")
    if not rel:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Prevent path traversal
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise HTTPException(status_code=400, detail="Invalid asset path")

    resolved = _resolve(rel)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    if request.method == "HEAD":
        import mimetypes
        from email.utils import formatdate

        size = os.path.getsize(resolved)
        mtime = os.path.getmtime(resolved)
        content_type, _ = mimetypes.guess_type(resolved)

        headers = {
            "Content-Length": str(size),
            "Accept-Ranges": "bytes",
            "Last-Modified": formatdate(mtime, usegmt=True),
        }
        if content_type:
            headers["Content-Type"] = content_type

        return Response(status_code=200, headers=headers)

    return FileResponse(resolved)


# ========================================================================================
# SHOWROOM: Auto-updated feed of finished renders + delete controls
# ========================================================================================


@app.get("/api/showroom/manifest")
async def get_showroom_manifest():
    """
    Return the showroom manifest.

    Note: this endpoint exists so the Showroom page can load even before the first render
    (when output/showroom/showcase_manifest.json may not exist yet).
    """
    try:
        from . import showroom as showroom_lib

        data = showroom_lib.load_manifest()
        auto_import = str(os.getenv("SHOWROOM_AUTO_IMPORT_ON_EMPTY") or "1").strip().lower() in ("1", "true", "yes", "on")
        default_packs = (os.getenv("SHOWROOM_IMPORT_PACKS") or "showcase_pack_edge").strip()
        items = data.get("items") if isinstance(data, dict) else None
        if auto_import and (not isinstance(items, list) or len(items) == 0):
            # Best-effort: pull in older generations so the Showroom isn't empty on first open.
            packs = [p.strip() for p in default_packs.split(",") if p.strip()] or None
            showroom_lib.import_existing(packs=packs, include_company_demo=True, include_output_root=False, trim=False, max_items=200)
            data = showroom_lib.load_manifest()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/showroom/item/{item_id}")
async def delete_showroom_item(item_id: str, delete_file: bool = Query(True)):
    """Delete an item from the showroom (and optionally its MP4 file)."""
    try:
        from . import showroom as showroom_lib

        ok = showroom_lib.delete_item(item_id=item_id, delete_file=bool(delete_file))
        if not ok:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "deleted", "id": item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/showroom/import_existing")
async def import_existing_showroom(
    packs: Optional[str] = Query(None, description="Comma-separated pack folder names under output/"),
    include_company_demo: bool = Query(True),
    include_output_root: bool = Query(False),
    trim: bool = Query(False, description="If true, re-encode/trim via ffmpeg; default copies for speed."),
    max_items: int = Query(500),
):
    """Import older generations into the showroom (copies videos into output/showroom)."""
    try:
        from . import showroom as showroom_lib

        pack_list: list[str] | None = None
        if packs:
            pack_list = [p.strip() for p in str(packs).split(",") if p.strip()]
        else:
            default_packs = (os.getenv("SHOWROOM_IMPORT_PACKS") or "showcase_pack_edge").strip()
            pack_list = [p.strip() for p in default_packs.split(",") if p.strip()] or None
        return showroom_lib.import_existing(
            packs=pack_list,
            include_company_demo=bool(include_company_demo),
            include_output_root=bool(include_output_root),
            trim=bool(trim),
            max_items=int(max_items),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/showroom/reset")
async def reset_showroom(delete_files: bool = Query(True)):
    """Clear showroom manifest and (optionally) delete MP4s in output/showroom."""
    try:
        from . import showroom as showroom_lib

        return showroom_lib.reset_showroom(delete_files=bool(delete_files))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/showroom/restore_best_15s")
async def restore_best_15s(
    pack: str = Query("showcase_pack_edge", description="Pack folder under output/ (must include showcase_manifest.json)."),
    delete_files: bool = Query(False, description="If true, delete MP4s in output/showroom before restoring."),
):
    """
    Restore the showroom to the canonical 15s pack, but re-compose each ad using the cached plan audio paths.

    This avoids any paid TTS/video regeneration and produces higher-quality VO (when cached OpenAI/Eleven audio exists).
    """
    try:
        from . import showroom as showroom_lib
        from .providers.composer import Composer

        pack_name = str(pack or "").strip() or "showcase_pack_edge"
        pack_manifest = Path(config.OUTPUT_DIR) / pack_name / "showcase_manifest.json"
        if not pack_manifest.exists():
            raise HTTPException(status_code=404, detail=f"Pack manifest not found: {pack_manifest}")

        showroom_lib.reset_showroom(delete_files=bool(delete_files))

        data = json.loads(pack_manifest.read_text(encoding="utf-8"))
        items = data.get("items")
        if not isinstance(items, list) or not items:
            raise HTTPException(status_code=400, detail=f"Pack manifest has no items: {pack_manifest}")

        category_by_project: dict[str, str] = {}
        for it in items:
            if not isinstance(it, dict):
                continue
            plan_name = str(it.get("plan") or "").strip()
            pid = str(it.get("project_id") or "").strip()
            if not pid and plan_name:
                # Plans are `plan_<project_id>.json`.
                try:
                    pid = plan_name.replace("plan_", "").replace(".json", "")
                except Exception:
                    pid = ""
            cat = str(it.get("category") or "").strip()
            if pid and cat:
                category_by_project[pid] = cat

        audio_dir = Path(config.ASSETS_DIR) / "audio"
        bgm_candidates = sorted(audio_dir.glob("bgm_loop_*_30s.mp3"), key=lambda p: p.name) or sorted(
            audio_dir.glob("bgm_*.mp3"), key=lambda p: p.name
        )

        def _pick_bgm(seed: str) -> str | None:
            if not bgm_candidates:
                return None
            import hashlib

            h = hashlib.md5(seed.encode("utf-8", errors="ignore")).hexdigest()
            idx = int(h[:8], 16) % len(bgm_candidates)
            return str(bgm_candidates[idx])

        def _safe_https(url: str) -> str:
            u = str(url or "").strip()
            if not u:
                return ""
            if u.startswith("http://") or u.startswith("https://"):
                return u
            return f"https://{u.lstrip('/')}"

        cta_variants = [
            "Scan to learn more.",
            "Try it today.",
            "See what’s possible.",
            "Built for busy people.",
        ]

        composer = Composer()

        # Per-ad env overrides (restored after each compose) so the closes/QR aren’t identical across brands.
        env_keys = [
            "ENDCARD_ENABLED",
            "ENDCARD_STYLE",
            "ENDCARD_ACCENT",
            "ENDCARD_SEED",
            "ENDCARD_TITLE",
            "ENDCARD_SUBTITLE",
            "ENDCARD_URL",
            "BGM_VOLUME",
            "VO_VOLUME",
            "BGM_DUCKING",
        ]
        env_backup = {k: os.environ.get(k) for k in env_keys}

        errors: list[dict] = []
        restored: list[dict] = []

        for it in items:
            if not isinstance(it, dict):
                continue

            name = str(it.get("name") or "").strip() or "Render"
            url = str(it.get("url") or "").strip()
            category = str(it.get("category") or "").strip()
            plan_name = str(it.get("plan") or "").strip()
            project_id = None

            try:
                if not plan_name:
                    raise RuntimeError("Missing plan filename in pack manifest item.")

                plan_path = Path(config.OUTPUT_DIR) / plan_name
                if not plan_path.exists():
                    raise FileNotFoundError(f"Missing plan: {plan_path}")

                state = ProjectState.model_validate_json(plan_path.read_text(encoding="utf-8"))
                project_id = str(getattr(state, "id", "") or "") or None

                if not state.script or not state.script.scenes or not state.script.lines:
                    raise RuntimeError("Plan is missing script/scenes/lines.")

                missing_audio = [
                    idx
                    for idx, line in enumerate(state.script.lines)
                    if not getattr(line, "audio_path", None) or not os.path.exists(str(line.audio_path))
                ]
                if missing_audio:
                    raise RuntimeError(f"Missing cached VO audio for line(s): {missing_audio}")

                # Ensure BGM is present (some older plans were generated without it).
                if not getattr(state, "bgm_path", None) or not os.path.exists(str(state.bgm_path)):
                    picked = _pick_bgm(project_id or name)
                    if picked and os.path.exists(picked):
                        state.bgm_path = picked

                # Endcard + QR (uses qrcode in the venv).
                seed = project_id or name
                import hashlib

                cta = cta_variants[int(hashlib.md5(seed.encode("utf-8", errors="ignore")).hexdigest()[:8], 16) % len(cta_variants)]

                os.environ["ENDCARD_ENABLED"] = "1"
                os.environ["ENDCARD_STYLE"] = "auto"
                os.environ["ENDCARD_ACCENT"] = "auto"
                os.environ["ENDCARD_SEED"] = seed
                os.environ["ENDCARD_TITLE"] = name
                os.environ["ENDCARD_SUBTITLE"] = cta
                os.environ["ENDCARD_URL"] = _safe_https(url)
                os.environ["BGM_VOLUME"] = "0.16"
                os.environ["VO_VOLUME"] = "1.0"
                os.environ["BGM_DUCKING"] = "1"

                final_path = composer.compose(state, transition_type=str(getattr(state, "transition_type", "fade") or "fade"))
                item_out = showroom_lib.publish_render(
                    final_video_path=final_path,
                    project_id=project_id,
                    title=name,
                    url=url,
                    category=category,
                    plan_filename=plan_name,
                    trim=False,
                )
                restored.append(item_out)
            except Exception as e:
                errors.append(
                    {
                        "name": name,
                        "project_id": project_id,
                        "plan": plan_name,
                        "error": str(e),
                    }
                )
            finally:
                for k in env_keys:
                    v = env_backup.get(k)
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

        manifest = showroom_lib.load_manifest()
        manifest.setdefault("notes", [])
        try:
            manifest["notes"].insert(0, "Restored best 15s pack (cached VO + endcards).")
        except Exception:
            pass
        if errors:
            manifest.setdefault("errors", [])
            manifest["errors"] = [
                {"key": str(e.get("project_id") or e.get("plan") or e.get("name") or "unknown"), "name": str(e.get("name") or "unknown"), "error": str(e.get("error") or "")}
                for e in errors
            ]

        # Final pass: ensure categories match the pack metadata (some older plans used a generic style label).
        try:
            for it in manifest.get("items") or []:
                if not isinstance(it, dict):
                    continue
                pid = str(it.get("project_id") or "").strip()
                cat = category_by_project.get(pid)
                if cat:
                    it["category"] = cat
        except Exception:
            pass
        showroom_lib.save_manifest(manifest)
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
