#!/usr/bin/env python3
"""
Generate a single 15s commercial for a real company URL (demo-safe: no logos, no readable text).
Uses:
- Veo text-to-video for visuals (3 scenes: 4s/4s/8s)
- Edge TTS voice for VO (huge free voice library)
- Reuses an existing cached BGM track if available (avoids paid BGM generation)
- Endcard + optional grade in post (Composer)

Usage (Windows PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  .\\.venv\\Scripts\\python.exe scripts\\generate_company_ad.py --url https://tailscale.com --name Tailscale
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import uuid
from pathlib import Path

import requests
from openai import OpenAI

from ott_ad_builder.config import config
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState, Scene, Script, ScriptLine


def _sanitize_company_name(value: str) -> str:
    s = re.sub(r"\s+", " ", (value or "").strip())
    s = re.sub(r"[^\w \-&+.]", "", s)
    return s[:60].strip() or "Company"


def _fetch_site_summary(url: str) -> dict:
    out = {"title": "", "description": "", "url": url}
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": "botspot-demo/1.0"})
        resp.raise_for_status()
        html = resp.text or ""
        # Cheap extraction (avoid heavyweight parsing).
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_m:
            out["title"] = re.sub(r"\s+", " ", title_m.group(1)).strip()[:120]
        desc_m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]*content=["\'](.*?)["\']',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if desc_m:
            out["description"] = re.sub(r"\s+", " ", desc_m.group(1)).strip()[:240]
        # Grab a few headlines for richer context.
        h = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.IGNORECASE | re.DOTALL)
        if h:
            clean = []
            for x in h[:10]:
                t = re.sub(r"<[^>]+>", " ", x)
                t = re.sub(r"\s+", " ", t).strip()
                if t and len(t) <= 120:
                    clean.append(t)
            out["headlines"] = clean[:6]
    except Exception:
        pass
    return out


def _pick_cached_bgm() -> str | None:
    audio_dir = Path(config.ASSETS_DIR) / "audio"
    if not audio_dir.exists():
        return None
    candidates = sorted(audio_dir.glob("bgm_*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    return str(candidates[0])


def _make_scenes(category: str, vibe: str) -> list[Scene]:
    cat = (category or "modern product").strip()
    return [
        Scene(
            id=1,
            duration=4,
            visual_prompt=f"Premium cinematic {vibe} establishing still: {cat} world, clean geometric composition, modern lighting. No logos, no readable text.",
            motion_prompt=(
                f"Premium cinematic {vibe}. Establish the {cat} world with real humans and realistic movement. "
                "Camera: smooth steadicam close-medium, gentle push-in. "
                "No logos, no readable text, no floating objects, no duplicated limbs."
            ),
            audio_prompt=None,
        ),
        Scene(
            id=2,
            duration=4,
            visual_prompt=f"Detail craft still: hands-in-action moment that shows {cat} benefit. No logos, no readable text.",
            motion_prompt=(
                f"Detail craft shot for {cat}: tactile realism, premium lighting, subtle motion. "
                "If screens appear, keep them dark/out-of-focus with abstract shapes only (no UI text). "
                "Camera: macro close-up, smooth move then lock."
            ),
            audio_prompt=None,
        ),
        Scene(
            id=3,
            duration=8,
            visual_prompt=f"Payoff hero still: confident customer moment for {cat}. No readable text (endcard added in post).",
            motion_prompt=(
                f"Payoff hero shot for {cat}: confident customer moment, warm but premium. "
                "Camera: slow dolly back to reveal scene, then hold steady for endcard. "
                "No logos, no readable text, no floating objects."
            ),
            audio_prompt=None,
        ),
    ]


def _make_vo_lines(name: str, description: str, *, voice_id: str) -> list[ScriptLine]:
    # Keep it short and general; avoid verbatim copying from site.
    desc = (description or "").strip()
    if desc:
        # Keep it one clause.
        desc = re.sub(r"[.!?].*$", "", desc).strip()
        desc = re.sub(r"\s+", " ", desc)[:120]
    beat2 = desc or "A clean, modern product built for speed, clarity, and confidence."

    return [
        ScriptLine(
            speaker="Narrator",
            voice_id=voice_id,
            scene_id=1,
            time_range="0.0-4.6s",
            text=f"{name}. Make the work feel effortless.",
        ),
        ScriptLine(
            speaker="Narrator",
            voice_id=voice_id,
            scene_id=2,
            time_range="4.6-9.4s",
            text=beat2,
        ),
        ScriptLine(
            speaker="Narrator",
            voice_id=voice_id,
            scene_id=3,
            time_range="9.4-14.6s",
            text=f"Try {name} today. See what you can ship this week.",
        ),
    ]

def _llm_story_pack(*, name: str, url: str, site: dict, category_hint: str, vibe_hint: str) -> dict | None:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None
    client = OpenAI(api_key=api_key)

    headlines = site.get("headlines") or []
    if not isinstance(headlines, list):
        headlines = []

    prompt = {
        "company_name": name,
        "url": url,
        "meta_title": site.get("title") or "",
        "meta_description": site.get("description") or "",
        "headlines": headlines,
        "constraints": [
            "15 seconds total, 3 scenes (4s, 4s, 8s).",
            "No logos, no brand marks, no readable text in video scenes.",
            "Avoid claims that require verification (no numbers, no 'best', no awards).",
            "Write a mini-story: problem -> solution -> payoff.",
            "Voiceover must be short enough to fit each slot.",
        ],
        "category_hint": category_hint,
        "vibe_hint": vibe_hint,
        "output_format": "JSON only",
        "schema": {
            "category": "string",
            "vibe": "string",
            "grade": "one of: cool, warm, clean, vibrant, crisp, none",
            "endcard_subtitle": "string (<= 80 chars)",
            "scenes": [
                {"id": 1, "duration": 4, "visual_prompt": "string", "motion_prompt": "string"},
                {"id": 2, "duration": 4, "visual_prompt": "string", "motion_prompt": "string"},
                {"id": 3, "duration": 8, "visual_prompt": "string", "motion_prompt": "string"},
            ],
            "vo": [
                {"scene_id": 1, "time_range": "0.0-4.6s", "text": "string"},
                {"scene_id": 2, "time_range": "4.6-9.4s", "text": "string"},
                {"scene_id": 3, "time_range": "9.4-14.6s", "text": "string"},
            ],
        },
    }

    resp = client.responses.create(
        model=os.getenv("OPENAI_MODEL") or "gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": "You are an ad director + copywriter. Output JSON only (no markdown).",
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
    )
    text = (resp.output_text or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("scenes") and data.get("vo"):
            return data
    except Exception:
        return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--category", default="software company")
    ap.add_argument("--vibe", default="tech")
    ap.add_argument("--voice", default="edge:en-US-GuyNeural", help="Use edge:* or sapi:* or ElevenLabs voice id.")
    ap.add_argument("--grade", default="cool", help="none|warm|cool|clean|vibrant|crisp")
    ap.add_argument("--story", action="store_true", help="Use LLM to generate a mini-story script + better scene prompts.")
    ap.add_argument("--out-dir", default="output", help="Output directory under repo root.")
    args = ap.parse_args()

    url = str(args.url).strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    site = _fetch_site_summary(url)
    name = _sanitize_company_name(args.name or site.get("title") or url.replace("https://", "").replace("http://", "").split("/")[0])
    category = str(args.category or "").strip()
    vibe = str(args.vibe or "").strip()
    voice_id = str(args.voice or "").strip()
    grade = str(args.grade or "").strip().lower()

    project_id = str(uuid.uuid4())
    out_dir = (Path(__file__).resolve().parents[1] / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Post settings (Composer).
    os.environ["ENDCARD_ENABLED"] = "1"
    os.environ["ENDCARD_STYLE"] = "random"
    os.environ["ENDCARD_TEXT_ALIGN"] = "center"
    os.environ["ENDCARD_ACCENT"] = "random"
    os.environ["ENDCARD_BOX_ALPHA"] = "0.48"
    os.environ["ENDCARD_DURATION"] = "2.6"
    os.environ["ENDCARD_SEED"] = f"{project_id}:{time.time()}"
    os.environ["ENDCARD_TITLE"] = name
    os.environ["ENDCARD_SUBTITLE"] = (site.get("description") or category)[:120]
    os.environ["ENDCARD_URL"] = url.replace("https://", "").replace("http://", "").rstrip("/")
    os.environ["ENDCARD_QR"] = "1"
    os.environ["ENDCARD_QR_URL"] = url
    os.environ["GRADE_PRESET"] = grade if grade else "none"

    pack = None
    if args.story:
        pack = _llm_story_pack(name=name, url=url, site=site, category_hint=category, vibe_hint=vibe)

    if isinstance(pack, dict):
        category = str(pack.get("category") or category).strip() or category
        vibe = str(pack.get("vibe") or vibe).strip() or vibe
        grade = str(pack.get("grade") or grade).strip().lower() or grade
        os.environ["GRADE_PRESET"] = grade if grade else "none"
        endcard_sub = str(pack.get("endcard_subtitle") or "").strip()
        if endcard_sub:
            os.environ["ENDCARD_SUBTITLE"] = endcard_sub[:120]

        scenes = []
        for s in pack.get("scenes") or []:
            scenes.append(
                Scene(
                    id=int(s.get("id") or 0),
                    duration=int(s.get("duration") or 0),
                    visual_prompt=str(s.get("visual_prompt") or ""),
                    motion_prompt=str(s.get("motion_prompt") or ""),
                    audio_prompt=None,
                )
            )
        lines = []
        for v in pack.get("vo") or []:
            lines.append(
                ScriptLine(
                    speaker="Narrator",
                    voice_id=voice_id,
                    scene_id=int(v.get("scene_id") or 0),
                    time_range=str(v.get("time_range") or ""),
                    text=str(v.get("text") or ""),
                )
            )
        # Guard if LLM returned garbage.
        if not scenes or not lines:
            scenes = _make_scenes(category=category, vibe=vibe)
            lines = _make_vo_lines(name=name, description=str(site.get("description") or ""), voice_id=voice_id)
    else:
        scenes = _make_scenes(category=category, vibe=vibe)
        lines = _make_vo_lines(name=name, description=str(site.get("description") or ""), voice_id=voice_id)

    script = Script(lines=lines, mood="commercial", scenes=scenes)

    state = ProjectState(
        id=project_id,
        user_input=f"Online company demo: {name} ({url})",
        status="images_complete",
        script=script,
    )

    plan_dir = Path(config.OUTPUT_DIR)
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"plan_{project_id}.json"
    plan_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    # 1) Videos (Veo text-to-video)
    gen = AdGenerator(project_id=project_id)
    gen.generate_videos_only(project_id=project_id)

    # 2) Reuse cached BGM if available (avoid paid BGM generation).
    updated = ProjectState(**json.loads(plan_path.read_text("utf-8")))
    bgm = _pick_cached_bgm()
    if bgm and os.path.exists(bgm):
        updated.bgm_path = bgm

    # Ensure VO uses the requested voice provider.
    for line in updated.script.lines or []:
        line.voice_id = voice_id
        line.audio_path = None
    plan_path.write_text(updated.model_dump_json(indent=2), encoding="utf-8")

    assemble = AdGenerator(project_id=project_id)
    assemble.remix_audio_only(
        script=updated.script,
        regenerate_all=True,
        include_bgm=False,
        include_sfx=False,
    )

    final = assemble.state.final_video_path
    if not final or not os.path.exists(final):
        raise RuntimeError("Final render missing")

    safe = re.sub(r"[^a-zA-Z0-9_\\-]+", "_", name.lower()).strip("_")[:40] or "company"
    out_full = out_dir / f"{safe}_{project_id}_full.mp4"
    out_15s = out_dir / f"{safe}_{project_id}_15s.mp4"
    shutil.copyfile(final, out_full)

    # Trim to 15s for safety.
    subprocess_args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(out_full),
        "-t",
        "15",
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
        "afade=t=out:st=14.6:d=0.4",
        str(out_15s),
    ]
    import subprocess

    subprocess.check_call(subprocess_args)

    print("OK")
    print(f"Name: {name}")
    print(f"URL:  {url}")
    print(f"Out:  {out_15s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
