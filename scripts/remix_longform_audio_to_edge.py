#!/usr/bin/env python3
"""
Remix long-form projects to Edge neural TTS (free) and re-publish to Showroom.

Use this when paid TTS quotas (OpenAI/ElevenLabs) are exhausted but you still need
a human-sounding demo VO quickly.

Usage (PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  $env:SHOWROOM_TRIM_ENABLE="0"
  .\\.venv\\Scripts\\python.exe scripts\\remix_longform_audio_to_edge.py --project-id <uuid> [--project-id <uuid>]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from ott_ad_builder.config import config
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.showroom import publish_render
from ott_ad_builder.state import ProjectState


def _load_state(project_id: str) -> ProjectState:
    plan_path = Path(config.OUTPUT_DIR) / f"plan_{project_id}.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing plan: {plan_path}")
    return ProjectState(**json.loads(plan_path.read_text(encoding="utf-8")))


def _speaker_voice_map(state: ProjectState) -> dict[str, str]:
    speakers = []
    for line in state.script.lines or []:
        s = str(getattr(line, "speaker", "") or "").strip()
        if s:
            speakers.append(s)

    unique = []
    seen = set()
    for s in speakers:
        k = s.strip().lower()
        if k and k not in seen:
            seen.add(k)
            unique.append(k)

    # Two solid Edge neural voices (usually the least "robotic" for demos).
    narrator_f = os.getenv("EDGE_VOICE_FEMALE") or "en-US-JennyNeural"
    narrator_m = os.getenv("EDGE_VOICE_MALE") or "en-US-GuyNeural"

    mapping: dict[str, str] = {}
    for k in unique:
        if k in ("narrator", "voiceover", "vo"):
            mapping[k] = f"edge:{narrator_m}"
            continue
        # Heuristic: map common feminine names to female voice (demo-only).
        if any(token in k for token in ("maya", "sara", "mia", "ava", "ella", "olivia", "emma")):
            mapping[k] = f"edge:{narrator_f}"
        else:
            mapping[k] = f"edge:{narrator_m}"
    return mapping


def remix_one(project_id: str) -> str:
    gen = AdGenerator(project_id=project_id)
    gen.state = _load_state(project_id)

    # Ensure endcard/QR has a URL source of truth.
    endcard_title = ""
    endcard_url = ""
    if isinstance(getattr(gen.state, "strategy", None), dict):
        bc = gen.state.strategy.get("brand_card")
        if isinstance(bc, dict):
            endcard_title = str(bc.get("brand_name") or "").strip()
        prefs = gen.state.strategy.get("applied_preferences")
        if isinstance(prefs, dict):
            endcard_url = str(prefs.get("url") or "").strip()
    if not endcard_title:
        endcard_title = project_id

    # Allow manual override (useful for non-URL demo brands).
    endcard_url = (os.getenv("ENDCARD_URL_OVERRIDE") or "").strip() or endcard_url

    os.environ.setdefault("ENDCARD_ENABLED", "1")
    os.environ["ENDCARD_TITLE"] = endcard_title
    if endcard_url:
        os.environ["ENDCARD_URL"] = endcard_url
        os.environ["ENDCARD_QR"] = "1"

    # Edge tuning (keep natural).
    os.environ.setdefault("EDGE_TTS_RATE", "+0%")
    os.environ.setdefault("EDGE_TTS_PITCH", "+0Hz")
    os.environ.setdefault("EDGE_TTS_VOLUME", "+0%")

    # Mix defaults.
    os.environ.setdefault("BGM_DUCKING", "1")
    os.environ.setdefault("BGM_VOLUME", "0.11")
    os.environ.setdefault("VO_VOLUME", "1.25")

    gen.remix_audio_only(
        regenerate_all=True,
        include_bgm=True,  # will fall back to cached loops if Eleven BGM fails
        speaker_voice_map=_speaker_voice_map(gen.state),
    )

    final_path = str(gen.state.final_video_path or "")
    if not final_path or not os.path.exists(final_path):
        raise RuntimeError(f"Remix produced no final video for {project_id}")

    out_dir = Path("output") / "longform"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{project_id}_edge_remix.mp4"
    shutil.copyfile(final_path, dst)

    title = ""
    url = endcard_url
    category = ""
    if isinstance(getattr(gen.state, "strategy", None), dict):
        bc = gen.state.strategy.get("brand_card")
        if isinstance(bc, dict):
            title = str(bc.get("brand_name") or bc.get("brand") or "").strip()
            url = str(bc.get("url") or bc.get("website") or url or "").strip()
            category = str(bc.get("category") or "").strip()
        if not title:
            title = str(gen.state.strategy.get("product_name") or "").strip()
    if not title:
        title = project_id

    publish_render(
        final_video_path=str(dst),
        project_id=project_id,
        title=title,
        url=url,
        category=category,
        plan_filename=f"plan_{project_id}.json",
        trim=False,
    )

    return str(dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", action="append", required=True)
    args = ap.parse_args()

    os.environ.setdefault("SHOWROOM_TRIM_ENABLE", "0")

    for pid in args.project_id:
        out = remix_one(pid.strip())
        print(f"[OK] Remixed: {pid} -> {out}")


if __name__ == "__main__":
    main()
