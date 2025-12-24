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
    """Handles parallel image generation with GPT-5.2 review (strict demo mode)"""

    def __init__(self, image_provider, state, spatial_provider):
        self.image_provider = image_provider
        self.state = state
        self.spatial = spatial_provider  # GPT-5.2 for continuity + review
        # Disabled: kept only to avoid legacy code paths raising AttributeError.
        self.nano_banana = None
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
            # Demo reliability: text-free UI is hard; allow extra retries so we don't
            # ship a scene with gibberish/letters on screens.
            max_retries = 4
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
                    print(f"   [Scene {scene.id}] NOTE: Prompt adjusted for continuity")

            while attempts <= max_retries:
                image_path = self.image_provider.generate_image(
                    current_prompt,
                    seed=self.state.seed + scene.id,
                    image_input=uploaded_asset_path
                )

                if not (self.spatial and self.spatial.is_available()):
                    raise RuntimeError("GPT-5.2 is required for image review in strict demo mode.")

                # GPT-5.2 VISION review (actually sees the image)
                review = self.spatial.review_generated_image(
                    intended_prompt=current_prompt,
                    image_path=image_path,  # Pass actual image for vision analysis
                    scene_context={"scene_id": scene.id, "total_scenes": total_scenes},
                )
                score = review.get("quality_score", 7)
                is_acceptable = review.get("is_acceptable", True)
                improved_prompt = review.get("improved_prompt")
                issues = review.get("issues", [])
                first_issue = issues[0] if issues else None
                reason = first_issue or "OK"
                what_i_see = (review.get("what_i_see") or "").strip()

                # If GPT says it's acceptable, don't over-reroll just to chase an 8/10.
                # Avoids prompt drift and retry pollution.
                pass_threshold = max(int(quality_threshold) - 1, 7)
                if is_acceptable and score >= pass_threshold:
                    print(f"   [Scene {scene.id}] PASS ({score}/10): {reason}")
                    self.state.add_log(f"[VISUALS] Scene {scene.id} PASS ({score}/10)")
                    # Save description for next scene continuity
                    if what_i_see:
                        self._previous_scene_description = f"Scene {scene.id}: {what_i_see}"
                    else:
                        self._previous_scene_description = f"Scene {scene.id}: {current_prompt[:200]}"
                    break
                else:
                    print(f"   [Scene {scene.id}] NEEDS FIX ({score}/10 < {quality_threshold}): {reason}")
                    self.state.add_log(f"[VISUALS] Scene {scene.id} NEEDS FIX ({score}/10): {reason}")

                    # NANO BANANA: Try content fix if it's a content issue (not technical)
                    if self.nano_banana and self.nano_banana.is_available() and issues:
                        if self.nano_banana.is_content_issue(issues):
                            print(f"   [Scene {scene.id}] [NANO_BANANA] Trying content fix...")
                            fixed_path = self.nano_banana.fix_image_issues(image_path, issues)
                            if fixed_path and fixed_path != image_path:
                                image_path = fixed_path
                                print(f"   [Scene {scene.id}] [NANO_BANANA] Content fixed")
                                self.state.add_log(f"[NANO_BANANA] Scene {scene.id} content fixed")
                                # Don't increment attempts - this was a fix, not a regenerate
                                continue  # Re-evaluate the fixed image
                        else:
                            print(f"   [Scene {scene.id}] Technical issue - Topaz needed (skipping)")

                    issue_text = " ".join(str(x) for x in (issues or [])).lower()
                    saw_text_issue = any(
                        k in issue_text
                        for k in (
                            "text",
                            "letters",
                            "numbers",
                            "word",
                            "caption",
                            "subtitle",
                            "watermark",
                            "gibberish",
                        )
                    )
                    saw_screen_issue = any(
                        k in issue_text
                        for k in ("screen", "monitor", "laptop", "ui", "dashboard", "menu")
                    )
                    saw_play_icon_issue = ("play" in issue_text) and ("icon" in issue_text)

                    # Demo-time pragmatism: only hard-fail on text/UI issues (most visible).
                    # If this is a non-text miss (e.g. missing a prop), accept after one retry
                    # so we don't burn minutes rerolling a minor detail.
                    if not (saw_text_issue or saw_screen_issue) and attempts >= 1 and score >= 6:
                        print(f"   [Scene {scene.id}] SOFT PASS ({score}/10): {reason}")
                        self.state.add_log(f"[VISUALS] Scene {scene.id} SOFT PASS ({score}/10)")
                        if what_i_see:
                            self._previous_scene_description = f"Scene {scene.id}: {what_i_see}"
                        else:
                            self._previous_scene_description = f"Scene {scene.id}: {current_prompt[:200]}"
                        break

                    # REGENERATE: Use GPT-5.2 improved prompt if available
                    if improved_prompt:
                        current_prompt = improved_prompt
                        print(f"   [Scene {scene.id}] RETRY: Regenerating with GPT-5.2 improved prompt")
                    else:
                        if first_issue:
                            current_prompt = f"{current_prompt}. IMPORTANT FIX: {first_issue}"
                        else:
                            current_prompt = (
                                f"{current_prompt}. IMPORTANT FIX: reduce artifacts; avoid any readable text/gibberish; "
                                "keep screens abstract and icon-only; improve realism and consistency."
                            )

                    # If the failure is text/UI-related, force a stronger constraint that removes the root cause:
                    # avoid literal screens/menus entirely and push toward abstract holographic icons/real-world metaphors.
                    if saw_text_issue or saw_screen_issue:
                        current_prompt = (
                            f"{current_prompt}\n\n"
                            "ABSOLUTE REQUIREMENT: no readable text/letters/numbers/glyphs anywhere. "
                            "Avoid literal screens/monitors/laptops; if a device appears, its screen must be OFF/DARK and out-of-focus. "
                            "Any UI must be abstract holographic shapes/icons only (no menus, no labels, no status bars)."
                        )

                    if saw_play_icon_issue:
                        current_prompt = (
                            f"{current_prompt}\n\n"
                            "ABSOLUTE: if a brand mark/icon appears, it must NOT be a play triangle, camera icon, or clapperboard; use unique abstract geometry."
                        )
                    attempts += 1

            scene.visual_prompt = current_prompt  # Update with final prompt
            return scene.id, image_path

        except Exception as e:
            print(f"   [Scene {scene.id}] ERROR: {e}")
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
        self._speaker_voice_map: dict[str, str | None] = {}
        self._explicit_voice_map: dict[str, str] = self._load_explicit_voice_map()

    @staticmethod
    def _load_explicit_voice_map() -> dict[str, str]:
        """
        Optional explicit speaker->voice routing, configured via env var.

        Supported formats:
          - JSON: ELEVENLABS_VOICE_MAP={"Maya":"<voice_id>","Ethan":"<voice_id>","Narrator":"<voice_id>"}
          - KV:   ELEVENLABS_VOICE_MAP=Maya=<voice_id>,Ethan=<voice_id>,Narrator=<voice_id>

        Also supported (alias): ELEVENLABS_SPEAKER_VOICE_MAP (same formats).

        This avoids any UI changes: the planner can invent characters and you can
        map them to specific ElevenLabs voices for demo-day consistency.
        """
        raw = (os.getenv("ELEVENLABS_VOICE_MAP") or os.getenv("ELEVENLABS_SPEAKER_VOICE_MAP") or "").strip()
        if not raw:
            return {}

        mapping: dict[str, str] = {}

        # JSON form
        if raw.startswith("{"):
            try:
                import json

                data = json.loads(raw)
                if isinstance(data, dict):
                    for k, v in data.items():
                        key = str(k or "").strip().lower()
                        value = str(v or "").strip()
                        if key and value:
                            mapping[key] = value
                    return mapping
            except Exception:
                # Fall back to KV parsing below
                pass

        # KV form
        for part in raw.replace(";", ",").split(","):
            item = part.strip()
            if not item or "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if key and value:
                mapping[key] = value
        return mapping

    @staticmethod
    def _get_max_vo_workers() -> int:
        """
        ElevenLabs accounts commonly enforce a low concurrent-request limit.
        Default to 2 for demo reliability and allow overriding via env var.
        """
        raw = (os.getenv("ELEVENLABS_MAX_CONCURRENCY") or "").strip()
        if not raw:
            return 2
        try:
            value = int(raw)
        except ValueError:
            return 2
        return max(1, min(value, 5))

    def _resolve_voice_id(self, speaker: str) -> str | None:
        """
        Optional multi-voice support for dialogue-heavy ads.

        Env vars (optional):
        - ELEVENLABS_VOICE_ID (primary)            (already supported by provider)
        - ELEVENLABS_VOICE_ID_SECONDARY (secondary character voice)
        - ELEVENLABS_VOICE_ID_NARRATOR (narrator/VO)

        If not provided, falls back to the provider defaults.
        """
        speaker_name = (speaker or "").strip()
        if not speaker_name:
            return None

        # Normalize verbose speaker labels like "Nate at his desk, doom-checking charts" -> "Nate"
        normalized = speaker_name
        for sep in (",", " - ", " — ", ":"):
            if sep in normalized:
                normalized = normalized.split(sep, 1)[0].strip()
        if " at " in normalized and len(normalized.split()) > 2:
            normalized = normalized.split(" at ", 1)[0].strip()
        if len(normalized) > 24 and " " in normalized:
            normalized = normalized.split()[0].strip()
        if normalized:
            speaker_name = normalized

        mapped = self._explicit_voice_map.get(speaker_name.lower())
        if mapped:
            return mapped

        narrator_voice = os.getenv("ELEVENLABS_VOICE_ID_NARRATOR")
        secondary_voice = os.getenv("ELEVENLABS_VOICE_ID_SECONDARY") or os.getenv("ELEVENLABS_VOICE_ID_2")
        primary_voice = os.getenv("ELEVENLABS_VOICE_ID")

        if speaker_name.lower() in ("narrator", "voiceover", "vo") and narrator_voice:
            return narrator_voice.strip() or None

        if speaker_name in self._speaker_voice_map:
            return self._speaker_voice_map[speaker_name]

        # Assign primary to first character, secondary to second (if configured), then reuse primary.
        assigned = None
        if not self._speaker_voice_map:
            assigned = primary_voice.strip() if primary_voice else None
        elif secondary_voice:
            assigned = secondary_voice.strip() or None
        else:
            assigned = primary_voice.strip() if primary_voice else None

        self._speaker_voice_map[speaker_name] = assigned
        return assigned

    def generate_vo_batch(self, script_lines):
        """Generate all voice-over in parallel"""
        results = []

        lines_to_generate = [(i, line) for i, line in enumerate(script_lines) if not line.audio_path]

        if not lines_to_generate:
            return results

        max_workers = min(self._get_max_vo_workers(), len(lines_to_generate))
        print(f"   [PARALLEL] Generating {len(lines_to_generate)} VO lines concurrently (max_workers={max_workers})...")

        failures: list[tuple[int, Any]] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_line = {
                executor.submit(
                    self.audio.generate_speech,
                    line.text,
                    (getattr(line, "voice_id", None) or self._resolve_voice_id(getattr(line, "speaker", ""))),
                ): (idx, line)
                for idx, line in lines_to_generate
            }

            for future in as_completed(future_to_line):
                idx, line = future_to_line[future]
                try:
                    audio_path = future.result()
                    results.append((idx, audio_path))
                    print(f"   [VO] Line {idx+1} OK")
                except Exception as e:
                    print(f"   [VO] Line {idx+1} ERROR: {e}")
                    results.append((idx, None))
                    failures.append((idx, line))

        # Retry failed lines sequentially (handles 429 too_many_concurrent_requests gracefully).
        if failures:
            import time
            print(f"   [VO] Retrying {len(failures)} failed lines sequentially...")
            for idx, line in failures:
                if getattr(line, "audio_path", None):
                    continue
                last_error = None
                for attempt in range(3):
                    try:
                        voice_id = getattr(line, "voice_id", None) or self._resolve_voice_id(getattr(line, "speaker", ""))
                        audio_path = self.audio.generate_speech(line.text, voice_id)
                        # Update results entry (keep return type stable).
                        results = [(i, (audio_path if i == idx else p)) for (i, p) in results]
                        line.audio_path = audio_path
                        print(f"   [VO] Line {idx+1} OK (retry)")
                        last_error = None
                        break
                    except Exception as e:
                        last_error = e
                        message = str(e).lower()
                        # Back off on rate limits / concurrency limits.
                        if "429" in message or "too_many_concurrent_requests" in message or "rate" in message:
                            time.sleep(2 ** attempt)
                            continue
                        break
                if last_error is not None:
                    print(f"   [VO] Line {idx+1} FAILED after retries: {last_error}")

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
                    print(f"   [SFX] Scene {scene.id} OK")
                except Exception as e:
                    print(f"   [SFX] Scene {scene.id} ERROR: {e}")
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
                print(f"   [BGM] ERROR: {e}")

        # Assign results
        for idx, audio_path in vo_results:
            script.lines[idx].audio_path = audio_path

        for scene_id, sfx_path in sfx_results:
            scene = next(s for s in script.scenes if s.id == scene_id)
            scene.sfx_path = sfx_path

        return bgm_path


