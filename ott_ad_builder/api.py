from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .pipeline import AdGenerator
from .state import ProjectState, Script
import os
import json
from .config import config

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

class GenerateRequest(BaseModel):
    project_id: str
    script: Script # User might have edited the script

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

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """Step 1: Generate the plan."""
    try:
        generator = AdGenerator()
        state_dict = generator.plan(request.user_input)
        return state_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Step 2: Start asset generation and assembly (Async)."""
    
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
