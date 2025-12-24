#!/usr/bin/env python3
"""
Generate ONE 30s "superhero cinematic" commercial with minimal cost:
- Uses Veo 3.1 text-to-video (no Fal/Flux images, no GPT planning).
- 4 clips total: 6s + 8s + 8s + 8s = 30s.
- Preserves Veo native audio by assembling with straight cuts (USE_CLIP_AUDIO=1).

Usage (PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  $env:SHOWROOM_TRIM_ENABLE="0"
  .\\.venv\\Scripts\\python.exe scripts\\generate_superhero_botspot_30s.py
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from ott_ad_builder.config import config
from ott_ad_builder.providers.video_google import GoogleVideoProvider
from ott_ad_builder.providers.composer import Composer
from ott_ad_builder.showroom import publish_render
from ott_ad_builder.state import ProjectState, Script, Scene


def main() -> None:
    # Keep it to ONE video.
    project_id = str(uuid.uuid4())

    # Enable Veo native audio and preserve it in final assembly.
    os.environ["VEO_GENERATE_AUDIO"] = "1"
    os.environ["USE_CLIP_AUDIO"] = "1"
    os.environ["CLIP_AUDIO_ONLY"] = "1"
    os.environ.setdefault("LOUDNORM_I", "-16")
    os.environ.setdefault("LOUDNORM_TP", "-1.5")
    os.environ.setdefault("LOUDNORM_LRA", "8")

    # Endcard + QR (no mid-video text, to avoid Veo text artifacts).
    os.environ["ENDCARD_ENABLED"] = "1"
    os.environ["ENDCARD_STYLE"] = "auto"
    os.environ["ENDCARD_ACCENT"] = "auto"
    os.environ["ENDCARD_TITLE"] = "BotSpot"
    os.environ["ENDCARD_SUBTITLE"] = "Automate the grind. Keep the control."
    os.environ["ENDCARD_URL"] = "https://botspot.trade"
    os.environ["ENDCARD_QR"] = "1"

    # No showroom trimming for long-form.
    os.environ.setdefault("SHOWROOM_TRIM_ENABLE", "0")

    # Build a 30s spot from 4 clips (6+8+8+8).
    scenes: list[Scene] = [
        Scene(
            id=1,
            duration=6,
            visual_prompt="",
            audio_prompt=None,
            motion_prompt=(
                "Cinematic superhero cold open, photoreal live-action. Night city street, rain-slick asphalt, neon reflections, "
                "a small sedan tipped onto its side after a near-miss. A bystander reaches out. "
                "A masked hero steps into frame, cape whipping. "
                "Camera: handheld wide establishing shot, then quick push-in. "
                "Action: the hero plants their feet, grips the car frame. "
                "Audio: cinematic impacts and whooshes, city ambience, NO dialogue, NO narration, NO lyrics. "
                "No readable text, no logos, no watermarks."
            ),
        ),
        Scene(
            id=2,
            duration=8,
            visual_prompt="",
            audio_prompt=None,
            motion_prompt=(
                "Superhero strength moment, premium blockbuster style. Close-medium 50mm, shallow DOF, practical sparks, rain droplets. "
                "Action: the hero LIFTS the car upright in one clean motion; dust and debris fall; crowd reacts silently. "
                "Camera: smooth gimbal orbit 120 degrees, ending on hero profile. "
                "Audio: heavy lift creak, thud, whoosh, NO dialogue. "
                "No readable text, no logos, no watermarks."
            ),
        ),
        Scene(
            id=3,
            duration=8,
            visual_prompt="",
            audio_prompt=None,
            motion_prompt=(
                "Escalation: a runaway truck skids into frame. Hero launches forward. "
                "Action: hero grabs the truck bumper and redirects it into a safe stop; shockwave ripples puddles; slow-motion spray. "
                "Camera: low-angle tracking shot, then speed-ramp to slow motion, then hard stop. "
                "Audio: tire squeal, impact thump, sub bass hit, NO dialogue. "
                "No readable text, no logos, no watermarks."
            ),
        ),
        Scene(
            id=4,
            duration=8,
            visual_prompt="",
            audio_prompt=None,
            motion_prompt=(
                "Product reveal without cheesy UI text. Dawn breaks. Hero removes glove, taps a phone once. "
                "On the phone: abstract icon-only dashboard shapes, NO readable text. "
                "Action: chaos calms, notifications turn into clean geometric pulses. Hero nods, walks away. "
                "Camera: over-the-shoulder close-up rack focus from phone to hero, then slow dolly back for endcard hold. "
                "Audio: subtle tech pulse, resolve chord, NO dialogue, NO lyrics. "
                "No readable text, no logos, no watermarks."
            ),
        ),
    ]

    veo = GoogleVideoProvider()
    # "Epic" pushes the prompt enhancer toward big, cinematic moves.
    veo.set_aesthetic_style("epic")
    veo.set_seed(int(project_id.split("-")[0], 16) % (2**32))

    for scene in scenes:
        op = veo.submit_async("", scene.motion_prompt, duration=int(scene.duration))
        scene.video_path = veo.poll_task(op, scene.motion_prompt)

    state = ProjectState(
        id=project_id,
        user_input="Superhero Cinematic — BotSpot (30s)",
        script=Script(lines=[], scenes=scenes, mood="epic"),
        strategy={
            "product_name": "BotSpot",
            "brand_card": {
                "brand_name": "BotSpot",
                "category": "Superhero Cinematic (demo)",
                "call_to_action": "Scan to try it.",
                "url": "https://botspot.trade",
            },
            "applied_preferences": {"url": "https://botspot.trade"},
        },
        transition_type="cut",
        veo_generate_audio=True,
    )

    composer = Composer()
    final_path = composer.compose(state, transition_type="cut")

    out_dir = Path(config.OUTPUT_DIR) / "superhero"
    out_dir.mkdir(parents=True, exist_ok=True)
    named = out_dir / "botspot_superhero_30s.mp4"
    Path(final_path).replace(named)

    publish_render(
        final_video_path=str(named),
        project_id=project_id,
        title="BotSpot — Superhero Cinematic (30s)",
        url="https://botspot.trade",
        category="Superhero Cinematic (demo)",
        plan_filename=None,
        trim=False,
    )

    print(f"[DONE] {named}")


if __name__ == "__main__":
    main()

