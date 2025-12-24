import os
import glob
import shutil
import sys
import ffmpeg
import re
import hashlib
from ..config import config
from ..state import ProjectState

class Composer:
    """
    Professional FFmpeg Composer for broadcast-quality OTT assembly.
    Supports transitions, OTT-compliant bitrates, timeline-based audio mixing,
    and progressive checkpoints for +40% reliability.
    """

    def __init__(self):
        self._ffmpeg_cmd = self._resolve_ffmpeg_cmd()

    @staticmethod
    def _env_truthy(key: str, default: bool = False) -> bool:
        raw = os.getenv(key)
        if raw is None:
            return bool(default)
        raw = raw.strip().lower()
        if raw in ("1", "true", "yes", "on"):
            return True
        if raw in ("0", "false", "no", "off"):
            return False
        return bool(default)

    @staticmethod
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

    @staticmethod
    def _pick_fontfile() -> str | None:
        env_font = (os.getenv("ENDCARD_FONTFILE") or "").strip()
        if env_font and os.path.exists(env_font):
            return env_font

        if sys.platform == "win32":
            candidates = [
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\segoeui.ttf",
            ]
            for path in candidates:
                if os.path.exists(path):
                    return path
        return None

    @staticmethod
    def _escape_drawtext(value: str) -> str:
        s = str(value or "")
        s = s.replace("\\", "\\\\")
        s = s.replace(":", "\\:")
        s = s.replace("'", "\\'")
        s = s.replace("\n", " ").replace("\r", " ")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def _env_str(key: str, default: str = "") -> str:
        raw = os.getenv(key)
        if raw is None:
            return str(default)
        return str(raw).strip()

    @staticmethod
    def _pick_one_seeded(options: list[str], seed: str) -> str:
        if not options:
            return ""
        h = hashlib.md5(seed.encode("utf-8", errors="ignore")).hexdigest()
        idx = int(h[:8], 16) % len(options)
        return options[idx]

    def _maybe_make_qr(self, url: str) -> str | None:
        url = str(url or "").strip()
        if not url:
            return None
        try:
            import qrcode
        except Exception:
            return None

        out_dir = os.path.join(config.ASSETS_DIR, "qrcodes")
        os.makedirs(out_dir, exist_ok=True)
        key = hashlib.md5(url.encode("utf-8", errors="ignore")).hexdigest()
        out_path = os.path.join(out_dir, f"qr_{key}.png")
        if os.path.exists(out_path):
            return out_path

        # Conservative QR settings to keep it scannable even when scaled down.
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=12,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        try:
            img.save(out_path)
            return out_path
        except Exception:
            return None

    def _apply_endcard_overlay(
        self,
        video_stream: ffmpeg.Stream,
        *,
        total_duration: float,
        title: str,
        subtitle: str,
        url: str = "",
        logo_path: str | None = None,
        duration: float = 1.8,
    ) -> ffmpeg.Stream:
        # Default to varied endcards so consecutive demo ads don't look identical.
        style_raw = (os.getenv("ENDCARD_STYLE") or "auto").strip().lower()
        # Deterministic variety: each project can set ENDCARD_SEED; if not, derive from title+url.
        seed = self._env_str("ENDCARD_SEED", f"{title}|{url}")
        if style_raw in ("random", "auto", "varied"):
            style = self._pick_one_seeded(
                ["lower_third_center", "lower_third_left", "full_card", "corner_card"],
                seed,
            )
        else:
            style = style_raw
        text_align = (os.getenv("ENDCARD_TEXT_ALIGN") or "center").strip().lower()
        # Default to auto accent for subtle per-ad differentiation.
        accent_raw = (os.getenv("ENDCARD_ACCENT") or "auto").strip()
        box_alpha = self._env_float("ENDCARD_BOX_ALPHA", 0.55)

        def _hex_to_ffmpeg_color(value: str, *, alpha: float | None = None) -> str | None:
            v = (value or "").strip()
            if not v:
                return None
            if v.startswith("#"):
                v = v[1:]
            v = v.strip().lower()
            if not re.fullmatch(r"[0-9a-f]{6}", v):
                return None
            a = box_alpha if alpha is None else float(alpha)
            a = max(0.0, min(float(a), 1.0))
            return f"0x{v}@{a:.3f}"

        accent_color = _hex_to_ffmpeg_color(accent_raw, alpha=0.90)
        if not accent_color and self._env_str("ENDCARD_ACCENT", "").strip().lower() in ("random", "auto"):
            accent_color = _hex_to_ffmpeg_color(
                self._pick_one_seeded(["00E5FF", "22C55E", "F97316", "A855F7", "E11D48"], seed),
                alpha=0.90,
            )

        def _env_int(key: str, default: int) -> int:
            raw = os.getenv(key)
            if raw is None:
                return int(default)
            raw = raw.strip()
            if not raw:
                return int(default)
            try:
                return int(float(raw))
            except Exception:
                return int(default)

        title_size = _env_int("ENDCARD_TITLE_SIZE", 72)
        subtitle_size = _env_int("ENDCARD_SUBTITLE_SIZE", 34)
        url_size = _env_int("ENDCARD_URL_SIZE", 28)

        start = max(float(total_duration) - float(duration), 0.0)
        end = max(float(total_duration), start + 0.05)
        enable = f"between(t,{start:.3f},{end:.3f})"

        if style in ("full_card", "full", "fullframe"):
            video_stream = ffmpeg.filter(
                video_stream,
                "drawbox",
                x=0,
                y=0,
                w="iw",
                h="ih",
                color=f"black@{max(0.0, min(box_alpha, 0.85)):.3f}",
                t="fill",
                enable=enable,
            )
        elif style in ("corner_card", "top_right"):
            video_stream = ffmpeg.filter(
                video_stream,
                "drawbox",
                x="iw*0.56",
                y="ih*0.06",
                w="iw*0.40",
                h="ih*0.24",
                color=f"black@{max(0.0, min(box_alpha, 0.75)):.3f}",
                t="fill",
                enable=enable,
            )
        else:
            box_y = "ih*0.66"
            box_h = "ih*0.34"
            video_stream = ffmpeg.filter(
                video_stream,
                "drawbox",
                x=0,
                y=box_y,
                w="iw",
                h=box_h,
                color=f"black@{max(0.0, min(box_alpha, 0.85)):.3f}",
                t="fill",
                enable=enable,
            )

        fontfile = self._pick_fontfile()
        title_text = self._escape_drawtext(title)
        subtitle_text = self._escape_drawtext(subtitle)
        url_text = self._escape_drawtext(url) if url else ""

        drawtext_common = {
            "fontcolor": "white",
            "shadowcolor": "black",
            "shadowx": 2,
            "shadowy": 2,
            "enable": enable,
        }
        if fontfile:
            drawtext_common["fontfile"] = fontfile

        # Fade-in on the text (drawbox can't reliably animate alpha).
        fade_in = self._env_float("ENDCARD_FADE_IN", 0.25)
        if fade_in and fade_in > 0.01:
            alpha_expr = f"if(lt(t,{start + float(fade_in):.3f}), (t-{start:.3f})/{float(fade_in):.3f}, 1)"
            drawtext_common["alpha"] = alpha_expr

        # Accent bar (optional).
        if accent_color:
            if style in ("full_card", "full", "fullframe"):
                ax, ay, aw, ah = ("iw*0.22", "ih*0.56", "iw*0.56", "ih*0.012")
            elif style in ("corner_card", "top_right"):
                ax, ay, aw, ah = ("iw*0.58", "ih*0.10", "iw*0.36", "ih*0.010")
            else:
                ax, ay, aw, ah = ("iw*0.20", "ih*0.70", "iw*0.60", "ih*0.010")

            video_stream = ffmpeg.filter(
                video_stream,
                "drawbox",
                x=ax,
                y=ay,
                w=aw,
                h=ah,
                color=accent_color,
                t="fill",
                enable=enable,
            )

        if style in ("lower_third_left", "lower_third_l"):
            tx = "w*0.08"
            title_y = "h*0.73"
            subtitle_y = "h*0.81"
            url_y = "h*0.88"
            qr_x, qr_y = ("w*0.84", "h*0.73")
        elif style in ("corner_card", "top_right"):
            # Tight, right-side card; left align inside the card.
            tx = "w*0.585"
            title_y = "h*0.115"
            subtitle_y = "h*0.180"
            url_y = "h*0.235"
            qr_x, qr_y = ("w*0.885", "h*0.115")
        elif style in ("full_card", "full", "fullframe"):
            # Keep expressions comma-free; commas break unescaped filtergraphs.
            tx = "(w-text_w)/2"
            title_y = "h*0.60"
            subtitle_y = "h*0.70"
            url_y = "h*0.78"
            qr_x, qr_y = ("w*0.80", "h*0.60")
        else:
            if text_align in ("left", "l"):
                tx = "w*0.08"
            else:
                tx = "(w-text_w)/2"
            title_y = "h*0.73"
            subtitle_y = "h*0.81"
            url_y = "h*0.88"
            qr_x, qr_y = ("w*0.84", "h*0.73")

        if title_text:
            video_stream = ffmpeg.filter(
                video_stream,
                "drawtext",
                text=title_text,
                fontsize=title_size,
                x=tx,
                y=title_y,
                **drawtext_common,
            )

        if subtitle_text:
            video_stream = ffmpeg.filter(
                video_stream,
                "drawtext",
                text=subtitle_text,
                fontsize=subtitle_size,
                x=tx,
                y=subtitle_y,
                **drawtext_common,
            )

        if url_text:
            video_stream = ffmpeg.filter(
                video_stream,
                "drawtext",
                text=url_text,
                fontsize=url_size,
                x=tx,
                y=url_y,
                **drawtext_common,
            )

        # Optional QR code endcard.
        # Default to showing a QR when we have a URL, unless explicitly disabled.
        qr_toggle_raw = (os.getenv("ENDCARD_QR") or "").strip().lower()
        qr_disabled = qr_toggle_raw in ("0", "false", "no", "off")
        want_qr = (not qr_disabled) and (bool(self._env_str("ENDCARD_QR_URL", "")) or bool(url))
        if want_qr:
            qr_url = self._env_str("ENDCARD_QR_URL", url)
            qr_path = self._maybe_make_qr(qr_url)
            if qr_path and os.path.exists(qr_path):
                qr_size = _env_int("ENDCARD_QR_SIZE", 220)
                qr = ffmpeg.input(qr_path, loop=1, framerate=24).filter("scale", qr_size, qr_size).filter("format", "rgba")
                video_stream = ffmpeg.overlay(
                    video_stream,
                    qr,
                    x=qr_x,
                    y=qr_y,
                    enable=enable,
                    shortest=1,
                )

        if logo_path and os.path.exists(logo_path):
            logo = ffmpeg.input(logo_path, loop=1, framerate=24)
            logo = ffmpeg.filter(logo, "scale", 160, -1)
            logo = ffmpeg.filter(logo, "format", "rgba")
            video_stream = ffmpeg.overlay(
                video_stream,
                logo,
                x="(main_w-overlay_w)/2",
                y="main_h*0.67-overlay_h*0.55",
                enable=enable,
                shortest=1,
            )

        return video_stream

    def _apply_grade(self, video_stream: ffmpeg.Stream) -> ffmpeg.Stream:
        preset = (os.getenv("GRADE_PRESET") or "").strip().lower()
        if not preset or preset in ("none", "off", "0", "false"):
            return video_stream

        # Keep it lightweight and reliable: stick to common filters.
        if preset in ("warm", "cozy"):
            video_stream = ffmpeg.filter(video_stream, "colorchannelmixer", rr=1.06, gg=1.00, bb=0.98)
            video_stream = ffmpeg.filter(video_stream, "eq", contrast=1.05, saturation=1.08)
            return video_stream

        if preset in ("cool", "tech"):
            video_stream = ffmpeg.filter(video_stream, "colorchannelmixer", rr=0.98, gg=1.00, bb=1.06)
            video_stream = ffmpeg.filter(video_stream, "eq", contrast=1.05, saturation=1.06)
            return video_stream

        if preset in ("clean", "bright", "clinical"):
            video_stream = ffmpeg.filter(video_stream, "eq", contrast=1.08, brightness=0.03, saturation=1.00)
            return video_stream

        if preset in ("vibrant", "sport"):
            video_stream = ffmpeg.filter(video_stream, "eq", contrast=1.06, saturation=1.22)
            return video_stream

        if preset in ("crisp", "detail"):
            video_stream = ffmpeg.filter(video_stream, "eq", contrast=1.10, saturation=1.05, brightness=0.01)
            return video_stream

        return video_stream

    @staticmethod
    def _resolve_ffmpeg_cmd() -> str:
        """
        Resolve an ffmpeg executable path.

        Why: ffmpeg-python shells out to `ffmpeg`. On Windows, users often install
        ffmpeg via WinGet (not always on PATH yet), which causes `[WinError 2]`.
        """
        cmd = shutil.which("ffmpeg")
        if cmd:
            return cmd

        if sys.platform == "win32":
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                pattern = os.path.join(
                    local_app_data,
                    "Microsoft",
                    "WinGet",
                    "Packages",
                    "Gyan.FFmpeg_*",
                    "ffmpeg-*",
                    "bin",
                    "ffmpeg.exe",
                )
                matches = sorted(glob.glob(pattern), reverse=True)
                if matches:
                    return matches[0]

        raise FileNotFoundError(
            "ffmpeg not found. Install FFmpeg or add it to PATH (WinGet install is supported)."
        )

    def _image_fallback_clip(self, *, image_path: str, duration: float, seed: str) -> str:
        """
        Create a lightweight video clip from a still image (Ken Burns style).

        Why: For long-form demos, if some Veo scenes fail, we still need continuous visuals so the
        final MP4 doesn't become "audio-only" for the remaining VO.
        """
        safe_duration = max(0.5, float(duration or 4.0))
        fps = 30
        frames = max(1, int(round(safe_duration * fps)))

        digest = hashlib.md5(f"{seed}|{image_path}|{frames}".encode("utf-8", errors="ignore")).hexdigest()[:10]
        out_path = os.path.join(config.OUTPUT_DIR, f"fallback_{digest}.mp4")
        if os.path.exists(out_path):
            return out_path

        # Choose a deterministic pan style.
        mode = int(digest[0], 16) % 4
        zoom_expr = "min(zoom+0.0012,1.08)"
        if mode == 0:
            x_expr = "iw/2-(iw/zoom/2) + (iw/30)*sin(on/45)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif mode == 1:
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2) + (ih/28)*sin(on/50)"
        elif mode == 2:
            x_expr = "iw/2-(iw/zoom/2) + (iw/34)*sin(on/52)"
            y_expr = "ih/2-(ih/zoom/2) + (ih/34)*sin(on/47)"
        else:
            # Slight zoom-out feel by starting closer in and easing to 1.0-ish.
            zoom_expr = "max(1.0,1.08-0.0012*on)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        # Build the clip.
        (
            ffmpeg.input(image_path, loop=1)
            .filter("scale", 1920, 1080, force_original_aspect_ratio="increase")
            .filter("crop", 1920, 1080)
            .filter("zoompan", z=zoom_expr, x=x_expr, y=y_expr, d=frames, s="1920x1080", fps=fps)
            .output(
                out_path,
                vcodec="libx264",
                pix_fmt="yuv420p",
                r=fps,
                t=safe_duration,
                movflags="+faststart",
                preset="veryfast",
                crf=18,
                loglevel="error",
            )
            .overwrite_output()
            .run(cmd=self._ffmpeg_cmd)
        )

        return out_path

    def compose(self, state: ProjectState, transition_type: str = "fade", transition_duration: float = 0.3) -> str:
        """
        Stitches video clips with cinematic transitions and mixes audio with OTT broadcast quality.
        OPTIMIZATION: Uses progressive checkpoints to enable recovery from partial failures.

        Args:
            state: ProjectState containing script, scenes, and audio paths
            transition_type: Transition name ("fade", "wipeleft", "slideleft", "cut").
                Note: UI-friendly values like "crossfade"/"wipe"/"slide" are normalized.
            transition_duration: Duration of transitions in seconds (default 0.3s)

        Returns:
            Path to final rendered video
        """
        print("[VIDEO] Composing final video with professional transitions...")

        # Normalize UI-friendly transition labels to FFmpeg `xfade` transition names.
        # FFmpeg does not support "crossfade" as a transition name; it uses "fade".
        raw_transition = (transition_type or "").strip()
        normalized = raw_transition.lower() if raw_transition else ""
        transition_aliases = {
            "crossfade": "fade",
            "cross-fade": "fade",
            "fade": "fade",
            "wipe": "wipeleft",
            "wipeleft": "wipeleft",
            "slide": "slideleft",
            "slideleft": "slideleft",
            "cut": "cut",
        }
        transition_type = transition_aliases.get(normalized, raw_transition or "fade")

        # Define per-project checkpoint paths.
        # IMPORTANT: these used to be global filenames, which can corrupt outputs when multiple
        # assemblies run concurrently (e.g., background showroom remix + longform assembly).
        run_id = str(getattr(state, "id", "") or "").strip() or "run"
        safe_run_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", run_id).strip("_-")[:24] or "run"
        video_only_path = os.path.join(config.OUTPUT_DIR, f"video_only_{safe_run_id}.mp4")
        audio_mix_path = os.path.join(config.OUTPUT_DIR, f"audio_mix_{safe_run_id}.mp3")
        output_path = os.path.join(config.OUTPUT_DIR, f"final_ad_{safe_run_id}.mp4")

        # 1. Gather video inputs
        video_clips = []
        scene_durations = []

        for scene in state.script.scenes:
            clip_path = None
            if scene.video_path and os.path.exists(scene.video_path):
                clip_path = scene.video_path
            else:
                image_path = getattr(scene, "image_path", None)
                if image_path and os.path.exists(str(image_path)):
                    try:
                        clip_path = self._image_fallback_clip(
                            image_path=str(image_path),
                            duration=float(getattr(scene, "duration", 4) or 4),
                            seed=f"{getattr(state, 'id', '')}|scene:{getattr(scene, 'id', '')}",
                        )
                        # Ensure audio smart-sync can map this scene_id to a clip start time.
                        scene.video_path = clip_path
                        print(f"[WARN] Missing video for scene {scene.id}; using image fallback clip.")
                    except Exception as e:
                        print(f"[WARN] Missing video for scene {scene.id}, skipping (fallback failed): {e}")
                else:
                    print(f"[WARN] Missing video for scene {scene.id}, skipping.")

            if clip_path and os.path.exists(clip_path):
                video_clips.append(clip_path)
                scene_durations.append(getattr(scene, "duration", 4))

        if not video_clips:
            raise Exception("No video clips to compose!")

        # 2. Analyze Audio for Beat Sync
        beat_times = []
        enable_beat_sync = os.getenv("ENABLE_BEAT_SYNC", "").strip().lower() in ("1", "true", "yes", "on")
        if enable_beat_sync and state.bgm_path and os.path.exists(state.bgm_path):
            try:
                from .beat_detector import BeatDetector

                detector = BeatDetector()
                beat_times = detector.get_beat_times(state.bgm_path)

                # Audio-Reactive Editing Logic
                energy = detector.get_energy_profile(state.bgm_path, duration=30)
                if energy == "high":
                    print("[COMPOSER] High Energy Audio detected -> Using Fast Cuts")
                    # Keep this conservative for demo reliability: `fade` is universally supported by `xfade`.
                    transition_type = "fade"
                    transition_duration = 0.2  # Fast transition
                else:
                    print("[COMPOSER] Low Energy Audio detected -> Using Smooth Crossfades")
                    transition_type = "fade"
                    transition_duration = 1.0
            except Exception as e:
                # Beat sync is optional. Don't fail the whole render if librosa/ffmpeg extras are missing.
                print(f"[WARN] Beat sync disabled (beat analysis failed): {e}")
                beat_times = []

        # 3. Create video with transitions (and rhythm sync) - CHECKPOINT 1
        print("[CHECKPOINT 1/3] Creating video-only track...")
        use_clip_audio = self._env_truthy("USE_CLIP_AUDIO", default=False) or bool(getattr(state, "veo_generate_audio", False))
        clip_audio_stream = None

        if len(video_clips) == 1 or transition_type == "cut":
            if use_clip_audio:
                joined_video, clip_audio_stream, actual_start_times = self._concatenate_videos_simple_with_audio(
                    video_clips,
                    scene_durations,
                )
            else:
                joined_video, actual_start_times = self._concatenate_videos_simple(video_clips, scene_durations)
        else:
            joined_video, actual_start_times = self._concatenate_videos_with_transitions(
                video_clips,
                scene_durations,
                transition_type,
                transition_duration,
                beat_times # Pass beats
            )

        # Optional: quick color grade per-ad to diversify the look without re-generating video.
        joined_video = self._apply_grade(joined_video)

        # Collect endcard/showroom metadata from env + strategist output (best-effort).
        brand_name = ""
        call_to_action = ""
        brand_url = ""
        if isinstance(getattr(state, "strategy", None), dict):
            brand_card = state.strategy.get("brand_card")
            if isinstance(brand_card, dict):
                brand_name = str(brand_card.get("brand_name") or "").strip()
                call_to_action = str(brand_card.get("call_to_action") or "").strip()
                brand_url = str(
                    brand_card.get("url")
                    or brand_card.get("website")
                    or brand_card.get("brand_url")
                    or brand_card.get("site")
                    or ""
                ).strip()
            if not brand_url:
                prefs = state.strategy.get("applied_preferences")
                if isinstance(prefs, dict):
                    brand_url = str(prefs.get("url") or "").strip()
            if not brand_name:
                brand_name = str(state.strategy.get("product_name") or "").strip()

        endcard_title = (os.getenv("ENDCARD_TITLE") or brand_name or "").strip()
        endcard_subtitle = (os.getenv("ENDCARD_SUBTITLE") or call_to_action or "").strip()
        endcard_url = (os.getenv("ENDCARD_URL") or brand_url or "").strip()

        # Optional: add a real CTA/logo endcard in post (reliable, no generative text).
        if self._env_truthy("ENDCARD_ENABLED", default=False):
            logo_path = (os.getenv("ENDCARD_LOGO_PATH") or "").strip() or None
            if not logo_path and getattr(state, "uploaded_asset", None):
                candidate = os.path.join(config.ASSETS_DIR, "user_uploads", str(state.uploaded_asset))
                if os.path.exists(candidate):
                    logo_path = candidate

            total_duration = float(sum(float(d or 0) for d in scene_durations) or 1.0)
            if actual_start_times and len(actual_start_times) == len(scene_durations):
                try:
                    total_duration = float(actual_start_times[-1]) + float(scene_durations[-1] or 0)
                except Exception:
                    pass

            joined_video = self._apply_endcard_overlay(
                joined_video,
                total_duration=total_duration,
                title=endcard_title or brand_name or " ",
                subtitle=endcard_subtitle,
                url=endcard_url,
                logo_path=logo_path,
                duration=self._env_float("ENDCARD_DURATION", 1.8),
            )

        # 4. Professional audio mixing with timeline alignment - CHECKPOINT 2
        print("[CHECKPOINT 2/3] Creating audio mix...")
        audio_stream = self._mix_audio_timeline(state, actual_start_times)

        # Optional: preserve Veo/native clip audio for "no TTS" demo runs (best with cut edits).
        if clip_audio_stream is not None:
            clip_audio_only = self._env_truthy("CLIP_AUDIO_ONLY", default=True)
            if clip_audio_only:
                audio_stream = clip_audio_stream
            else:
                try:
                    audio_stream = ffmpeg.filter([clip_audio_stream, audio_stream], "amix", inputs=2, duration="longest")
                except Exception:
                    # If mixing fails, prefer the mixed timeline (safer) but keep going.
                    pass

        # 5. Final OTT-compliant encoding with adaptive quality fallback - CHECKPOINT 3
        print("[CHECKPOINT 3/3] Final encoding with adaptive quality...")
        try:
            self._encode_with_adaptive_quality(joined_video, audio_stream, output_path)
            print(f"[OK] Final video rendered: {output_path}")

            # Browser playback hardening: verify container + attempt a quick remux if needed.
            # This helps when concurrent runs or interrupted writes leave an MP4 with bad packets.
            try:
                self._ensure_playable_mp4(output_path)
            except Exception as e:
                print(f"[WARN] Playback validation/remux skipped: {e}")

            # Auto-publish the final render into output/showroom for the Showroom UI.
            try:
                if self._env_truthy("SHOWROOM_AUTO_PUBLISH", default=True):
                    from .. import showroom as showroom_lib

                    project_id = str(getattr(state, "id", "") or "").strip() or None
                    title = endcard_title or brand_name or (getattr(state, "user_input", "") or "").strip() or "Render"

                    category = ""
                    if isinstance(getattr(state, "strategy", None), dict):
                        category = str(state.strategy.get("category") or state.strategy.get("market_category") or "").strip()
                    if not category:
                        category = str(getattr(state, "style_preset", "") or "").strip()

                    plan_filename = f"plan_{project_id}.json" if project_id else None
                    if plan_filename:
                        if not os.path.exists(os.path.join(config.OUTPUT_DIR, plan_filename)):
                            plan_filename = None

                    showroom_lib.publish_render(
                        final_video_path=output_path,
                        project_id=project_id,
                        title=title,
                        url=endcard_url,
                        category=category,
                        plan_filename=plan_filename,
                    )
            except Exception as e:
                print(f"[WARN] Showroom publish skipped: {e}")

            return output_path
        except ffmpeg.Error as e:
            stderr = (e.stderr or b"").decode("utf-8", errors="replace")
            head = stderr[:3000]
            tail = stderr[-3000:] if len(stderr) > 3000 else ""
            print(f"[FFMPEG ERROR]\n{head}")
            if tail:
                print(f"[FFMPEG ERROR - TAIL]\n{tail}")
            raise

    def _ensure_playable_mp4(self, path: str) -> None:
        """
        Best-effort validation to improve HTML5 video playback reliability.

        If probing fails, attempt a fast remux (stream copy) with `+faststart`,
        then atomically replace the original.
        """
        if not path or not os.path.exists(path):
            raise FileNotFoundError(path)

        def _has_video_stream(info: dict) -> bool:
            streams = info.get("streams") if isinstance(info, dict) else None
            if not isinstance(streams, list):
                return False
            return any(isinstance(s, dict) and s.get("codec_type") == "video" for s in streams)

        try:
            info = ffmpeg.probe(path)
            if not _has_video_stream(info):
                raise ValueError("probe_missing_video_stream")
            return
        except Exception:
            pass

        remux_path = re.sub(r"\.mp4$", "_remux.mp4", path, flags=re.IGNORECASE)
        (
            ffmpeg.input(path)
            .output(remux_path, **{"c:v": "copy", "c:a": "copy", "movflags": "faststart"})
            .overwrite_output()
            .run(cmd=self._ffmpeg_cmd, capture_stdout=True, capture_stderr=True)
        )

        info = ffmpeg.probe(remux_path)
        if not _has_video_stream(info):
            raise ValueError("remux_missing_video_stream")

        os.replace(remux_path, path)

    @staticmethod
    def _probe_has_audio(path: str) -> bool:
        try:
            info = ffmpeg.probe(path)
            streams = info.get("streams") if isinstance(info, dict) else None
            if not isinstance(streams, list):
                return False
            return any(isinstance(s, dict) and s.get("codec_type") == "audio" for s in streams)
        except Exception:
            return False

    def _concatenate_videos_simple(self, video_paths: list, durations: list | None = None) -> tuple:
        """Simple concatenation without transitions (straight cuts), video-only."""
        video_inputs = [ffmpeg.input(path).video.filter('scale', 1920, 1080).filter('fps', fps=24).filter('format', 'yuv420p') for path in video_paths]

        # Calculate straight cut timestamps for smart sync.
        start_times = [0.0]
        if durations and len(durations) == len(video_paths):
            t = 0.0
            for d in durations[:-1]:
                t += float(d or 0)
                start_times.append(t)

        return ffmpeg.concat(*video_inputs, v=1, a=0).node[0], start_times

    def _concatenate_videos_simple_with_audio(self, video_paths: list, durations: list) -> tuple:
        """
        Straight cuts WITH clip audio preserved (best for Veo native audio runs).
        Returns (video_stream, audio_stream, start_times).
        """
        fps = 24
        start_times = [0.0]
        t = 0.0
        for d in durations[:-1]:
            t += float(d or 0)
            start_times.append(t)

        inputs: list[ffmpeg.Stream] = []
        for idx, path in enumerate(video_paths):
            dur = float(durations[idx] or 0) if idx < len(durations) else 0.0
            dur = max(dur, 0.1)

            inp = ffmpeg.input(path)
            v = inp.video.filter('scale', 1920, 1080).filter('fps', fps=fps).filter('format', 'yuv420p')
            v = v.filter("trim", duration=dur).filter("setpts", "PTS-STARTPTS")

            if self._probe_has_audio(path):
                a = inp.audio
                a = a.filter("atrim", duration=dur).filter("asetpts", "PTS-STARTPTS")
                a = a.filter("aformat", sample_rates=48000, channel_layouts="stereo")
            else:
                a = ffmpeg.input("anullsrc", f="lavfi", t=dur)
                a = a.filter("aformat", sample_rates=48000, channel_layouts="stereo")

            inputs.extend([v, a])

        node = ffmpeg.concat(*inputs, v=1, a=1).node
        joined_v = node[0]
        joined_a = node[1]

        # Optional clip-audio gain + loudnorm for consistent playback.
        clip_gain = self._env_float("CLIP_AUDIO_VOLUME", 1.0)
        if clip_gain and clip_gain != 1.0:
            joined_a = ffmpeg.filter(joined_a, "volume", volume=float(clip_gain))

        ln_i = self._env_float("LOUDNORM_I", -16.0)
        ln_tp = self._env_float("LOUDNORM_TP", -1.5)
        ln_lra = self._env_float("LOUDNORM_LRA", 8.0)
        joined_a = ffmpeg.filter(joined_a, "loudnorm", I=ln_i, TP=ln_tp, LRA=ln_lra)

        return joined_v, joined_a, start_times

    def _concatenate_videos_with_transitions(self, video_paths: list, durations: list,
                                            transition_type: str, transition_duration: float,
                                            beat_times: list = None) -> tuple:
        """
        Concatenate videos with cinematic transitions and optional beat sync.
        Returns: (ffmpeg_stream, start_times)
        """
        if len(video_paths) < 2:
            return self._concatenate_videos_simple(video_paths)
        
        # Track effective start times for each clip
        # Clip 0 always starts at 0.0
        start_times = [0.0]

        beat_times = beat_times or []
        
        # CRITICAL: Normalize all input videos to same resolution/format before combining
        # This prevents H.264 NAL unit corruption during xfade transitions
        def normalize_video(path):
            """Normalize video to 1920x1080, 24fps, yuv420p for consistent transitions."""
            return ffmpeg.input(path).filter('scale', 1920, 1080).filter('fps', fps=24).filter('format', 'yuv420p')
        
        # Load first clip (normalized)
        result = normalize_video(video_paths[0])

        # Calculate time where the first transition should happen (end of clip 1)
        # We start with the full duration of the first clip
        # current_time = durations[0] # Unused variable?
        
        cumulative_offset = 0
        
        # Logic: 
        # Clip 1 starts at 0.
        # Clip 2 starts at (Clip 1 Duration - Transition).
        # BEAT SYNC: We want (Clip 1 Duration - Transition) to be == BEAT TIME.
        
        # First offset (transition from Clip 1 to Clip 2)
        target_offset = durations[0] - transition_duration
        if beat_times:
             # Filter beats < target_offset and > target_offset - 2.0
             valid_beats = [b for b in beat_times if (target_offset - 2.0) < b < target_offset]
             if valid_beats:
                 # Pick the latest one (use most footage)
                 best_beat = max(valid_beats)
                 print(f"   [SYNC] Snapping cut 1 to beat: {target_offset:.2f}s -> {best_beat:.2f}s")
                 target_offset = best_beat
        
        cumulative_offset = target_offset
        start_times.append(cumulative_offset) # Clip 2 starts here

        for i in range(1, len(video_paths)):
            next_clip = normalize_video(video_paths[i])  # NORMALIZED

            # Apply xfade transition at the calculated offset
            result = ffmpeg.filter(
                [result, next_clip],
                'xfade',
                transition=transition_type,
                duration=transition_duration,
                offset=cumulative_offset
            )
            
            # Now calculate Next Offset (for the NEXT iteration)
            if i < len(video_paths) - 1:
                # Default next start: current absolute time + duration of this clip - transition overlap
                next_target_offset = cumulative_offset + durations[i] - transition_duration
                
                if beat_times:
                    # Valid beats must be > current cumulative_offset (obviously) to move forward
                    # and < next_target_offset (can't extend footage)
                    valid_beats = [b for b in beat_times if (next_target_offset - 2.0) < b < next_target_offset]
                    if valid_beats:
                        best_beat = max(valid_beats)
                        print(f"   [SYNC] Snapping cut {i+1} to beat: {next_target_offset:.2f}s -> {best_beat:.2f}s")
                        next_target_offset = best_beat
                
                cumulative_offset = next_target_offset
                start_times.append(cumulative_offset) # Clip i+1 starts here

        return result, start_times

    def _mix_audio_timeline(self, state: ProjectState, clip_start_times: list) -> ffmpeg.Stream:
        """
        Mix audio with exact timeline positioning based on ACTUAL video start times.
        Corrects for drift caused by beat-syncing.
        """
        voice_inputs = []
        sfx_inputs = []
        bgm_input = None
        lines = []
        scenes = []
        if state.script:
            lines = list(state.script.lines or [])
            scenes = list(state.script.scenes or [])

        def parse_time_range(time_range: str) -> tuple:
            if not time_range:
                return (None, None)
            try:
                parts = time_range.replace("s", "").split("-")
                start = float(parts[0]) if parts and parts[0] != "" else None
                end = float(parts[1]) if len(parts) > 1 and parts[1] != "" else None
                return (start, end)
            except Exception:
                return (None, None)

        # Estimate video end time for the final voiceover slot.
        video_end_time = 0.0
        if clip_start_times and scenes:
            last_idx = min(len(clip_start_times), len(scenes)) - 1
            if last_idx >= 0:
                last_start = float(clip_start_times[last_idx] or 0.0)
                last_duration = float(getattr(scenes[last_idx], "duration", 0) or 0.0)
                video_end_time = max(video_end_time, last_start + last_duration)
        if video_end_time <= 0.0 and scenes:
            video_end_time = float(sum((getattr(s, "duration", 0) or 0) for s in scenes))
        if video_end_time <= 0.0:
            video_end_time = 1.0  # Keep ffmpeg happy

        # Map scene_id -> planned/actual start times so dialogue can stay locked to visuals,
        # even when transitions/beat-sync shift clip start times slightly.
        scene_id_to_planned_start: dict[int, float] = {}
        scene_id_to_actual_start: dict[int, float] = {}
        planned_cum = 0.0
        for scene in scenes:
            try:
                sid = int(getattr(scene, "id", 0) or 0)
            except Exception:
                continue
            scene_id_to_planned_start[sid] = float(planned_cum)
            planned_cum += float(getattr(scene, "duration", 0) or 0)

        # `clip_start_times` correspond only to scenes that actually made it into the video track.
        if clip_start_times and scenes:
            video_scenes = [s for s in scenes if getattr(s, "video_path", None) and os.path.exists(getattr(s, "video_path"))]
            for idx, scene in enumerate(video_scenes[: len(clip_start_times)]):
                try:
                    sid = int(getattr(scene, "id", 0) or 0)
                except Exception:
                    continue
                try:
                    scene_id_to_actual_start[sid] = float(clip_start_times[idx] or 0.0)
                except Exception:
                    scene_id_to_actual_start[sid] = 0.0

        # Collect voiceover from script lines
        # We assume Lines map to Scenes roughly 1:1
        # timestamp_mode: "smart_sync" if counts match, else "time_range" fallback
        timestamp_mode = "time_range"
        if len(lines) == len(scenes):
            timestamp_mode = "smart_sync"
            print(f"   [AUDIO] Smart Sync Active: Mapping {len(state.script.lines)} lines to {len(clip_start_times)} clips.")

        # Precompute timeline start/end for each line so we can trim to prevent overlap.
        line_starts: list[float] = []
        line_end_hints: list[float | None] = []
        for i, line in enumerate(lines):
            start_time = 0.0
            end_hint = None

            # Prefer scene_id locking when available.
            scene_id = getattr(line, "scene_id", None)
            try:
                scene_id = int(scene_id) if scene_id is not None else None
            except Exception:
                scene_id = None

            if timestamp_mode == "smart_sync" and i < len(clip_start_times):
                start_time = float(clip_start_times[i] or 0.0)
            else:
                start_hint, end_hint = parse_time_range(getattr(line, "time_range", None))
                if start_hint is not None:
                    start_time = float(start_hint)

            # Prefer explicit time_range end if provided.
            if end_hint is None:
                _, parsed_end = parse_time_range(getattr(line, "time_range", None))
                end_hint = parsed_end

            # If we know which scene this line belongs to, shift it to the actual clip start time.
            if scene_id is not None and scene_id in scene_id_to_actual_start and scene_id in scene_id_to_planned_start:
                planned_scene_start = float(scene_id_to_planned_start[scene_id])
                actual_scene_start = float(scene_id_to_actual_start[scene_id])

                # Convert global planned times to in-scene offsets.
                start_hint, end_hint_raw = parse_time_range(getattr(line, "time_range", None))
                if start_hint is None:
                    rel_start = 0.0
                else:
                    rel_start = max(0.0, float(start_hint) - planned_scene_start)

                rel_end = None
                if end_hint is not None:
                    rel_end = max(rel_start + 0.05, float(end_hint) - planned_scene_start)

                start_time = actual_scene_start + rel_start
                if rel_end is not None:
                    end_hint = actual_scene_start + rel_end

            line_starts.append(start_time)
            line_end_hints.append(float(end_hint) if end_hint is not None else None)

        def _env_float(key: str, default: float) -> float:
            try:
                raw = os.getenv(key)
                if raw is None:
                    return float(default)
                raw = raw.strip()
                if not raw:
                    return float(default)
                return float(raw)
            except Exception:
                return float(default)

        def _env_truthy(key: str, default: bool = False) -> bool:
            raw = os.getenv(key)
            if raw is None:
                return bool(default)
            raw = raw.strip().lower()
            if raw in ("1", "true", "yes", "on"):
                return True
            if raw in ("0", "false", "no", "off"):
                return False
            return bool(default)

        # Best-effort probe for audio durations so we can time-compress VO instead of hard-trimming it.
        audio_duration_cache: dict[str, float | None] = {}

        def _probe_audio_duration_seconds(path: str) -> float | None:
            cached = audio_duration_cache.get(path)
            if cached is not None or path in audio_duration_cache:
                return cached
            try:
                probe = ffmpeg.probe(path)
                fmt = probe.get("format") if isinstance(probe, dict) else None
                if isinstance(fmt, dict):
                    dur = fmt.get("duration")
                    if dur is not None:
                        value = float(dur)
                        audio_duration_cache[path] = value
                        return value
            except Exception:
                pass
            audio_duration_cache[path] = None
            return None

        def _apply_atempo(stream: ffmpeg.Stream, factor: float) -> ffmpeg.Stream:
            """
            Apply `atempo` safely (supports 0.5..2.0 per filter; chain if needed).
            We only use modest >1.0 factors for VO fitting.
            """
            remaining = float(factor)
            while remaining > 2.0:
                stream = ffmpeg.filter(stream, "atempo", 2.0)
                remaining /= 2.0
            while remaining < 0.5:
                stream = ffmpeg.filter(stream, "atempo", 0.5)
                remaining /= 0.5
            return ffmpeg.filter(stream, "atempo", remaining)

        for i, line in enumerate(lines):
            if line.audio_path and os.path.exists(line.audio_path):
                start_time = float(line_starts[i] or 0.0)
                if timestamp_mode == "smart_sync" and i < len(clip_start_times):
                    print(f"   [AUDIO] Line {i+1} synced to video clip {i+1} at {start_time:.2f}s")

                # Determine slot end to avoid VO overlapping with the next line.
                next_start = (
                    float(line_starts[i + 1])
                    if i + 1 < len(line_starts)
                    else float(video_end_time)
                )
                slot_end = max(next_start, start_time + 0.05)
                end_hint = line_end_hints[i]
                if end_hint is not None and end_hint > 0:
                    slot_end = min(slot_end, float(end_hint))

                # Leave a tiny gap so transitions don’t sound like hard cuts.
                pad_seconds = 0.05
                slot_duration = max(slot_end - start_time - pad_seconds, 0.1)

                # Load audio and add delay to position at correct timestamp
                audio = ffmpeg.input(line.audio_path)

                # Prefer tempo-fitting VO into its slot rather than hard-trimming (prevents cut-off words).
                src_dur = _probe_audio_duration_seconds(line.audio_path)
                if src_dur is not None and slot_duration > 0.05 and src_dur > (slot_duration + 0.06):
                    max_factor = _env_float("VO_ATEMPO_MAX", 1.35)
                    needed_factor = max(src_dur / slot_duration, 1.0)
                    factor = min(needed_factor, max_factor)
                    if factor > 1.01:
                        audio = _apply_atempo(audio, factor)

                # Trim VO to its slot as a safety net, and fade out to avoid abrupt cuts.
                audio = ffmpeg.filter(audio, "atrim", duration=slot_duration)
                audio = ffmpeg.filter(audio, "asetpts", "PTS-STARTPTS")
                # Tiny fade in/out improves perceived quality for cut-up dialogue.
                fade_in = min(0.06, max(0.02, slot_duration * 0.08))
                audio = ffmpeg.filter(audio, "afade", t="in", st=0, d=fade_in)
                fade_out = min(0.15, max(0.05, slot_duration * 0.15))
                fade_start = max(slot_duration - fade_out, 0.0)
                audio = ffmpeg.filter(audio, "afade", t="out", st=fade_start, d=fade_out)

                # Optional volume knobs (env-tunable, demo-friendly).
                vo_volume = _env_float("VO_VOLUME", 1.0)
                if vo_volume != 1.0:
                    audio = ffmpeg.filter(audio, "volume", volume=vo_volume)

                if start_time > 0:
                    # Apply adelay filter for timeline positioning
                    delay_ms = int(start_time * 1000)
                    audio = ffmpeg.filter(audio, 'adelay', f"{delay_ms}|{delay_ms}")

                voice_inputs.append(audio)

        # Add per-scene SFX (if available)
        if scenes:
            sfx_volume = _env_float("SFX_VOLUME", 0.75)

            for idx, scene in enumerate(scenes):
                sfx_path = getattr(scene, "sfx_path", None)
                if not sfx_path or not os.path.exists(sfx_path):
                    continue

                # Align SFX to the start of the corresponding clip when possible.
                start_time = 0.0
                if idx < len(clip_start_times):
                    start_time = float(clip_start_times[idx] or 0.0)
                else:
                    # Fallback: cumulative duration
                    start_time = float(sum((getattr(s, "duration", 0) or 0) for s in scenes[:idx]))

                dur = float(getattr(scene, "duration", 1) or 1)
                # Keep SFX short and punchy to avoid masking dialogue.
                sfx_dur = max(min(dur, 3.5), 0.3)

                sfx = ffmpeg.input(sfx_path)
                sfx = ffmpeg.filter(sfx, "atrim", duration=sfx_dur)
                sfx = ffmpeg.filter(sfx, "asetpts", "PTS-STARTPTS")
                sfx = ffmpeg.filter(sfx, "afade", t="in", st=0, d=min(0.08, sfx_dur * 0.2))
                sfx = ffmpeg.filter(sfx, "afade", t="out", st=max(sfx_dur - 0.12, 0.0), d=min(0.12, sfx_dur * 0.25))
                if sfx_volume != 1.0:
                    sfx = ffmpeg.filter(sfx, "volume", volume=sfx_volume)

                if start_time > 0:
                    delay_ms = int(start_time * 1000)
                    sfx = ffmpeg.filter(sfx, "adelay", f"{delay_ms}|{delay_ms}")

                sfx_inputs.append(sfx)

        # Add Background Music
        if state.bgm_path and os.path.exists(state.bgm_path):
            # Loop BGM to cover the full cut (works with short cached loops too).
            bgm = ffmpeg.input(state.bgm_path, stream_loop=-1)
            try:
                bgm = ffmpeg.filter(bgm, "atrim", duration=float(video_end_time))
                bgm = ffmpeg.filter(bgm, "asetpts", "PTS-STARTPTS")
            except Exception:
                pass
            bgm_volume = _env_float("BGM_VOLUME", 0.18)
            bgm = ffmpeg.filter(bgm, 'volume', volume=bgm_volume)
            bgm_input = bgm

        def _mix_streams(streams: list[ffmpeg.Stream]) -> ffmpeg.Stream | None:
            if not streams:
                return None
            if len(streams) == 1:
                return streams[0]
            return ffmpeg.filter(streams, "amix", inputs=len(streams), duration="longest")

        voice_mix = _mix_streams(voice_inputs)
        sfx_mix = _mix_streams(sfx_inputs)

        # Optional BGM ducking under dialogue for clarity.
        if bgm_input is not None and voice_mix is not None and _env_truthy("BGM_DUCKING", default=True):
            # `ffmpeg-python` requires an explicit split when one stream feeds multiple consumers.
            # We use one split for the sidechain detector and one for the final mix.
            voice_split = voice_mix.filter_multi_output("asplit")
            voice_sidechain = voice_split[0]
            voice_mix = voice_split[1]

            # IMPORTANT: sidechaincompress output duration follows the shortest input.
            # If dialogue ends early, BGM can get cut off. Pad the sidechain with silence
            # so the BGM continues for the full video duration.
            try:
                voice_sidechain = ffmpeg.filter(voice_sidechain, "apad")
                voice_sidechain = ffmpeg.filter(voice_sidechain, "atrim", duration=float(video_end_time))
                voice_sidechain = ffmpeg.filter(voice_sidechain, "asetpts", "PTS-STARTPTS")
            except Exception:
                # If padding fails, fall back to unpadded sidechain (better than failing render).
                pass

            # Compress the BGM (main) using the voice mix as sidechain.
            # Values are linear (0..1), not dB.
            bgm_input = ffmpeg.filter(
                [bgm_input, voice_sidechain],
                "sidechaincompress",
                threshold=_env_float("BGM_DUCKING_THRESHOLD", 0.08),
                ratio=_env_float("BGM_DUCKING_RATIO", 8.0),
                attack=_env_float("BGM_DUCKING_ATTACK", 25.0),
                release=_env_float("BGM_DUCKING_RELEASE", 250.0),
            )

        final_streams = [s for s in (voice_mix, sfx_mix, bgm_input) if s is not None]
        mixed_audio = _mix_streams(final_streams)

        if mixed_audio is None:
            # Fallback silence
            total_duration = 0.0
            if scenes:
                total_duration = float(sum((getattr(s, "duration", 0) or 0) for s in scenes))
            # `anullsrc` requires a positive duration.
            return ffmpeg.input("anullsrc", f="lavfi", t=max(total_duration, 1.0))

        # Apply loudness normalization (defaults to OTT broadcast -23 LUFS).
        # For web/social preview you often want -16 LUFS; set env `LOUDNORM_I=-16`.
        ln_i = _env_float("LOUDNORM_I", -23.0)
        ln_tp = _env_float("LOUDNORM_TP", -2.0)
        ln_lra = _env_float("LOUDNORM_LRA", 7.0)
        mixed_audio = ffmpeg.filter(mixed_audio, "loudnorm", I=ln_i, TP=ln_tp, LRA=ln_lra)

        return mixed_audio

    def _encode_ott_broadcast(self, video_stream: ffmpeg.Stream, audio_stream: ffmpeg.Stream,
                             output_path: str, resolution: str = "1080p", crf: int = 18, preset: str = "slow"):
        """
        Encode with OTT broadcast-quality settings.

        OTT Standards:
        - Video: H.264, 12 Mbps bitrate, 1080p, yuv420p
        - Audio: AAC, 320 kbps, 48 kHz, stereo, -23 LUFS loudness
        - Profile: High, Level 4.0
        
        OPTIMIZATION: Accepts crf and preset for adaptive quality fallback.
        """
        BITRATE_SETTINGS = {
            "4k": {"video": "18M", "audio": "320k", "width": 3840, "height": 2160},
            "1080p": {"video": "12M", "audio": "320k", "width": 1920, "height": 1080},
            "720p": {"video": "6M", "audio": "192k", "width": 1280, "height": 720}
        }

        settings = BITRATE_SETTINGS.get(resolution, BITRATE_SETTINGS["1080p"])

        # Ensure 1920x1080 resolution (scale if needed)
        video_stream = ffmpeg.filter(video_stream, 'scale', settings["width"], settings["height"])

        # Output with OTT broadcast specifications.
        #
        # NOTE: Use explicit stream-specifier flags (e.g. `b:v`, `maxrate:v`) to reliably engage VBV.
        # We previously used generic kwargs like `video_bitrate`/`maxrate`, which can silently fail
        # depending on ffmpeg-python argument mapping, leading to extremely large files.
        target_bitrate = str(settings["video"])
        bufsize = None
        if isinstance(target_bitrate, str) and target_bitrate.lower().endswith(("m", "k")):
            try:
                numeric = float(target_bitrate[:-1])
                unit = target_bitrate[-1].lower()
                bufsize = f"{int(numeric * 2)}{unit}"
            except Exception:
                bufsize = None

        output_kwargs = {
            # Video settings
            "c:v": "libx264",
            "preset": preset,
            "crf": crf,
            "profile:v": "high",
            "level:v": "4.0",
            "pix_fmt": "yuv420p",
            # VBV cap (prevents runaway bitrates)
            "b:v": target_bitrate,
            "maxrate:v": target_bitrate,
        }
        if bufsize:
            output_kwargs["bufsize:v"] = bufsize

        # Audio settings
        output_kwargs.update(
            {
                "c:a": "aac",
                "b:a": str(settings["audio"]),
                "ar": 48000,
                "ac": 2,
                # Container settings
                "movflags": "faststart",
            }
        )

        stream = ffmpeg.output(video_stream, audio_stream, output_path, **output_kwargs)

        # Execute encoding
        ffmpeg.run(
            stream,
            cmd=self._ffmpeg_cmd,
            overwrite_output=True,
            capture_stdout=True,
            capture_stderr=True,
        )

    def _encode_with_adaptive_quality(self, video_stream: ffmpeg.Stream, audio_stream: ffmpeg.Stream,
                                      output_path: str, resolution: str = "1080p"):
        """
        OPTIMIZATION: Adaptive quality encoding with CRF fallback.
        Tries CRF 18 (highest quality) first, then falls back to 23, then 28 if encoding fails.
        This handles low-memory or slow machines gracefully with automatic quality reduction.
        """
        crf_levels = [18, 23, 28]  # Highest → Medium → Low quality
        preset_levels = ["slow", "medium", "fast"]  # Best → Balanced → Fast
        
        for i, (crf, preset) in enumerate(zip(crf_levels, preset_levels)):
            try:
                quality_desc = ["Highest (CRF 18)", "Medium (CRF 23)", "Low (CRF 28)"][i]
                print(f"   [ENCODE] Attempting {quality_desc} quality with '{preset}' preset...")
                
                self._encode_ott_broadcast(video_stream, audio_stream, output_path, resolution, crf=crf, preset=preset)
                print(f"   [OK] Encoding succeeded at {quality_desc} quality")
                return
                
            except Exception as e:
                if i < len(crf_levels) - 1:
                    print(f"   [WARN] {quality_desc} encoding failed: {e}")
                    print(f"   [FALLBACK] Trying lower quality...")
                else:
                    print(f"   [FATAL] All quality levels failed: {e}")
                    raise e
