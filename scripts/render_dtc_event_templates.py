"""Render every DTC event template (Figma node 3613:146) with neutral sample data.

    uv run python scripts/render_dtc_event_templates.py [OUT_DIR] [template ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from banner_generator.event_cover import fit_cover
from banner_generator.renderer import RenderSpec, render

ROOT = Path(__file__).resolve().parents[1] / "banner_generator" / "templates" / "dtc-event"
SAMPLE_TITLE = "Sample event title that fills the lines of the Figma design"


def sample_data(entry: dict, portrait: str, logo: str) -> dict:
    names = [f"Speaker {n}" for n in range(1, entry["speakerCount"] + 1)]
    title = SAMPLE_TITLE if len(entry["title"]["keys"]) > 1 else "Sample"
    data = fit_cover(entry, title, names)
    for speaker in entry["speakers"]:
        data[speaker["portrait"]] = portrait
    if entry["sponsorLogo"]:
        data["sponsor_logo"] = logo
    return data


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "output/dtc-event")
    only = set(sys.argv[2:])
    portrait = (ROOT / "assets" / "placeholder-portrait.png").as_uri()
    logo = (ROOT / "assets" / "placeholder-logo.png").as_uri()
    for entry in json.loads((ROOT / "manifest.json").read_text()):
        if only and entry["template"] not in only:
            continue
        spec = RenderSpec(template=f"dtc-event/{entry['template']}", output=out / f"{entry['template']}.png",
                          width=entry["width"], height=entry["height"], data=sample_data(entry, portrait, logo))
        print(render(spec))


if __name__ == "__main__":
    main()
