import argparse
import glob
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.config import config
from ott_ad_builder.providers.composer import Composer
from ott_ad_builder.showroom import publish_render, reset_showroom, load_manifest, save_manifest
from ott_ad_builder.state import ProjectState


def _ensure_ffmpeg_on_path() -> None:
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


def _safe_https(url: str) -> str:
    u = str(url or "").strip()
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return f"https://{u.lstrip('/')}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore showroom to best 15s pack using cached VO/BGM (no new API calls).")
    parser.add_argument("--pack", default="showcase_pack_edge", help="Pack folder under output/ (must include showcase_manifest.json).")
    parser.add_argument("--delete-files", action="store_true", help="Delete MP4s in output/showroom before restoring.")
    args = parser.parse_args()

    _ensure_ffmpeg_on_path()

    pack = str(args.pack or "").strip() or "showcase_pack_edge"
    pack_manifest = Path(config.OUTPUT_DIR) / pack / "showcase_manifest.json"
    if not pack_manifest.exists():
        raise SystemExit(f"Pack manifest not found: {pack_manifest}")

    reset_showroom(delete_files=bool(args.delete_files))

    data = json.loads(pack_manifest.read_text(encoding="utf-8"))
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit(f"Pack manifest has no items: {pack_manifest}")

    category_by_project: dict[str, str] = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        plan_name = str(it.get("plan") or "").strip()
        pid = str(it.get("project_id") or "").strip()
        if not pid and plan_name:
            pid = plan_name.replace("plan_", "").replace(".json", "")
        cat = str(it.get("category") or "").strip()
        if pid and cat:
            category_by_project[pid] = cat

    audio_dir = Path(config.ASSETS_DIR) / "audio"
    bgm_candidates = sorted(audio_dir.glob("bgm_loop_*_30s.mp3"), key=lambda p: p.name) or sorted(
        audio_dir.glob("bgm_*.mp3"), key=lambda p: p.name
    )

    def pick_bgm(seed: str) -> str | None:
        if not bgm_candidates:
            return None
        h = hashlib.md5(seed.encode("utf-8", errors="ignore")).hexdigest()
        return str(bgm_candidates[int(h[:8], 16) % len(bgm_candidates)])

    cta_variants = [
        "Scan to learn more.",
        "Try it today.",
        "See what’s possible.",
        "Built for busy people.",
    ]

    composer = Composer()

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

            if not getattr(state, "bgm_path", None) or not os.path.exists(str(state.bgm_path)):
                picked = pick_bgm(project_id or name)
                if picked and os.path.exists(picked):
                    state.bgm_path = picked

            seed = project_id or name
            cta = cta_variants[
                int(hashlib.md5(seed.encode("utf-8", errors="ignore")).hexdigest()[:8], 16) % len(cta_variants)
            ]

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
            publish_render(
                final_video_path=final_path,
                project_id=project_id,
                title=name,
                url=url,
                category=category,
                plan_filename=plan_name,
                trim=False,
            )
            print(f"[OK] {name} ({project_id})")
        except Exception as e:
            errors.append({"name": name, "project_id": project_id, "plan": plan_name, "error": str(e)})
            print(f"[ERR] {name}: {e}")
        finally:
            for k in env_keys:
                v = env_backup.get(k)
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    manifest = load_manifest()
    manifest.setdefault("notes", [])
    manifest["notes"].insert(0, "Restored best 15s pack (cached VO + endcards).")
    if errors:
        manifest.setdefault("errors", [])
        manifest["errors"] = [
            {
                "key": str(e.get("project_id") or e.get("plan") or e.get("name") or "unknown"),
                "name": str(e.get("name") or "unknown"),
                "error": str(e.get("error") or ""),
            }
            for e in errors
        ]

    # Ensure categories match the pack metadata (avoid generic labels).
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
    save_manifest(manifest)
    print(f"[DONE] Showroom items: {len(manifest.get('items') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
