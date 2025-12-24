from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import hashlib
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import config


@dataclass(frozen=True)
class ShowroomItem:
    id: str
    created_at: str
    name: str
    url: str
    category: str
    video: str
    plan: str | None
    project_id: str | None
    signature: str | None


def showroom_dir() -> Path:
    p = Path(config.OUTPUT_DIR) / "showroom"
    p.mkdir(parents=True, exist_ok=True)
    return p


def manifest_path() -> Path:
    return showroom_dir() / "showcase_manifest.json"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _slug(value: str) -> str:
    s = re.sub(r"\s+", " ", (value or "").strip()).lower()
    s = re.sub(r"[^a-z0-9 _\\-]", "", s)
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s).strip("_")
    return (s[:48] or "render").strip("_")


def _safe_url(value: str) -> str:
    u = str(value or "").strip()
    u = u.replace("https://", "").replace("http://", "").strip().strip("/")
    return u


def load_manifest() -> dict:
    mp = manifest_path()
    if not mp.exists():
        return {"generated_at": _now(), "items": [], "errors": [], "notes": ["Auto-populated showroom."]}
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("items", [])
            return data
    except Exception:
        pass
    return {"generated_at": _now(), "items": [], "errors": [], "notes": ["Auto-populated showroom."]}


def save_manifest(data: dict) -> None:
    data = dict(data or {})
    data["generated_at"] = _now()
    mp = manifest_path()
    mp.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ffmpeg_cmd() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _trim_to_seconds(*, src: Path, dst: Path, seconds: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Re-encode with a small fade-out for clean endings.
    subprocess.check_call(
        [
            _ffmpeg_cmd(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-t",
            str(int(seconds)),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            f"afade=t=out:st={max(0.0, float(seconds) - 0.4):.2f}:d=0.4",
            str(dst),
        ]
    )


def publish_render(
    *,
    final_video_path: str,
    project_id: str | None = None,
    title: str,
    url: str = "",
    category: str = "",
    plan_filename: str | None = None,
    trim: bool | None = None,
) -> dict:
    """
    Copy (and optionally trim) a final MP4 into the showroom and append to manifest.
    Returns the new manifest item dict.
    """
    src = Path(final_video_path)
    if not src.exists():
        raise FileNotFoundError(f"Video not found: {src}")

    target_seconds = int(float(os.getenv("SHOWROOM_TRIM_SECONDS") or "15"))
    env_trim = str(os.getenv("SHOWROOM_TRIM_ENABLE") or "1").strip().lower() in ("1", "true", "yes", "on")
    do_trim = env_trim if trim is None else bool(trim)

    sig = f"{src.stat().st_size}:{int(src.stat().st_mtime)}"
    data = load_manifest()
    items = data.get("items")
    if not isinstance(items, list):
        items = []

    # De-dupe before copying:
    # - skip if exact signature already published for this project_id
    # - skip if a render for this project_id already exists (Showroom is meant to show the "best" cut)
    existing_item: dict | None = None
    for it in items:
        if not isinstance(it, dict):
            continue
        if project_id and str(it.get("project_id") or "") == project_id:
            if str(it.get("signature") or "") == sig:
                return it
            if str(os.getenv("SHOWROOM_DEDUPE_PROJECT") or "1").strip().lower() in ("1", "true", "yes", "on"):
                existing_item = it
                break

    # If we already have an item for this project, replace it (keeps showroom concise and up-to-date).
    if existing_item is not None:
        try:
            old_video = str(existing_item.get("video") or "").replace("\\", "/").lstrip("/")
            old_path = showroom_dir() / Path(old_video).name
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass
        try:
            items = [it for it in items if not (isinstance(it, dict) and it.get("id") == existing_item.get("id"))]
        except Exception:
            pass

    slug = _slug(title)
    pid_short = (project_id or "")[:8] if project_id else ""
    digest = hashlib.md5(f"{src.name}:{sig}".encode("utf-8", errors="ignore")).hexdigest()[:10]
    base = f"{slug}_{pid_short}_{digest}".strip("_")

    dst_dir = showroom_dir()
    dst = dst_dir / f"{base}.mp4"
    if dst.exists():
        # Extremely defensive: prevent accidental overwrites.
        dst = dst_dir / f"{base}_{uuid.uuid4().hex[:6]}.mp4"
    if do_trim and target_seconds > 0:
        _trim_to_seconds(src=src, dst=dst, seconds=target_seconds)
    else:
        if src.resolve() != dst.resolve():
            dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    item = ShowroomItem(
        id=str(uuid.uuid4()),
        created_at=_now(),
        name=title.strip() or "Render",
        url=_safe_url(url),
        category=(category or "").strip(),
        video=dst.name,
        plan=plan_filename,
        project_id=project_id,
        signature=sig,
    )

    items.insert(
        0,
        {
            "id": item.id,
            "created_at": item.created_at,
            "name": item.name,
            "url": item.url,
            "category": item.category,
            "video": item.video,
            "plan": item.plan,
            "project_id": item.project_id,
            "signature": item.signature,
        },
    )

    data["items"] = items
    save_manifest(data)
    return items[0]


_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _extract_project_id(*, plan: str | None, video_name: str | None) -> str | None:
    for value in (plan or "", video_name or ""):
        m = _UUID_RE.search(str(value))
        if m:
            return m.group(0)
    return None


def import_existing(
    *,
    packs: list[str] | None = None,
    include_company_demo: bool = True,
    include_output_root: bool = False,
    trim: bool = False,
    max_items: int = 500,
) -> dict:
    """
    Import older renders into the showroom by copying from:
    - output/<pack>/showcase_manifest.json (preferred, includes metadata)
    - output/company_demo/*_15s.mp4 (optional)
    - output/*_15s.mp4 (optional, conservative)
    """
    out_root = Path(config.OUTPUT_DIR)
    imported = 0
    skipped = 0
    errors: list[dict] = []

    def _try_publish(*, src: Path, title: str, url: str, category: str, plan: str | None):
        nonlocal imported, skipped
        if imported >= int(max_items):
            skipped += 1
            return
        try:
            pid = _extract_project_id(plan=plan, video_name=src.name)
            publish_render(
                final_video_path=str(src),
                project_id=pid,
                title=title,
                url=url,
                category=category,
                plan_filename=plan,
                trim=bool(trim),
            )
            imported += 1
        except Exception as e:
            errors.append({"src": str(src), "error": str(e)})

    # 1) Import from pack manifests (best metadata).
    pack_dirs: list[Path] = []
    showroom_name = showroom_dir().name
    if packs:
        for p in packs:
            pp = (out_root / str(p)).resolve()
            if pp.exists() and pp.is_dir():
                pack_dirs.append(pp)
    else:
        for d in sorted(out_root.iterdir()):
            if d.is_dir() and d.name != showroom_name and (d / "showcase_manifest.json").exists():
                pack_dirs.append(d)

    for pack_dir in pack_dirs:
        mp = pack_dir / "showcase_manifest.json"
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append({"src": str(mp), "error": f"manifest_read_failed: {e}"})
            continue

        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue

        for it in items:
            if not isinstance(it, dict):
                continue
            video = str(it.get("video") or "").strip()
            if not video or not video.lower().endswith(".mp4"):
                continue
            src = pack_dir / video
            if not src.exists():
                errors.append({"src": str(src), "error": "missing_video"})
                continue
            title = str(it.get("name") or src.stem).strip() or src.stem
            url = str(it.get("url") or "").strip()
            category = str(it.get("category") or "").strip()
            plan = str(it.get("plan") or "").strip() or None
            if plan:
                # Only keep plan if it exists in output/ (served by /api/assets/<plan>).
                if not (out_root / plan).exists():
                    plan = None
            _try_publish(src=src, title=title, url=url, category=category, plan=plan)

    # 2) Import company_demo renders (no manifest).
    if include_company_demo:
        demo_dir = out_root / "company_demo"
        if demo_dir.exists():
            for src in sorted(demo_dir.glob("*_15s.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
                # e.g. tailscale_<uuid>_15s.mp4 -> "tailscale"
                base = re.sub(r"_[0-9a-fA-F-]{36}_15s$", "", src.stem)
                title = base.replace("_", " ").strip().title() or "Company Demo"
                plan = None
                pid = _extract_project_id(plan=None, video_name=src.name)
                if pid and (out_root / f"plan_{pid}.json").exists():
                    plan = f"plan_{pid}.json"
                _try_publish(src=src, title=title, url="", category="company_demo", plan=plan)

    # 3) Optionally import from output root (conservative).
    if include_output_root:
        ignore = {
            "final_ad.mp4",
            "video_only.mp4",
        }
        for src in sorted(out_root.glob("*_15s.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
            if src.name in ignore:
                continue
            title = re.sub(r"_[0-9a-fA-F-]{36}_15s$", "", src.stem).replace("_", " ").strip().title() or src.stem
            _try_publish(src=src, title=title, url="", category="output", plan=None)

    return {"imported": imported, "skipped": skipped, "errors": errors, "packs": [p.name for p in pack_dirs]}


def reset_showroom(*, delete_files: bool = True) -> dict:
    """Clear the showroom manifest and (optionally) delete MP4 files in output/showroom."""
    d = showroom_dir()
    deleted = 0
    if delete_files:
        for p in d.glob("*.mp4"):
            try:
                p.unlink()
                deleted += 1
            except Exception:
                pass
    mp = manifest_path()
    try:
        if mp.exists():
            mp.unlink()
    except Exception:
        pass
    save_manifest({"items": [], "errors": [], "notes": ["Auto-populated showroom."]})
    return {"deleted_files": deleted}


def delete_item(*, item_id: str, delete_file: bool = True) -> bool:
    item_id = str(item_id or "").strip()
    if not item_id:
        return False

    data = load_manifest()
    items = data.get("items")
    if not isinstance(items, list):
        return False

    kept: list[dict] = []
    deleted: dict | None = None
    for it in items:
        if isinstance(it, dict) and str(it.get("id") or "") == item_id:
            deleted = it
            continue
        if isinstance(it, dict):
            kept.append(it)

    if deleted is None:
        return False

    if delete_file:
        fn = str(deleted.get("video") or "").replace("\\", "/").lstrip("/")
        # Only allow deleting within output/showroom.
        target = showroom_dir() / Path(fn).name
        if target.exists():
            try:
                target.unlink()
            except Exception:
                pass

    data["items"] = kept
    save_manifest(data)
    return True
