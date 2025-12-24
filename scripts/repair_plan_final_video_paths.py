import json
import os
import re
import shutil
from pathlib import Path


def _safe_run_id(project_id: str) -> str:
    run_id = str(project_id or "").strip() or "run"
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", run_id).strip("_-")[:24] or "run"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return None
    except Exception:
        return None


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "output"
    showroom_dir = output_dir / "showroom"
    manifest_path = showroom_dir / "showcase_manifest.json"

    showroom_by_project: dict[str, str] = {}
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
        if isinstance(manifest, dict):
            items = manifest.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    pid = str(item.get("project_id") or "").strip()
                    video = str(item.get("video") or "").strip()
                    if pid and video:
                        showroom_by_project[pid] = video

    plans = sorted(output_dir.glob("plan_*.json"))
    updated = 0
    skipped = 0

    for plan_path in plans:
        data = _load_json(plan_path)
        if not isinstance(data, dict):
            skipped += 1
            continue

        project_id = str(data.get("id") or "").strip() or plan_path.stem.replace("plan_", "")
        final_path = str(data.get("final_video_path") or "").strip()
        if os.path.basename(final_path) != "final_ad.mp4":
            continue

        safe = _safe_run_id(project_id)
        candidates: list[Path] = []

        direct = output_dir / f"final_ad_{safe}.mp4"
        if direct.exists():
            candidates.append(direct)

        candidates.extend(sorted(output_dir.glob(f"final_ad_{safe}*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True))
        candidates = [p for p in candidates if p.exists()]

        chosen: Path | None = candidates[0] if candidates else None

        if chosen is None:
            # Heuristic fallback: match other outputs that embed the project id (or its prefix).
            pid_prefix = project_id[:8]
            heuristic: list[Path] = []
            for pat in (f"*{project_id}*.mp4", f"*{pid_prefix}*.mp4"):
                heuristic.extend(output_dir.glob(pat))
            # Avoid selecting the global/known-bad filename and absurdly large debug exports.
            heuristic = [
                p
                for p in heuristic
                if p.exists()
                and p.name.lower() != "final_ad.mp4"
                and p.stat().st_size < 300 * 1024 * 1024
            ]
            heuristic.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            chosen = heuristic[0] if heuristic else None

        if chosen is None:
            showroom_name = showroom_by_project.get(project_id)
            if showroom_name:
                showroom_src = showroom_dir / showroom_name
                if showroom_src.exists():
                    # Copy into output/ so frontend basename-only lookups still work.
                    chosen = output_dir / f"final_ad_{safe}.mp4"
                    if not chosen.exists():
                        shutil.copy2(showroom_src, chosen)

        if chosen is None or not chosen.exists():
            skipped += 1
            continue

        data["final_video_path"] = str(chosen.resolve())
        _write_json(plan_path, data)
        updated += 1

    print(f"[repair] updated={updated} skipped={skipped} total_plans={len(plans)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
