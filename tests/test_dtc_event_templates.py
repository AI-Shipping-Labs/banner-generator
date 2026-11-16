import json
import re
from pathlib import Path

import pytest

from banner_generator.renderer import render_html, resolve_template

ROOT = Path(__file__).resolve().parents[1] / "banner_generator" / "templates" / "dtc-event"
MANIFEST = json.loads((ROOT / "manifest.json").read_text())


def test_all_sixteen_figma_frames_are_imported():
    assert len(MANIFEST) == 16
    assert {m["figmaNode"] for m in MANIFEST} == {"3613:146"}
    assert {(m["width"], m["height"]) for m in MANIFEST} == {(2000, 2000), (2400, 1350)}


def test_no_guest_portraits_or_names_are_committed():
    assert sorted(p.name for p in (ROOT / "assets").iterdir()) == sorted(
        ["Ubuntu-LICENSE.txt", "Ubuntu.ttf", "icon-workshop.png", "placeholder-logo.png", "placeholder-portrait.png", "texture.png", "ubuntu.css"]
    )
    text = json.dumps(MANIFEST)
    for banned in ("Bouchard", "Sofiia", "Hordiienko", "Zeljkovic"):
        assert banned not in text


@pytest.mark.parametrize("entry", MANIFEST, ids=lambda e: e["template"])
def test_template_declares_every_slot_and_nothing_else(entry):
    html = (ROOT / entry["template"] / "template.html").read_text()
    slots = set(re.findall(r"\$\{(\w+)\}", html))
    expected = {entry["label"]["key"], *entry["title"]["keys"]}
    for speaker in entry["speakers"]:
        expected |= {*speaker["nameKeys"], speaker["portrait"]}
    if entry["sponsorLogo"]:
        expected.add("sponsor_logo")
    assert slots == expected
    # The design has no date line and no DataTalks.Club logo: only what Figma drew.
    assert "date" not in html.lower().replace("update", "")
    assert "<image" in html and "texture.png" in html


@pytest.mark.parametrize("entry", MANIFEST, ids=lambda e: e["template"])
def test_template_resolves_and_fills(entry):
    path = resolve_template(f"dtc-event/{entry['template']}")
    data = {entry["label"]["key"]: entry["label"]["default"], **{k: "x" for k in entry["title"]["keys"]}}
    for speaker in entry["speakers"]:
        data.update({k: "n" for k in speaker["nameKeys"]}, **{speaker["portrait"]: "data:image/png;base64,AAAA"})
    if entry["sponsorLogo"]:
        data["sponsor_logo"] = "data:image/png;base64,AAAA"
    html = render_html(path, data, entry["width"], entry["height"])
    assert "${" not in html
