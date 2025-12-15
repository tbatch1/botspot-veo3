import json
import os
import time
from .state import ProjectState
from .providers.gemini import GeminiProvider
from .providers.researcher import ResearcherProvider
from .providers.strategist import StrategistProvider
from .providers.spatial_reasoning import SpatialReasoningProvider
from .providers.compliance import ComplianceProvider
from .providers.nano_banana import NanoBananaProvider
from .config import config
from .parallel_utils import (
    ParallelImageGenerator,
    ParallelAudioGenerator,
    ParallelVideoGenerator,
    CharacterConsistencyExtractor,
    SmartCritiqueCache
)
from .utils.style_detector import StyleDetector

class AdGenerator:
    """The Orchestrator."""
    
    def __init__(self, project_id: str = None):
        if project_id:
            self.state = ProjectState(id=project_id, user_input="")
        else:
            self.state = ProjectState(user_input="")
        self.llm = GeminiProvider()  # Kept for image critiques only
        self.spatial = SpatialReasoningProvider()  # GPT-5.2 for formatting
        self.nano_banana = NanoBananaProvider()  # Nano Banana for content fixes
        self.researcher = ResearcherProvider()
        self.strategist = StrategistProvider()
        self.compliance = ComplianceProvider()
        
    def _get_plan_path(self):
        return os.path.join(config.OUTPUT_DIR, f"plan_{self.state.id}.json")

    def plan(self, user_input: str, config_overrides: dict = None) -> dict:
        """
        Phase 2: The Brain.
        Generates the cinematic plan and saves it to plan_{id}.json.

        Args:
            user_input: User's creative brief or URL
            config_overrides: Optional dict from UI with style, duration, platform, mood, url
                Example: {"style": ["Cinematic"], "url": "http...", "mood": "Premium"}
        """
        self.state.user_input = user_input
        self.state.update_status("planning")
        
        # Ensure config_overrides is always a dict to avoid NoneType errors
        if config_overrides is None:
            config_overrides = {}

        # Phase 1.5: Research (if URL provided in input OR config)
        context = user_input
        industry = "General"
        website_data = ""
        
        # Check for URL in config_overrides first (new UI), then user_input (legacy)
        target_url = config_overrides.get('url') if config_overrides else None
        if not target_url and user_input.startswith("http"):
            target_url = user_input

        if target_url:
            print(f"[URL] Detected: {target_url}. Launching Researcher...")
            self.state.add_log(f"[RESEARCH] Analyzing target URL: {target_url}...")
            brief = self.researcher.fetch_and_analyze(target_url)
            print(f"[RESEARCH] Brief:\n{brief[:500]}...")
            self.state.add_log(f"[RESEARCH] Site analysis complete. Extracted {len(brief)} chars of context.")
            context = brief
            website_data = brief
            # Simple heuristic to extract industry from brief for compliance
            if "Industry:" in brief:
                try:
                    industry = brief.split("Industry:")[1].split("\n")[0].strip()
                except:
                    pass
            
            # Save brief to state
            self.state.research_brief = brief

        print(f"[BRAIN] Brainstorming cinematic ad concept...")
        self.state.add_log(f"[STRATEGY] Initializing creative brainstorm for: {user_input}")

        target_duration = config_overrides.get('duration', 30) if config_overrides else 30
        script_data = None
        strategy = None
        
        # NEW: Try GPT-5.2 unified creative direction first (replaces Claude + GPT handoff)
        if self.spatial.is_available():
            self.state.add_log(f"[GPT-5.2] Running full creative direction...")
            try:
                strategy, script_data = self.spatial.full_creative_direction(
                    topic=user_input,
                    website_data=website_data,
                    constraints=config_overrides or {},
                    target_duration=target_duration
                )
                scene_count = len(script_data.get('scenes', []))
                self.state.add_log(f"[GPT-5.2] Created strategy + {scene_count} scenes in one pass")
                
                # Validate
                if scene_count == 0:
                    print("[WARNING] GPT-5.2 returned 0 scenes. Falling back to Claude.")
                    self.state.add_log("[WARNING] GPT-5.2 returned 0 scenes. Using Claude fallback...")
                    strategy = None
                    script_data = None
                else:
                    # Save strategy to state
                    self.state.strategy = strategy
            except Exception as e:
                print(f"[ERROR] GPT-5.2 full creative failed: {e}. Falling back to Claude.")
                self.state.add_log(f"[ERROR] GPT-5.2 failed: {str(e)}. Using Claude fallback...")
                strategy = None
                script_data = None
        
        # Fallback to Claude Strategist + GPT Formatter (old flow)
        if strategy is None or script_data is None:
            self.state.add_log(f"[CLAUDE] Using Claude strategist (legacy flow)...")
            strategy = self.strategist.develop_strategy(
                topic=user_input,
                website_data=website_data,
                constraints=config_overrides or {}
            )
            self.state.add_log(f"[STRATEGY] Strategic angle developed: {strategy.get('angle', 'N/A')}")
            
            # Format with GPT-5.2 or fallback
            if self.spatial.is_available():
                try:
                    script_data = self.spatial.format_claude_scenes(
                        strategy=strategy,
                        target_duration=target_duration
                    )
                    scene_count = len(script_data.get('scenes', []))
                    self.state.add_log(f"[GPT-5.2] Formatted {scene_count} scenes with spatial specs.")
                    
                    # VALIDATION: Check if GPT-5.2 returned empty scenes
                    if scene_count == 0:
                        print("[WARNING] GPT-5.2 returned 0 scenes. Falling back to Gemini.")
                        self.state.add_log("[WARNING] GPT-5.2 returned 0 scenes. Falling back to Gemini...")
                        script_data = None  # Force fallback
                        
                except Exception as e:
                    print(f"[ERROR] GPT-5.2 formatting failed: {e}. Falling back to Gemini.")
                    self.state.add_log(f"[ERROR] GPT-5.2 failed: {str(e)}. Using Gemini fallback...")
                    script_data = None  # Force fallback
            
            # Save strategy to state for Claude path
            self.state.strategy = strategy
        
        # Fallback to Gemini if GPT-5.2 unavailable, failed, or returned empty
        if script_data is None or len(script_data.get('scenes', [])) == 0:
            self.state.add_log(f"[GEMINI] Fallback: Generating cinematic screenplay...")
            script_data = self.llm.generate_plan(
                user_input=user_input, 
                config_overrides=config_overrides,
                strategy=strategy
            )
            self.state.add_log(f"[GEMINI] Screenplay generated with {len(script_data.scenes) if hasattr(script_data, 'scenes') else 0} scenes.")
        
        # Convert dict to Script object if needed
        from .state import Script, Scene, ScriptLine
        if isinstance(script_data, dict):
            scenes = [Scene(**s) if isinstance(s, dict) else s for s in script_data.get('scenes', [])]
            lines = [ScriptLine(**l) if isinstance(l, dict) else l for l in script_data.get('lines', [])]
            script = Script(scenes=scenes, lines=lines)
        else:
            script = script_data

        # Phase 2.5: Compliance Check
        script = self.compliance.review(script, industry=industry)

        self.state.script = script

        # Extract and save frontend cinematography preferences to state
        if config_overrides:
            # Save transition preference for later use in Composer
            if config_overrides.get('transition'):
                # Map frontend transition names to FFmpeg xfade filter names
                transition_map = {
                    "Crossfade": "crossfade",
                    "Fade": "fade",
                    "Wipe": "wipe",
                    "Slide": "slide",
                    "Cut": "cut",
                }
                frontend_transition = config_overrides.get('transition')
                self.state.transition_type = transition_map.get(frontend_transition, "crossfade")

            if config_overrides.get('image_provider'):
                self.state.image_provider = config_overrides.get('image_provider')

            # Save uploaded asset reference
            if config_overrides.get('uploaded_asset'):
                self.state.uploaded_asset = config_overrides.get('uploaded_asset')
            
            # Save multiple uploaded assets
            if config_overrides.get('uploaded_assets'):
                assets = config_overrides.get('uploaded_assets')
                if isinstance(assets, list):
                    self.state.uploaded_assets = assets
                    print(f"[PIPELINE] Received {len(assets)} uploaded assets: {assets}")
                    # Ensure backward compatibility: set primary asset to first one if not set
                    if not self.state.uploaded_asset and len(assets) > 0:
                        self.state.uploaded_asset = assets[0]

        # Apply Strategist Recommendations (if not overridden by User Checkbox)
        if strategy and "production_recommendations" in strategy:
            recs = strategy["production_recommendations"]
            
            # 1. Visual Engine
            if not config_overrides.get('image_provider') and recs.get('visual_engine'):
                rec_engine = recs['visual_engine'].lower()
                if rec_engine in ["flux", "imagen"]:
                    self.state.image_provider = rec_engine
                    print(f"[STRATEGY] Strategist recommends Visual Engine: {rec_engine.upper()}")

            # 2. Video Engine
            if recs.get('video_engine'):
                rec_video = recs['video_engine'].lower()
                if rec_video in ["runway", "veo"]:
                    self.state.video_model = rec_video
                    print(f"[STRATEGY] Strategist recommends Video Engine: {rec_video.upper()}")

        # --- Phase 1.5: Style Detection (ADAPTIVE PROMPTING) ---
        print(f"\n[PHASE 1.5] Style Detection...")
        self.state.add_log("[PHASE 1.5] Detecting creative style intent...")

        detector = StyleDetector()
        style_profile = detector.detect_style(
            user_input=user_input,
            constraints=config_overrides,
            research_brief=self.state.research_brief if self.state.research_brief else None
        )

        self.state.detected_style = style_profile

        # Log detected style for transparency
        aesthetic = style_profile['aesthetic']
        confidence = style_profile['confidence_breakdown']['aesthetic']
        overall_conf = style_profile['confidence']
        print(f"   [STYLE] Detected aesthetic: {aesthetic.upper()} (confidence: {confidence:.0%})")
        print(f"   [STYLE] Overall confidence: {overall_conf:.0%}")
        self.state.add_log(f"[STYLE] Aesthetic detected: {aesthetic} ({confidence:.0%} confidence)")

        if style_profile['format'] != 'standard':
            format_type = style_profile['format']
            print(f"   [STYLE] Format type: {format_type}")
            self.state.add_log(f"[STYLE] Format: {format_type}")

        if style_profile['tone'] != 'professional':
            tone = style_profile['tone']
            print(f"   [STYLE] Tone: {tone}")
            self.state.add_log(f"[STYLE] Tone: {tone}")

        # Update status to planned BEFORE saving
        self.state.update_status("planned")
        self.state.add_log(f"[SYSTEM] PLAN_COMPLETE. Transitioning to Asset Generation Phase.")

        # Save to plan_{id}.json
        plan_path = self._get_plan_path()
        with open(plan_path, "w") as f:
            f.write(self.state.model_dump_json(indent=2))

        print(f"[SUCCESS] Cinematic plan generated and saved to: {plan_path}")

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
            self.state.add_log("[PHASE 3] Starting Asset Generation...")
            # Use real providers for production
            from .providers.imagen import ImagenProvider
            from .providers.flux import FluxProvider
            from .providers.fal_flux import FalFluxProvider
            from .providers.elevenlabs import ElevenLabsProvider
            from .providers.mock import MockElevenLabsProvider
            from .providers.composition import CompositionProvider

            # IMAGE PROVIDER SELECTION (Dec 2025 - Priority Order):
            # 1. Fal.ai Flux 1.1 Pro (Fastest, LoRA support for product lock)
            # 2. Replicate Flux 1.1 Pro (Good fallback)
            # 3. Imagen 4 Ultra (Final fallback)
            image_provider = None
            
            if config.FAL_API_KEY and config.FAL_API_KEY != "":
                print("   [VISUALS] Using Fal.ai Flux 1.1 Pro (Primary - LoRA capable)")
                self.state.add_log("[VISUALS] Fal.ai Flux 1.1 Pro initialized")
                image_provider = FalFluxProvider()
            elif config.REPLICATE_API_TOKEN and config.REPLICATE_API_TOKEN != "":
                print("   [VISUALS] Using Replicate Flux 1.1 Pro (Fallback)")
                self.state.add_log("[VISUALS] Replicate Flux 1.1 Pro initialized")
                image_provider = FluxProvider()
            else:
                print("   [VISUALS] No Flux API, using Imagen 4 Ultra (Fallback)")
                self.state.add_log("[VISUALS] Fallback to Imagen 4 Ultra")
                imagen = ImagenProvider()
                image_provider = imagen
                
                # ADAPTIVE PROMPTING: Set aesthetic style on Imagen provider
                if self.state.detected_style:
                    aesthetic = self.state.detected_style['aesthetic']
                    imagen.set_aesthetic_style(aesthetic)
                    print(f"   [ADAPTIVE] Imagen 4 Ultra configured for {aesthetic.upper()} aesthetic")
                    self.state.add_log(f"[ADAPTIVE] Imagen configured: {aesthetic} style")

            # Use real ElevenLabs if API key configured, otherwise use mock
            try:
                if config.ELEVENLABS_API_KEY and config.ELEVENLABS_API_KEY != "mock_elevenlabs_key":
                    eleven = ElevenLabsProvider()  # Real ElevenLabs for voice/SFX
                    print("   Using ElevenLabs for audio generation")
                else:
                    eleven = MockElevenLabsProvider()  # Mock audio (for testing)
                    print("   Using Mock audio provider (ElevenLabs API key not configured)")
            except Exception as e:
                print(f"   [WARN] ElevenLabs init failed, using mock: {e}")
                eleven = MockElevenLabsProvider()

            composer_tool = CompositionProvider()

            # Visuals - PARALLEL GENERATION with Character Consistency
            print(f"\n   [OPTIMIZATION] Using parallel image generation (3x faster)")
            self.state.add_log("[OPTIMIZATION] Parallel image generation enabled")

            # Check for uploaded asset (Image-to-Image)
            uploaded_asset_path = None
            if self.state.uploaded_asset:
                possible_path = os.path.join(config.ASSETS_DIR, "user_uploads", self.state.uploaded_asset)
                if os.path.exists(possible_path):
                    uploaded_asset_path = possible_path
                    print(f"   [VISUALS] Using Uploaded Reference: {self.state.uploaded_asset}")

            # Handle composition scenes separately (can't parallelize easily)
            composition_scenes = [s for s in self.state.script.scenes if s.composition_sources and not s.image_path]
            for scene in composition_scenes:
                print(f"   [COMPOSE] Composing scene {scene.id} from {len(scene.composition_sources)} sources...")
                try:
                    scene.image_path = composer_tool.compose(scene.composition_sources, scene.visual_prompt)
                    self.state.add_log(f"[VISUALS] Composed Scene {scene.id}")
                except Exception as e:
                    print(f"   [ERROR] Composition Failed for Scene {scene.id}: {e}")
                    self.state.add_log(f"[ERROR] Composition Failed for Scene {scene.id}: {str(e)}")

            # Parallel generation for standard scenes (WITH GPT-5.2 + NANO BANANA)
            try:
                start_time = time.time()
                parallel_gen = ParallelImageGenerator(image_provider, self.llm, self.state, self.spatial, self.nano_banana)
                self.state.script.scenes = parallel_gen.generate_parallel(
                    self.state.script.scenes,
                    uploaded_asset_path=uploaded_asset_path,
                    max_workers=5  # Increased from 3 for speed
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Image generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Parallel image generation: {elapsed:.1f}s")

                # Character Consistency Extraction & Injection
                print(f"\n   [OPTIMIZATION] Extracting character consistency...")
                consistency_extractor = CharacterConsistencyExtractor(self.llm)
                self.state.script.scenes = consistency_extractor.inject_consistency_references(
                    self.state.script.scenes
                )
                self.state.add_log("[OPTIMIZATION] Character consistency references injected")

                # NARRATIVE QUALITY GATE (Claude reviews full story coherence)
                if self.state.strategy:
                    print(f"\n   [QUALITY GATE] Claude reviewing narrative coherence...")
                    scene_descriptions = [
                        s.visual_prompt[:100] if hasattr(s, 'visual_prompt') else str(s)[:100]
                        for s in self.state.script.scenes
                    ]
                    scene_dicts = [
                        {"visual_prompt": s.visual_prompt, "id": s.id} 
                        for s in self.state.script.scenes
                    ]
                    coherence = self.strategist.review_narrative_coherence(
                        scenes=scene_dicts,
                        original_strategy=self.state.strategy,
                        generated_descriptions=scene_descriptions
                    )
                    self.state.add_log(f"[NARRATIVE] Coherence score: {coherence.get('score', 'N/A')}/10")
                    
                    # AUTO-REGENERATE: If scenes have issues, regenerate them (WITH LIMITS)
                    if not coherence.get('is_coherent', True):
                        scene_notes = coherence.get('scene_notes', {})
                        flagged_scenes = [
                            (int(k), v) for k, v in scene_notes.items() 
                            if v is not None and v != "null"
                        ]
                        
                        # SAFEGUARDS: Prevent runaway loops
                        MAX_SCENES_TO_REGENERATE = 2  # Never regenerate more than 2 scenes
                        flagged_scenes = flagged_scenes[:MAX_SCENES_TO_REGENERATE]
                        
                        if flagged_scenes:
                            print(f"\n   [AUTO-FIX] Regenerating {len(flagged_scenes)} flagged scene(s) (max {MAX_SCENES_TO_REGENERATE})...")
                            self.state.add_log(f"[AUTO-FIX] Regenerating {len(flagged_scenes)} flagged scenes")
                            
                            for scene_id, issue in flagged_scenes:
                                # Find the scene
                                scene = next((s for s in self.state.script.scenes if s.id == scene_id), None)
                                if not scene:
                                    continue
                                
                                # SAFEGUARD: Only regenerate once per scene
                                if hasattr(scene, '_regenerated') and scene._regenerated:
                                    print(f"   [AUTO-FIX] Scene {scene_id} already regenerated, skipping")
                                    continue
                                
                                print(f"   [AUTO-FIX] Scene {scene_id}: {issue[:60]}...")
                                
                                # Improve the prompt based on Claude's feedback
                                improved_prompt = f"{scene.visual_prompt}. NARRATIVE FIX: {issue}"
                                scene.visual_prompt = improved_prompt
                                
                                # Regenerate the image
                                try:
                                    scene.image_path = image_provider.generate_image(
                                        improved_prompt,
                                        seed=self.state.seed + scene_id + 100  # Different seed
                                    )
                                    scene._regenerated = True  # Mark as regenerated
                                    print(f"   [AUTO-FIX] Scene {scene_id} regenerated ✓")
                                    self.state.add_log(f"[AUTO-FIX] Scene {scene_id} regenerated successfully")
                                except Exception as regen_error:
                                    print(f"   [AUTO-FIX] Scene {scene_id} regeneration failed: {regen_error}")
                                    self.state.add_log(f"[AUTO-FIX] Scene {scene_id} failed: {str(regen_error)}")
                        else:
                            for issue in coherence.get('issues', [])[:2]:
                                self.state.add_log(f"[NARRATIVE] Issue: {issue}")

            except Exception as e:
                print(f"   [ERROR] Parallel image generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel generation failed: {str(e)}")

                # Fallback to sequential generation
                print(f"   [FALLBACK] Switching to sequential generation...")
                self.state.add_log("[FALLBACK] Using sequential image generation")

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

            # Audio - PARALLEL GENERATION (VO, SFX, BGM)
            print(f"\n   [OPTIMIZATION] Using parallel audio generation (3x faster)")
            self.state.add_log("[OPTIMIZATION] Parallel audio generation enabled")

            # Deriving mood from strategy for BGM
            mood_prompt = "Cinematic Ambient"
            if self.state.strategy and 'cinematic_direction' in self.state.strategy:
                mood_notes = self.state.strategy['cinematic_direction'].get('mood_notes', '')
                if mood_notes:
                    mood_prompt = mood_notes

            # Calculate BGM duration
            total_duration = sum(scene.duration for scene in self.state.script.scenes) + 5

            try:
                start_time = time.time()
                parallel_audio = ParallelAudioGenerator(eleven, self.state)
                self.state.bgm_path = parallel_audio.generate_all_audio(
                    self.state.script,
                    bgm_duration=total_duration
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Audio generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Parallel audio generation: {elapsed:.1f}s")

            except Exception as e:
                print(f"   [ERROR] Parallel audio generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel audio failed: {str(e)}")

                # Fallback to sequential generation
                print(f"   [FALLBACK] Switching to sequential audio generation...")
                self.state.add_log("[FALLBACK] Using sequential audio generation")

                # VO
                for i, line in enumerate(self.state.script.lines):
                    if not line.audio_path:
                        try:
                            print(f"   Generating VO for Line {i+1}...")
                            line.audio_path = eleven.generate_speech(line.text)
                        except Exception as e2:
                            print(f"   [ERROR] VO Line {i+1} failed: {e2}")

                # SFX
                for scene in self.state.script.scenes:
                    if not scene.sfx_path and scene.audio_prompt:
                        try:
                            print(f"   Generating SFX for Scene {scene.id}...")
                            scene.sfx_path = eleven.generate_sfx(scene.audio_prompt)
                        except Exception as e2:
                            print(f"   [ERROR] SFX Scene {scene.id} failed: {e2}")

                # BGM
                if not self.state.bgm_path:
                    try:
                        print(f"   Generating BGM...")
                        self.state.bgm_path = eleven.generate_bgm(mood_prompt, duration=total_duration)
                    except Exception as e2:
                        print(f"   [ERROR] BGM failed: {e2}")
            
            self.save_state()

            # --- Phase 4: Motion ---
            print(f"\n[PHASE 4] Motion Synthesis...")
            self.state.add_log(f"[PHASE 4] Starting Motion Synthesis...")

            # Import video providers: Veo 3.1 Ultra (primary) and Runway (fallback)
            from .providers.video_google import GoogleVideoProvider
            from .providers.runway import RunwayProvider

            # Initialize providers - PREMIUM QUALITY MODE
            veo = GoogleVideoProvider()  # Primary: Veo 3.1 Ultra (highest quality, tied #1 in benchmarks)
            runway = RunwayProvider()  # Fallback: Runway Gen-3 Turbo (speed & reliability)

            # ADAPTIVE PROMPTING: Set aesthetic style on Veo provider
            if self.state.detected_style:
                aesthetic = self.state.detected_style['aesthetic']
                veo.set_aesthetic_style(aesthetic)
                print(f"   [ADAPTIVE] Veo 3.1 Ultra configured for {aesthetic.upper()} aesthetic")
                self.state.add_log(f"[ADAPTIVE] Veo configured: {aesthetic} style")

            # PREMIUM QUALITY: Parallel video generation with Veo 3.1 Ultra
            print(f"   [PREMIUM QUALITY] Parallel video generation with Veo 3.1 Ultra")
            self.state.add_log("[PREMIUM QUALITY] Parallel video generation active (Veo 3.1 Ultra + Runway fallback)")

            try:
                start_time = time.time()
                parallel_video = ParallelVideoGenerator(veo, runway, self.state)
                self.state.script.scenes = parallel_video.generate_parallel(
                    self.state.script.scenes,
                    max_workers=3  # Poll up to 3 videos concurrently
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Video generation completed in {elapsed:.1f}s")
            except Exception as e:
                print(f"   [ERROR] Parallel video generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel video generation failed: {str(e)}")
                # Note: ParallelVideoGenerator has internal Runway fallback, so this is a true failure

            self.save_state()

            # --- Phase 5: Assembly ---
            print("\n[PHASE 5] Final Assembly...")
            self.state.add_log("[PHASE 5] Assembling Final Video...")

            # Validate we have video clips before attempting assembly
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
                print(f"   [WARN] {missing_count} scenes failed video generation, proceeding with {len(video_clips)} clips")
                self.state.add_log(f"[WARN] Partial success: {len(video_clips)}/{len(self.state.script.scenes)} scenes")

            try:
                from .providers.composer import Composer
                composer = Composer()

                # Use transition preference from state (set during plan phase)
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

            # --- Phase 6: Mastering (4K Upscale) ---
            # DISABLED for Free Tier (Topaz/Replicate costs money)
            # if config.REPLICATE_API_TOKEN:
            #     print("\n[PHASE 6] Mastering (4K Topaz Upscale)...")
            #     ...
            self.state.add_log("[MASTERING] 4K Upscale Skipped (Free Tier Active).")

            # Print Performance Summary
            print("\n" + "="*80)
            print("PIPELINE COMPLETE - PERFORMANCE SUMMARY")
            print("="*80)

            # Count successes
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
            # Top-level error handler - catches any uncaught exceptions
            error_msg = f"Generation failed: {str(e)}"
            print(f"\n[FATAL ERROR] {error_msg}")
            print(f"[ERROR] Full traceback saved to logs")

            # Add detailed error context to state
            import traceback
            self.state.add_log(f"[FATAL] {error_msg}")
            self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")

            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()

            # Print what succeeded before failure
            print("\n" + "="*80)
            print("PARTIAL RESULTS BEFORE FAILURE")
            print("="*80)
            image_count = len([s for s in self.state.script.scenes if s.image_path])
            video_count = len([s for s in self.state.script.scenes if s.video_path])
            print(f"Images generated: {image_count}/{len(self.state.script.scenes)}")
            print(f"Videos generated: {video_count}/{len(self.state.script.scenes)}")
            print(f"State saved to: {self._get_plan_path()}")
            print("="*80 + "\n")

            raise  # Re-raise so background task wrapper can catch it

    # ========================================================================================
    # APPROVAL WORKFLOW: Stage-Based Methods for Client Demo
    # ========================================================================================
    # These methods split the resume() pipeline into 3 approval gates:
    # 1. generate_images_only() - Creates images + audio, then STOPS
    # 2. generate_videos_only() - Animates videos, then STOPS
    # 3. assemble_final() - Assembles final video
    # ========================================================================================

    def generate_images_only(self, project_id: str = None):
        """
        APPROVAL GATE 1: Generate images and audio, then STOP.
        Sets status to 'images_complete' when done.
        Frontend polls /status and shows approval UI when this status is reached.
        """
        if project_id:
            self.state.id = project_id

        plan_path = self._get_plan_path()
        if not os.path.exists(plan_path):
            error_msg = f"No plan found at {plan_path}"
            print(f"[ERROR] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise FileNotFoundError(error_msg)

        print(f"[LOAD] Loading plan from: {plan_path}")
        with open(plan_path, "r") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        print(f"[APPROVAL_GATE_1] Starting image generation for: {self.state.user_input}")
        self.state.status = "generating_images"
        self.state.add_log("[APPROVAL_GATE_1] User approved strategy. Starting image + audio generation...")
        self.save_state()

        try:
            # --- PHASE 3A: Image + Audio Generation (Copied from resume() lines 189-349) ---
            print("\n[PHASE 3A] Generating Images & Audio...")
            self.state.add_log("[PHASE 3A] Starting Asset Generation...")

            from .providers.imagen import ImagenProvider
            from .providers.flux import FluxProvider
            from .providers.fal_flux import FalFluxProvider
            from .providers.elevenlabs import ElevenLabsProvider
            from .providers.mock import MockElevenLabsProvider
            from .providers.composition import CompositionProvider

            # IMAGE PROVIDER SELECTION (Dec 2025 - Priority Order):
            # 1. Fal.ai Flux 1.1 Pro (Fastest, LoRA support for product lock)
            # 2. Replicate Flux 1.1 Pro (Good fallback)
            # 3. Imagen 4 Ultra (Final fallback)
            image_provider = None
            
            if config.FAL_API_KEY and config.FAL_API_KEY != "":
                print("   [VISUALS] Using Fal.ai Flux 1.1 Pro (Primary - LoRA capable)")
                self.state.add_log("[VISUALS] Fal.ai Flux 1.1 Pro initialized")
                image_provider = FalFluxProvider()
            elif config.REPLICATE_API_TOKEN and config.REPLICATE_API_TOKEN != "":
                print("   [VISUALS] Using Replicate Flux 1.1 Pro (Fallback)")
                self.state.add_log("[VISUALS] Replicate Flux 1.1 Pro initialized")
                image_provider = FluxProvider()
            else:
                print("   [VISUALS] No Flux API, using Imagen 4 Ultra (Fallback)")
                self.state.add_log("[VISUALS] Fallback to Imagen 4 Ultra")
                imagen = ImagenProvider()
                image_provider = imagen

            # Audio provider
            try:
                if config.ELEVENLABS_API_KEY and config.ELEVENLABS_API_KEY != "mock_elevenlabs_key":
                    eleven = ElevenLabsProvider()
                    print("   Using ElevenLabs for audio generation")
                else:
                    eleven = MockElevenLabsProvider()
                    print("   Using Mock audio provider (ElevenLabs API key not configured)")
            except Exception as e:
                print(f"   [WARN] ElevenLabs init failed, using mock: {e}")
                eleven = MockElevenLabsProvider()

            composer_tool = CompositionProvider()

            # Visuals - PARALLEL GENERATION
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
                print(f"   [COMPOSE] Composing scene {scene.id} from {len(scene.composition_sources)} sources...")
                try:
                    scene.image_path = composer_tool.compose(scene.composition_sources, scene.visual_prompt)
                    self.state.add_log(f"[VISUALS] Composed Scene {scene.id}")
                except Exception as e:
                    print(f"   [ERROR] Composition Failed for Scene {scene.id}: {e}")
                    self.state.add_log(f"[ERROR] Composition Failed for Scene {scene.id}: {str(e)}")

            # Parallel generation for standard scenes (WITH GPT-5.2 + NANO BANANA)
            try:
                start_time = time.time()
                parallel_gen = ParallelImageGenerator(image_provider, self.llm, self.state, self.spatial, self.nano_banana)
                self.state.script.scenes = parallel_gen.generate_parallel(
                    self.state.script.scenes,
                    uploaded_asset_path=uploaded_asset_path,
                    max_workers=3
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Image generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Parallel image generation: {elapsed:.1f}s")

                # VALIDATION: Check if ANY images were generated
                succeeded = [s for s in self.state.script.scenes if s.image_path]
                if not succeeded:
                    raise Exception("All scenes failed image generation. Check Fal.ai API key or credits.")
                elif len(succeeded) < len(self.state.script.scenes):
                    print(f"   [WARNING] {len(self.state.script.scenes) - len(succeeded)} scenes failed.")
                    self.state.add_log(f"[WARNING] {len(self.state.script.scenes) - len(succeeded)} scenes failed to generate.")

                # Character Consistency
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
                self.state.add_log("[FALLBACK] Using sequential image generation")

                for scene in self.state.script.scenes:
                    if not scene.image_path and not scene.composition_sources:
                        try:
                            print(f"   Generating Image for Scene {scene.id}...")
                            scene.image_path = image_provider.generate_image(
                                scene.visual_prompt,
                                seed=self.state.seed + scene.id,
                                image_input=uploaded_asset_path
                            )
                            self.state.add_log(f"[VISUALS] Scene {scene.id} created (sequential)")
                        except Exception as e2:
                            print(f"   [ERROR] Scene {scene.id} failed: {e2}")
                            self.state.add_log(f"[ERROR] Scene {scene.id} failed: {str(e2)}")

            # Audio - PARALLEL GENERATION
            print(f"\n   [OPTIMIZATION] Using parallel audio generation (3x faster)")
            self.state.add_log("[OPTIMIZATION] Parallel audio generation enabled")

            # Derive mood from strategy
            mood_prompt = "Cinematic Ambient"
            if self.state.strategy and 'cinematic_direction' in self.state.strategy:
                mood_notes = self.state.strategy['cinematic_direction'].get('mood_notes', '')
                if mood_notes:
                    mood_prompt = mood_notes

            total_duration = sum(scene.duration for scene in self.state.script.scenes) + 5

            try:
                start_time = time.time()
                parallel_audio = ParallelAudioGenerator(eleven, self.state)
                self.state.bgm_path = parallel_audio.generate_all_audio(
                    self.state.script,
                    bgm_duration=total_duration
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Audio generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Parallel audio generation: {elapsed:.1f}s")

            except Exception as e:
                print(f"   [ERROR] Parallel audio generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel audio failed: {str(e)}")

                # Fallback to sequential
                print(f"   [FALLBACK] Switching to sequential audio generation...")
                self.state.add_log("[FALLBACK] Using sequential audio generation")

                # VO
                for i, line in enumerate(self.state.script.lines):
                    if not line.audio_path:
                        try:
                            print(f"   Generating VO for Line {i+1}...")
                            line.audio_path = eleven.generate_speech(line.text)
                        except Exception as e2:
                            print(f"   [ERROR] VO Line {i+1} failed: {e2}")

                # SFX
                for scene in self.state.script.scenes:
                    if not scene.sfx_path and scene.audio_prompt:
                        try:
                            print(f"   Generating SFX for Scene {scene.id}...")
                            scene.sfx_path = eleven.generate_sfx(scene.audio_prompt)
                        except Exception as e2:
                            print(f"   [ERROR] SFX Scene {scene.id} failed: {e2}")

                # BGM
                if not self.state.bgm_path:
                    try:
                        print(f"   Generating BGM...")
                        self.state.bgm_path = eleven.generate_bgm(mood_prompt, duration=total_duration)
                    except Exception as e2:
                        print(f"   [ERROR] BGM failed: {e2}")

            # APPROVAL GATE: Mark as complete and STOP
            self.state.status = "images_complete"
            print(f"\n[APPROVAL_GATE_1] Images + Audio Complete!")
            print(f"[APPROVAL_GATE_1] Waiting for user approval to proceed to video generation...")
            self.state.add_log("[APPROVAL_GATE_1] Images + Audio complete. Awaiting user approval...")

            # Print summary for frontend
            image_success = len([s for s in self.state.script.scenes if s.image_path])
            print(f"   Images:  {image_success}/{len(self.state.script.scenes)} scenes")
            print(f"   VO:      {len([l for l in self.state.script.lines if l.audio_path])}/{len(self.state.script.lines)} lines")
            print(f"   BGM:     {'Yes' if self.state.bgm_path else 'No'}")

            self.save_state()

        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            print(f"\n[FATAL ERROR] {error_msg}")

            import traceback
            self.state.add_log(f"[FATAL] {error_msg}")
            self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")

            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise

    def generate_videos_only(self, project_id: str = None):
        """
        APPROVAL GATE 2: Generate videos from existing images, then STOP.
        Sets status to 'videos_complete' when done.
        Frontend polls /status and shows approval UI when this status is reached.
        """
        if project_id:
            self.state.id = project_id

        plan_path = self._get_plan_path()
        if not os.path.exists(plan_path):
            error_msg = f"No plan found at {plan_path}"
            print(f"[ERROR] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise FileNotFoundError(error_msg)

        print(f"[LOAD] Loading plan from: {plan_path}")
        with open(plan_path, "r") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        print(f"[APPROVAL_GATE_2] Starting video generation for: {self.state.user_input}")
        self.state.status = "generating_videos"
        self.state.add_log("[APPROVAL_GATE_2] User approved images. Starting video generation...")
        self.save_state()

        try:
            # --- PHASE 4: Motion Synthesis ---
            print(f"\n[PHASE 4] Motion Synthesis...")
            self.state.add_log(f"[PHASE 4] Starting Motion Synthesis...")

            # Import video providers: Runway and Veo (Kling removed per user request)
            from .providers.video_google import GoogleVideoProvider
            from .providers.runway import RunwayProvider

            runway = RunwayProvider()
            veo = GoogleVideoProvider()

            # OPTIMIZATION: Parallel video generation (-60 seconds per commercial)
            print(f"   [OPTIMIZATION] Parallel video generation enabled (submit-all-then-poll)")
            self.state.add_log("[OPTIMIZATION] Parallel video generation active (Veo 3.1 Ultra + Runway fallback)")

            try:
                start_time = time.time()
                parallel_video = ParallelVideoGenerator(runway, veo, self.state)
                self.state.script.scenes = parallel_video.generate_parallel(
                    self.state.script.scenes,
                    max_workers=3  # Poll up to 3 videos concurrently
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Video generation completed in {elapsed:.1f}s")
            except Exception as e:
                print(f"   [ERROR] Parallel video generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel video generation failed: {str(e)}")

            # APPROVAL GATE: Mark as complete and STOP
            self.state.status = "videos_complete"
            print(f"\n[APPROVAL_GATE_2] Video Generation Complete!")
            print(f"[APPROVAL_GATE_2] Waiting for user approval to proceed to final assembly...")
            self.state.add_log("[APPROVAL_GATE_2] Videos complete. Awaiting user approval...")

            # Print summary
            video_success = len([s for s in self.state.script.scenes if s.video_path])
            print(f"   Videos:  {video_success}/{len(self.state.script.scenes)} scenes")

            self.save_state()

        except Exception as e:
            error_msg = f"Video generation failed: {str(e)}"
            print(f"\n[FATAL ERROR] {error_msg}")

            import traceback
            self.state.add_log(f"[FATAL] {error_msg}")
            self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")

            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise

    def assemble_final(self, project_id: str = None):
        """
        APPROVAL GATE 3: Assemble final video from existing clips.
        Sets status to 'completed' when done.
        """
        if project_id:
            self.state.id = project_id

        plan_path = self._get_plan_path()
        if not os.path.exists(plan_path):
            error_msg = f"No plan found at {plan_path}"
            print(f"[ERROR] {error_msg}")
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise FileNotFoundError(error_msg)

        print(f"[LOAD] Loading plan from: {plan_path}")
        with open(plan_path, "r") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        print(f"[APPROVAL_GATE_3] Starting final assembly for: {self.state.user_input}")
        self.state.status = "assembling"
        self.state.add_log("[APPROVAL_GATE_3] User approved videos. Starting final assembly...")
        self.save_state()

        try:
            # --- PHASE 5: Assembly (Copied from resume() lines 436-512) ---
            print("\n[PHASE 5] Final Assembly...")
            self.state.add_log("[PHASE 5] Assembling Final Video...")

            # Validate video clips
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
                print(f"   [WARN] {missing_count} scenes failed video generation, proceeding with {len(video_clips)} clips")
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

            # Mastering disabled for free tier
            self.state.add_log("[MASTERING] 4K Upscale Skipped (Free Tier Active).")

            # Performance Summary
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
            self.state.add_log("[APPROVAL_GATE_3] Final assembly complete!")
            self.save_state()

        except Exception as e:
            error_msg = f"Assembly failed: {str(e)}"
            print(f"\n[FATAL ERROR] {error_msg}")

            import traceback
            self.state.add_log(f"[FATAL] {error_msg}")
            self.state.add_log(f"[TRACEBACK] {traceback.format_exc()}")

            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            raise

    def save_state(self):
        plan_path = self._get_plan_path()
        with open(plan_path, "w") as f:
            f.write(self.state.model_dump_json(indent=2))
