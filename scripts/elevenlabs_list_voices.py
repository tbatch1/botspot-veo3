#!/usr/bin/env python3
"""
List ElevenLabs voices available to the configured API key.

Usage:
  python scripts/elevenlabs_list_voices.py
"""

from __future__ import annotations

import json
import sys
import urllib.request

from ott_ad_builder.config import config


def main() -> int:
    api_key = (config.ELEVENLABS_API_KEY or "").strip()
    if not api_key:
        print("ELEVENLABS_API_KEY missing in .env")
        return 1

    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))

    voices = data.get("voices") if isinstance(data, dict) else None
    if not isinstance(voices, list):
        print("Unexpected response from ElevenLabs voices endpoint.")
        return 2

    print(f"Voices ({len(voices)}):")
    for v in voices:
        if not isinstance(v, dict):
            continue
        voice_id = str(v.get("voice_id") or "").strip()
        name = str(v.get("name") or "").strip()
        category = str(v.get("category") or "").strip()
        labels = v.get("labels")
        labels_txt = ""
        if isinstance(labels, dict) and labels:
            # Keep it compact and stable.
            keys = sorted(k for k in labels.keys() if isinstance(k, str))
            labels_txt = " | labels: " + ", ".join(f"{k}={labels.get(k)}" for k in keys[:6])
        print(f"- {voice_id} | {name} | {category}{labels_txt}")

    print("")
    print("Tip: set speaker mapping for this project via:")
    print('  ELEVENLABS_VOICE_MAP="Maya=<voice_id>,Ethan=<voice_id>,Narrator=<voice_id>"')
    return 0


if __name__ == "__main__":
    sys.exit(main())