class ParallelVideoGenerator:
    """
    PREMIUM QUALITY: Parallel video generation with Veo 3.1 Ultra only.
    Submits all video tasks at once to Veo 3.1, then polls all in parallel.
    """

    def __init__(self, veo_provider, runway_provider, state):
        self.veo = veo_provider
        self.runway = runway_provider
        self.state = state

    def _resolve_engine(self) -> str:
        raw = str(getattr(self.state, "video_model", "") or "").strip().lower()
        if raw in ("", "default"):
            raw = "auto"
        if raw not in ("auto", "veo", "runway"):
            raw = "auto"
        return raw

    @staticmethod
    def _normalize_duration_seconds(value: Any) -> int:
        """
        Veo supports only a small set of durations per request.
        Normalize to the nearest supported value for reliability.
        """
        allowed = (4, 6, 8)
        try:
            duration = int(value)
        except (TypeError, ValueError):
            duration = 4

        if duration in allowed:
            return duration

        # Pick nearest; on ties prefer the shorter duration.
        return min(allowed, key=lambda v: (abs(v - duration), v))

    @staticmethod
    def _is_prompt_blocked_error(message: str) -> bool:
        lower = (message or "").lower()
        return (
            "usage guidelines" in lower
            or "prompt could not be submitted" in lower
            or "try rephrasing" in lower
            or "violat" in lower and "guideline" in lower
        )

    @staticmethod
    def _safe_motion_prompt(original: str) -> str:
        """
        Veo can occasionally reject prompts during async validation.
        For demo reliability, retry once with an ultra-generic motion-only prompt.
        """
        lower = (original or "").lower()
        if "handheld" in lower:
            camera = "Subtle handheld stabilization"
        elif "pan" in lower:
            camera = "Slow, smooth pan"
        elif "tilt" in lower:
            camera = "Slow, smooth tilt"
        elif "zoom" in lower:
            camera = "Gentle zoom-in"
        else:
            camera = "Slow dolly-in"

        # Keep this motion-only, short, and policy-safe.
        return f"{camera}; gentle parallax; natural blink; relaxed expression; smooth motion."

    def _submit_video_task(self, scene, delay: float = 0, retry: int = 0) -> tuple:
        """Submit a single video task and return (scene, task_id or None)."""
        engine = self._resolve_engine()
        if engine == "auto":
            # Auto: prefer Veo when prompt-only (no image) or when Veo native audio is enabled.
            if not getattr(scene, "image_path", None) or bool(getattr(self.state, "veo_generate_audio", False)):
                engine = "veo"
            else:
                engine = "runway" if self.runway is not None else "veo"
        try:
            # Staggered delay to prevent rate limiting
            if delay > 0:
                import time
                time.sleep(delay)

            if engine == "runway":
                if self.runway is None:
                    raise Exception("Runway provider not configured")
                if not getattr(scene, "image_path", None):
                    raise Exception("Runway requires image_path (I2V)")
                print(f"   [PARALLEL VIDEO] Submitting Scene {scene.id} to Runway...")
                duration = int(getattr(scene, "duration", 5) or 5)
                task_id = self.runway.submit_async(scene.image_path, scene.motion_prompt, duration=duration)
                self.state.add_log(f"[RUNWAY] Scene {scene.id} submitted: {task_id[:30]}...")
                return (scene, task_id, "runway")

            print(f"   [PARALLEL VIDEO] Submitting Scene {scene.id} to Veo 3.1 Ultra...")
            duration = self._normalize_duration_seconds(getattr(scene, "duration", 4))
            task_id = self.veo.submit_async(getattr(scene, "image_path", None), scene.motion_prompt, duration=duration)
            self.state.add_log(f"[VEO] Scene {scene.id} submitted: {task_id[:30]}...")
            return (scene, task_id, "veo")
        except Exception as e:
            error_msg = str(e)[:150]
            provider_tag = "RUNWAY" if engine == "runway" else "VEO"
            print(f"   [PARALLEL VIDEO] {provider_tag} submit failed for Scene {scene.id}: {error_msg}")
            self.state.add_log(f"[{provider_tag} ERROR] Scene {scene.id}: {error_msg}")
            
            # Retry with longer delay for rate limiting
            if retry < 2 and ("rate" in error_msg.lower() or "quota" in error_msg.lower() or "429" in error_msg):
                wait_time = 10 * (retry + 1)  # 10s, 20s
                print(f"   [PARALLEL VIDEO] Rate limited, waiting {wait_time}s before retry {retry + 1}...")
                import time
                time.sleep(wait_time)
                return self._submit_video_task(scene, delay=0, retry=retry + 1)
                
            return (scene, None, "failed")

    def _poll_video_task(self, scene, task_id: str, provider: str, retry: int = 0) -> tuple:
        """Poll a video task until completion."""
        try:
            if provider == "runway":
                video_path = self.runway.poll_task(task_id, scene.motion_prompt)
                return (scene, video_path)
            video_path = self.veo.poll_task(task_id, scene.motion_prompt)
            return (scene, video_path)
        except Exception as e:
            full_msg = str(e)
            error_msg = full_msg[:200]
            if provider == "runway":
                print(f"   [PARALLEL VIDEO] Runway polling failed for Scene {scene.id}: {error_msg}")
                self.state.add_log(f"[RUNWAY POLL ERROR] Scene {scene.id}: {error_msg}")
            else:
                print(f"   [PARALLEL VIDEO] Polling failed for Scene {scene.id}: {error_msg}")
                self.state.add_log(f"[VEO POLL ERROR] Scene {scene.id}: {error_msg}")

            # One-shot retry if Veo rejects the prompt during async validation.
            if provider == "veo" and retry < 1 and self._is_prompt_blocked_error(full_msg):
                safe_prompt = self._safe_motion_prompt(scene.motion_prompt)
                print(f"   [PARALLEL VIDEO] Scene {scene.id}: prompt blocked; retrying with sanitized motion prompt...")
                self.state.add_log(f"[VEO RETRY] Scene {scene.id}: prompt blocked; retrying with sanitized motion prompt")
                try:
                    duration = self._normalize_duration_seconds(getattr(scene, "duration", 4))
                    new_task_id = self.veo.submit_async(getattr(scene, "image_path", None), safe_prompt, duration=duration)
                    self.state.add_log(f"[VEO] Scene {scene.id} resubmitted: {new_task_id[:30]}...")
                    # Update scene prompt so the saved hash matches the retried render.
                    scene.motion_prompt = safe_prompt
                    return self._poll_video_task(scene, new_task_id, provider, retry=retry + 1)
                except Exception as retry_err:
                    retry_msg = str(retry_err)[:200]
                    print(f"   [PARALLEL VIDEO] Scene {scene.id}: retry failed: {retry_msg}")
                    self.state.add_log(f"[VEO RETRY ERROR] Scene {scene.id}: {retry_msg}")

            # Cross-provider fallback once (Runway -> Veo or Veo -> Runway).
            if retry < 1:
                try:
                    if provider == "runway":
                        duration = self._normalize_duration_seconds(getattr(scene, "duration", 4))
                        new_task_id = self.veo.submit_async(getattr(scene, "image_path", None), scene.motion_prompt, duration=duration)
                        self.state.add_log(f"[FALLBACK] Scene {scene.id}: Runway→Veo resubmitted: {new_task_id[:30]}...")
                        return self._poll_video_task(scene, new_task_id, "veo", retry=retry + 1)
                    if provider == "veo" and self.runway is not None and getattr(scene, "image_path", None):
                        duration = int(getattr(scene, "duration", 5) or 5)
                        new_task_id = self.runway.submit_async(scene.image_path, scene.motion_prompt, duration=duration)
                        self.state.add_log(f"[FALLBACK] Scene {scene.id}: Veo→Runway resubmitted: {new_task_id[:30]}...")
                        return self._poll_video_task(scene, new_task_id, "runway", retry=retry + 1)
                except Exception as fb_err:
                    fb_msg = str(fb_err)[:200]
                    self.state.add_log(f"[FALLBACK ERROR] Scene {scene.id}: {fb_msg}")

            return (scene, None)

    def generate_parallel(self, scenes: List, max_workers: int = 3) -> List:
        """
        Generate videos for all scenes in parallel.
        1. Submit all tasks at once (async)
        2. Poll all tasks in parallel (ThreadPoolExecutor)
        """
        # Allow text-to-video when `image_path` is missing: Veo supports prompt-only generation.
        scenes_to_generate = [s for s in scenes if not getattr(s, "video_path", None)]

        if not scenes_to_generate:
            print("   [PARALLEL VIDEO] No scenes need video generation")
            return scenes

        print(f"   [PARALLEL VIDEO] Generating {len(scenes_to_generate)} videos concurrently...")
        self.state.add_log(f"[OPTIMIZATION] Parallel video generation: {len(scenes_to_generate)} scenes")

        # Phase 1: Submit all tasks with staggered delays to prevent rate limiting
        engine = self._resolve_engine()
        engine_label = {"auto": "Auto", "veo": "Veo 3.1 Ultra", "runway": "Runway Gen-3"}.get(engine, "Auto")
        print(f"   [PHASE 1/2] Submitting all {len(scenes_to_generate)} video tasks ({engine_label})...")
        video_tasks = []
        for i, scene in enumerate(scenes_to_generate):
            # Add delay between submissions to prevent rate limiting.
            # Veo is more sensitive than Runway.
            delay = i * (5.0 if engine in ("auto", "veo") else 1.0)
            scene, task_id, provider = self._submit_video_task(scene, delay=delay)
            if task_id:
                video_tasks.append((scene, task_id, provider))
            else:
                print(f"   [FATAL] Scene {scene.id} failed: submit failed")
                self.state.add_log(f"[ERROR] Scene {scene.id} failed: submit failed")
                scene.video_path = None

        if not video_tasks:
            print("   [PARALLEL VIDEO] No tasks to poll (all failed)")
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
                        print(f"   [PARALLEL VIDEO] OK Scene {scene.id} complete")
                        self.state.add_log(f"[VIDEO] Scene {scene.id} generated successfully")
                    else:
                        print(f"   [PARALLEL VIDEO] ERROR Scene {scene.id} failed")
                        self.state.add_log(f"[ERROR] Scene {scene.id} video generation failed")
                except Exception as e:
                    print(f"   [PARALLEL VIDEO] ERROR Scene {scene.id} exception: {e}")
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
