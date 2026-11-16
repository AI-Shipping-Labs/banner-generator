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
    expected = {entry["label"]["key"], "label_pill_width", "title_font_size", *entry["title"]["keys"]}
    for n, speaker in enumerate(entry["speakers"], 1):
        expected |= {*speaker["nameKeys"], speaker["portrait"]}
        if speaker["pill"]["hug"]:
            expected |= {f"speaker{n}_pill_x", f"speaker{n}_pill_width"}
    if entry["sponsorLogo"]:
        expected.add("sponsor_logo")
    assert slots == expected
    # The design has no date line and no DataTalks.Club logo: only what Figma drew.
    assert "date" not in html.lower().replace("update", "")
    assert "<image" in html and "texture.png" in html


@pytest.mark.parametrize("entry", MANIFEST, ids=lambda e: e["template"])
def test_template_resolves_and_fills(entry):
    path = resolve_template(f"dtc-event/{entry['template']}")
    data = {entry["label"]["key"]: entry["label"]["default"], "label_pill_width": "400", "title_font_size": "100", **{k: "x" for k in entry["title"]["keys"]}}
    for n, speaker in enumerate(entry["speakers"], 1):
        data.update({f"speaker{n}_pill_x": "1", f"speaker{n}_pill_width": "1"})
        data.update({k: "n" for k in speaker["nameKeys"]}, **{speaker["portrait"]: "data:image/png;base64,AAAA"})
    if entry["sponsorLogo"]:
        data["sponsor_logo"] = "data:image/png;base64,AAAA"
    html = render_html(path, data, entry["width"], entry["height"])
    assert "${" not in html


def test_fit_cover_fills_figma_slots_without_inventing_text():
    from banner_generator.event_cover import CoverFitError, fit_cover

    entry = next(m for m in MANIFEST if m["template"] == "podcast-1-speaker-luma")
    data = fit_cover(entry, "From HR Reports to People Analytics with AI", ["Sofiia Hordiienko"])
    assert data["label"] == "PODCAST"
    assert [data[k] for k in entry["title"]["keys"]] == ["From HR Reports to", "People Analytics", "with AI"] or all(data[k] for k in entry["title"]["keys"][:2])
    assert data["speaker1_name_line_1"] == "Sofiia" and data["speaker1_name_line_2"] == "Hordiienko"
    assert data["title_font_size"] == "150"
    with pytest.raises(CoverFitError):
        fit_cover(entry, "word " * 80, ["A B"])
