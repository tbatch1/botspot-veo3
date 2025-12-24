import argparse
import glob
import os
import shutil
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState
from ott_ad_builder.providers.elevenlabs import ElevenLabsProvider
from ott_ad_builder.parallel_utils import ParallelAudioGenerator


def _ensure_ffmpeg_on_path() -> None:
    """
    Composer uses ffmpeg/ffprobe via ffmpeg-python. Make sure they're on PATH.
    Mirrors the logic in `start_backend.bat`, but usable from a Python script.
    """
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    root = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    if not root or not os.path.isdir(root):
        return

    candidates = glob.glob(os.path.join(root, "Gyan.FFmpeg_*", "ffmpeg-*", "bin", "ffmpeg.exe"))
    if not candidates:
        return

    ffmpeg_dir = os.path.dirname(candidates[0])
    os.environ["PATH"] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate VO (with slot-fit) and re-assemble using existing video clips.")
    parser.add_argument("--project-id", required=True, help="Project id (plan_<id>.json in output/).")
    parser.add_argument("--output-name", default="", help="Optional output filename (mp4) under output/.")
    parser.add_argument(
        "--redraft-dialogue",
        action="store_true",
        help="Use GPT-5.2 to re-draft dialogue for the existing scenes (keeps visuals/videos, improves pacing).",
    )
    args = parser.parse_args()

    _ensure_ffmpeg_on_path()

    project_id = args.project_id.strip()
    if not project_id:
        raise SystemExit("--project-id is required")

    gen = AdGenerator(project_id=project_id)
    plan_path = gen._get_plan_path()
    if not os.path.exists(plan_path):
        raise FileNotFoundError(f"Plan not found: {plan_path}")

    print(f"[LOAD] {plan_path}")
    gen.state = ProjectState.model_validate_json(open(plan_path, "r", encoding="utf-8").read())

    if not gen.state.script or not gen.state.script.lines or not gen.state.script.scenes:
        raise RuntimeError("Plan is missing script lines/scenes.")

    # Validate we have existing video clips (we are remixing, not regenerating video).
    missing = [s.id for s in gen.state.script.scenes if not s.video_path or not os.path.exists(s.video_path)]
    if missing:
        raise RuntimeError(f"Missing video clips for scene(s): {missing}. Run video generation first.")

    eleven = ElevenLabsProvider()
    if not getattr(eleven, "client", None):
        raise RuntimeError("ElevenLabs client failed to initialize. Check ELEVENLABS_API_KEY.")

    if args.redraft_dialogue:
        if not isinstance(gen.state.strategy, dict):
            raise RuntimeError("Cannot redraft dialogue: plan is missing strategy.")

        print("[DIALOGUE] Re-drafting dialogue for existing scenes (GPT-5.2)...")
        # Re-snap before polishing so scene windows are well-defined.
        gen._align_dialogue_to_scenes(gen.state.script, strategy=gen.state.strategy, freeze_speakers=False)

        # Dialogue doctor pass (speakers + scene sync).
        polished = gen.spatial.polish_dialogue_lines(gen.state.strategy, gen.state.script, target_duration=15)
        if polished:
            from ott_ad_builder.state import ScriptLine

            gen.state.script.lines = [ScriptLine(**l) for l in polished if isinstance(l, dict)]
            gen._align_dialogue_to_scenes(gen.state.script, strategy=gen.state.strategy, freeze_speakers=True)

        # Tighten text to the assigned time ranges (keeps timing, improves VO fit).
        tightened = gen.spatial.tighten_dialogue_to_time_ranges(gen.state.strategy, gen.state.script, target_duration=15)
        if tightened:
            from ott_ad_builder.state import ScriptLine

            gen.state.script.lines = [ScriptLine(**l) for l in tightened if isinstance(l, dict)]

    # Force VO regeneration so the remix is consistent with current settings + code.
    for line in gen.state.script.lines:
        line.audio_path = None

    print(f"[AUDIO] Regenerating VO for {len(gen.state.script.lines)} line(s)...")
    pa = ParallelAudioGenerator(eleven, gen.state)
    vo_results = pa.generate_vo_batch(gen.state.script.lines)
    for idx, audio_path in vo_results:
        if audio_path:
            gen.state.script.lines[idx].audio_path = audio_path

    # Slot-fit pass (may rewrite + regenerate a few lines).
    print("[AUDIO] Fitting VO to time slots (auto-rewrite/regenerate if needed)...")
    gen._auto_fit_voiceover_lines(eleven, strategy=gen.state.strategy if isinstance(gen.state.strategy, dict) else None)

    # Assemble using existing clips.
    print("[ASSEMBLY] Composing final video (existing clips + new audio)...")
    from ott_ad_builder.providers.composer import Composer

    composer = Composer()
    final_path = composer.compose(gen.state, transition_type=getattr(gen.state, "transition_type", "fade"))
    if not final_path or not os.path.exists(final_path):
        raise RuntimeError("Composer returned invalid path.")

    # Optionally copy to a stable, shareable name.
    if args.output_name.strip():
        out_name = args.output_name.strip()
        if not out_name.lower().endswith(".mp4"):
            out_name += ".mp4"
        dst = os.path.join(os.path.dirname(final_path), out_name)
    else:
        dst = os.path.join(os.path.dirname(final_path), f"final_ad_{project_id}_remix.mp4")

    try:
        shutil.copyfile(final_path, dst)
        print(f"[OK] Saved: {dst}")
    except Exception as e:
        print(f"[WARN] Could not copy output: {e}")
        dst = final_path

    gen.state.final_video_path = dst
    gen.state.status = "completed"
    gen.save_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
