import json
import os
import time
from .state import ProjectState
from .providers.researcher import ResearcherProvider
from .providers.researcher import ResearcherProvider
from .providers.spatial_reasoning import SpatialReasoningProvider
from .providers.agency_director import AgencyDirector
from .config import config
from .parallel_utils import (
    ParallelImageGenerator,
    ParallelAudioGenerator,
    ParallelVideoGenerator,
)
from .utils.style_detector import StyleDetector
from .showroom import publish_render

class AdGenerator:
    """The Orchestrator."""
    
    def __init__(self, project_id: str = None):
        if project_id:
            self.state = ProjectState(id=project_id, user_input="")
        else:
            self.state = ProjectState(user_input="")

        # Strict demo foundation: GPT-5.2 handles all logic side.
        # Other LLM providers are intentionally disabled/unused.
        self.spatial = SpatialReasoningProvider()
        self.spatial = SpatialReasoningProvider()
        self.researcher = ResearcherProvider()
        self.agency = AgencyDirector()

    @staticmethod
    def _parse_duration_seconds(value, default_seconds: int = 15) -> int:
        """
        Frontend sends durations like "15s". Normalize to integer seconds.
        """
        if value is None:
            return default_seconds
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else default_seconds
        return default_seconds

    @staticmethod
    def _normalize_veo_duration_seconds(value: int) -> int:
        """
        Veo supports only 4, 6, or 8 second clips per request.
        """
        allowed = (4, 6, 8)
        try:
            duration = int(value)
        except (TypeError, ValueError):
            duration = 4

        if duration in allowed:
            return duration

        # Pick nearest supported duration; on ties prefer the shorter duration
        # to keep demo runs fast and stable.
        return min(allowed, key=lambda v: (abs(v - duration), v))

    @staticmethod
    def _parse_time_range_seconds(time_range: str) -> tuple[float | None, float | None]:
        if not time_range:
            return (None, None)
        try:
            parts = str(time_range).replace("s", "").split("-")
            start = float(parts[0]) if parts and parts[0].strip() else None
            end = float(parts[1]) if len(parts) > 1 and parts[1].strip() else None
            return (start, end)
        except Exception:
            return (None, None)

    @staticmethod
    def _fmt_s(seconds: float) -> str:
        value = round(float(seconds), 1)
        if value.is_integer():
            return f"{int(value)}s"
        return f"{value:.1f}s"

    @staticmethod
    def _estimate_spoken_seconds(text: str) -> float:
        """
        Rough TTS duration estimate to help pack lines into a scene window.
        """
        words = [w for w in str(text or "").split() if w]
        # ~2.7 words/sec + a small constant for breath/punctuation.
        seconds = (len(words) / 2.7) + 0.2
        return max(0.6, min(seconds, 3.8))

    def _adjust_scene_durations_for_audio(self) -> None:
        """
        AUDIO-FIRST TIMING: Adjust scene durations based on actual TTS length.
        
        1. Measure actual VO duration for each line
        2. Store as line.actual_duration
        3. Adjust scene durations using timing_engine
        4. Snap to beat grid if available
        
        Called AFTER TTS generation, BEFORE video generation.
        """
        if not self.state or not self.state.script:
            return
        
        scenes = getattr(self.state.script, "scenes", []) or []
        lines = getattr(self.state.script, "lines", []) or []
        
        if not scenes or not lines:
            return
        
        import os
        
        # Step 1: Measure actual duration for each line
        try:
            from .utils.timing_engine import probe_audio_duration
            
            for line in lines:
                audio_path = getattr(line, "audio_path", None)
                if audio_path and os.path.exists(str(audio_path)):
                    duration = probe_audio_duration(str(audio_path))
                    line.actual_duration = duration
                    if duration > 0:
                        print(f"   [VO MEASURED] Line: {duration:.2f}s")
                else:
                    line.actual_duration = 0.0
        except Exception as e:
            self.state.add_log(f"[WARN] VO duration measurement failed: {str(e)}")
            return
        
        # Step 2: Adjust scene durations using timing engine
        try:
            from .utils.timing_engine import adjust_scene_durations
            
            beat_grid = getattr(self.state, "beat_grid", None)
            
            adjusted_scenes = adjust_scene_durations(
                scenes=scenes,
                lines=lines,
                beat_grid=beat_grid,
                vo_buffer=0.5,
                min_scene_duration=4.0
            )
            
            self.state.script.scenes = adjusted_scenes
            self.state.add_log("[AUDIO-FIRST] Scene durations adjusted for VO fit")
        except Exception as e:
            self.state.add_log(f"[WARN] Scene adjustment failed: {str(e)}")

    def _auto_fit_voiceover_lines(self, eleven, strategy: dict | None = None) -> None:
        """
        Post-TTS safety pass: ensure generated ElevenLabs audio fits each line's time_range.

        Why: Even with good planning, TTS can run long due to pauses, delivery, or voice model variance.
        This pass measures actual audio duration and (optionally) rewrites + regenerates only the lines
        that exceed their slot, up to a small retry budget.
        """
        if not self.state or not self.state.script or not getattr(self.state.script, "lines", None):
            return

        import os
        import re

        def _env_float(key: str, default: float) -> float:
            raw = os.getenv(key)
            if raw is None:
                return float(default)
            raw = raw.strip()
            if not raw:
                return float(default)
            try:
                return float(raw)
            except Exception:
                return float(default)

        def _env_int(key: str, default: int) -> int:
            raw = os.getenv(key)
            if raw is None:
                return int(default)
            raw = raw.strip()
            if not raw:
                return int(default)
            try:
                return int(raw)
            except Exception:
                return int(default)

        def _env_truthy(key: str, default: bool = True) -> bool:
            raw = os.getenv(key)
            if raw is None:
                return bool(default)
            raw = raw.strip().lower()
            if raw in ("1", "true", "yes", "on"):
                return True
            if raw in ("0", "false", "no", "off"):
                return False
            return bool(default)

        if not _env_truthy("VO_FIT_ENABLED", default=True):
            return

        max_retries = max(0, _env_int("VO_FIT_MAX_RETRIES", 2))
        over_ratio = max(1.0, _env_float("VO_FIT_OVERAGE_RATIO", 1.08))
        over_seconds = max(0.0, _env_float("VO_FIT_OVERAGE_SECONDS", 0.12))

        # Probe durations via ffmpeg-python (requires ffprobe on PATH).
        try:
            import ffmpeg  # type: ignore
        except Exception:
            self.state.add_log("[WARN] VO fit skipped: ffmpeg/ffprobe not available")
            return

        def _probe_audio_duration_seconds(path: str) -> float | None:
            try:
                probe = ffmpeg.probe(path)
                fmt = probe.get("format") if isinstance(probe, dict) else None
                if isinstance(fmt, dict):
                    dur = fmt.get("duration")
                    if dur is not None:
                        return float(dur)
            except Exception:
                return None
            return None

        def _count_sentence_endings(text: str) -> int:
            # Count only real sentence endings: '!'/'?' anywhere, '.' only when followed by whitespace or end.
            return len(re.findall(r"[!?]|\.(?=\s|$)", str(text or "")))

        def _deterministic_shorten(text: str, *, max_words: int, max_sentence_endings: int, tight_slot: bool) -> str:
            t = str(text or "").strip()
            t = re.sub(r"\s+", " ", t).strip()
            if tight_slot:
                t = re.sub(r"^\[[^\]]{1,24}\]\s*", "", t).strip()

            # Reduce pauses by converting early sentence endings to commas.
            endings = list(re.finditer(r"[!?]|\.(?=\s|$)", t))
            if len(endings) > max_sentence_endings and max_sentence_endings >= 1:
                keep_from = max(len(endings) - max_sentence_endings, 0)
                chars = list(t)
                for m in endings[:keep_from]:
                    chars[m.start()] = ","
                t = "".join(chars)
                t = re.sub(r",\s*", ", ", t)
                t = re.sub(r"\s+", " ", t).strip()

            # Trim to max words by dropping trailing clauses first.
            words = [w for w in t.split() if w]
            if len(words) > max_words:
                parts = [p.strip() for p in t.split(",") if p.strip()]
                while len(" ".join(parts).split()) > max_words and len(parts) > 1:
                    parts = parts[:-1]
                t = ", ".join(parts).strip()
                words = [w for w in t.split() if w]
                if len(words) > max_words:
                    t = " ".join(words[:max_words]).strip()

            # Remove dangling stopwords.
            stopwords = {
                "a",
                "an",
                "the",
                "and",
                "or",
                "but",
                "to",
                "of",
                "for",
                "with",
                "at",
                "in",
                "on",
                "all",
                "just",
            }
            words = [w for w in t.split() if w]
            while words and words[-1].strip(".,!?").lower() in stopwords:
                words.pop()
            t = " ".join(words).strip()

            if t and not re.search(r"[\.\!\?]$", t) and not re.search(r"\]$", t):
                t = f"{t}."
            return t

        # Preserve speaker->voice routing across retries (don't reshuffle primary/secondary).
        from .parallel_utils import ParallelAudioGenerator

        voice_router = ParallelAudioGenerator(eleven, self.state)
        voice_id_by_speaker: dict[str, str | None] = {}
        for line in list(self.state.script.lines or []):
            speaker = str(getattr(line, "speaker", "") or "").strip()
            if speaker not in voice_id_by_speaker:
                voice_id_by_speaker[speaker] = voice_router._resolve_voice_id(speaker)

        # Scene lookup for context.
        scenes_by_id: dict[int, object] = {}
        for scene in list(self.state.script.scenes or []):
            try:
                sid = int(getattr(scene, "id", 0) or 0)
            except Exception:
                continue
            if sid > 0:
                scenes_by_id[sid] = scene

        effective_strategy = strategy if isinstance(strategy, dict) else (self.state.strategy if isinstance(self.state.strategy, dict) else {})

        fixed = 0
        checked = 0
        for line in list(self.state.script.lines or []):
            audio_path = getattr(line, "audio_path", None)
            if not audio_path or not os.path.exists(str(audio_path)):
                continue

            start, end = self._parse_time_range_seconds(getattr(line, "time_range", "") or "")
            if start is None or end is None or float(end) <= float(start):
                continue

            # Composer uses a tiny pad; mirror it so we target a safe slot.
            slot_seconds = max(float(end - start) - 0.05, 0.2)
            measured = _probe_audio_duration_seconds(str(audio_path))
            if measured is None:
                continue

            checked += 1
            if measured <= (slot_seconds * over_ratio) and measured <= (slot_seconds + over_seconds):
                continue

            # Only do a couple of retries; keep demo runs fast/reliable.
            speaker = str(getattr(line, "speaker", "") or "").strip()
            scene_id = getattr(line, "scene_id", None)
            try:
                scene_id_int = int(scene_id) if scene_id is not None else None
            except Exception:
                scene_id_int = None

            scene_obj = scenes_by_id.get(scene_id_int or 0)
            scene_payload = None
            if scene_obj is not None:
                scene_payload = {
                    "id": scene_id_int,
                    "visual_prompt": str(getattr(scene_obj, "visual_prompt", "") or ""),
                    "visual_beat": str(getattr(scene_obj, "visual_prompt", "") or "").split("\n", 1)[0][:240],
                    "on_screen": [speaker] if speaker and speaker.lower() not in ("narrator", "voiceover", "vo") else [],
                }

            original_text = str(getattr(line, "text", "") or "")
            words_now = len([w for w in original_text.split() if w]) or 1
            tight_slot = slot_seconds <= 1.6
            max_sentence_endings = 1 if slot_seconds <= 2.0 else 2
            # Aim to shorten proportionally to the overage (with some buffer).
            ratio = max(measured / max(slot_seconds, 0.2), 1.0)
            target_words = max(1, int((words_now / ratio) * 0.90))
            target_words = min(target_words, max(1, int(round(slot_seconds * 2.2 + 1.0))))

            for attempt in range(max_retries + 1):
                if measured <= (slot_seconds * over_ratio) and measured <= (slot_seconds + over_seconds):
                    break

                max_words = max(1, target_words - attempt)  # tighten slightly each retry

                new_text = ""
                try:
                    new_text = self.spatial.rewrite_line_for_slot(
                        strategy=effective_strategy,
                        scene=scene_payload,
                        speaker=speaker,
                        original_text=original_text,
                        slot_seconds=slot_seconds,
                        max_words=max_words,
                        max_sentence_endings=max_sentence_endings,
                        measured_audio_seconds=measured,
                    )
                except Exception:
                    new_text = ""

                if not new_text:
                    new_text = _deterministic_shorten(
                        original_text,
                        max_words=max_words,
                        max_sentence_endings=max_sentence_endings,
                        tight_slot=tight_slot,
                    )

                # If still no meaningful change, tighten deterministically.
                if new_text.strip() == original_text.strip():
                    new_text = _deterministic_shorten(
                        original_text,
                        max_words=max_words,
                        max_sentence_endings=max_sentence_endings,
                        tight_slot=True,
                    )

                # Guardrails: don't introduce lots of pauses.
                if _count_sentence_endings(new_text) > max_sentence_endings:
                    new_text = _deterministic_shorten(
                        new_text,
                        max_words=max_words,
                        max_sentence_endings=max_sentence_endings,
                        tight_slot=True,
                    )

                # Apply + regenerate.
                line.text = new_text
                voice_id = voice_id_by_speaker.get(speaker)
                try:
                    line.audio_path = eleven.generate_speech(new_text, voice_id)
                except Exception as e:
                    self.state.add_log(f"[WARN] VO fit regen failed for '{speaker}': {str(e)}")
                    break

                measured = _probe_audio_duration_seconds(str(line.audio_path)) or measured
                fixed += 1
                original_text = new_text

        if checked:
            self.state.add_log(f"[AUDIO] VO fit check: {fixed} regen(s) over {checked} probed line(s)")

    def _align_dialogue_to_scenes(self, script, strategy: dict | None = None, freeze_speakers: bool = False) -> None:
        """
        Snap dialogue to scene windows so speech lands on the correct visuals.

        - Assign each line to a scene_id (prefer existing scene_id, else infer from speaker/time/order)
        - Ensure time_range stays fully within that scene's time window
        - Optional: if freeze_speakers is False, re-route unmatched speakers to the on-screen primary_subject
        """
        if not script or not getattr(script, "scenes", None) or not getattr(script, "lines", None):
            return

        scenes = list(script.scenes or [])
        lines = list(script.lines or [])
        if not scenes or not lines:
            return

        import re

        # Build scene timeline windows (planned timeline).
        scene_windows: list[tuple[int, float, float]] = []
        cumulative = 0.0
        for scene in scenes:
            try:
                scene_id = int(getattr(scene, "id", 0) or 0)
            except Exception:
                scene_id = len(scene_windows) + 1
            duration = float(getattr(scene, "duration", 0) or 0)
            start = cumulative
            end = cumulative + max(duration, 0.0)
            scene_windows.append((scene_id, start, end))
            cumulative = end

        if not scene_windows:
            return

        id_to_idx = {scene_id: idx for idx, (scene_id, _, _) in enumerate(scene_windows)}
        total_duration = max(scene_windows[-1][2], 1.0)

        # Optional: use the character bible as the source of truth for speaker names.
        character_names: list[str] = []
        if isinstance(strategy, dict):
            chars = strategy.get("characters")
            if isinstance(chars, list):
                for ch in chars:
                    if isinstance(ch, dict):
                        name = str(ch.get("name") or "").strip()
                        if name:
                            character_names.append(name)
        name_map = {n.lower(): n for n in character_names}

        def _canonical_speaker(value: str) -> str:
            s = (value or "").strip()
            if not s:
                return ""
            lower = s.lower()
            if lower in ("narrator", "voiceover", "vo"):
                return "Narrator"

            # If the string contains a known name, prefer that (handles verbose speaker labels).
            for nl, canon in name_map.items():
                if re.search(rf"\\b{re.escape(nl)}\\b", lower):
                    return canon

            # Strip common descriptive suffixes.
            for sep in (",", " - ", " — ", ":", " at ", " in "):
                if sep in s:
                    head = s.split(sep, 1)[0].strip()
                    if head:
                        lower_head = head.lower()
                        if lower_head in name_map:
                            return name_map[lower_head]
                        # If the first token is a known name, use it.
                        first = head.split()[0] if head.split() else head
                        if first.lower() in name_map:
                            return name_map[first.lower()]
                        return head

            # Fallback: first token (keeps speaker stable for VO routing).
            first = s.split()[0] if s.split() else s
            if first.lower() in name_map:
                return name_map[first.lower()]
            return first or s

        def _is_narrator(name: str) -> bool:
            return (name or "").strip().lower() in ("narrator", "voiceover", "vo")

        def _scene_mentions(scene, name: str) -> bool:
            if not name:
                return False
            if _is_narrator(name):
                return True
            needle = re.escape(name.strip())
            pattern = re.compile(rf"\\b{needle}\\b", re.IGNORECASE)
            for field in ("primary_subject", "visual_prompt", "subject_description"):
                value = str(getattr(scene, field, "") or "")
                if value and pattern.search(value):
                    return True
            return False

        # Capacity per scene (avoid crowding lines into a 4s scene).
        max_lines_per_scene: list[int] = []
        for scene in scenes:
            dur = float(getattr(scene, "duration", 0) or 0)
            if dur <= 4:
                max_lines_per_scene.append(3)
            elif dur <= 6:
                max_lines_per_scene.append(4)
            else:
                max_lines_per_scene.append(5)
        assigned_counts = [0 for _ in scenes]

        # Pre-parse hints for stable ordering.
        start_hints: list[float | None] = []
        for line in lines:
            start_hint, _ = self._parse_time_range_seconds(getattr(line, "time_range", "") or "")
            start_hints.append(start_hint)

        # Assign scene_id for each line.
        for i, line in enumerate(lines):
            speaker_raw = str(getattr(line, "speaker", "") or "").strip()
            speaker = _canonical_speaker(speaker_raw)
            if not freeze_speakers and speaker and speaker != speaker_raw:
                line.speaker = speaker
            if _is_narrator(speaker):
                speaker = "Narrator"
                if not freeze_speakers:
                    line.speaker = speaker

            explicit_scene_id = getattr(line, "scene_id", None)
            try:
                explicit_scene_id = int(explicit_scene_id) if explicit_scene_id is not None else None
            except Exception:
                explicit_scene_id = None

            candidate_scene_ids = []
            if speaker and not _is_narrator(speaker):
                for scene_id, _, _ in scene_windows:
                    idx = id_to_idx.get(scene_id)
                    if idx is None:
                        continue
                    if _scene_mentions(scenes[idx], speaker):
                        candidate_scene_ids.append(scene_id)

            assigned_scene_id = None

            # In strict planning mode, GPT provides scene_id. Treat it as authoritative if valid.
            if explicit_scene_id in id_to_idx:
                assigned_scene_id = explicit_scene_id
            else:
                # Use time hint if it falls into a scene window.
                start_hint = start_hints[i]
                if start_hint is not None:
                    for scene_id, start, end in scene_windows:
                        if float(start_hint) >= start and float(start_hint) < end:
                            # If we know which scenes the speaker appears in, don't place them
                            # into an off-screen scene just because the time hint falls there.
                            if (not candidate_scene_ids) or (scene_id in candidate_scene_ids) or _is_narrator(speaker):
                                assigned_scene_id = scene_id
                            break

            # If still not assigned, use a speaker-matching scene with remaining capacity.
            if assigned_scene_id is None and candidate_scene_ids:
                for scene_id in candidate_scene_ids:
                    idx = id_to_idx.get(scene_id)
                    if idx is None:
                        continue
                    if assigned_counts[idx] < max_lines_per_scene[idx]:
                        assigned_scene_id = scene_id
                        break
                if assigned_scene_id is None:
                    assigned_scene_id = candidate_scene_ids[0]

            # Final fallback: distribute evenly across scenes.
            if assigned_scene_id is None:
                idx = min(int(i * len(scenes) / max(len(lines), 1)), len(scenes) - 1)
                assigned_scene_id = scene_windows[idx][0]

            # If the speaker doesn't appear in the chosen scene and we can edit speakers,
            # reroute to the scene's primary_subject for better on-screen match.
            chosen_idx = id_to_idx.get(assigned_scene_id)
            # IMPORTANT: Do not rewrite valid character speakers (it causes tone/person mismatches).
            # Only reroute if the planner produced an unknown/invalid speaker label.
            if (
                chosen_idx is not None
                and speaker
                and not _is_narrator(speaker)
                and character_names
                and speaker not in character_names
                and not _scene_mentions(scenes[chosen_idx], speaker)
            ):
                primary = str(getattr(scenes[chosen_idx], "primary_subject", "") or "").strip()
                primary_canon = _canonical_speaker(primary)
                if primary_canon and not freeze_speakers:
                    line.speaker = primary_canon

            line.scene_id = assigned_scene_id
            if chosen_idx is not None:
                assigned_counts[chosen_idx] += 1

        # Enforce per-scene dialogue line budgets to prevent "machine-gun" VO
        # that must be time-compressed or hard-trimmed (common demo failure mode).
        # Prefer moving overflow lines to the next feasible scene for that speaker.
        scene_id_to_lines: dict[int, list[tuple[int, object]]] = {}
        for idx, line in enumerate(lines):
            try:
                sid = int(getattr(line, "scene_id", 0) or 0)
            except Exception:
                continue
            if sid in id_to_idx:
                scene_id_to_lines.setdefault(sid, []).append((idx, line))

        # Current counts per scene index.
        counts = [0 for _ in scenes]
        for sid, group in scene_id_to_lines.items():
            scene_idx = id_to_idx.get(sid)
            if scene_idx is not None:
                counts[scene_idx] = len(group)

        def _scene_ids_for_speaker(name: str) -> list[int]:
            if not name:
                return []
            if _is_narrator(name):
                return [sid for sid, _, _ in scene_windows]
            ids: list[int] = []
            for sid, _, _ in scene_windows:
                idx = id_to_idx.get(sid)
                if idx is None:
                    continue
                if _scene_mentions(scenes[idx], name):
                    ids.append(sid)
            return ids

        for scene_idx, (scene_id, _, _) in enumerate(scene_windows):
            cap = max_lines_per_scene[scene_idx] if scene_idx < len(max_lines_per_scene) else None
            if cap is None or cap <= 0:
                continue
            group = scene_id_to_lines.get(scene_id) or []
            if len(group) <= cap:
                continue

            # Move the last lines first (keeps the opening beats in the intended scene).
            overflow = group[cap:]
            scene_id_to_lines[scene_id] = group[:cap]
            counts[scene_idx] = cap

            for orig_idx, line in overflow:
                speaker_name = _canonical_speaker(str(getattr(line, "speaker", "") or "").strip())
                preferred_scene_ids = _scene_ids_for_speaker(speaker_name)

                def _can_place(target_idx: int, target_sid: int) -> bool:
                    if target_idx < 0 or target_idx >= len(counts):
                        return False
                    if counts[target_idx] >= max_lines_per_scene[target_idx]:
                        return False
                    # If we have explicit candidate scenes for the speaker, respect them.
                    if preferred_scene_ids and target_sid not in preferred_scene_ids and not _is_narrator(speaker_name):
                        return False
                    return True

                target_sid = None
                # Prefer forward scenes for narrative flow.
                for offset in range(1, len(scene_windows) + 1):
                    f_idx = scene_idx + offset
                    if f_idx < len(scene_windows):
                        f_sid = scene_windows[f_idx][0]
                        if _can_place(f_idx, f_sid):
                            target_sid = f_sid
                            break
                    b_idx = scene_idx - offset
                    if b_idx >= 0:
                        b_sid = scene_windows[b_idx][0]
                        if _can_place(b_idx, b_sid):
                            target_sid = b_sid
                            break

                if target_sid is None:
                    # No capacity anywhere. Keep it in the original scene as a last resort.
                    target_sid = scene_id
                    target_idx = scene_idx
                else:
                    target_idx = id_to_idx.get(target_sid, scene_idx)

                line.scene_id = target_sid
                scene_id_to_lines.setdefault(target_sid, []).append((orig_idx, line))
                if 0 <= target_idx < len(counts):
                    counts[target_idx] += 1

        # Pack time ranges inside each scene window.
        lines_by_scene: dict[int, list[tuple[int, object]]] = {}
        for idx, line in enumerate(lines):
            try:
                sid = int(getattr(line, "scene_id", 0) or 0)
            except Exception:
                sid = 0
            if sid not in id_to_idx:
                sid = scene_windows[min(idx, len(scene_windows) - 1)][0]
                line.scene_id = sid
            lines_by_scene.setdefault(sid, []).append((idx, line))

        for scene_id, scene_start, scene_end in scene_windows:
            group = lines_by_scene.get(scene_id) or []
            if not group:
                continue

            scene_idx = id_to_idx.get(scene_id)
            scene_duration = max(scene_end - scene_start, 0.1)

            # Order within scene: use original time hints if present, else original order.
            group.sort(key=lambda item: ((start_hints[item[0]] is None), start_hints[item[0]] or 0.0, item[0]))

            n = len(group)
            gap = 0.05
            pad_in = min(0.08, scene_duration * 0.05)
            pad_out = min(0.08, scene_duration * 0.05)
            available = scene_duration - pad_in - pad_out - gap * (n - 1)
            if available < 0.3:
                pad_in = 0.0
                pad_out = 0.0
                gap = 0.02
                available = max(scene_duration - gap * (n - 1), 0.1)

            weights = [self._estimate_spoken_seconds(getattr(line, "text", "")) for _, line in group]
            total_w = sum(weights) or 1.0
            scale = available / total_w if total_w > 0 else 1.0
            # Keep things punchy in short scenes; don't over-stretch to fill.
            scale = min(scale, 1.0) if scene_duration <= 4.5 else scale

            durations = [max(0.25, w * scale) for w in weights]
            # Re-normalize if min clamps pushed us over budget.
            dur_sum = sum(durations) or 1.0
            if dur_sum > available and dur_sum > 0:
                shrink = available / dur_sum
                durations = [max(0.2, d * shrink) for d in durations]

            t = scene_start + pad_in
            for (orig_idx, line), dur in zip(group, durations):
                start = max(scene_start, min(t, scene_end))
                end = max(start + 0.1, min(start + dur, scene_end - pad_out))
                line.time_range = f"{self._fmt_s(start)}-{self._fmt_s(end)}"
                t = end + gap

        # Reorder lines by final start time so downstream audio mixing is stable.
        def _line_sort_key(line) -> float:
            start, _ = self._parse_time_range_seconds(getattr(line, "time_range", "") or "")
            return float(start) if start is not None else total_duration + 1.0

        script.lines.sort(key=_line_sort_key)
        self.state.add_log(f"[ALIGN] Snapped {len(script.lines)} dialogue lines to scene windows")

    def _ensure_scene_characters_match_dialogue(self, script) -> None:
        """
        Ensure that any speaking character for a scene is explicitly mentioned in that scene prompt.

        This improves generative adherence (Veo/Flux) so on-screen action matches dialogue, reducing
        the classic "audio doesn't match who is visible" demo failure mode.
        """
        if not script or not getattr(script, "scenes", None) or not getattr(script, "lines", None):
            return

        import re

        scene_to_speakers: dict[int, list[str]] = {}
        for line in list(script.lines or []):
            speaker = str(getattr(line, "speaker", "") or "").strip()
            if not speaker or speaker.lower() in ("narrator", "voiceover", "vo"):
                continue
            try:
                sid = int(getattr(line, "scene_id", 0) or 0)
            except Exception:
                continue
            if sid <= 0:
                continue
            scene_to_speakers.setdefault(sid, [])
            if speaker not in scene_to_speakers[sid]:
                scene_to_speakers[sid].append(speaker)

        if not scene_to_speakers:
            return

        for scene in list(script.scenes or []):
            try:
                sid = int(getattr(scene, "id", 0) or 0)
            except Exception:
                continue
            needed = scene_to_speakers.get(sid) or []
            if not needed:
                continue

            primary = str(getattr(scene, "primary_subject", "") or "")
            desc = str(getattr(scene, "subject_description", "") or "")
            visual = str(getattr(scene, "visual_prompt", "") or "")
            haystack = f"{primary}\n{desc}\n{visual}".lower()

            missing: list[str] = []
            for name in needed:
                if not re.search(rf"\\b{re.escape(name.lower())}\\b", haystack):
                    missing.append(name)

            if not missing:
                continue

            cast = ", ".join(needed) if len(needed) > 1 else needed[0]
            if len(needed) == 1:
                anchor = f"On-screen: {cast}, clearly visible. "
            elif len(needed) == 2:
                anchor = f"On-screen: {cast}, both clearly visible. "
            else:
                anchor = f"On-screen: {cast}, all clearly visible. "
            if not visual.lower().startswith("on-screen:"):
                scene.visual_prompt = anchor + visual

            if cast and cast.lower() not in primary.lower():
                primary_clean = primary.strip()
                if not primary_clean:
                    scene.primary_subject = cast
                else:
                    scene.primary_subject = f"{primary_clean} ({cast})"

        self.state.add_log("[SCENES] Ensured scene prompts include speaking characters")
        
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
        else:
            # Log the key user-facing controls so the UI can verify they're applied.
            def _fmt(val):
                if isinstance(val, list):
                    parts = [str(v).strip() for v in val if str(v).strip()]
                    return ", ".join(parts)
                return str(val).strip() if val is not None else ""

            self.state.add_log(
                "[INPUT] "
                f"topic='{_fmt(config_overrides.get('topic'))}', "
                f"url='{_fmt(config_overrides.get('url'))}', "
                f"style='{_fmt(config_overrides.get('style'))}', "
                f"mood='{_fmt(config_overrides.get('mood'))}', "
                f"platform='{_fmt(config_overrides.get('platform'))}', "
                f"template='{_fmt(config_overrides.get('commercial_style'))}', "
                f"camera='{_fmt(config_overrides.get('camera_style'))}', "
                f"image_guidance='{_fmt(config_overrides.get('image_guidance'))}', "
                f"video_model='{_fmt(config_overrides.get('video_model'))}', "
                f"player_mode='{_fmt(config_overrides.get('player_mode'))}'"
            )

        # Auto-variety defaults (prevents the "one-trick pony" look when users leave defaults).
        # UI can send "auto"; here we convert that into concrete, deterministic choices per brand.
        try:
            import hashlib

            def _is_auto(v) -> bool:
                if v is None:
                    return True
                if isinstance(v, str):
                    return v.strip().lower() in ("", "auto", "random", "varied", "default")
                if isinstance(v, list):
                    cleaned = [str(x).strip() for x in v if str(x).strip()]
                    if not cleaned:
                        return True
                    return all(x.lower() in ("auto", "random", "varied", "default") for x in cleaned)
                return False

            def _seeded_pick(options: list[str], seed_str: str) -> str:
                if not options:
                    return ""
                h = hashlib.md5(seed_str.encode("utf-8", errors="ignore")).hexdigest()
                idx = int(h[:8], 16) % len(options)
                return options[idx]

            seed_basis = f"{str(config_overrides.get('url') or '').strip()}|{user_input}".strip()

            # 1) Commercial template: pick a different iconic arc per brand by default.
            if _is_auto(config_overrides.get("commercial_style")):
                from .constants.iconic_templates import ICONIC_TEMPLATES

                template_key = _seeded_pick(list(ICONIC_TEMPLATES.keys()), seed_basis or str(self.state.id))
                if template_key:
                    config_overrides["commercial_style"] = template_key

            template_now = str(config_overrides.get("commercial_style") or "").strip()

            # 2) Lighting + grade: avoid always defaulting to teal/orange blockbuster.
            if _is_auto(config_overrides.get("lighting_preference")):
                lighting_pool = {
                    "tech_reveal": ["studio", "bright"],
                    "problem_solution": ["studio", "bright"],
                    "catchphrase_comedy": ["bright", "natural"],
                    "mascot_story": ["natural", "bright"],
                    "emotional_journey": ["natural", "moody"],
                    "aspirational_lifestyle": ["natural", "bright"],
                    "sensory_metaphor": ["dramatic", "moody"],
                }.get(template_now, ["natural", "studio", "bright", "moody", "dramatic"])
                config_overrides["lighting_preference"] = _seeded_pick(lighting_pool, seed_basis + "|lighting")

            if _is_auto(config_overrides.get("color_grade")):
                grade_pool = {
                    "tech_reveal": ["kodak_5219", "fuji_film_stock", "bleach_bypass"],
                    "problem_solution": ["kodak_5219", "bleach_bypass", "fuji_film_stock"],
                    "catchphrase_comedy": ["fuji_film_stock", "kodak_5219"],
                    "mascot_story": ["fuji_film_stock", "vintage_analog"],
                    "emotional_journey": ["kodak_5219", "vintage_analog"],
                    "aspirational_lifestyle": ["kodak_5219", "fuji_film_stock"],
                    "sensory_metaphor": ["vintage_analog", "hollywood_blockbuster", "neon_cyberpunk"],
                }.get(template_now, ["kodak_5219", "fuji_film_stock", "bleach_bypass", "vintage_analog", "neon_cyberpunk"])
                config_overrides["color_grade"] = _seeded_pick(grade_pool, seed_basis + "|grade")

            # 3) Camera movement: if user picked Auto, let GPT decide per-scene by leaving blank.
            if _is_auto(config_overrides.get("camera_style")):
                config_overrides["camera_style"] = []

            # Log resolved auto selections for demo transparency.
            try:
                self.state.add_log(
                    "[AUTO] "
                    f"template='{str(config_overrides.get('commercial_style') or '').strip()}', "
                    f"lighting='{str(config_overrides.get('lighting_preference') or '').strip()}', "
                    f"grade='{str(config_overrides.get('color_grade') or '').strip()}', "
                    f"camera='{', '.join([str(x) for x in (config_overrides.get('camera_style') or [])])}'"
                )
            except Exception:
                pass

        except Exception:
            pass

        # Phase 1.5: Research (if URL provided in input OR config)
        context = user_input
        website_data = ""
        
        def _normalize_url(candidate: str | None) -> str | None:
            if not candidate:
                return None
            s = str(candidate).strip().strip('"').strip("'")
            if not s:
                return None
            if s.lower().startswith(("http://", "https://")):
                return s
            # Domain-only input (common in demos): botspot.trade → https://botspot.trade
            if "." in s and " " not in s and "/" not in s and "@" not in s:
                return f"https://{s}"
            return None

        # Check for URL in config_overrides first (new UI), then try topic-as-url, then user_input (legacy).
        target_url = _normalize_url(config_overrides.get("url") if config_overrides else None)

        # If the user pasted a domain/URL into the Topic box, treat it as the URL source of truth.
        if not target_url:
            target_url = _normalize_url(config_overrides.get("topic") if config_overrides else None)

        # Fallback: parse a URL from the free-form prompt string (e.g., "URL: https://…").
        if not target_url:
            import re
            match = re.search(r"\bURL:\s*(\S+)", user_input or "")
            if match:
                target_url = _normalize_url(match.group(1))

        # Allow domain-only prompts (e.g. "botspot.trade") and URL-first prompts.
        if not target_url and user_input:
            first_token = (user_input or "").strip().split()[0]
            target_url = _normalize_url(first_token)

        if target_url:
            # If URL was inferred (e.g. user pasted a domain into Topic), persist it so
            # downstream logic and plan verification can see the resolved URL.
            if config_overrides is not None and not str(config_overrides.get("url") or "").strip():
                config_overrides["url"] = target_url

            print(f"[URL] Detected: {target_url}. Launching Researcher...")
            self.state.add_log(f"[RESEARCH] Analyzing target URL: {target_url}...")
            extracted = self.researcher.fetch_and_extract(target_url)
            print(f"[RESEARCH] Extracted:\n{extracted[:500]}...")
            self.state.add_log(f"[RESEARCH] Site extraction complete. Extracted {len(extracted)} chars of context.")
            context = extracted
            website_data = extracted
            self.state.research_brief = extracted

        print(f"[BRAIN] Brainstorming cinematic ad concept...")
        self.state.add_log(f"[STRATEGY] Initializing creative brainstorm for: {user_input}")

        target_duration = self._parse_duration_seconds(config_overrides.get("duration"), default_seconds=15)

        # ========================================================================================
        # Video Model Selection (Veo vs Runway)
        # ========================================================================================
        raw_video_model = str(config_overrides.get("video_model") or "").strip().lower()
        if raw_video_model in ("", "auto", "default", "recommended"):
            video_model = "auto"
        elif raw_video_model in ("veo", "google", "vertex", "veo3"):
            video_model = "veo"
        elif raw_video_model in ("runway", "runwayml", "gen3", "gen-3"):
            video_model = "runway"
        else:
            video_model = "auto"
        config_overrides["video_model"] = video_model
        self.state.video_model = video_model

        # ========================================================================================
        # Reference Image Guidance (Prompt + I2I)
        # ========================================================================================
        try:
            from .state import UploadedAsset as UploadedAssetModel
            from PIL import Image

            def _norm_guidance(v: object) -> str:
                raw = str(v or "").strip().lower()
                if raw in ("", "auto", "default"):
                    return "i2i_only"
                if raw in ("none", "off", "disabled", "no"):
                    return "none"
                if raw in ("veo", "veo_only", "veo_text", "veo_text_only", "text_to_video", "text-to-video", "t2v"):
                    return "veo_text_only"
                if raw in ("i2i", "image", "image_directed", "image-directed", "i2i_only"):
                    return "i2i_only"
                if raw in ("prompt", "prompt_only", "prompt-directed", "prompt_directed"):
                    return "prompt_only"
                if raw in ("both", "prompt+i2i", "prompt_and_i2i", "prompt+image", "prompt_image"):
                    return "prompt_and_i2i"
                return raw or "i2i_only"

            guidance = _norm_guidance(config_overrides.get("image_guidance"))
            config_overrides["image_guidance"] = guidance
            self.state.image_guidance = guidance
            if guidance == "veo_text_only":
                # "Total Veo" mode: skip image generation and let Veo generate visuals (and optionally native audio).
                # Also force cut edits so we can preserve Veo clip audio in the final assembly.
                self.state.veo_generate_audio = True
                self.state.transition_type = "cut"
                # Runway requires source images, so force Veo when doing prompt-only runs.
                self.state.video_model = "veo"

            uploads_v2 = config_overrides.get("uploaded_assets_v2")
            if isinstance(uploads_v2, list):
                parsed: list[UploadedAssetModel] = []
                for rec in uploads_v2:
                    if not isinstance(rec, dict):
                        continue
                    filename = str(rec.get("filename") or "").strip()
                    if not filename:
                        continue
                    mode = str(rec.get("mode") or "reference").strip().lower() or "reference"
                    if mode not in ("reference", "direct"):
                        mode = "reference"
                    parsed.append(UploadedAssetModel(filename=filename, mode=mode))
                if parsed:
                    self.state.uploaded_assets_v2 = parsed

            if guidance == "veo_text_only":
                config_overrides["video_model"] = "veo"

            # Persist UI playback strategy with the project (helps demos on machines/browsers with quirks).
            raw_player_mode = str(config_overrides.get("player_mode") or "").strip().lower()
            if raw_player_mode in ("", "auto", "default"):
                player_mode = "auto"
            elif raw_player_mode in ("direct", "mp4", "url"):
                player_mode = "direct"
            elif raw_player_mode in ("blob", "download", "objecturl", "object_url"):
                player_mode = "blob"
            else:
                player_mode = "auto"
            config_overrides["player_mode"] = player_mode
            self.state.player_mode = player_mode

            def _pick_reference_upload_path() -> str | None:
                refs = [a for a in (self.state.uploaded_assets_v2 or []) if str(getattr(a, "mode", "")).lower() == "reference"]
                if not refs:
                    return None
                candidate = os.path.join(config.ASSETS_DIR, "user_uploads", str(refs[0].filename))
                return candidate if os.path.exists(candidate) else None

            def _style_guide_from_image(path: str) -> str:
                img = Image.open(path).convert("RGB")
                # Small thumb for fast stats.
                thumb = img.resize((128, 128))
                pixels = list(thumb.getdata())
                if not pixels:
                    return "Reference style: unavailable."

                # Brightness/contrast (luma).
                lum = [(0.2126 * r + 0.7152 * g + 0.0722 * b) for (r, g, b) in pixels]
                mean_l = sum(lum) / len(lum)
                var_l = sum((x - mean_l) ** 2 for x in lum) / max(1, len(lum) - 1)
                std_l = var_l ** 0.5

                # Saturation (HSV-ish quick approximation).
                sat = []
                for (r, g, b) in pixels:
                    mx = max(r, g, b)
                    mn = min(r, g, b)
                    sat.append(0 if mx == 0 else (mx - mn) / mx)
                mean_s = sum(sat) / len(sat)

                # Temperature (warm vs cool).
                mean_r = sum(p[0] for p in pixels) / len(pixels)
                mean_b = sum(p[2] for p in pixels) / len(pixels)
                temp = mean_r - mean_b

                def _bucket(val: float, lo: float, hi: float) -> str:
                    if val < lo:
                        return "low"
                    if val > hi:
                        return "high"
                    return "medium"

                brightness = _bucket(mean_l, 90, 170)
                contrast = _bucket(std_l, 35, 70)
                saturation = _bucket(mean_s, 0.18, 0.40)
                temperature = "warm" if temp > 18 else ("cool" if temp < -18 else "neutral")

                # Dominant palette (quantized).
                q = thumb.quantize(colors=6, method=2)
                pal = q.getpalette() or []
                counts = sorted(q.getcolors() or [], reverse=True)
                colors: list[str] = []
                for count, idx in counts[:5]:
                    base = idx * 3
                    if base + 2 >= len(pal):
                        continue
                    r, g, b = pal[base], pal[base + 1], pal[base + 2]
                    colors.append(f"#{r:02X}{g:02X}{b:02X}")
                colors = [c for i, c in enumerate(colors) if c and c not in colors[:i]]

                return (
                    "Reference style guide (apply to all scenes): "
                    f"palette {', '.join(colors) if colors else 'auto'}, "
                    f"lighting {brightness}-key, {contrast}-contrast, "
                    f"color {temperature} temperature, {saturation} saturation. "
                    "No readable text; screens off unless abstract icon-only UI."
                )

            # Prompt enrichment from reference image (palette/lighting only; no object detection).
            if guidance in ("prompt_only", "prompt_and_i2i"):
                ref_path = _pick_reference_upload_path()
                if ref_path:
                    guide = _style_guide_from_image(ref_path)
                    self.state.reference_style_guide = guide
                    config_overrides["reference_style_guide"] = guide
                    self.state.add_log("[REFERENCE] Prompt enrichment enabled from reference image (style-only)")
        except Exception as e:
            self.state.add_log(f"[WARN] Reference image guidance skipped: {str(e)}")

        if not self.spatial.is_available():
            raise RuntimeError("GPT-5.2 is required for planning. Set OPENAI_API_KEY in the root .env file.")

        self.state.add_log("[GPT-5.2] Running full creative direction...")
        
        # [AGENCY DIRECTOR PIPELINE]
        # Attempt to use the new 4-step Agency Director. 
        # If it fails (or isn't available), fall back to the legacy single-shot Spatial Reasoning.
        strategy = None
        script_data = None
        
        try:
            if self.agency.is_available():
                self.state.add_log("[AGENCY] Engaging Agency Director (4-Step Pipeline)...")
                strategy, script_data = self.agency.run_pipeline(
                    topic=user_input,
                    website_data=website_data,
                    constraints=config_overrides or {},
                    target_duration=target_duration
                )
                self.state.add_log("[AGENCY] Pipeline execution successful.")
        except Exception as e:
            print(f"[AGENCY] Pipeline failed ({type(e).__name__}): {e}")
            self.state.add_log(f"[WARN] Agency Director failed. Falling back to legacy brain. Error: {e}")
            strategy = None
            script_data = None
            
        if not strategy or not script_data:
            if self.agency.is_available(): # Only log if we TRIED agency and failed/skipped
                 self.state.add_log("[FALLBACK] Running legacy Spatial Reasoning...")
            
            strategy, script_data = self.spatial.full_creative_direction(
                topic=user_input,
                website_data=website_data,
                constraints=config_overrides or {},
                target_duration=target_duration,
            )

        scene_count = len(script_data.get("scenes", [])) if isinstance(script_data, dict) else 0
        if scene_count == 0:
            raise RuntimeError("GPT-5.2 returned 0 scenes. Cannot proceed in strict mode.")

        self.state.add_log(f"[GPT-5.2] Created strategy + {scene_count} scenes")
        self.state.strategy = strategy
        
        # Convert dict to Script object if needed
        from .state import Script, Scene, ScriptLine
        if isinstance(script_data, dict):
            scenes = [Scene(**s) if isinstance(s, dict) else s for s in script_data.get('scenes', [])]
            
            # Map speaker names to voice styles for emotive TTS
            char_map = {}
            for ch in (strategy.get("characters") or []):
                if isinstance(ch, dict):
                    name = str(ch.get("name") or "").strip()
                    style = str(ch.get("voice_style") or "").strip()
                    if name and style:
                        char_map[name] = style

            lines = []
            for l in script_data.get('lines', []):
                if isinstance(l, dict):
                    # Inject voice_style if missing
                    if not l.get("voice_style"):
                        sp = str(l.get("speaker") or "").strip()
                        if sp in char_map:
                            l["voice_style"] = char_map[sp]
                    lines.append(ScriptLine(**l))
                else:
                    lines.append(l)

            script = Script(scenes=scenes, lines=lines)
        else:
            script = script_data

        # Normalize scene durations to Veo-supported values.
        for scene in script.scenes:
            scene.duration = self._normalize_veo_duration_seconds(scene.duration)

        # Duration reconciliation: GPT plans to target_duration, but crossfades shorten the cut
        # and models can under-shoot. Adjust 4/6/8s allocations so final length matches the UI.
        try:
            target = float(target_duration or 0) or 15.0
            trans = str(config_overrides.get("transition") or "").strip().lower()
            overlap = 0.0 if trans in ("cut",) else 0.3
            n = len(script.scenes or [])
            # Approximate: xfade overlaps reduce runtime by ~overlap*(n-1).
            desired_sum = target + overlap * max(0, n - 1)

            allowed = (4, 6, 8)

            def _bump(d: int) -> int:
                if d <= 4:
                    return 6
                if d <= 6:
                    return 8
                return 8

            def _drop(d: int) -> int:
                if d >= 8:
                    return 6
                if d >= 6:
                    return 4
                return 4

            # Deterministic but non-repeating across brands.
            import hashlib

            seed_str = f"{self.state.id}|{user_input}|{config_overrides.get('url') or ''}"
            seed_idx = int(hashlib.md5(seed_str.encode('utf-8', errors='ignore')).hexdigest()[:8], 16)

            def _total() -> float:
                return float(sum(float(getattr(s, "duration", 0) or 0) for s in (script.scenes or [])))

            total = _total()
            safety = 0
            tol = 1.0
            # Increase durations until we meet target.
            while total < (desired_sum - tol) and safety < 64:
                safety += 1
                progressed = False
                for k in range(n):
                    idx = (seed_idx + k) % max(n, 1)
                    s = script.scenes[idx]
                    d0 = int(getattr(s, "duration", 4) or 4)
                    if d0 not in allowed:
                        d0 = self._normalize_veo_duration_seconds(d0)
                    d1 = _bump(d0)
                    if d1 != d0:
                        s.duration = d1
                        progressed = True
                        total = _total()
                        if total >= (desired_sum - tol):
                            break
                if not progressed:
                    break

            # Decrease if we overshot significantly.
            safety = 0
            total = _total()
            while total > (desired_sum + tol) and safety < 64:
                safety += 1
                progressed = False
                for k in range(n):
                    idx = (seed_idx + k) % max(n, 1)
                    s = script.scenes[idx]
                    d0 = int(getattr(s, "duration", 4) or 4)
                    d1 = _drop(d0)
                    if d1 != d0:
                        s.duration = d1
                        progressed = True
                        total = _total()
                        if total <= (desired_sum + tol):
                            break
                if not progressed:
                    break

        except Exception:
            pass

        # Compute the final timeline.
        scene_starts: list[float] = []
        cumulative: float = 0.0
        for scene in script.scenes:
            scene_starts.append(cumulative)
            cumulative += float(scene.duration or 0)

        # Snap dialogue timing/speakers to the scene timeline so VO lands on the correct visuals.
        self._align_dialogue_to_scenes(script, strategy=strategy, freeze_speakers=False)

        # Dialogue polish pass: fix wrong-speaker responses and keep speaker labels clean.
        try:
            polished_lines = self.spatial.polish_dialogue_lines(strategy, script, target_duration=target_duration)
            if polished_lines:
                script.lines = [ScriptLine(**l) for l in polished_lines if isinstance(l, dict)]
                # Re-snap timings without changing speakers (the dialogue doctor decided them).
                self._align_dialogue_to_scenes(script, strategy=strategy, freeze_speakers=True)
                self.state.add_log("[DIALOGUE] Polished speaker attribution + tone")
        except Exception as e:
            self.state.add_log(f"[WARN] Dialogue polish skipped: {str(e)}")

        # Tighten dialogue text to fit the final time slots (prevents rushed/cut VO).
        try:
            tightened_lines = self.spatial.tighten_dialogue_to_time_ranges(strategy, script, target_duration=target_duration)
            if tightened_lines:
                script.lines = [ScriptLine(**l) for l in tightened_lines if isinstance(l, dict)]
                self.state.add_log("[DIALOGUE] Tightened line length to fit timing slots")
        except Exception as e:
            self.state.add_log(f"[WARN] Dialogue timing tighten skipped: {str(e)}")

        # Shot/prompt polish pass: rewrite scene prompts to match dialogue beats and improve framing.
        try:
            polished_scenes = self.spatial.polish_scene_prompts(strategy, script, target_duration=target_duration)
            if polished_scenes:
                # Update only the prompt fields we expect; preserve any already-generated asset paths.
                by_id = {int(getattr(s, "id", 0) or 0): s for s in (script.scenes or [])}
                for ps in polished_scenes:
                    try:
                        sid = int(ps.get("id") if isinstance(ps, dict) else None)
                    except Exception:
                        continue
                    if sid not in by_id:
                        continue
                    scene = by_id[sid]
                    if isinstance(ps, dict):
                        if ps.get("visual_prompt"):
                            scene.visual_prompt = str(ps.get("visual_prompt"))
                        if ps.get("motion_prompt"):
                            scene.motion_prompt = str(ps.get("motion_prompt"))
                        if ps.get("audio_prompt") is not None:
                            audio_val = str(ps.get("audio_prompt") or "").strip()
                            scene.audio_prompt = audio_val or None
                        if ps.get("primary_subject"):
                            scene.primary_subject = str(ps.get("primary_subject") or "").strip() or scene.primary_subject
                        if ps.get("subject_description"):
                            scene.subject_description = str(ps.get("subject_description") or "").strip() or scene.subject_description
                self.state.add_log("[SCENES] Polished shot framing + prompts for better video alignment")
        except Exception as e:
            self.state.add_log(f"[WARN] Scene prompt polish skipped: {str(e)}")

        # Ensure scenes explicitly mention any speaking characters for better generative adherence.
        self._ensure_scene_characters_match_dialogue(script)

        self.state.script = script

        # Extract and save frontend cinematography preferences to state
        if config_overrides:
            # Save transition preference for later use in Composer
            if config_overrides.get('transition'):
                # Map frontend transition names to FFmpeg xfade filter names
                transition_map = {
                    # Frontend values may come in as Title Case or lowercase.
                    # FFmpeg `xfade` supports named transitions like `fade`, `wipeleft`, `slideleft`.
                    "Crossfade": "fade",
                    "crossfade": "fade",
                    "Fade": "fade",
                    "fade": "fade",
                    "Wipe": "wipeleft",
                    "wipe": "wipeleft",
                    "Slide": "slideleft",
                    "slide": "slideleft",
                    "Cut": "cut",
                    "cut": "cut",
                }
                frontend_transition = config_overrides.get('transition')
                self.state.transition_type = transition_map.get(frontend_transition, "fade")

            # Optional: Veo native audio generation (embedded music/SFX/dialogue).
            # Off by default for demo reliability and controllability.
            if config_overrides.get("veo_generate_audio") is not None:
                self.state.veo_generate_audio = bool(config_overrides.get("veo_generate_audio"))

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
        self.state.image_provider = "flux"
        # Respect user UI selection; only default if unset.
        if not str(getattr(self.state, "video_model", "") or "").strip():
            self.state.video_model = "veo"

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
        with open(plan_path, "w", encoding="utf-8") as f:
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
        with open(plan_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        # Repair dialogue timing on resume so VO stays in the correct scene window,
        # without changing speakers (keeps previously generated VO audio valid).
        if self.state.script:
            self._align_dialogue_to_scenes(self.state.script, strategy=self.state.strategy, freeze_speakers=True)
            self._ensure_scene_characters_match_dialogue(self.state.script)
            self.save_state()

        print(f"[RESUME] Resuming project: {self.state.user_input}")

        try:
            # --- Phase 3: Assets ---
            print("\n[PHASE 3] Generating Assets...")
            self.state.add_log("[PHASE 3] Starting Asset Generation...")
            # Strict demo: single providers only (no fallbacks)
            from .providers.fal_flux import FalFluxProvider
            from .providers.elevenlabs import ElevenLabsProvider
            from .providers.tts_router import TTSRouterProvider
            from .providers.tts_router import TTSRouterProvider

            print("   [VISUALS] Using Fal.ai Flux (only)")
            self.state.add_log("[VISUALS] Fal.ai Flux initialized")
            image_provider = FalFluxProvider()

            eleven = ElevenLabsProvider()
            tts = TTSRouterProvider(eleven=eleven if getattr(eleven, "client", None) else None)
            if getattr(eleven, "client", None):
                print("   [AUDIO] Using ElevenLabs + routed TTS (OpenAI/SAPI supported)")
                self.state.add_log("[AUDIO] ElevenLabs Voice initialized (router enabled)")
            else:
                print("   [AUDIO] ElevenLabs unavailable; using routed TTS (OpenAI/SAPI only)")
                self.state.add_log("[AUDIO] ElevenLabs unavailable; OpenAI/SAPI only")

            # Visuals - PARALLEL GENERATION with Character Consistency
            print(f"\n   [OPTIMIZATION] Using parallel image generation (3x faster)")
            self.state.add_log("[OPTIMIZATION] Parallel image generation enabled")

            # Check for uploaded asset (Image-to-Image), gated by image_guidance.
            uploaded_asset_path = None
            guidance = str(getattr(self.state, "image_guidance", "") or "i2i_only").strip().lower()
            allow_i2i = guidance in ("i2i_only", "prompt_and_i2i", "i2i", "both")
            if allow_i2i and self.state.uploaded_asset:
                possible_path = os.path.join(config.ASSETS_DIR, "user_uploads", self.state.uploaded_asset)
                if os.path.exists(possible_path):
                    uploaded_asset_path = possible_path
                    print(f"   [VISUALS] Using Uploaded Reference (I2I): {self.state.uploaded_asset}")
            elif self.state.uploaded_asset and not allow_i2i:
                print(f"   [VISUALS] Reference upload present but I2I disabled (image_guidance={guidance})")

            # NOTE: Image composition is disabled in strict demo mode.

            # Parallel generation for standard scenes (WITH GPT-5.2 + NANO BANANA)
            try:
                start_time = time.time()
                parallel_gen = ParallelImageGenerator(image_provider, self.state, self.spatial)
                self.state.script.scenes = parallel_gen.generate_parallel(
                    self.state.script.scenes,
                    uploaded_asset_path=uploaded_asset_path,
                    max_workers=5  # Increased from 3 for speed
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Image generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Parallel image generation: {elapsed:.1f}s")

                # NOTE: Character consistency pass disabled in strict demo mode.

                # NARRATIVE QUALITY GATE (disabled in strict demo mode)
                if False:
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
                                    print(f"   [AUTO-FIX] Scene {scene_id} regenerated (OK)")
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
                            scene.image_path = image_provider.generate_image(
                                scene.visual_prompt,
                                seed=self.state.seed + scene.id,
                                image_input=uploaded_asset_path
                            )
                            self.state.add_log(f"[VISUALS] Scene {scene.id} created (sequential)")
                        except Exception as e2:
                            print(f"   [ERROR] Scene {scene.id} failed: {e2}")
                            self.state.add_log(f"[ERROR] Scene {scene.id} failed: {str(e2)}")

            # Audio - VOICEOVER ONLY (ElevenLabs) for demo reliability
            print(f"\n   [AUDIO] Generating voiceover (ElevenLabs)...")
            self.state.add_log("[AUDIO] Generating voiceover (ElevenLabs)")

            # Total timeline duration (seconds) for music + SFX sizing.
            total_seconds = 0
            for s in (self.state.script.scenes or []):
                try:
                    total_seconds += int(getattr(s, "duration", 0) or 0)
                except Exception:
                    pass
            total_seconds = max(int(total_seconds), 1)

            try:
                start_time = time.time()
                # Smart voice selection using voice_router
                from .providers.voice_router import select_voice
                
                # Get mood/style from strategy for voice matching
                mood = ""
                style = ""
                if isinstance(self.state.strategy, dict):
                    prefs = self.state.strategy.get("applied_preferences", {})
                    if isinstance(prefs, dict):
                        mood = str(prefs.get("mood") or "").strip()
                        style = str(prefs.get("style") or "").strip()
                
                for line in (self.state.script.lines or []):
                    if not getattr(line, "voice_id", None):
                        # Use voice_hint from script if available
                        voice_hint = getattr(line, "voice_hint", None)
                        speaker = getattr(line, "speaker", "Narrator")
                        selected_voice = select_voice(
                            speaker=speaker,
                            voice_hint=voice_hint,
                            mood=mood,
                            style=style
                        )
                        if selected_voice:
                            line.voice_id = selected_voice
                        else:
                            # Silent scene - no voice needed
                            line.voice_id = None


                parallel_audio = ParallelAudioGenerator(tts, self.state)
                vo_results = parallel_audio.generate_vo_batch(self.state.script.lines)
                for idx, audio_path in vo_results:
                    self.state.script.lines[idx].audio_path = audio_path
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Voiceover generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Voiceover generation: {elapsed:.1f}s")

            except Exception as e:
                print(f"   [ERROR] Voiceover generation failed: {e}")
                self.state.add_log(f"[ERROR] Voiceover failed: {str(e)}")

                # Fallback to sequential VO generation (same provider)
                print(f"   [FALLBACK] Switching to sequential voiceover generation...")
                self.state.add_log("[FALLBACK] Using sequential voiceover generation")

                for i, line in enumerate(self.state.script.lines):
                    if not line.audio_path:
                        try:
                            print(f"   Generating VO for Line {i+1}...")
                            voice_id = getattr(line, "voice_id", None) or os.getenv("DEFAULT_TTS_VOICE", "openai:verse")
                            line.audio_path = tts.generate_speech(line.text, voice_id)
                        except Exception as e2:
                            print(f"   [ERROR] VO Line {i+1} failed: {e2}")

            # Post-TTS fit pass: rewrite/regenerate only lines that exceed their slot.
            try:
                self._auto_fit_voiceover_lines(tts, strategy=self.state.strategy if isinstance(self.state.strategy, dict) else None)
            except Exception as e:
                self.state.add_log(f"[WARN] VO fit pass skipped: {str(e)}")

            # AUDIO-FIRST TIMING: Adjust scene durations to fit audio
            try:
                self._adjust_scene_durations_for_audio()
            except Exception as e:
                self.state.add_log(f"[WARN] Audio-first timing skipped: {str(e)}")

            # Demo integrity: never proceed to SFX/BGM/video assembly if VO is missing.
            # A missing VO track yields a "random noises" output that looks broken to clients.
            try:
                from .parallel_utils import ParallelAudioGenerator

                voice_router = ParallelAudioGenerator(tts, self.state)
                missing_vo: list[int] = []
                for idx, line in enumerate(self.state.script.lines or []):
                    path = getattr(line, "audio_path", None)
                    if not path or not os.path.exists(path):
                        missing_vo.append(idx)

                if missing_vo:
                    self.state.add_log(f"[WARN] Missing VO for {len(missing_vo)} line(s). Retrying sequentially...")
                    for idx in missing_vo:
                        line = self.state.script.lines[idx]
                        speaker = str(getattr(line, "speaker", "") or "").strip()
                        try:
                            voice_id = getattr(line, "voice_id", None) or voice_router._resolve_voice_id(speaker)
                            line.audio_path = tts.generate_speech(str(getattr(line, "text", "") or ""), voice_id)
                        except Exception as regen_error:
                            self.state.add_log(f"[ERROR] VO regen failed for line {idx + 1}: {str(regen_error)}")

                # Final check: if still missing, abort before generating motion/assembly.
                missing_final = [
                    i
                    for i, line in enumerate(self.state.script.lines or [])
                    if not getattr(line, "audio_path", None) or not os.path.exists(str(getattr(line, "audio_path")))
                ]
                if missing_final:
                    raise RuntimeError(
                        f"Voiceover missing for {len(missing_final)} line(s). "
                        "Fix ElevenLabs config/rate limits and retry (cannot ship a silent demo)."
                    )
            except Exception as e:
                # Surface this as a hard failure so the user doesn't get a broken "no voice" video.
                print(f"   [FATAL] {e}")
                self.state.add_log(f"[FATAL] {str(e)}")
                self.state.status = "failed"
                self.state.error = str(e)
                self.save_state()
                raise

            # Optional: Sound effects per scene (ElevenLabs SFX) if audio_prompt exists.
            print(f"\n   [AUDIO] Generating sound effects (ElevenLabs SFX)...")
            self.state.add_log("[AUDIO] Generating SFX (ElevenLabs)")
            try:
                parallel_audio = ParallelAudioGenerator(eleven, self.state)
                sfx_results = parallel_audio.generate_sfx_batch(self.state.script.scenes)
                for scene_id, sfx_path in sfx_results:
                    scene = next((s for s in self.state.script.scenes if getattr(s, "id", None) == scene_id), None)
                    if scene and sfx_path:
                        scene.sfx_path = sfx_path
                ok = len([s for s in self.state.script.scenes if getattr(s, "sfx_path", None)])
                self.state.add_log(f"[AUDIO] SFX generated for {ok}/{len(self.state.script.scenes)} scenes")
            except Exception as e:
                print(f"   [WARN] SFX generation skipped/failed: {e}")
                self.state.add_log(f"[WARN] SFX generation failed: {str(e)}")

            # Optional: Background music bed (ElevenLabs BGM) to enable beat-sync edits.
            print(f"\n   [AUDIO] Generating music bed (ElevenLabs BGM)...")
            self.state.add_log("[AUDIO] Generating BGM (ElevenLabs)")
            # Reuse an existing BGM on resume to avoid unnecessary extra calls.
            if self.state.bgm_path and os.path.exists(self.state.bgm_path):
                self.state.add_log("[AUDIO] Reusing existing BGM")
            else:
                self.state.bgm_path = None
                try:
                    bgm_prompt = ""
                    
                    # Try to use music_direction from the new Creative Agency pipeline
                    if isinstance(self.state.strategy, dict):
                        music_dir = self.state.strategy.get("music_direction")
                        if isinstance(music_dir, dict):
                            # Build a rich BGM prompt from music direction
                            genre = music_dir.get("genre", "cinematic")
                            energy = music_dir.get("energy_curve", "build to climax")
                            bpm = music_dir.get("bpm_feel", "medium")
                            vibe = music_dir.get("vibe_keywords", "powerful")
                            
                            bgm_prompt = f"{genre} instrumental, {vibe}, {bpm} tempo, {energy} energy"
                            print(f"   [MUSIC DIRECTOR] Using rich prompt: {bgm_prompt}")
                        else:
                            # Fallback to audio_signature
                            audio_sig = self.state.strategy.get("audio_signature")
                            if isinstance(audio_sig, dict):
                                bgm_prompt = str(audio_sig.get("bgm_prompt") or "").strip()
                    
                    if not bgm_prompt:
                        # Fallback: derive from mood + template if GPT didn't provide it.
                        mood = ""
                        if isinstance(self.state.strategy, dict):
                            prefs = self.state.strategy.get("applied_preferences")
                            if isinstance(prefs, dict):
                                mood = str(prefs.get("mood") or "").strip()
                        bgm_prompt = f"{mood or 'cinematic'} instrumental music, professional, high quality"
                    
                    bgm_path = eleven.generate_bgm(bgm_prompt, duration=total_seconds)
                    if bgm_path and os.path.exists(bgm_path):
                        self.state.bgm_path = bgm_path
                        self.state.add_log("[AUDIO] BGM generated successfully")
                    else:
                        self.state.add_log("[WARN] BGM generation returned empty path")
                except Exception as e:
                    print(f"   [WARN] BGM generation skipped/failed: {e}")
                    self.state.add_log(f"[WARN] BGM generation failed: {str(e)}")

            # === AUDIO-FIRST: Extract beat grid from BGM ===
            self.state.beat_grid = None
            if self.state.bgm_path and os.path.exists(self.state.bgm_path):
                try:
                    from .utils.beat_detector import extract_beat_grid
                    self.state.beat_grid = extract_beat_grid(
                        self.state.bgm_path,
                        duration=total_seconds,
                        fallback_bpm=120
                    )
                    self.state.add_log(f"[BEAT] Grid extracted: {self.state.beat_grid.get('bpm', 0):.0f} BPM")
                except Exception as e:
                    print(f"   [WARN] Beat detection failed: {e}")
                    self.state.add_log(f"[WARN] Beat detection failed: {str(e)}")

            self.save_state()

            # --- Phase 4: Motion ---
            print(f"\n[PHASE 4] Motion Synthesis...")
            self.state.add_log(f"[PHASE 4] Starting Motion Synthesis...")

            # Video - Veo 3.1 Ultra (only)
            from .providers.video_google import GoogleVideoProvider

            veo = GoogleVideoProvider()
            try:
                veo.set_generate_audio(bool(getattr(self.state, "veo_generate_audio", False)))
            except Exception:
                pass

            # ADAPTIVE PROMPTING: Set aesthetic style on Veo provider
            if self.state.detected_style:
                aesthetic = self.state.detected_style['aesthetic']
                veo.set_aesthetic_style(aesthetic)
                print(f"   [ADAPTIVE] Veo 3.1 Ultra configured for {aesthetic.upper()} aesthetic")
                self.state.add_log(f"[ADAPTIVE] Veo configured: {aesthetic} style")

            # Best practice: keep a consistent seed across scenes for stable style.
            veo.set_seed(self.state.seed)
            self.state.add_log(f"[VEO] Seed set: {self.state.seed}")

            # PREMIUM QUALITY: Parallel video generation with Veo 3.1 Ultra
            print(f"   [PREMIUM QUALITY] Parallel video generation with Veo 3.1 Ultra")
            self.state.add_log("[VIDEO] Parallel video generation active (Veo 3.1 Ultra only)")

            # Optional: prompt-level look guidance from reference image (affects motion prompts for Veo).
            try:
                guidance = str(getattr(self.state, "image_guidance", "") or "i2i_only").strip().lower()
                style_guide = str(getattr(self.state, "reference_style_guide", "") or "").strip()
                if guidance == "veo_text_only":
                    for s in (self.state.script.scenes or []):
                        try:
                            s.image_path = None
                        except Exception:
                            pass
                        vp = str(getattr(s, "visual_prompt", "") or "").strip()
                        mp = str(getattr(s, "motion_prompt", "") or "").strip()
                        combined = " ".join([p for p in (vp, mp) if p]).strip()
                        if style_guide:
                            combined = f"[REF_STYLE] {style_guide} {combined}".strip()
                        s.motion_prompt = combined or mp or vp
                    self.state.add_log("[REFERENCE] Veo Max Prompt enabled (text-to-video, no image stage)")

                if style_guide and guidance in ("prompt_only", "prompt_and_i2i", "prompt"):
                    tag = "[REF_STYLE]"
                    for s in (self.state.script.scenes or []):
                        mp = str(getattr(s, "motion_prompt", "") or "")
                        if tag not in mp:
                            s.motion_prompt = f"{tag} {style_guide} {mp}".strip()
                    self.state.add_log("[REFERENCE] Applied reference style guide to motion prompts")
            except Exception:
                pass

            try:
                start_time = time.time()
                # Optional Runway support for users who prefer Gen-3 I2V shots.
                runway = None
                try:
                    from .providers.runway import RunwayProvider

                    if str(getattr(config, "RUNWAY_API_KEY", "") or "").strip():
                        runway = RunwayProvider()
                except Exception:
                    runway = None

                parallel_video = ParallelVideoGenerator(veo, runway, self.state)
                self.state.script.scenes = parallel_video.generate_parallel(
                    self.state.script.scenes,
                    max_workers=2  # Reduce concurrency for demo reliability
                )
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Video generation completed in {elapsed:.1f}s")
            except Exception as e:
                print(f"   [ERROR] Parallel video generation failed: {e}")
                self.state.add_log(f"[ERROR] Parallel video generation failed: {str(e)}")
                # Note: No fallback providers in strict demo mode

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
        with open(plan_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.state = ProjectState(**data)

        print(f"[APPROVAL_GATE_1] Starting image generation for: {self.state.user_input}")
        self.state.status = "generating_images"
        self.state.add_log("[APPROVAL_GATE_1] User approved strategy. Starting image + audio generation...")
        self.save_state()

        try:
            # "Total Veo" mode: skip image/audio generation entirely and move to the next approval gate.
            guidance = str(getattr(self.state, "image_guidance", "") or "i2i_only").strip().lower()
            if guidance == "veo_text_only":
                self.state.add_log("[APPROVAL_GATE_1] Skipping image generation (Veo Max Prompt mode).")
                self.state.add_log("[APPROVAL_GATE_1] Skipping VO/BGM/SFX generation (Veo native audio mode).")
                # Ensure downstream stages behave correctly.
                self.state.veo_generate_audio = True
                self.state.transition_type = "cut"
                self.state.status = "images_complete"
                self.save_state()
                print(f"\n[APPROVAL_GATE_1] Skipped images/audio (Veo Max Prompt).")
                return

            # --- PHASE 3A: Image + Audio Generation (Copied from resume() lines 189-349) ---
            print("\n[PHASE 3A] Generating Images & Audio...")
            self.state.add_log("[PHASE 3A] Starting Asset Generation...")

            # Strict demo: single providers only (no fallbacks)
            from .providers.fal_flux import FalFluxProvider
            from .providers.elevenlabs import ElevenLabsProvider
            from .providers.tts_router import TTSRouterProvider

            print("   [VISUALS] Using Fal.ai Flux (only)")
            self.state.add_log("[VISUALS] Fal.ai Flux initialized")
            image_provider = FalFluxProvider()

            eleven = ElevenLabsProvider()
            tts = TTSRouterProvider(eleven=eleven if getattr(eleven, "client", None) else None)
            if getattr(eleven, "client", None):
                print("   [AUDIO] Using ElevenLabs + routed TTS (OpenAI/SAPI supported)")
                self.state.add_log("[AUDIO] ElevenLabs Voice initialized (router enabled)")
            else:
                print("   [AUDIO] ElevenLabs unavailable; using routed TTS (OpenAI/SAPI only)")
                self.state.add_log("[AUDIO] ElevenLabs unavailable; OpenAI/SAPI only")

            # Visuals - PARALLEL GENERATION
            print(f"\n   [OPTIMIZATION] Using parallel image generation (3x faster)")
            self.state.add_log("[OPTIMIZATION] Parallel image generation enabled")

            # Check for uploaded asset (reference mode for I2I), gated by image_guidance.
            uploaded_asset_path = None
            guidance = str(getattr(self.state, "image_guidance", "") or "i2i_only").strip().lower()
            allow_i2i = guidance in ("i2i_only", "prompt_and_i2i", "i2i", "both")

            if allow_i2i:
                # Use v2 uploads if available, looking for reference-mode uploads
                reference_uploads = [a for a in self.state.uploaded_assets_v2 if a.mode == "reference"]
                if reference_uploads:
                    possible_path = os.path.join(config.ASSETS_DIR, "user_uploads", reference_uploads[0].filename)
                    if os.path.exists(possible_path):
                        uploaded_asset_path = possible_path
                        print(f"   [VISUALS] Using Reference Upload (I2I): {reference_uploads[0].filename}")
                elif self.state.uploaded_asset:
                    # Legacy fallback
                    possible_path = os.path.join(config.ASSETS_DIR, "user_uploads", self.state.uploaded_asset)
                    if os.path.exists(possible_path):
                        uploaded_asset_path = possible_path
                        print(f"   [VISUALS] Using Uploaded Reference (I2I): {self.state.uploaded_asset}")
            else:
                # Keep direct scene uploads working; just don't force I2I guidance.
                if self.state.uploaded_assets_v2 or self.state.uploaded_asset:
                    print(f"   [VISUALS] Reference uploads present but I2I disabled (image_guidance={guidance})")

            # Handle direct uploads - copy files directly instead of AI generation
            scenes_for_ai = []
            for scene in self.state.script.scenes:
                if scene.image_source and scene.image_source.startswith("upload:"):
                    # Direct upload - copy file to image_path
                    filename = scene.image_source.replace("upload:", "")
                    source_path = os.path.join(config.ASSETS_DIR, "user_uploads", filename)
                    if os.path.exists(source_path):
                        import shutil
                        dest_path = os.path.join(config.ASSETS_DIR, "images", f"scene_{scene.id}_{filename}")
                        shutil.copy2(source_path, dest_path)
                        scene.image_path = dest_path
                        print(f"   [VISUALS] Scene {scene.id} using direct upload: {filename}")
                        self.state.add_log(f"[VISUALS] Scene {scene.id} using uploaded image: {filename}")
                    else:
                        print(f"   [WARNING] Upload not found for Scene {scene.id}: {filename}")
                        scenes_for_ai.append(scene)  # Fallback to AI
                else:
                    # AI generation needed
                    scenes_for_ai.append(scene)

            # NOTE: Image composition is disabled in strict demo mode.

            # Parallel generation for AI scenes only (WITH GPT-5.2 + NANO BANANA)
            try:
                start_time = time.time()
                if scenes_for_ai:
                    parallel_gen = ParallelImageGenerator(image_provider, self.state, self.spatial)
                    generated_scenes = parallel_gen.generate_parallel(
                        scenes_for_ai,
                        uploaded_asset_path=uploaded_asset_path,
                        max_workers=3
                    )
                    # Update the original scenes list with generated results
                    for gen_scene in generated_scenes:
                        for i, scene in enumerate(self.state.script.scenes):
                            if scene.id == gen_scene.id:
                                self.state.script.scenes[i] = gen_scene
                                break
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

                # NOTE: Character consistency pass disabled in strict demo mode.

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

            # Audio - VOICEOVER ONLY for demo reliability (supports ElevenLabs + OpenAI/SAPI via router).
            print(f"\n   [AUDIO] Generating voiceover (router)...")
            self.state.add_log("[AUDIO] Generating voiceover (router)")
            self.state.bgm_path = None

            try:
                start_time = time.time()
                for line in (self.state.script.lines or []):
                    if not getattr(line, "voice_id", None):
                        line.voice_id = os.getenv("DEFAULT_TTS_VOICE", "openai:verse")
                parallel_audio = ParallelAudioGenerator(tts, self.state)
                vo_results = parallel_audio.generate_vo_batch(self.state.script.lines)
                for idx, audio_path in vo_results:
                    self.state.script.lines[idx].audio_path = audio_path
                elapsed = time.time() - start_time
                print(f"   [PERFORMANCE] Voiceover generation completed in {elapsed:.1f}s")
                self.state.add_log(f"[PERFORMANCE] Voiceover generation: {elapsed:.1f}s")

            except Exception as e:
                print(f"   [ERROR] Voiceover generation failed: {e}")
                self.state.add_log(f"[ERROR] Voiceover failed: {str(e)}")

                # Fallback to sequential VO generation (same provider)
                print(f"   [FALLBACK] Switching to sequential voiceover generation...")
                self.state.add_log("[FALLBACK] Using sequential voiceover generation")

                for i, line in enumerate(self.state.script.lines):
                    if not line.audio_path:
                        try:
                            print(f"   Generating VO for Line {i+1}...")
                            voice_id = getattr(line, "voice_id", None) or os.getenv("DEFAULT_TTS_VOICE", "openai:verse")
                            line.audio_path = tts.generate_speech(line.text, voice_id)
                        except Exception as e2:
                            print(f"   [ERROR] VO Line {i+1} failed: {e2}")

            # Post-TTS fit pass: rewrite/regenerate only lines that exceed their slot.
            try:
                self._auto_fit_voiceover_lines(tts, strategy=self.state.strategy if isinstance(self.state.strategy, dict) else None)
            except Exception as e:
                self.state.add_log(f"[WARN] VO fit pass skipped: {str(e)}")

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
        with open(plan_path, "r", encoding="utf-8") as f:
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

            # Video - Veo 3.1 Ultra (only)
            from .providers.video_google import GoogleVideoProvider

            veo = GoogleVideoProvider()
            try:
                veo.set_generate_audio(bool(getattr(self.state, "veo_generate_audio", False)))
            except Exception:
                pass
            veo.set_seed(self.state.seed)
            self.state.add_log(f"[VEO] Seed set: {self.state.seed}")

            # OPTIMIZATION: Parallel video generation (-60 seconds per commercial)
            print(f"   [OPTIMIZATION] Parallel video generation enabled (submit-all-then-poll)")
            self.state.add_log("[VIDEO] Parallel video generation active (Veo 3.1 Ultra only)")

            # Optional: prompt-level look guidance from reference image (affects motion prompts for Veo).
            try:
                guidance = str(getattr(self.state, "image_guidance", "") or "i2i_only").strip().lower()
                style_guide = str(getattr(self.state, "reference_style_guide", "") or "").strip()

                # Veo Max Prompt (text-to-video): combine visual + motion prompts and do not use image inputs.
                if guidance == "veo_text_only":
                    for s in (self.state.script.scenes or []):
                        try:
                            s.image_path = None
                        except Exception:
                            pass
                        vp = str(getattr(s, "visual_prompt", "") or "").strip()
                        mp = str(getattr(s, "motion_prompt", "") or "").strip()
                        combined = " ".join([p for p in (vp, mp) if p]).strip()
                        if style_guide:
                            combined = f"[REF_STYLE] {style_guide} {combined}".strip()
                        s.motion_prompt = combined or mp or vp
                    self.state.add_log("[REFERENCE] Veo Max Prompt enabled (text-to-video, no image stage)")

                if style_guide and guidance in ("prompt_only", "prompt_and_i2i", "prompt"):
                    tag = "[REF_STYLE]"
                    for s in (self.state.script.scenes or []):
                        mp = str(getattr(s, "motion_prompt", "") or "")
                        if tag not in mp:
                            s.motion_prompt = f"{tag} {style_guide} {mp}".strip()
                    self.state.add_log("[REFERENCE] Applied reference style guide to motion prompts")
            except Exception:
                pass

            try:
                start_time = time.time()
                runway = None
                try:
                    from .providers.runway import RunwayProvider

                    if str(getattr(config, "RUNWAY_API_KEY", "") or "").strip():
                        runway = RunwayProvider()
                except Exception:
                    runway = None

                parallel_video = ParallelVideoGenerator(veo, runway, self.state)
                self.state.script.scenes = parallel_video.generate_parallel(
                    self.state.script.scenes,
                    max_workers=2  # Reduce concurrency for demo reliability
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
        with open(plan_path, "r", encoding="utf-8") as f:
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
            self.state.add_log("[COMPLETED] Final video assembled successfully")
            
            # [SHOWROOM] Auto-publish
            try:
                self.state.add_log("[SHOWROOM] Publishing to showroom manifest...")
                publish_render(self.state.id, self.state.final_video_path)
            except Exception as e:
                print(f"[WARN] Showroom publish failed: {e}")
                self.state.add_log(f"[WARN] Showroom publish failed: {e}")

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

    def remix_audio_only(
        self,
        *,
        script=None,
        regenerate_all: bool = False,
        include_sfx: bool = False,
        include_bgm: bool = False,
        bgm_prompt: str | None = None,
        sfx_style: str | None = None,
        speaker_voice_map: dict[str, str] | None = None,
    ) -> None:
        """
        Regenerate voiceover (and optionally SFX/BGM) and re-compose the final video
        without regenerating images/videos.

        Intended for fast iteration on voice casting and timing from the UI.
        """
        plan_path = self._get_plan_path()
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.state = ProjectState(**data)

        if script is not None:
            self.state.script = script

        if not self.state.script:
            raise RuntimeError("No script present; cannot remix audio.")

        from .providers.elevenlabs import ElevenLabsProvider
        from .parallel_utils import ParallelAudioGenerator
        from .providers.tts_router import TTSRouterProvider

        self.state.status = "remixing_audio"
        self.state.add_log("[AUDIO] Remixing audio (VO/SFX/BGM)...")
        self.save_state()

        # Apply speaker->voice mapping (UI-friendly) by stamping per-line `voice_id` if not already set.
        mapping: dict[str, str] = {}
        if isinstance(speaker_voice_map, dict):
            for k, v in speaker_voice_map.items():
                key = str(k or "").strip().lower()
                val = str(v or "").strip()
                if key and val:
                    mapping[key] = val

        if mapping:
            for line in self.state.script.lines or []:
                speaker = str(getattr(line, "speaker", "") or "").strip().lower()
                if speaker and speaker in mapping:
                    line.voice_id = mapping[speaker]

            # Any speaker remap implies VO needs re-generation.
            regenerate_all = True

        eleven = ElevenLabsProvider()
        tts = TTSRouterProvider(eleven=eleven)
        parallel_audio = ParallelAudioGenerator(tts, self.state)

        # Clear audio paths for any lines we want to regenerate.
        if regenerate_all:
            for line in self.state.script.lines or []:
                line.audio_path = None
        else:
            # Only regenerate missing audio files.
            for line in self.state.script.lines or []:
                path = getattr(line, "audio_path", None)
                if not path or not os.path.exists(str(path)):
                    line.audio_path = None

        # Generate VO.
        start_time = time.time()
        vo_results = parallel_audio.generate_vo_batch(self.state.script.lines)
        for idx, audio_path in vo_results:
            if audio_path:
                self.state.script.lines[idx].audio_path = audio_path
        elapsed = time.time() - start_time
        self.state.add_log(f"[PERFORMANCE] VO remix: {elapsed:.1f}s")

        # Optional SFX (uses scene.audio_prompt when present, or derives from sfx_style).
        if include_sfx:
            # Map sfx_style to default prompts
            sfx_style_prompts = {
                "cinematic": "cinematic transition, subtle whoosh, dramatic impact",
                "minimal": "soft, subtle transition sound",
                "punchy": "punchy impact hit, bass thump, energy burst",
                "whoosh": "smooth whoosh sound, air movement, transition",
                "tech": "digital glitch, futuristic beep, tech transition",
                "none": None,
            }
            default_sfx_prompt = sfx_style_prompts.get(sfx_style or "cinematic", sfx_style_prompts["cinematic"])
            
            for scene in self.state.script.scenes or []:
                # Use existing audio_prompt or apply default from sfx_style
                if not getattr(scene, "audio_prompt", None) and default_sfx_prompt:
                    scene.audio_prompt = default_sfx_prompt
                if getattr(scene, "audio_prompt", None):
                    scene.sfx_path = None
            try:
                sfx_results = parallel_audio.generate_sfx_batch(self.state.script.scenes)
                for scene_id, sfx_path in sfx_results:
                    if not sfx_path:
                        continue
                    for s in self.state.script.scenes:
                        if getattr(s, "id", None) == scene_id:
                            s.sfx_path = sfx_path
                            break
            except Exception as e:
                self.state.add_log(f"[WARN] SFX remix failed: {str(e)}")

        # Optional BGM (prompt-based).
        if include_bgm:
            total_seconds = 0
            for s in self.state.script.scenes or []:
                try:
                    total_seconds += int(getattr(s, "duration", 0) or 0)
                except Exception:
                    pass
            total_seconds = max(int(total_seconds), 1)
            prompt = (bgm_prompt or "").strip()
            if not prompt:
                prompt = "bright, sunny indie-pop, guitar, handclaps, light percussion, upbeat, 105 BPM"

            def _pick_cached_bgm() -> str | None:
                try:
                    from pathlib import Path

                    audio_dir = Path(config.ASSETS_DIR) / "audio"
                    if not audio_dir.exists():
                        return None
                    # Prefer explicit loops when available.
                    candidates = list(audio_dir.glob("bgm_loop_*.mp3"))
                    if not candidates:
                        candidates = list(audio_dir.glob("bgm_*.mp3"))
                    if not candidates:
                        return None
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return str(candidates[0])
                except Exception:
                    return None

            try:
                # ElevenLabs BGM endpoints often cap duration to <=30s; Composer can loop.
                candidate = eleven.generate_bgm(prompt, duration=min(total_seconds, 30))
                if candidate and os.path.exists(str(candidate)):
                    self.state.bgm_path = str(candidate)
                else:
                    raise RuntimeError("BGM generation returned empty path")
            except Exception as e:
                cached = _pick_cached_bgm()
                if cached and os.path.exists(str(cached)):
                    self.state.bgm_path = cached
                    self.state.add_log(f"[AUDIO] Using cached BGM loop: {os.path.basename(cached)}")
                else:
                    self.state.bgm_path = None
                    self.state.add_log(f"[WARN] BGM remix failed: {str(e)}")

        # If we have video clips, re-assemble final MP4 with the updated audio.
        try:
            has_any_video = any(
                (getattr(s, "video_path", None) and os.path.exists(str(getattr(s, "video_path"))))
                for s in (self.state.script.scenes or [])
            )
            if has_any_video:
                from .providers.composer import Composer

                self.state.add_log("[ASSEMBLY] Re-composing final video with updated audio...")
                composer = Composer()
                final_path = composer.compose(self.state, transition_type=self.state.transition_type)
                if final_path and os.path.exists(final_path):
                    self.state.final_video_path = final_path
                    self.state.status = "completed"
                    self.state.add_log(f"[SUCCESS] Audio remix complete: {final_path}")
                else:
                    raise RuntimeError("Composer returned invalid path during remix.")
            else:
                # No videos yet; keep pipeline at the image-approval stage.
                self.state.status = "images_complete"
                self.state.add_log("[AUDIO] VO remix complete (no videos yet).")

            self.save_state()
        except Exception as e:
            self.state.status = "failed"
            self.state.error = f"Audio remix assembly failed: {str(e)}"
            self.state.add_log(f"[ERROR] {self.state.error}")
            self.save_state()
            raise

    def save_state(self):
        plan_path = self._get_plan_path()
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(self.state.model_dump_json(indent=2))
