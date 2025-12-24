#!/usr/bin/env python3
"""
Remix long-form projects to ElevenLabs VO (+ optional BGM) and re-publish to Showroom.

Why: If OpenAI TTS quota is exhausted, we still need human VO for the demo.

Usage (PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  $env:SHOWROOM_TRIM_ENABLE="0"
  .\\.venv\\Scripts\\python.exe scripts\\remix_longform_audio_to_eleven.py --project-id <uuid> [--project-id <uuid>]
"""

from __future__ import annotations

import argparse
import os
import shutil
import json
from pathlib import Path

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.config import config
from ott_ad_builder.state import ProjectState
from ott_ad_builder.showroom import publish_render


def _pick_env(*names: str) -> str:
    for k in names:
        v = str(os.getenv(k) or "").strip()
        if v:
            return v
    return ""


def remix_one(project_id: str, *, include_bgm: bool) -> str:
    gen = AdGenerator(project_id=project_id)

    narrator = _pick_env("ELEVENLABS_VOICE_ID_NARRATOR", "ELEVENLABS_VOICE_ID")
    secondary = _pick_env("ELEVENLABS_VOICE_ID_SECONDARY", "ELEVENLABS_VOICE_ID_2")
    primary = _pick_env("ELEVENLABS_VOICE_ID")

    # Load state so we can build a speaker map.
    plan_path = Path(config.OUTPUT_DIR) / f"plan_{project_id}.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing plan: {plan_path}")
    gen.state = ProjectState(**json.loads(plan_path.read_text(encoding="utf-8")))
    speakers = []
    for line in gen.state.script.lines or []:
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

    speaker_map: dict[str, str] = {}
    for k in unique:
        if k in ("narrator", "voiceover", "vo") and narrator:
            speaker_map[k] = narrator
        elif secondary:
            speaker_map[k] = secondary
        elif primary:
            speaker_map[k] = primary
        elif narrator:
            speaker_map[k] = narrator

    bgm_prompt = None
    if include_bgm and isinstance(getattr(gen.state, "strategy", None), dict):
        audio_sig = gen.state.strategy.get("audio_signature")
        if isinstance(audio_sig, dict):
            bgm_prompt = str(audio_sig.get("bgm_prompt") or "").strip() or None

    gen.remix_audio_only(
        regenerate_all=True,
        include_bgm=include_bgm,
        bgm_prompt=bgm_prompt,
        speaker_voice_map=speaker_map,
    )

    final_path = str(gen.state.final_video_path or "")
    if not final_path or not os.path.exists(final_path):
        raise RuntimeError(f"Remix produced no final video for {project_id}")

    # Keep a named copy in output/longform for convenience.
    out_dir = Path("output") / "longform"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{project_id}_eleven_remix.mp4"
    shutil.copyfile(final_path, dst)

    # Publish/replace showroom entry for this project.
    title = ""
    url = ""
    category = ""
    if isinstance(getattr(gen.state, "strategy", None), dict):
        bc = gen.state.strategy.get("brand_card")
        if isinstance(bc, dict):
            title = str(bc.get("brand_name") or bc.get("brand") or "").strip()
            url = str(bc.get("url") or bc.get("website") or "").strip()
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
    ap.add_argument("--no-bgm", action="store_true")
    args = ap.parse_args()

    os.environ.setdefault("SHOWROOM_TRIM_ENABLE", "0")
    os.environ.setdefault("BGM_DUCKING", "1")
    os.environ.setdefault("BGM_VOLUME", "0.11")
    os.environ.setdefault("VO_VOLUME", "1.25")

    for pid in args.project_id:
        out = remix_one(pid.strip(), include_bgm=not args.no_bgm)
        print(f"[OK] Remixed: {pid} -> {out}")


if __name__ == "__main__":
    main()
