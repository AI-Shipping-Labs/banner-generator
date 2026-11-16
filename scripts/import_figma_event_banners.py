"""Import the DTC "Templates -> Event Banners" Figma section (node 3613:146).

Input is the private kit exported from Figma (dataops-knowledge/banner-generator, whose
`sources/event-banners.svg` is the Figma export). Each frame's HTML/SVG is kept as exported
(same vector shapes, colours, coordinates, font sizes, baselines). Only the data slots are
re-keyed by role so one source can be filled by the CLI and by DataOps:

* guest portraits, names and sponsor logos are NOT copied (this repo is public). Each
  portrait slot keeps its circle and becomes `${speakerN_portrait}` (centre-cropped to the
  same circle); sponsor/project logos become `${sponsor_logo}`;
* text lines get role keys: `label`, `title_line_N`, `speakerN_name_line_N`;
* text lines that Figma centred get `text-anchor="middle"` at the centre measured from the
  Figma example text (Ubuntu Bold metrics); left-aligned lines stay left-aligned.

Usage:
    uv run python scripts/import_figma_event_banners.py PATH/TO/dataops-knowledge/banner-generator
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import ImageFont

OUT = Path(__file__).resolve().parents[1] / "banner_generator" / "templates" / "dtc-event"
NS = "http://www.w3.org/2000/svg"
XL = "http://www.w3.org/1999/xlink"
ET.register_namespace("", NS)
ET.register_namespace("xlink", XL)
Q = f"{{{NS}}}"
HREF = f"{{{XL}}}href"
LABELS = {"podcast", "webinar", "workshop", "open source spotlight"}
SLOT = re.compile(r"\$\{(\w+)\}")

# Frame -> (event type, layout, sponsored). `webinar-2-speakers-2` and `youtube-workshop-sponsored`
# are labelled WORKSHOP in the Figma source even though their frame names say webinar.
CATALOG = {
    "podcast-1-speaker-luma": ("podcast", "square"),
    "youtube-podcast": ("podcast", "landscape"),
    "podcast-2-speakers": ("podcast", "square"),
    "youtube-podcast-2": ("podcast", "landscape"),
    "webinar-1-speaker": ("webinar", "square"),
    "youtube-webinar": ("webinar", "landscape"),
    "webinar-2-speakers": ("webinar", "square"),
    "youtube-webinar-2": ("webinar", "landscape"),
    "webinar-2-speakers-2": ("workshop", "square"),
    "workshop-1-speaker": ("workshop", "square"),
    "youtube-workshop": ("workshop", "landscape"),
    "workshop-1-speaker-sponsored": ("workshop", "square"),
    "youtube-wokshop-sponsored": ("workshop", "landscape"),
    "youtube-workshop-sponsored": ("workshop", "landscape"),
    "youtube-oss": ("oss", "landscape"),
    "youtube-oss-2": ("oss", "landscape"),
}


def bold_font() -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(OUT / "assets" / "Ubuntu.ttf"), 1000)
    f.set_variation_by_name("Bold")
    return f


def main(kit: Path) -> None:
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for src, dst in [("Ubuntu.ttf", "Ubuntu.ttf"), ("ubuntu.css", "ubuntu.css"), ("Ubuntu-LICENSE.txt", "Ubuntu-LICENSE.txt"),
                     ("83362816935588881575.png", "texture.png"), ("b693c4a9b0a11e51776f.png", "icon-workshop.png")]:
        shutil.copy(kit / "assets" / src, OUT / "assets" / dst)
    font = bold_font()
    adv = {chr(c): round(font.getlength(chr(c)) / 1000, 4) for c in range(32, 127)}
    adv.update({c: round(font.getlength(c) / 1000, 4) for c in "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝßàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿĀāĆćČčĐđĒēĘęĚěĞğİıŁłŃńŌōŒœŘřŚśŞşŠšŪūŹźŻżŽž–—‘’“”…·•"})
    (OUT / "font-metrics.json").write_text(json.dumps({"font": "Ubuntu Bold", "advance": adv}, ensure_ascii=False, indent=0))

    def text_width(text: str, size: float) -> float:
        return font.getlength(text) * size / 1000

    kit_manifest = {m["template"]: m for m in json.loads((kit / "manifest.json").read_text())}
    out_manifest = []
    for name in sorted(CATALOG):
        meta = kit_manifest[name]
        html = (kit / "templates" / name / "template.html").read_text()
        example = json.loads((kit / "templates" / name / "example.json").read_text())["data"]
        root = ET.fromstring(re.search(r"<svg.*</svg>", html, re.S).group(0))
        defs = root.find(Q + "defs")
        byid = {e.get("id"): e for e in defs.iter() if e.get("id")}
        order = {id(e): i for i, e in enumerate(root.iter())}

        # Portrait slots: every #Photo group fills an ellipse with a pattern; give each slot its own image.
        photos = sorted((g for g in root.iter(Q + "g") if (g.get("id") or "").startswith("#Photo")), key=lambda g: order[id(g)])
        portraits = []
        for n, g in enumerate(photos, 1):
            rect = next(r for r in g.iter(Q + "rect") if "url(#pattern" in (r.get("fill") or ""))
            pat = byid[re.search(r"url\(#([^)]+)\)", rect.get("fill")).group(1)]
            for child in list(pat):
                pat.remove(child)
            pat.set("patternContentUnits", "objectBoundingBox")
            ET.SubElement(pat, Q + "image", {"width": "1", "height": "1", "preserveAspectRatio": "xMidYMid slice", HREF: "${speaker%d_portrait}" % n})
            portraits.append(f"speaker{n}_portrait")

        # Source images: keep shared design art (texture, workshop icon), slot out logos, drop leftovers.
        logo_slot = False
        for image in list(defs.iter(Q + "image")):
            href = image.get(HREF, "")
            data_name = image.get("data-name", "")
            if not href.startswith("${image_"):
                continue
            size = (image.get("width"), image.get("height"))
            if data_name == "texture.png":
                image.set(HREF, "../assets/texture.png")
            elif size == ("512", "512"):
                image.set(HREF, "../assets/icon-workshop.png")
            elif data_name.lower().endswith(".png") and (size[0] in ("2400", "800", "827")):
                image.set(HREF, "${sponsor_logo}")
                logo_slot = True
            else:
                defs.remove(image)  # a guest portrait image: replaced by the slot pattern above
        # Re-point any <use> that still referenced a removed portrait image (none remain after pattern rewrite).

        # Text roles.
        label = title = None
        names = []
        for t in root.iter(Q + "text"):
            tid = (t.get("id") or "").strip()
            if re.match(r"Names", tid):
                names.append(t)
            elif t.get("font-size") == "80" and len(list(t)) == 1 and re.sub(r"[_\d]+$", "", tid).lower() in LABELS:
                label = t
            else:
                title = t

        def retarget(t: ET.Element, prefix: str, centre: bool) -> dict:
            spans = list(t)
            size = float(t.get("font-size"))
            lines = [example[SLOT.search(s.text).group(1)] for s in spans]
            widths = [text_width(line.rstrip(), size) for line in lines]
            xs = [float(s.get("x")) for s in spans]
            centred = centre and len({round(x, 1) for x in xs}) > 1
            if centre and len(spans) == 1:
                centred = True
            keys = []
            centre_x = sum(x + w / 2 for x, w in zip(xs, widths)) / len(spans)
            for j, s in enumerate(spans, 1):
                key = f"{prefix}_line_{j}" if len(spans) > 1 else prefix
                s.text = "${%s}" % key
                keys.append(key)
                if centred:
                    s.set("x", f"{centre_x:.2f}")
                    s.set("text-anchor", "middle")
            return {"keys": keys, "fontSize": size, "align": "center" if centred else "left", "defaultText": lines[0].rstrip(),
                    "widestExampleLine": round(max(widths))}

        label_info = retarget(label, "label", False)
        title_info = retarget(title, "title", True)
        speakers = []
        for n, t in enumerate(names, 1):
            info = retarget(t, f"speaker{n}_name", True)
            info["portrait"] = portraits[n - 1] if n - 1 < len(portraits) else None
            speakers.append(info)
        label_default = label_info["defaultText"]

        # Figma's (non-bold style) `font-weight="bold"` is kept. Write the template.
        dst = OUT / name
        dst.mkdir(parents=True, exist_ok=True)
        svg = ET.tostring(root, encoding="unicode")
        (dst / "template.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../assets/ubuntu.css">'
            "<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg{display:block}</style></head><body>"
            + svg + "</body></html>", encoding="utf-8")
        event_type, layout = CATALOG[name]
        out_manifest.append({
            "template": name, "sourceFrame": meta["sourceFrame"], "figmaNode": "3613:146", "eventType": event_type, "layout": layout,
            "width": meta["width"], "height": meta["height"], "speakerCount": len(speakers), "sponsorLogo": logo_slot,
            "label": {"key": label_info["keys"][0], "default": label_default, "fontSize": label_info["fontSize"]},
            "title": {k: title_info[k] for k in ("keys", "fontSize", "align", "widestExampleLine")},
            "speakers": [{"nameKeys": s["keys"], "fontSize": s["fontSize"], "portrait": s["portrait"]} for s in speakers],
        })
    (OUT / "manifest.json").write_text(json.dumps(out_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Imported {len(out_manifest)} Figma frames into {OUT}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
