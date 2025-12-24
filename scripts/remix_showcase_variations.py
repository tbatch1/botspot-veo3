#!/usr/bin/env python3
"""
Remix an existing showcase pack to add variety (different narrator voices + endcard styles),
without regenerating video (no new Veo calls).

Usage (Windows PowerShell):
  cd botspot-veo3
  $env:PYTHONPATH="."
  .\\.venv\\Scripts\\python.exe scripts\\remix_showcase_variations.py --pack output\\showcase_pack
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from elevenlabs.client import ElevenLabs

from ott_ad_builder.config import config
from ott_ad_builder.pipeline import AdGenerator
from ott_ad_builder.state import ProjectState, ScriptLine


@dataclass(frozen=True)
class VoiceProfile:
    key: str
    accent: str | None
    gender: str | None
    search: str | None
    label: str


def _safe_name(value: str) -> str:
    s = re.sub(r"\s+", " ", (value or "").strip())
    s = re.sub(r"[^a-zA-Z0-9 _\\-\\+&]", "", s)
    return s[:40].strip() or "Voice"

def _run_powershell(script: str) -> str:
    return subprocess.check_output(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _sapi_list_voices() -> list[dict]:
    script = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $s.GetInstalledVoices() | ForEach-Object {
  [PSCustomObject]@{
    Name = $_.VoiceInfo.Name
    Gender = $_.VoiceInfo.Gender.ToString()
    Culture = $_.VoiceInfo.Culture.Name
  }
}
$voices | ConvertTo-Json
"""
    raw = _run_powershell(script).strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [v for v in parsed if isinstance(v, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except Exception:
        return []
    return []


def _sapi_speak_to_wav(*, text: str, voice_name: str, out_path: Path, rate: int = 2) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Use a single-quoted here-string to avoid escaping the content.
    ps = rf"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('{voice_name}')
$synth.Rate = {int(rate)}
$synth.Volume = 100
$synth.SetOutputToWaveFile('{str(out_path)}')
$synth.Speak(@'
{text}
'@)
$synth.Dispose()
"""
    _run_powershell(ps)


def _pick_and_add_voice(
    *,
    client: ElevenLabs,
    profile: VoiceProfile,
) -> str:
    def score(v: dict) -> tuple[int, int, int, int]:
        cat = str(v.get("category") or "")
        has_preview = bool(v.get("preview_url"))
        free_ok = bool(v.get("free_users_allowed", True))
        featured_flag = bool(v.get("featured"))
        cat_score = 3 if cat == "high_quality" else (2 if cat == "professional" else 1)
        return (1 if free_ok else 0, 1 if has_preview else 0, 1 if featured_flag else 0, cat_score)

    attempts = [
        dict(accent=profile.accent, gender=profile.gender, search=profile.search, featured=True),
        dict(accent=profile.accent, gender=profile.gender, search=profile.search, featured=False),
        dict(accent=None, gender=profile.gender, search=profile.search, featured=True),
        dict(accent=None, gender=profile.gender, search=profile.search, featured=False),
        dict(accent=None, gender=None, search=profile.search, featured=True),
        dict(accent=None, gender=None, search=profile.search, featured=False),
    ]

    for params in attempts:
        resp = client.voices.get_shared(
            page_size=64,
            accent=params["accent"],
            gender=params["gender"],
            search=params["search"],
            featured=params["featured"],
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

        new_name = _safe_name(f"{profile.label} - {name}")
        added = client.voices.share(public_user_id=public_owner_id, voice_id=voice_id, new_name=new_name)
        return getattr(added, "voice_id", None) or voice_id

    raise RuntimeError(f"No voice found for profile={profile.key}")


def _trim_15s(*, input_path: Path, output_path: Path) -> None:
    subprocess.check_call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
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
            str(output_path),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", default="output/showcase_pack", help="Path to existing pack folder.")
    parser.add_argument("--variant", default="v2", help="Variant suffix used in output filenames.")
    parser.add_argument("--tts", default="edge", choices=["edge", "sapi", "elevenlabs"], help="Voice generator to use.")
    args = parser.parse_args()

    if args.tts == "elevenlabs" and not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY missing; set it in botspot-veo3/.env (or env var).")

    pack_dir = Path(args.pack).resolve()
    manifest_path = pack_dir / "showcase_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest.get("items") or []
    if not items:
        raise RuntimeError("No items found in manifest.")

    # Loudness/mix defaults (VO-forward).
    os.environ["LOUDNORM_I"] = os.getenv("LOUDNORM_I", "-16")
    os.environ["LOUDNORM_TP"] = os.getenv("LOUDNORM_TP", "-1.5")
    os.environ["LOUDNORM_LRA"] = os.getenv("LOUDNORM_LRA", "8")
    os.environ["BGM_DUCKING"] = os.getenv("BGM_DUCKING", "1")
    os.environ["BGM_VOLUME"] = os.getenv("BGM_VOLUME", "0.08")
    os.environ["VO_VOLUME"] = os.getenv("VO_VOLUME", "1.40")
    os.environ["SFX_VOLUME"] = os.getenv("SFX_VOLUME", "0.70")

    voices: dict[str, str] = {}
    if args.tts == "elevenlabs":
        voice_profiles: list[VoiceProfile] = [
            VoiceProfile(key="warm_female_us", accent="american", gender="female", search="warm", label="Warm US Female"),
            VoiceProfile(key="confident_male_us", accent="american", gender="male", search="corporate", label="Confident US Male"),
            VoiceProfile(key="bright_female_uk", accent="british", gender="female", search="commercial", label="Bright UK Female"),
            VoiceProfile(key="calm_male", accent=None, gender="male", search="narration", label="Calm Male"),
        ]

        client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        for p in voice_profiles:
            try:
                voices[p.key] = _pick_and_add_voice(client=client, profile=p)
            except Exception:
                continue
    elif args.tts == "sapi":
        installed = _sapi_list_voices()
        if not installed:
            raise RuntimeError("No Windows SAPI voices found (System.Speech).")

        def pick_sapi(*, gender: str | None) -> str:
            g = (gender or "").strip().lower()
            # Prefer en-US if present.
            candidates = []
            for v in installed:
                vg = str(v.get("Gender") or "").strip().lower()
                if g and vg and g != vg:
                    continue
                candidates.append(v)
            if not candidates:
                candidates = installed

            us = [v for v in candidates if str(v.get("Culture") or "").lower().startswith("en-us")]
            pool = us or candidates
            return str(pool[0].get("Name") or "").strip() or str(installed[0].get("Name") or "").strip()

        voices = {
            "warm_female_us": pick_sapi(gender="female"),
            "confident_male_us": pick_sapi(gender="male"),
            "bright_female_uk": pick_sapi(gender="female"),
            "calm_male": pick_sapi(gender="male"),
        }
    else:
        # Edge TTS: huge free catalog. Use a small curated set for stable demos.
        voices = {
            "warm_female_us": "edge:en-US-JennyNeural",
            "confident_male_us": "edge:en-US-GuyNeural",
            "bright_female_uk": "edge:en-GB-SoniaNeural",
            "calm_male": "edge:en-GB-RyanNeural",
        }

    # Endcard styles + accents (varied, demo-safe).
    endcard_presets = [
        {"style": "random", "align": "center", "accent": "random", "alpha": "0.50"},
    ]

    # Simple per-category mapping for voice and endcard.
    def pick_voice_key(category: str) -> str:
        c = (category or "").lower()
        if "gym" in c or "fitness" in c:
            return "confident_male_us"
        if "dental" in c or "clinic" in c:
            return "warm_female_us"
        if "coffee" in c or "bakery" in c:
            return "bright_female_uk"
        if "ai" in c or "software" in c:
            return "calm_male"
        return "warm_female_us"

    def pick_grade(category: str) -> str:
        c = (category or "").lower()
        if "ai" in c or "software" in c:
            return "cool"
        if "coffee" in c or "bakery" in c:
            return "warm"
        if "gym" in c or "fitness" in c:
            return "vibrant"
        if "dental" in c or "clinic" in c:
            return "clean"
        if "detailing" in c or "auto" in c or "car" in c:
            return "crisp"
        return "neutral"

    started = time.time()
    updated_items: list[dict] = []
    errors: list[dict] = []

    for idx, item in enumerate(items, start=1):
        key = str(item.get("key") or "").strip()
        name = str(item.get("name") or "").strip()
        plan_name = str(item.get("plan") or "").strip()
        category = str(item.get("category") or "").strip()
        if not key or not plan_name:
            continue

        try:
            plan_path = Path(config.OUTPUT_DIR) / plan_name
            if not plan_path.exists():
                raise FileNotFoundError(f"Missing plan: {plan_path}")

            preset = endcard_presets[(idx - 1) % len(endcard_presets)]
            os.environ["ENDCARD_ENABLED"] = "1"
            os.environ["ENDCARD_STYLE"] = preset["style"]
            os.environ["ENDCARD_TEXT_ALIGN"] = preset["align"]
            os.environ["ENDCARD_ACCENT"] = preset["accent"]
            os.environ["ENDCARD_BOX_ALPHA"] = preset["alpha"]
            os.environ["ENDCARD_DURATION"] = "2.6"
            os.environ["ENDCARD_TITLE_SIZE"] = "72"
            os.environ["ENDCARD_SUBTITLE_SIZE"] = "34"
            os.environ["ENDCARD_URL_SIZE"] = "28"
            os.environ["ENDCARD_SEED"] = f"{key}:{args.variant}:{time.time()}"
            os.environ["ENDCARD_QR"] = "1"
            os.environ["ENDCARD_QR_URL"] = str(item.get("url") or "").strip() or ""

            os.environ["ENDCARD_TITLE"] = name
            os.environ["ENDCARD_SUBTITLE"] = str(item.get("category") or "").strip()
            os.environ["ENDCARD_URL"] = str(item.get("url") or "").strip()

            # Post-grade to reduce the "all sunset / all orange" look.
            grade = pick_grade(category)
            os.environ["GRADE_PRESET"] = grade

            voice_key = pick_voice_key(category)
            voice_id = voices.get(voice_key) or next(iter(voices.values()))

            state = ProjectState(**json.loads(plan_path.read_text(encoding="utf-8")))

            # Ensure we don't accidentally trigger a paid BGM generation call.
            state.bgm_path = None

            new_lines: list[ScriptLine] = []
            for li, line in enumerate(state.script.lines or [], start=1):
                speaker = (getattr(line, "speaker", "") or "").strip().lower()
                if speaker in ("narrator", "voiceover", "vo"):
                    if args.tts == "elevenlabs" or args.tts == "edge":
                        line.voice_id = voice_id
                        # Let the pipeline regenerate VO if credits exist.
                        line.audio_path = None
                    else:
                        audio_dir = Path(config.ASSETS_DIR) / "audio"
                        wav_out = audio_dir / f"vo_sapi_{state.id}_{args.variant}_{li}.wav"
                        _sapi_speak_to_wav(text=str(line.text or ""), voice_name=voice_id, out_path=wav_out, rate=2)
                        line.audio_path = str(wav_out)
                new_lines.append(line)
            state.script.lines = new_lines

            gen = AdGenerator(project_id=state.id)
            gen.remix_audio_only(
                script=state.script,
                regenerate_all=(args.tts in ("elevenlabs", "edge")),
                include_bgm=False,
                include_sfx=False,
            )

            final_path = Path(gen.state.final_video_path or "")
            if not final_path.exists():
                raise RuntimeError("Missing final render")

            full_out = pack_dir / f"{key}_{state.id}_{args.variant}_full.mp4"
            shutil.copyfile(final_path, full_out)

            trimmed_out = pack_dir / f"{key}_{state.id}_{args.variant}_15s.mp4"
            _trim_15s(input_path=full_out, output_path=trimmed_out)

            updated_items.append(
                {
                    "key": key,
                    "name": name,
                    "url": str(item.get("url") or ""),
                    "category": category,
                    "video": trimmed_out.name,
                    "plan": plan_name,
                    "voice_profile": voice_key,
                    "endcard_style": preset["style"],
                    "endcard_accent": preset["accent"],
                }
            )
            print(f"[{idx}/{len(items)}] OK: {trimmed_out.name}")
        except Exception as e:
            msg = str(e)
            errors.append({"key": key, "name": name, "error": msg})
            print(f"[{idx}/{len(items)}] ERROR: {name}: {msg}")

    new_manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "variant": args.variant,
        "voices": voices,
        "items": updated_items,
        "errors": errors,
        "notes": [
            "Remixed from existing video clips (no new Veo generations).",
            "Varied narrator voice + endcard style/accents per ad.",
        ],
    }

    out_manifest_path = pack_dir / "showcase_manifest.json"
    out_manifest_path.write_text(json.dumps(new_manifest, indent=2), encoding="utf-8")

    elapsed = time.time() - started
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"Updated manifest: {out_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
