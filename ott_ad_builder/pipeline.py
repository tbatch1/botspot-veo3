import json
import os
from .state import ProjectState
from .providers.gemini import GeminiProvider
from .providers.researcher import ResearcherProvider
from .providers.compliance import ComplianceProvider
from .config import config

class AdGenerator:
    """The Orchestrator."""
    
    def __init__(self, project_id: str = None):
        if project_id:
            self.state = ProjectState(id=project_id, user_input="")
        else:
            self.state = ProjectState(user_input="")
        self.llm = GeminiProvider()
        self.researcher = ResearcherProvider()
        self.compliance = ComplianceProvider()
        
    def _get_plan_path(self):
        return os.path.join(config.OUTPUT_DIR, f"plan_{self.state.id}.json")

    def plan(self, user_input: str) -> dict:
        """
        Phase 2: The Brain.
        Generates the plan and saves it to plan_{id}.json.
        """
        self.state.user_input = user_input
        self.state.update_status("planning")
        
        # Phase 1.5: Research (if URL)
        context = user_input
        industry = "General"
        
        if user_input.startswith("http"):
            print(f"[URL] Detected. Launching Researcher...")
            brief = self.researcher.fetch_and_analyze(user_input)
            print(f"[RESEARCH] Brief:\n{brief}")
            context = brief
            # Simple heuristic to extract industry from brief for compliance
            if "Industry:" in brief:
                try:
                    industry = brief.split("Industry:")[1].split("\n")[0].strip()
                except:
                    pass

        print(f"[BRAIN] Brainstorming ad concept...")
        
        # Call Gemini
        script = self.llm.generate_plan(context)
        
        # Phase 2.5: Compliance Check
        script = self.compliance.review(script, industry=industry)
        
        self.state.script = script
        
        # Save to plan_{id}.json
        plan_path = self._get_plan_path()
        with open(plan_path, "w") as f:
            f.write(self.state.model_dump_json(indent=2))

        self.state.update_status("planned")
        print(f"[SUCCESS] Plan generated and saved to: {plan_path}")

        return self.state.model_dump()

    def resume(self, project_id: str = None):
        """
        Phase 3-6: Execution.
        Loads plan_{id}.json and executes the full pipeline.
        """
        if project_id:
            self.state.id = project_id
            
        plan_path = self._get_plan_path()
        if not os.path.exists(plan_path):
            print(f"[ERROR] No plan found at {plan_path}")
            return

        print(f"[LOAD] Loading plan from: {plan_path}")
        with open(plan_path, "r") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        print(f"[RESUME] Resuming project: {self.state.user_input}")

        try:
            # --- Phase 3: Assets ---
            print("\n[PHASE 3] Generating Assets...")
            # Use real providers for production
            from .providers.imagen import ImagenProvider
            from .providers.elevenlabs import ElevenLabsProvider
            from .providers.mock import MockElevenLabsProvider
            from .providers.composition import CompositionProvider

            imagen = ImagenProvider()  # Real Imagen 4 (Nano Banana Pro)

            # Use real ElevenLabs if API key configured, otherwise use mock
            try:
                if config.ELEVENLABS_API_KEY and config.ELEVENLABS_API_KEY != "mock_elevenlabs_key":
                    eleven = ElevenLabsProvider()  # Real ElevenLabs for voice/SFX
                    print("   Using ElevenLabs for audio generation")
                else:
                    eleven = MockElevenLabsProvider()  # Mock audio (for testing)
                    print("   Using Mock audio provider (ElevenLabs API key not configured)")
            except Exception as e:
                print(f"   ⚠️ ElevenLabs init failed, using mock: {e}")
                eleven = MockElevenLabsProvider()

            composer_tool = CompositionProvider()

            # Visuals
            for i, scene in enumerate(self.state.script.scenes):
                if not scene.image_path:
                    print(f"   Generating Image for Scene {scene.id}...")
                    try:
                        if scene.composition_sources:
                            print(f"   [COMPOSE] Composing scene from {len(scene.composition_sources)} sources...")
                            scene.image_path = composer_tool.compose(scene.composition_sources, scene.visual_prompt)
                        else:
                            scene.image_path = imagen.generate_image(scene.visual_prompt)
                    except Exception as e:
                        print(f"   [ERROR] Image Gen Failed: {e}")

            # Audio (VO)
            for i, line in enumerate(self.state.script.lines):
                if not line.audio_path:
                    print(f"   Generating VO for Line {i+1}...")
                    try:
                        # Dynamic voice selection could happen here
                        line.audio_path = eleven.generate_speech(line.text)
                    except Exception as e:
                        print(f"   [ERROR] VO Gen Failed: {e}")

            # Audio (SFX)
            for i, scene in enumerate(self.state.script.scenes):
                if not scene.sfx_path and scene.audio_prompt:
                    print(f"   Generating SFX for Scene {scene.id}...")
                    try:
                        scene.sfx_path = eleven.generate_sfx(scene.audio_prompt)
                    except Exception as e:
                        print(f"   [ERROR] SFX Gen Failed: {e}")

            self.save_state()

            # --- Phase 4: Motion ---
            print(f"\n[PHASE 4] Motion Synthesis ({self.state.video_model})...")
            # Import both Veo and Runway providers
            from .providers.video_google import GoogleVideoProvider
            from .providers.runway import RunwayProvider

            veo = GoogleVideoProvider()  # Real Vertex AI Veo with native audio
            runway = RunwayProvider()  # Runway Gen-3 Turbo for immediate video generation

            for i, scene in enumerate(self.state.script.scenes):
                if scene.image_path and not scene.video_path:
                    print(f"   Animating Scene {scene.id}...")
                    try:
                        if self.state.video_model == "veo":
                            scene.video_path = veo.generate_video(scene.motion_prompt, scene.image_path)
                        else:
                            scene.video_path = runway.animate(scene.image_path, scene.motion_prompt)
                    except Exception as e:
                        print(f"   [ERROR] Animation Failed: {e}")
                        # Fallback logic could go here

            self.save_state()

            # --- Phase 5: Assembly ---
            print("\n[PHASE 5] Final Assembly...")
            from .providers.composer import Composer
            composer = Composer()

            final_path = composer.compose(self.state)
            self.state.final_video_path = final_path
            self.state.status = "completed"
            self.save_state()
            print(f"\n[DONE] Video saved to: {final_path}")

        except Exception as e:
            # Top-level error handler - catches any uncaught exceptions
            error_msg = f"Generation failed: {str(e)}"
            print(f"\n[ERROR] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise  # Re-raise so background task wrapper can catch it

    def save_state(self):
        plan_path = self._get_plan_path()
        with open(plan_path, "w") as f:
            f.write(self.state.model_dump_json(indent=2))
