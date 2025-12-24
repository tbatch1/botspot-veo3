#!/usr/bin/env python3
"""
Rebuild a showcase manifest from existing generated videos (no generation).

This is helpful if a manifest was overwritten during remix experiments.

Usage:
  cd botspot-veo3
  $env:PYTHONPATH="."
  .\\.venv\\Scripts\\python.exe scripts\\rebuild_showcase_manifest.py --src-pack output\\showcase_pack --dst-pack output\\showcase_pack_v4
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from ott_ad_builder.config import config


@dataclass(frozen=True)
class Business:
    key: str
    name: str
    url: str
    category: str


def _default_businesses() -> list[Business]:
    return [
        Business(
            key="botspot_trade",
            name="BotSpot.trade",
            url="botspot.trade",
            category="AI trading platform (demo-safe)",
        ),
        Business(
            key="bluebonnet_coffee",
            name="Bluebonnet Coffee",
            url="bluebonnetcoffee.example",
            category="coffee shop",
        ),
        Business(
            key="fitforge_gym",
            name="FitForge Gym",
            url="fitforge.example",
            category="gym",
        ),
        Business(
            key="sunrise_dental",
            name="Sunrise Dental",
            url="sunrisedental.example",
            category="dental clinic",
        ),
        Business(
            key="sparkle_detailing",
            name="Sparkle Mobile Detailing",
            url="sparkledetailing.example",
            category="mobile detailing",
        ),
        Business(
            key="gulfcoast_hvac",
            name="Gulf Coast HVAC",
            url="gulfcoasthvac.example",
            category="HVAC service",
        ),
        Business(
            key="hearth_home_bakery",
            name="Hearth & Home Bakery",
            url="hearthhomebakery.example",
            category="bakery",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-pack", default="output/showcase_pack", help="Existing pack folder containing videos.")
    parser.add_argument("--dst-pack", default="output/showcase_pack_v4", help="Destination pack folder for new manifest.")
    parser.add_argument("--copy-videos", action="store_true", help="Copy base videos into dst pack.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    src_pack = (root / args.src_pack).resolve()
    dst_pack = (root / args.dst_pack).resolve()
    dst_pack.mkdir(parents=True, exist_ok=True)

    # Find base videos in src pack (exclude remix variants like *_v4_15s.mp4).
    pat_src = r"^(?P<key>.+)_(?P<id>[0-9a-fA-F-]{36})_15s\.mp4$"
    pat = re.compile(pat_src)
    found: dict[str, dict] = {}
    scanned = 0
    kept = 0
    for f in src_pack.glob("*_15s.mp4"):
        scanned += 1
        if "_v" in f.stem:
            continue
        kept += 1
        m = pat.match(f.name)
        if not m:
            if kept == 1:
                print(f"First base candidate: {f.name}")
                print(f"Pattern: {pat_src}")
            continue
        key = m.group("key")
        pid = m.group("id")
        found[key] = {"video": f.name, "id": pid}
    print(f"Scanned {scanned} *_15s.mp4, kept {kept} base candidates, matched {len(found)} keys from: {src_pack}")

    items = []
    errors = []
    for b in _default_businesses():
        rec = found.get(b.key)
        if not rec:
            errors.append({"key": b.key, "name": b.name, "error": "Missing base video in src pack"})
            continue
        plan_name = f"plan_{rec['id']}.json"
        plan_path = Path(config.OUTPUT_DIR) / plan_name
        if not plan_path.exists():
            errors.append({"key": b.key, "name": b.name, "error": f"Missing plan in output/: {plan_name}"})
            continue
        items.append(
            {
                "key": b.key,
                "name": b.name,
                "url": b.url,
                "category": b.category,
                "video": rec["video"],
                "plan": plan_name,
            }
        )
        if args.copy_videos:
            src_video = src_pack / rec["video"]
            dst_video = dst_pack / rec["video"]
            if src_video.exists() and not dst_video.exists():
                dst_video.write_bytes(src_video.read_bytes())

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
        "errors": errors,
        "notes": [
            "Rebuilt manifest from existing base videos in src pack and plans in output/.",
            "Use remix_showcase_variations.py to create a new variant pack with different voices/endcards.",
        ],
    }

    out = dst_pack / "showcase_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote: {out}")
    if errors:
        print(f"Warnings: {len(errors)} items missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
