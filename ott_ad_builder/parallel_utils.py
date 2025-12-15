"""
Parallel execution utilities for OTT Ad Builder optimizations
Provides parallel image, audio, and video generation
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Any, Optional
import hashlib


class ParallelImageGenerator:
    """Handles parallel image generation with GPT-5.2 self-correction and Nano Banana content fixes"""

    def __init__(self, imagen_provider, llm_provider, state, spatial_provider=None, nano_banana=None):
        self.imagen = imagen_provider
        self.llm = llm_provider
        self.state = state
        self.spatial = spatial_provider  # GPT-5.2 for self-correction
        self.nano_banana = nano_banana  # Nano Banana for content fixes
        self._previous_scene_description = None  # For continuity

    def _get_quality_threshold(self, scene_id: int, total_scenes: int) -> int:
        """
        OPTIMIZATION: Adaptive quality thresholds based on scene importance.
        Scene 1 (first impression) and final scene (last impression) require higher quality.
        Middle scenes can be slightly lower for speed without sacrificing perceived quality.
        """
        if scene_id == 1:
            return 8  # First impression matters most
        elif scene_id == total_scenes:
            return 8  # Last impression matters for CTA
        else:
            return 7  # Middle scenes can be slightly lower

    def generate_single_image(self, scene, uploaded_asset_path=None, total_scenes=3):
        """Generate image for single scene with GPT-5.2 self-correction loop"""
        try:
            max_retries = 2
            attempts = 0
            image_path = None
            current_prompt = scene.visual_prompt
            
            # OPTIMIZATION: Adaptive quality threshold based on scene importance
            quality_threshold = self._get_quality_threshold(scene.id, total_scenes)

            print(f"   [Scene {scene.id}] Starting image generation (threshold: {quality_threshold}/10)...")

            # SELF-CORRECTION: Adjust prompt based on previous scene (if GPT-5.2 available)
            if self.spatial and self._previous_scene_description and scene.id > 1:
                narrative = self.state.strategy.get('core_concept', '') if self.state.strategy else ''
                current_prompt = self.spatial.adjust_next_scene_prompt(
                    previous_scene_output=self._previous_scene_description,
                    next_scene_prompt=current_prompt,
                    narrative_context=narrative
                )
                if current_prompt != scene.visual_prompt:
                    print(f"   [Scene {scene.id}] ✎ Prompt adjusted for continuity")

            while attempts <= max_retries:
                image_path = self.imagen.generate_image(
                    current_prompt,
                    seed=self.state.seed + scene.id,
                    image_input=uploaded_asset_path
                )

                # SELF-CORRECTION: Use GPT-5.2 VISION review if available
                if self.spatial and self.spatial.is_available():
                    # GPT-5.2 VISION review (actually sees the image)
                    review = self.spatial.review_generated_image(
                        intended_prompt=current_prompt,
                        image_path=image_path,  # Pass actual image for vision analysis
                        scene_context={"scene_id": scene.id, "total_scenes": total_scenes}
                    )
                    score = review.get("quality_score", 7)
                    is_acceptable = review.get("is_acceptable", True)
                    improved_prompt = review.get("improved_prompt")
                    issues = review.get("issues", [])
                    reason = issues[0] if issues else "Pass"
                else:
                    # Fallback to Gemini critique
                    critique = self.llm.critique_image(image_path, current_prompt)
                    score = critique.get("score", 10)
                    reason = critique.get("reason", "Pass")
                    is_acceptable = score >= quality_threshold
                    improved_prompt = None

                if is_acceptable and score >= quality_threshold:
                    print(f"   [Scene {scene.id}] ✓ PASS ({score}/10 >= {quality_threshold}): {reason}")
                    self.state.add_log(f"[VISUALS] Scene {scene.id} PASS ({score}/10)")
                    # Save description for next scene continuity
                    self._previous_scene_description = f"Scene {scene.id}: {current_prompt[:100]}"
                    break
                else:
                    print(f"   [Scene {scene.id}] ⚠ NEEDS FIX ({score}/10 < {quality_threshold}): {reason}")
                    self.state.add_log(f"[VISUALS] Scene {scene.id} NEEDS FIX ({score}/10): {reason}")

                    # NANO BANANA: Try content fix if it's a content issue (not technical)
                    if self.nano_banana and self.nano_banana.is_available() and issues:
                        if self.nano_banana.is_content_issue(issues):
                            print(f"   [Scene {scene.id}] 🍌 Trying Nano Banana content fix...")
                            fixed_path = self.nano_banana.fix_image_issues(image_path, issues)
                            if fixed_path and fixed_path != image_path:
                                image_path = fixed_path
                                print(f"   [Scene {scene.id}] 🍌 Content fixed by Nano Banana")
                                self.state.add_log(f"[NANO_BANANA] Scene {scene.id} content fixed")
                                # Don't increment attempts - this was a fix, not a regenerate
                                continue  # Re-evaluate the fixed image
                        else:
                            print(f"   [Scene {scene.id}] Technical issue - Topaz needed (skipping)")

                    # REGENERATE: Use GPT-5.2 improved prompt if available
                    if improved_prompt:
                        current_prompt = improved_prompt
                        print(f"   [Scene {scene.id}] ↻ Regenerating with GPT-5.2 improved prompt")
                    else:
                        current_prompt = f"{current_prompt}. IMPORTANT FIX: {reason}"
                    attempts += 1

            scene.visual_prompt = current_prompt  # Update with final prompt
            return scene.id, image_path

        except Exception as e:
            print(f"   [Scene {scene.id}] ✗ ERROR: {e}")
            return scene.id, None

    def generate_parallel(self, scenes: List, uploaded_asset_path=None, max_workers=3):
        """Generate images for all scenes in parallel"""
        scenes_to_generate = [s for s in scenes if not s.image_path]

        if not scenes_to_generate:
            print("   [PARALLEL] No scenes need image generation")
            return scenes

        print(f"   [PARALLEL] Generating {len(scenes_to_generate)} images concurrently (max_workers={max_workers})...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_scene = {
                executor.submit(self.generate_single_image, scene, uploaded_asset_path): scene
                for scene in scenes_to_generate
            }

            for future in as_completed(future_to_scene):
                scene = future_to_scene[future]
                try:
                    scene_id, image_path = future.result()
                    scene.image_path = image_path

                    if image_path:
                        self.state.add_log(f"[VISUALS] Scene {scene_id} completed successfully")
                    else:
                        self.state.add_log(f"[ERROR] Scene {scene_id} failed")

                except Exception as e:
                    print(f"   [FATAL] Scene {scene.id} exception: {e}")
                    self.state.add_log(f"[ERROR] Scene {scene.id} failed: {str(e)}")
                    scene.image_path = None

        return scenes


class ParallelAudioGenerator:
    """Handles parallel audio generation (VO, SFX, BGM)"""

    def __init__(self, audio_provider, state):
        self.audio = audio_provider
        self.state = state

    def generate_vo_batch(self, script_lines):
        """Generate all voice-over in parallel"""
        results = []

        lines_to_generate = [(i, line) for i, line in enumerate(script_lines) if not line.audio_path]

        if not lines_to_generate:
            return results

        print(f"   [PARALLEL] Generating {len(lines_to_generate)} VO lines concurrently...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_line = {
                executor.submit(self.audio.generate_speech, line.text): (idx, line)
                for idx, line in lines_to_generate
            }

            for future in as_completed(future_to_line):
                idx, line = future_to_line[future]
                try:
                    audio_path = future.result()
                    results.append((idx, audio_path))
                    print(f"   [VO] Line {idx+1} ✓")
                except Exception as e:
                    print(f"   [VO] Line {idx+1} ✗ Error: {e}")
                    results.append((idx, None))

        return results

    def generate_sfx_batch(self, scenes):
        """Generate all SFX in parallel"""
        results = []

        scenes_to_generate = [s for s in scenes if s.audio_prompt and not s.sfx_path]

        if not scenes_to_generate:
            return results

        print(f"   [PARALLEL] Generating {len(scenes_to_generate)} SFX tracks concurrently...")

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_scene = {
                executor.submit(self.audio.generate_sfx, scene.audio_prompt, scene.duration): scene
                for scene in scenes_to_generate
            }

            for future in as_completed(future_to_scene):
                scene = future_to_scene[future]
                try:
                    sfx_path = future.result()
                    results.append((scene.id, sfx_path))
                    print(f"   [SFX] Scene {scene.id} ✓")
                except Exception as e:
                    print(f"   [SFX] Scene {scene.id} ✗ Error: {e}")
                    results.append((scene.id, None))

        return results

    def generate_all_audio(self, script, bgm_duration):
        """Generate VO, SFX, and BGM in parallel"""
        print("   [PARALLEL] Generating VO, SFX, and BGM concurrently...")

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all three batches in parallel
            vo_future = executor.submit(self.generate_vo_batch, script.lines)
            sfx_future = executor.submit(self.generate_sfx_batch, script.scenes)
            bgm_future = executor.submit(self.audio.generate_bgm, "cinematic background music", bgm_duration)

            # Wait for all to complete
            vo_results = vo_future.result()
            sfx_results = sfx_future.result()
            bgm_path = None
            try:
                bgm_path = bgm_future.result()
            except Exception as e:
                print(f"   [BGM] ✗ Error: {e}")

        # Assign results
        for idx, audio_path in vo_results:
            script.lines[idx].audio_path = audio_path

        for scene_id, sfx_path in sfx_results:
            scene = next(s for s in script.scenes if s.id == scene_id)
            scene.sfx_path = sfx_path

        return bgm_path


class ParallelVideoGenerator:
    """
    PREMIUM QUALITY: Parallel video generation with Veo 3.1 Ultra primary.
    Submits all video tasks at once to Veo 3.1, then polls all in parallel.
    Falls back to Runway Gen-3 Turbo for reliability.
    """

    def __init__(self, veo_provider, runway_provider, state):
        self.veo = veo_provider
        self.runway = runway_provider
        self.state = state

    def _submit_video_task(self, scene, delay: float = 0, retry: int = 0) -> tuple:
        """Submit a single video task and return (scene, task_id or None)."""
        try:
            # Staggered delay to prevent rate limiting
            if delay > 0:
                import time
                time.sleep(delay)
            
            print(f"   [PARALLEL VIDEO] Submitting Scene {scene.id} to Veo 3.1 Ultra...")
            task_id = self.veo.submit_async(scene.image_path, scene.motion_prompt)
            self.state.add_log(f"[VEO] Scene {scene.id} submitted: {task_id[:30]}...")
            return (scene, task_id, "veo")
        except Exception as e:
            error_msg = str(e)[:150]
            print(f"   [PARALLEL VIDEO] Veo submit failed for Scene {scene.id}: {error_msg}")
            self.state.add_log(f"[VEO ERROR] Scene {scene.id}: {error_msg}")
            
            # Retry with longer delay for rate limiting
            if retry < 2 and ("rate" in error_msg.lower() or "quota" in error_msg.lower() or "429" in error_msg):
                wait_time = 10 * (retry + 1)  # 10s, 20s
                print(f"   [PARALLEL VIDEO] Rate limited, waiting {wait_time}s before retry {retry + 1}...")
                import time
                time.sleep(wait_time)
                return self._submit_video_task(scene, delay=0, retry=retry + 1)
                
            return (scene, None, "failed")

    def _poll_video_task(self, scene, task_id: str, provider: str) -> tuple:
        """Poll a video task until completion."""
        try:
            if provider == "veo":
                video_path = self.veo.poll_task(task_id, scene.motion_prompt)
            else:
                video_path = self.runway.poll_task(task_id, scene.motion_prompt)
            return (scene, video_path)
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"   [PARALLEL VIDEO] Polling failed for Scene {scene.id}: {error_msg}")
            self.state.add_log(f"[VEO POLL ERROR] Scene {scene.id}: {error_msg}")
            
            # Try Runway fallback for this scene
            try:
                print(f"   [FALLBACK] Trying Runway for Scene {scene.id}...")
                self.state.add_log(f"[FALLBACK] Scene {scene.id} switching to Runway...")
                video_path = self.runway.generate_video(scene.motion_prompt, scene.image_path)
                return (scene, video_path)
            except Exception as e2:
                error_msg2 = str(e2)[:150]
                print(f"   [PARALLEL VIDEO] Runway fallback also failed for Scene {scene.id}: {error_msg2}")
                self.state.add_log(f"[RUNWAY ERROR] Scene {scene.id}: {error_msg2}")
                return (scene, None)

    def generate_parallel(self, scenes: List, max_workers: int = 3) -> List:
        """
        Generate videos for all scenes in parallel.
        1. Submit all tasks at once (async)
        2. Poll all tasks in parallel (ThreadPoolExecutor)
        """
        scenes_to_generate = [s for s in scenes if s.image_path and not s.video_path]

        if not scenes_to_generate:
            print("   [PARALLEL VIDEO] No scenes need video generation")
            return scenes

        print(f"   [PARALLEL VIDEO] Generating {len(scenes_to_generate)} videos concurrently...")
        self.state.add_log(f"[OPTIMIZATION] Parallel video generation: {len(scenes_to_generate)} scenes")

        # Phase 1: Submit all tasks with STAGGERED DELAYS to prevent rate limiting
        print(f"   [PHASE 1/2] Submitting all {len(scenes_to_generate)} video tasks to Veo 3.1 Ultra...")
        video_tasks = []
        for i, scene in enumerate(scenes_to_generate):
            # Add 5s delay between submissions to prevent rate limiting (increased from 2s)
            delay = i * 5.0  # 0s, 5s, 10s for scenes 1, 2, 3
            scene, task_id, provider = self._submit_video_task(scene, delay=delay)
            if task_id:
                video_tasks.append((scene, task_id, provider))
            else:
                # Failed to submit - try Runway synchronously as fallback
                try:
                    print(f"   [FALLBACK] Trying Runway for Scene {scene.id}...")
                    self.state.add_log(f"[FALLBACK] Scene {scene.id} using Runway...")
                    scene.video_path = self.runway.generate_video(scene.motion_prompt, scene.image_path)
                    self.state.add_log(f"[VIDEO] Scene {scene.id} generated via Runway (fallback)")
                except Exception as e:
                    error_msg = str(e)[:80]
                    print(f"   [FATAL] Scene {scene.id} failed all providers: {error_msg}")
                    self.state.add_log(f"[ERROR] Scene {scene.id} failed: {error_msg}")

        if not video_tasks:
            print("   [PARALLEL VIDEO] No Veo tasks to poll (all fallback/failed)")
            return scenes

        # Phase 2: Poll all tasks in parallel
        print(f"   [PHASE 2/2] Polling {len(video_tasks)} tasks in parallel...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._poll_video_task, scene, task_id, provider): scene
                for scene, task_id, provider in video_tasks
            }

            for future in as_completed(futures):
                scene = futures[future]
                try:
                    scene, video_path = future.result()
                    if video_path:
                        scene.video_path = video_path
                        print(f"   [PARALLEL VIDEO] ✓ Scene {scene.id} complete")
                        self.state.add_log(f"[VIDEO] Scene {scene.id} generated successfully")
                    else:
                        print(f"   [PARALLEL VIDEO] ✗ Scene {scene.id} failed")
                        self.state.add_log(f"[ERROR] Scene {scene.id} video generation failed")
                except Exception as e:
                    print(f"   [PARALLEL VIDEO] ✗ Scene {scene.id} exception: {e}")
                    scene.video_path = None

        elapsed = time.time() - start_time
        print(f"   [PERFORMANCE] Parallel video generation completed in {elapsed:.1f}s")
        self.state.add_log(f"[PERFORMANCE] Parallel video generation: {elapsed:.1f}s")

        return scenes


class SmartCritiqueCache:
    """Smart caching for Gemini image critique to save time and cost"""

    def __init__(self):
        self.cache = {}  # prompt_hash -> critique result

    def get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()

    def get_cached_critique(self, prompt: str) -> Optional[Dict]:
        """Retrieve cached critique if available"""
        cache_key = self.get_cache_key(prompt)
        if cache_key in self.cache:
            print(f"[CRITIQUE] Using cached result for prompt")
            return self.cache[cache_key]
        return None

    def cache_critique(self, prompt: str, critique: Dict):
        """Save critique to cache"""
        cache_key = self.get_cache_key(prompt)
        self.cache[cache_key] = critique

    def critique_with_cache(self, llm_provider, image_path: str, prompt: str) -> Dict:
        """Critique with caching"""
        # Check cache first
        cached = self.get_cached_critique(prompt)
        if cached:
            return cached

        # Perform actual critique
        critique = llm_provider.critique_image(image_path, prompt)

        # Cache result
        self.cache_critique(prompt, critique)

        return critique


class CharacterConsistencyExtractor:
    """Extracts and tracks character/product consistency across scenes"""

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def extract_primary_subject(self, visual_prompt: str) -> Dict:
        """Extract primary character/product from Scene 1 prompt"""
        import json

        extraction_prompt = f"""
        Extract the PRIMARY CHARACTER or PRODUCT from this scene description:

        {visual_prompt}

        Return ONLY valid JSON (no markdown, no explanation):
        {{
            "subject_type": "character" or "product",
            "subject_name": "short identifier (e.g., 'businesswoman', 'sports car', 'smartphone')",
            "subject_description": "detailed appearance (1-2 sentences with age, clothing, colors, materials)"
        }}
        """

        try:
            response = self.llm.model.generate_content(extraction_prompt)
            text = response.text.strip()

            # Remove markdown if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Extract JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])

            print("[CONSISTENCY] Failed to parse extraction, using fallback")
            return {"subject_name": "main subject", "subject_description": "", "subject_type": "product"}

        except Exception as e:
            print(f"[CONSISTENCY] Extraction error: {e}")
            return {"subject_name": "main subject", "subject_description": "", "subject_type": "product"}

    def inject_consistency_references(self, scenes: List) -> List:
        """Extract subject from Scene 1 and inject references into Scene 2+"""
        if len(scenes) == 0:
            return scenes

        # Extract from Scene 1
        subject_info = self.extract_primary_subject(scenes[0].visual_prompt)

        scenes[0].primary_subject = subject_info.get('subject_name', '')
        scenes[0].subject_description = subject_info.get('subject_description', '')

        print(f"[CONSISTENCY] Extracted subject: '{scenes[0].primary_subject}'")
        if scenes[0].subject_description:
            print(f"[CONSISTENCY] Description: {scenes[0].subject_description[:100]}...")

        # Inject references into Scene 2+
        for i in range(1, len(scenes)):
            reference = f"the same {scenes[0].primary_subject} from Scene 1"
            if scenes[0].subject_description:
                reference += f" ({scenes[0].subject_description})"

            scenes[i].subject_reference = reference

            # PREPEND reference to visual prompt
            scenes[i].visual_prompt = f"[CONSISTENCY CRITICAL] Feature {reference}.\n\n{scenes[i].visual_prompt}"

            print(f"[CONSISTENCY] Scene {i+1} now references: {scenes[0].primary_subject}")

        return scenes
