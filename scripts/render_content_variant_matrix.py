from __future__ import annotations

import html
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from banner_generator.renderer import RenderSpec, load_spec, render, slugify

CONTENT_SPECS = [
    Path("examples/content-event.json"),
    Path("examples/content-workshop.json"),
    Path("examples/content-blog.json"),
    Path("examples/content-course.json"),
    Path("examples/content-project.json"),
    Path("examples/content-resource.json"),
]

VARIANTS = [
    ("asl-editorial-pulse", "Editorial Pulse"),
    ("asl-blueprint-path", "Blueprint Path"),
    ("asl-event-stage", "Event Stage"),
    ("asl-project-dossier", "Project Dossier"),
    ("asl-resource-stack", "Resource Stack"),
]


def variant_data(data: dict[str, object]) -> dict[str, object]:
    kind = str(data.get("kind") or "Content")
    meta_primary = str(data.get("meta_primary") or "AI Shipping Labs")
    meta_secondary = str(data.get("meta_secondary") or "Build / Ship / Learn")
    return {
        **data,
        "tag_one": kind,
        "tag_two": meta_primary,
        "tag_three": "AI Shipping Labs",
        "step_one": "Context",
        "step_two": "Build",
        "step_three": "Ship",
        "stat_label": meta_primary,
        "stat_value": meta_secondary.split("/")[0].strip() or kind,
    }


def render_matrix() -> dict[str, list[tuple[str, Path]]]:
    outputs: dict[str, list[tuple[str, Path]]] = {}
    for spec_path in CONTENT_SPECS:
        spec = load_spec(spec_path)
        title = str((spec.data or {}).get("title") or spec_path.stem)
        content_slug = slugify(title)
        outputs[content_slug] = []

        for template_name, label in VARIANTS:
            output = Path("output/content-matrix") / content_slug / f"{template_name}.png"
            render(
                RenderSpec(
                    template=template_name,
                    output=output,
                    size=spec.size,
                    format="png",
                    data=variant_data(spec.data or {}),
                    width=spec.width,
                    height=spec.height,
                )
            )
            print(output)
            outputs[content_slug].append((label, output))

    return outputs


def contact_sheet_html(title: str, items: list[tuple[str, Path]], columns: int) -> str:
    cards = "\n".join(
        f"""
        <figure>
          <img src="{path.resolve().as_uri()}" alt="">
          <figcaption>{html.escape(label)}</figcaption>
        </figure>
        """
        for label, path in items
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 32px;
      background: #f3f4f6;
      color: #111827;
      font-family: Inter, Arial, sans-serif;
    }}
    h1 {{
      margin: 0 0 24px;
      font-size: 28px;
      line-height: 1.2;
      font-weight: 800;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat({columns}, 360px);
      gap: 18px;
      align-items: start;
    }}
    figure {{
      margin: 0;
      background: #ffffff;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      overflow: hidden;
    }}
    img {{
      display: block;
      width: 360px;
      height: 189px;
      object-fit: cover;
    }}
    figcaption {{
      padding: 10px 12px;
      font-size: 13px;
      font-weight: 700;
      color: #374151;
    }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <section class="grid">{cards}</section>
</body>
</html>
"""


def write_contact_sheet(html_text: str, output: Path, width: int, height: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp_file:
        tmp_file.write(html_text)
        tmp_path = Path(tmp_file.name)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(tmp_path.resolve().as_uri(), wait_until="networkidle")
            page.screenshot(path=str(output), full_page=True)
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)
    print(output)


def render_contact_sheets(outputs: dict[str, list[tuple[str, Path]]]) -> None:
    all_items: list[tuple[str, Path]] = []
    for slug, items in outputs.items():
        write_contact_sheet(
            contact_sheet_html(slug.replace("-", " ").title(), items, columns=5),
            Path("output/contact-sheets/content-matrix") / f"{slug}.png",
            width=1920,
            height=360,
        )
        all_items.extend((f"{slug} / {label}", path) for label, path in items)

    write_contact_sheet(
        contact_sheet_html("AI Shipping Labs Content Variant Matrix", all_items, columns=5),
        Path("output/contact-sheets/content-matrix/all.png"),
        width=1920,
        height=1600,
    )


def main() -> None:
    render_contact_sheets(render_matrix())


if __name__ == "__main__":
    main()
