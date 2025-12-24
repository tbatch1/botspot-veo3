#!/usr/bin/env python3
"""
Generate two long-form demo commercials (60s + 30s) using the exact Studio pipeline
(plan -> images -> videos -> assemble), then publish into the Showroom.

Usage (PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  $env:SHOWROOM_TRIM_ENABLE="0"
  .\\.venv\\Scripts\\python.exe scripts\\generate_longform_demo_pair.py
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.showroom import publish_render


def _configure_mix() -> None:
    os.environ.setdefault("LOUDNORM_I", "-16")
    os.environ.setdefault("LOUDNORM_TP", "-1.5")
    os.environ.setdefault("LOUDNORM_LRA", "8")

    # VO-forward mix for demo playback.
    os.environ.setdefault("BGM_DUCKING", "1")
    os.environ.setdefault("BGM_VOLUME", "0.11")
    os.environ.setdefault("VO_VOLUME", "1.25")
    os.environ.setdefault("SFX_VOLUME", "0.70")

    # Endcards: varied by default (Composer seeds from title/url).
    os.environ.setdefault("ENDCARD_ENABLED", "1")
    os.environ.setdefault("ENDCARD_STYLE", "auto")
    os.environ.setdefault("ENDCARD_ACCENT", "auto")

    # OpenAI TTS quality.
    os.environ.setdefault("OPENAI_TTS_FORMAT", "wav")
    os.environ.setdefault("OPENAI_TTS_SPEED", "1.0")


def _copy_final(src: str, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return str(dst)


def run_one(*, title: str, url: str, category: str, user_brief: str, config: dict, voice: str, out_name: str) -> str:
    _configure_mix()
    os.environ["DEFAULT_TTS_VOICE"] = voice
    os.environ["ENDCARD_TITLE"] = title
    os.environ["ENDCARD_URL"] = url
    os.environ["ENDCARD_SUBTITLE"] = config.get("endcard_subtitle") or ""

    generator = AdGenerator()
    state = generator.plan(user_brief, config_overrides=config)
    project_id = str(state.get("id") or "")
    if not project_id:
        raise RuntimeError("Plan returned no project id")

    # Exact Studio workflow steps.
    generator.generate_images_only(project_id)
    generator.generate_videos_only(project_id)
    generator.assemble_final(project_id)

    final_path = str(generator.state.final_video_path or "")
    if not final_path or not os.path.exists(final_path):
        raise RuntimeError(f"Final render missing: {final_path}")

    # Keep a named copy in output/ for convenience.
    out_dir = Path("output") / "longform"
    named_path = _copy_final(final_path, out_dir / out_name)

    publish_render(
        final_video_path=named_path,
        project_id=project_id,
        title=title,
        url=url,
        category=category,
        plan_filename=f"plan_{project_id}.json",
        trim=False,
    )

    return project_id


def main() -> None:
    os.environ.setdefault("SHOWROOM_TRIM_ENABLE", "0")

    # 1) 60s gritty doc spot (very different look/feel).
    gym_title = "IronPeak Fitness"
    gym_url = "ironpeakfitness.com"
    gym_category = "Gym / Personal Training"
    gym_brief = (
        "Create a 60-second commercial for IronPeak Fitness. Make it feel like a real documentary-style mini story: "
        "a member starts exhausted, finds coaching, builds momentum, and ends confident. "
        "Use varied shots (wide, handheld close-ups, macro sweat/chalk, overhead, tracking). "
        "No on-screen readable text, no logos. Keep it grounded and human."
    )
    gym_config = {
        "topic": gym_title,
        "url": "",
        "style": ["Analog Film", "Cinematic"],
        "duration": "60s",
        "platform": ["YouTube TV"],
        "mood": ["Dramatic", "Aspirational"],
        "transition": "crossfade",
        "camera_style": ["Handheld", "Crane"],
        "lighting_preference": "auto",
        "color_grade": "bleach_bypass",
        "commercial_style": "emotional_journey",
        "endcard_subtitle": "Train with purpose. Leave stronger.",
    }

    # 2) 30s clean-tech reveal spot.
    bot_title = "BotSpot"
    bot_url = "https://botspot.trade"
    bot_category = "Trading Automation"
    bot_brief = (
        "Create a 30-second commercial for BotSpot. Story: a trader stuck in late-night chart chaos -> clean setup -> "
        "confident morning routine. Make it modern, premium, and specific. "
        "Use distinct camera angles and product metaphors without showing readable UI text. No logos."
    )
    bot_config = {
        "topic": bot_title,
        "url": bot_url,
        "style": ["Cinematic"],
        "duration": "30s",
        "platform": ["Netflix"],
        "mood": ["Premium", "Bold"],
        "transition": "crossfade",
        "camera_style": ["Steadicam", "Gimbal"],
        "lighting_preference": "studio",
        "color_grade": "kodak_5219",
        "commercial_style": "tech_reveal",
        "endcard_subtitle": "Less grind. More control.",
    }

    t0 = time.time()
    print("[LONGFORM] Generating 60s gym spot...")
    pid_gym = run_one(
        title=gym_title,
        url=gym_url,
        category=gym_category,
        user_brief=gym_brief,
        config=gym_config,
        voice="openai:verse",
        out_name="ironpeak_fitness_60s.mp4",
    )
    print(f"[LONGFORM] 60s complete: {pid_gym}")

    print("[LONGFORM] Generating 30s BotSpot spot...")
    pid_bot = run_one(
        title=bot_title,
        url=bot_url,
        category=bot_category,
        user_brief=bot_brief,
        config=bot_config,
        voice="openai:alloy",
        out_name="botspot_30s.mp4",
    )
    print(f"[LONGFORM] 30s complete: {pid_bot}")

    print(json.dumps({"gym_project_id": pid_gym, "botspot_project_id": pid_bot, "seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()

