"""Fill the `dtc-event` Figma templates (node 3613:146) from a title, label and speaker names.

The Figma frames fix the number of title/name lines, so the caller breaks text into lines.
This module does it with the template's own Ubuntu Bold metrics: it never changes the
design, only fills its slots, and it fails instead of overflowing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEMPLATE_DIR = Path(__file__).parent / "templates" / "dtc-event"
MIN_SCALE = 0.55
SCALE_STEP = 0.96
WIDTH_SLACK = 1.04  # a line may be 4% wider than the widest line Figma drew
HUG_LIMIT = 1.6  # a hugging name pill may grow to 1.6x the Figma pill


class CoverFitError(ValueError):
    pass


def load_manifest() -> list[dict[str, Any]]:
    return json.loads((TEMPLATE_DIR / "manifest.json").read_text())


def load_advances() -> dict[str, float]:
    return json.loads((TEMPLATE_DIR / "font-metrics.json").read_text())["advance"]


def text_width(text: str, size: float, advances: dict[str, float]) -> float:
    return sum(advances.get(ch, 0.6) for ch in text) * size


def _greedy(words: list[str], size: float, limit: float, advances: dict[str, float]) -> list[str]:
    out: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and text_width(candidate, size, advances) > limit:
            out.append(line)
            line = word
        else:
            line = candidate
    out.append(line)
    return out


def wrap_title(title: str, lines: int, size: float, max_width: float, advances: dict[str, float]) -> tuple[list[str], float]:
    """Word wrap into at most `lines` lines, shrinking the font (to 55%) only when needed.

    Uses as few lines as fit, then balances them (narrowest limit that keeps that line count)
    so a title never ends with a one-word orphan line.
    """
    words = title.split()
    scale = 1.0
    while scale >= MIN_SCALE - 1e-9:
        current = size * scale
        out = _greedy(words, current, max_width, advances)
        if len(out) <= lines and all(text_width(l, current, advances) <= max_width for l in out):
            low, high = max(text_width(w, current, advances) for w in words), max_width
            for _ in range(30):
                mid = (low + high) / 2
                if len(_greedy(words, current, mid, advances)) <= len(out):
                    high = mid
                else:
                    low = mid
            out = _greedy(words, current, high, advances)
            return out + [""] * (lines - len(out)), round(current, 2)
        scale *= SCALE_STEP
    raise CoverFitError(f"Title does not fit {lines} lines of the template at >= {int(MIN_SCALE * 100)}% size: {title!r}")


def split_name(name: str, lines: int, size: float, advances: dict[str, float]) -> list[str]:
    words = name.split()
    if lines == 1 or len(words) == 1:
        return [" ".join(words)] + [""] * (lines - 1)
    best = min(range(1, len(words)), key=lambda i: max(text_width(" ".join(words[:i]), size, advances), text_width(" ".join(words[i:]), size, advances)))
    return [" ".join(words[:best]), " ".join(words[best:])]


def fit_cover(entry: dict[str, Any], title: str, names: list[str], label: str | None = None) -> dict[str, str]:
    """Slot data for `dtc-event/<entry['template']>`. `label` overrides the frame's own label text."""
    advances = load_advances()
    if len(names) != entry["speakerCount"]:
        raise CoverFitError(f"{entry['template']} has {entry['speakerCount']} speaker slot(s), got {len(names)}")
    data: dict[str, str] = {}
    spec = entry["title"]
    max_width = round(spec["widestExampleLine"] * WIDTH_SLACK)
    lines, size = wrap_title(title, len(spec["keys"]), spec["fontSize"], max_width, advances)
    data.update(zip(spec["keys"], lines))
    data["title_font_size"] = f"{size:g}"  # only differs from the Figma size when the title is long
    label_text = label or entry["label"]["default"]
    pill = entry["label"]["pill"]
    wanted = text_width(label_text, entry["label"]["fontSize"], advances) + 2 * pill["textPad"]
    data[entry["label"]["key"]] = label_text
    data["label_pill_width"] = f"{max(pill['pillWidth'], round(wanted, 2)) if wanted > pill['pillWidth'] + 3 else pill['pillWidth']}"
    for n, (speaker, name) in enumerate(zip(entry["speakers"], names), 1):
        parts = split_name(name, len(speaker["nameKeys"]), speaker["fontSize"], advances)
        data.update(zip(speaker["nameKeys"], parts))
        pill = speaker["pill"]
        widest = max(text_width(p, speaker["fontSize"], advances) for p in parts)
        if pill["hug"]:
            width = round(widest + 2 * pill["textPad"], 2)
            if width > pill["pillWidth"] * HUG_LIMIT:
                raise CoverFitError(f"Speaker name too long for the name pill: {name!r}")
            data[f"speaker{n}_pill_width"] = str(width)
            data[f"speaker{n}_pill_x"] = str(round(pill["centerX"] - width / 2, 2))
        elif widest > pill["pillWidth"] * 0.92:
            raise CoverFitError(f"Speaker name too long for the name pill: {name!r}")
    return data
