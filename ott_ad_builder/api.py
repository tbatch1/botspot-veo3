from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from .pipeline import AdGenerator
from .state import ProjectState, Script
import os
import sys
import json
from .config import config

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

from fastapi import File, UploadFile
import shutil

@app.post("/api/upload")
async def upload_asset(file: UploadFile = File(...)):
    """Handle file uploads for the asset drop zone."""
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
            "url": f"/api/assets/user_uploads/{file.filename}"
        }
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
        with open(plan_path, "r") as f:
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

    with open(plan_path, "r") as f:
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

    with open(plan_path, "r") as f:
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

    with open(plan_path, "r") as f:
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

    with open(plan_path, "r") as f:
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
            image_path = flux.generate(scene.visual_prompt)
            
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

@app.get("/api/status/{project_id}")
async def get_status(project_id: str):
    """Check progress."""
    generator = AdGenerator(project_id=project_id)
    plan_path = generator._get_plan_path()
    
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="Project not found")
        
    with open(plan_path, "r") as f:
        data = json.load(f)
        return data

@app.get("/api/assets/{filename}")
async def get_asset(filename: str):
    # Serve static files (simple implementation)
    # In production, use Nginx or a proper static file server
    from fastapi.responses import FileResponse
    
    # Check images
    img_path = os.path.join(config.ASSETS_DIR, "images", filename)
    if os.path.exists(img_path):
        return FileResponse(img_path)
        
    # Check clips
    clip_path = os.path.join(config.ASSETS_DIR, "clips", filename)
    if os.path.exists(clip_path):
        return FileResponse(clip_path)
        
    # Check output
    out_path = os.path.join(config.OUTPUT_DIR, filename)
    if os.path.exists(out_path):
        return FileResponse(out_path)
        
    raise HTTPException(status_code=404, detail="Asset not found")
