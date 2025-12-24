#!/usr/bin/env python3
"""
Generate a pack of short OTT demo commercials (15s each) and write a showcase manifest.

Design goals:
- Demo-safe: no real logos, no unverifiable claims, no political persuasion.
- Repeatable: stable loudness + VO-forward mix.
- Fast iteration: 3 scenes per ad, narrator-only VO by default.

Usage (Windows PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  .\\.venv\\Scripts\\python.exe scripts\\generate_showcase_pack.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from elevenlabs.client import ElevenLabs

from ott_ad_builder.config import config
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState, Scene, Script, ScriptLine


@dataclass(frozen=True)
class Business:
    key: str
    name: str
    url: str
    category: str
    promise: str
    proof: str
    cta: str
    vibe: str


def _safe_name(value: str) -> str:
    s = re.sub(r"\s+", " ", (value or "").strip())
    s = re.sub(r"[^a-zA-Z0-9 _\-\+&]", "", s)
    return s[:40].strip() or "Voice"


def _pick_and_add_voice(
    *,
    client: ElevenLabs,
    accent: str | None,
    gender: str | None,
    search: str | None,
    label: str,
) -> str:
    """
    Pull a high-quality/pro voice from ElevenLabs Voice Library and add it to the account,
    returning a voice_id we can use for TTS.
    """

    def score(v: dict) -> tuple[int, int, int, int]:
        cat = str(v.get("category") or "")
        has_preview = bool(v.get("preview_url"))
        free_ok = bool(v.get("free_users_allowed", True))
        featured_flag = bool(v.get("featured"))
        cat_score = 3 if cat == "high_quality" else (2 if cat == "professional" else 1)
        return (1 if free_ok else 0, 1 if has_preview else 0, 1 if featured_flag else 0, cat_score)

    for featured in (True, False):
        resp = client.voices.get_shared(
            page_size=64,
            accent=accent or None,
            gender=gender or None,
            search=search or None,
            featured=featured,
        )
        payload = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
        voices = payload.get("voices") or []

        best = None
        best_s = (-1, -1, -1, -1)
        for v in voices:
            if not isinstance(v, dict):
                continue
            s = score(v)
            if s > best_s:
                best_s = s
                best = v
        if not best:
            continue

        public_owner_id = str(best.get("public_owner_id") or "").strip()
        voice_id = str(best.get("voice_id") or "").strip()
        name = str(best.get("name") or "").strip()
        if not public_owner_id or not voice_id:
            continue

        new_name = _safe_name(f"{label} - {name}")
        added = client.voices.share(public_user_id=public_owner_id, voice_id=voice_id, new_name=new_name)
        return getattr(added, "voice_id", None) or voice_id

    raise RuntimeError(f"No suitable narrator voice found (accent={accent}, gender={gender}, search={search})")


def _configure_demo_mix() -> None:
    # Web-friendly loudness so laptop playback sounds "right".
    os.environ["LOUDNORM_I"] = os.getenv("LOUDNORM_I", "-16")
    os.environ["LOUDNORM_TP"] = os.getenv("LOUDNORM_TP", "-1.5")
    os.environ["LOUDNORM_LRA"] = os.getenv("LOUDNORM_LRA", "8")

    # VO-forward mix.
    os.environ["BGM_DUCKING"] = os.getenv("BGM_DUCKING", "1")
    os.environ["BGM_VOLUME"] = os.getenv("BGM_VOLUME", "0.10")
    os.environ["VO_VOLUME"] = os.getenv("VO_VOLUME", "1.35")
    os.environ["SFX_VOLUME"] = os.getenv("SFX_VOLUME", "0.70")


def _configure_endcard(*, title: str, subtitle: str, url: str) -> None:
    os.environ["ENDCARD_ENABLED"] = "1"
    os.environ["ENDCARD_TITLE"] = title
    os.environ["ENDCARD_SUBTITLE"] = subtitle
    os.environ["ENDCARD_URL"] = url
    os.environ["ENDCARD_DURATION"] = "2.6"


def _make_scenes_for_business(b: Business) -> list[Scene]:
    # Text-to-video prompts must avoid logos/text; we add the endcard via drawtext.
    return [
        Scene(
            id=1,
            duration=4,
            visual_prompt=f"Premium cinematic {b.vibe} still: {b.category} vibe, clean modern composition. No logos, no readable text.",
            audio_prompt=None,
            motion_prompt=(
                f"Premium cinematic {b.vibe}. Establish the {b.category} world: clean, modern, human, grounded. "
                "Natural micro-movements, realistic hands, no duplicates. Camera: smooth steadicam close-medium, gentle push-in. "
                "No logos, no readable text, no floating objects."
            ),
        ),
        Scene(
            id=2,
            duration=4,
            visual_prompt=f"Detail craft shot still: hands-in-action, product/service moment for {b.category}. No logos, no readable text.",
            audio_prompt=None,
            motion_prompt=(
                f"Detail craft shot for {b.category}: hands-in-action, tactile realism, premium lighting. "
                "Camera: macro close-up, smooth move then lock. No logos, no readable text, no duplicated props."
            ),
        ),
        Scene(
            id=3,
            duration=8,
            visual_prompt=(
                f"Payoff hero shot still: satisfied customer moment for {b.category}, warm confident tone. "
                "No readable text (endcard added in post)."
            ),
            audio_prompt=None,
            motion_prompt=(
                f"Payoff hero shot for {b.category}: satisfied customer moment, warm confident tone. "
                "Camera: slow dolly back to reveal the scene, then hold steady for endcard moment. "
                "No logos, no readable text, no floating objects."
            ),
        ),
    ]


def _make_lines_for_business(b: Business, *, narrator_voice_id: str) -> list[ScriptLine]:
    # Keep VO inside a hard 15s trim window; last line ends at 14.6s.
    return [
        ScriptLine(
            speaker="Narrator",
            voice_id=narrator_voice_id,
            scene_id=1,
            time_range="0.0-4.6s",
            text=f"{b.name}. {b.promise}",
        ),
        ScriptLine(
            speaker="Narrator",
            voice_id=narrator_voice_id,
            scene_id=2,
            time_range="4.6-9.4s",
            text=b.proof,
        ),
        ScriptLine(
            speaker="Narrator",
            voice_id=narrator_voice_id,
            scene_id=3,
            time_range="9.4-14.6s",
            text=b.cta,
        ),
    ]


def _bgm_prompt_for_business(b: Business) -> str:
    if "software" in b.category.lower() or "ai" in b.category.lower():
        return "Modern tech commercial music: crisp, upbeat, confident, light synths, punchy drums, clean, premium."
    if "coffee" in b.category.lower() or "bakery" in b.category.lower():
        return "Warm indie-pop commercial bed: guitar, light percussion, sunny, friendly, premium."
    if "gym" in b.category.lower() or "fitness" in b.category.lower():
        return "High-energy modern beat: punchy drums, confident bass, upbeat tempo, motivational but clean."
    return "Premium commercial music: modern, upbeat, friendly, light percussion, clean and confident."


def _render_ad(*, business: Business, narrator_voice_id: str, out_dir: Path) -> dict:
    project_id = str(uuid.uuid4())

    _configure_demo_mix()
    _configure_endcard(
        title=business.name,
        subtitle=f"{business.category} • {business.promise}",
        url=business.url,
    )

    scenes = _make_scenes_for_business(business)
    lines = _make_lines_for_business(business, narrator_voice_id=narrator_voice_id)
    script = Script(lines=lines, mood="commercial", scenes=scenes)

    state = ProjectState(
        id=project_id,
        user_input=f"Showcase: {business.name}",
        status="images_complete",
        script=script,
    )

    # The pipeline reads/writes plans from config.OUTPUT_DIR, so always place the plan there.
    plan_dir = Path(config.OUTPUT_DIR)
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"plan_{project_id}.json"
    plan_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    try:
        gen = AdGenerator(project_id=project_id)
        gen.generate_videos_only(project_id=project_id)

        updated = ProjectState(**json.loads(plan_path.read_text("utf-8")))
        updated.script.lines = lines

        assemble = AdGenerator(project_id=project_id)
        assemble.remix_audio_only(
            script=updated.script,
            regenerate_all=True,
            include_bgm=True,
            include_sfx=False,
            bgm_prompt=_bgm_prompt_for_business(business),
        )

        final = assemble.state.final_video_path
        if not final or not os.path.exists(final):
            raise RuntimeError("Final render missing")

        full_path = out_dir / f"{business.key}_{project_id}_full.mp4"
        shutil.copyfile(final, full_path)

        trimmed_path = out_dir / f"{business.key}_{project_id}_15s.mp4"
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(full_path),
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
                str(trimmed_path),
            ]
        )

        return {
            "key": business.key,
            "name": business.name,
            "url": business.url,
            "category": business.category,
            "video": trimmed_path.name,
            "plan": plan_path.name,
        }
    except Exception as e:
        return {"key": business.key, "name": business.name, "error": str(e)}


def _default_businesses() -> list[Business]:
    # Keep these demo-safe (fictional) to avoid brand/logo/trademark issues.
    # BotSpot.trade is included per request.
    return [
        Business(
            key="botspot_trade",
            name="BotSpot.trade",
            url="botspot.trade",
            category="AI trading platform (demo-safe)",
            promise="Build no-code trading agents fast—rules over panic.",
            proof="Create, configure, and deploy automated agents with clear rules and guardrails.",
            cta="BotSpot.trade—build smart agents, stay in control.",
            vibe="tech",
        ),
        Business(
            key="bluebonnet_coffee",
            name="Bluebonnet Coffee",
            url="bluebonnetcoffee.example",
            category="coffee shop",
            promise="Small-batch coffee, big comfort—fast.",
            proof="Handcrafted espresso, smooth cold foam, and seasonal flavors—made fresh.",
            cta="Bluebonnet Coffee—swing by today.",
            vibe="warm lifestyle",
        ),
        Business(
            key="fitforge_gym",
            name="FitForge Gym",
            url="fitforge.example",
            category="gym",
            promise="Stronger in 30 minutes—no chaos.",
            proof="Coach-led sessions, smart programming, and a plan you can stick to.",
            cta="FitForge Gym—book your first session.",
            vibe="energetic",
        ),
        Business(
            key="sunrise_dental",
            name="Sunrise Dental",
            url="sunrisedental.example",
            category="dental clinic",
            promise="Calm care. Clear answers. Confident smiles.",
            proof="Modern imaging, gentle treatment, and transparent next steps.",
            cta="Sunrise Dental—schedule your checkup.",
            vibe="clean premium",
        ),
        Business(
            key="sparkle_detailing",
            name="Sparkle Mobile Detailing",
            url="sparkledetailing.example",
            category="mobile detailing",
            promise="Showroom clean—at your driveway.",
            proof="Foam wash, interior reset, and a finish that actually lasts.",
            cta="Sparkle Mobile Detailing—book a detail.",
            vibe="slick",
        ),
        Business(
            key="gulfcoast_hvac",
            name="Gulf Coast HVAC",
            url="gulfcoasthvac.example",
            category="HVAC service",
            promise="Cool air, fast fixes, no surprises.",
            proof="Same-week appointments, clear diagnostics, and dependable repairs.",
            cta="Gulf Coast HVAC—get comfortable again.",
            vibe="trustworthy",
        ),
        Business(
            key="hearth_home_bakery",
            name="Hearth & Home Bakery",
            url="hearthhomebakery.example",
            category="bakery",
            promise="Fresh-baked joy—warm, buttery, real.",
            proof="Flaky pastries, daily bread, and seasonal treats baked from scratch.",
            cta="Hearth & Home—grab something fresh today.",
            vibe="cozy",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="output", help="Output directory (relative to repo root).")
    parser.add_argument("--accent", default="american", help="Voice library accent filter.")
    parser.add_argument("--gender", default="female", help="Voice library gender filter.")
    parser.add_argument("--voice-search", default="news", help="Voice library search term.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    businesses = _default_businesses()

    if not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY missing; set it in botspot-veo3/.env (or env var).")

    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    narrator_voice_id = _pick_and_add_voice(
        client=client,
        accent=args.accent,
        gender=args.gender,
        search=args.voice_search,
        label="Showcase Narrator",
    )

    started = time.time()
    results: list[dict] = []
    for idx, b in enumerate(businesses, start=1):
        print(f"[{idx}/{len(businesses)}] Generating: {b.name}")
        item = _render_ad(business=b, narrator_voice_id=narrator_voice_id, out_dir=out_dir)
        results.append(item)
        if item.get("error"):
            print(f"  [ERROR] {b.name}: {item['error']}")
        else:
            print(f"  [OK] {item.get('video')}")

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "narrator_voice_id": narrator_voice_id,
        "items": [r for r in results if not r.get("error")],
        "errors": [r for r in results if r.get("error")],
        "notes": [
            "These are demo-safe fictional ads (except BotSpot.trade) generated without real logos.",
            "With budget: higher tiers unlock better voice quality/bitrate, more voice options, more video credits, and higher-res generations.",
        ],
    }

    manifest_path = out_dir / "showcase_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    elapsed = time.time() - started
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
