from __future__ import annotations

import html
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any

DEFAULT_SIZE = "og"
SIZES = {
    "og": (1200, 630),
    "wide": (1600, 900),
    "square": (1080, 1080),
    "linkedin": (1200, 627),
}


@dataclass(frozen=True)
class RenderSpec:
    template: str
    output: Path
    size: str = DEFAULT_SIZE
    format: str | None = None
    quality: int | None = None
    data: dict[str, Any] | None = None
    width: int | None = None
    height: int | None = None

    @property
    def viewport(self) -> tuple[int, int]:
        if self.width and self.height:
            return self.width, self.height
        return SIZES[self.size]


def load_spec(path: Path) -> RenderSpec:
    payload = json.loads(path.read_text())
    data = payload.get("data", {})
    known_keys = {"template", "output", "size", "format", "quality", "width", "height", "data"}
    inline_data = {key: value for key, value in payload.items() if key not in known_keys}
    data = {**data, **inline_data}

    return RenderSpec(
        template=payload["template"],
        output=Path(payload["output"]),
        size=payload.get("size", DEFAULT_SIZE),
        format=payload.get("format"),
        quality=payload.get("quality"),
        data=data,
        width=payload.get("width"),
        height=payload.get("height"),
    )


def render_html(template_path: Path, data: dict[str, Any], width: int, height: int) -> str:
    template = Template(template_path.read_text())
    values = {
        key: html.escape(str(value), quote=True)
        for key, value in data.items()
        if value is not None
    }
    values["width"] = str(width)
    values["height"] = str(height)
    values.setdefault("label", "")
    values.setdefault("title", "")
    values.setdefault("subtitle", "")
    values.setdefault("meta", "")
    values.setdefault("brand", "AI Shipping Labs")
    values.setdefault("accent", "Ship real things with AI")
    values.setdefault("kind", "Content")
    values.setdefault("kicker", "Build, ship, and learn with practical AI projects.")
    values.setdefault("meta_primary", "")
    values.setdefault("meta_secondary", "")
    values.setdefault("footer", "aishippinglabs.com")
    values.setdefault("title_size", "78")
    values.setdefault("subtitle_size", "30")
    values.setdefault("tag_one", "Build")
    values.setdefault("tag_two", "Ship")
    values.setdefault("tag_three", "Learn")
    values.setdefault("step_one", "Learn the pattern")
    values.setdefault("step_two", "Build the workflow")
    values.setdefault("step_three", "Ship the artifact")
    values.setdefault("stat_label", "Format")
    values.setdefault("stat_value", f"{width}x{height}")
    values.setdefault("name", "Jane Doe")
    values.setdefault("course_name", "7-Day AI Agents Crash-Course")
    values.setdefault("dates", "2026")
    values.setdefault("course_url", "https://aishippinglabs.com/courses/aihero")
    values.setdefault("certificate_id", "example")
    values.setdefault("certificate_url", "#")
    values.setdefault("qr", "assets/test-qr.svg")
    html_text = template.safe_substitute(values)
    base_href = f"{template_path.parent.resolve().as_uri()}/"
    return html_text.replace("<head>", f'<head>\n  <base href="{base_href}">', 1)


def resolve_template(name_or_path: str, template_dir: Path | None = None) -> Path:
    raw_path = Path(name_or_path)
    if raw_path.exists():
        return raw_path

    candidates = []
    if template_dir:
        candidates.append(template_dir / name_or_path)
        candidates.append(template_dir / f"{name_or_path}.html")
        candidates.append(template_dir / name_or_path / "template.html")

    bundled_dir = Path(__file__).parent / "templates"
    candidates.append(bundled_dir / name_or_path)
    candidates.append(bundled_dir / f"{name_or_path}.html")
    candidates.append(bundled_dir / name_or_path / "template.html")

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"Template not found: {name_or_path}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "banner"


def output_format(spec: RenderSpec) -> str:
    if spec.format:
        format_name = spec.format.lower()
    else:
        suffix = spec.output.suffix.lower().lstrip(".")
        format_name = "jpeg" if suffix in {"jpg", "jpeg"} else suffix

    if format_name not in {"png", "jpeg", "pdf"}:
        raise ValueError(f"Unsupported output format: {format_name or '(missing)'}")

    return format_name


def render(
    spec: RenderSpec,
    *,
    template_dir: Path | None = None,
    html_output: Path | None = None,
) -> Path:
    from playwright.sync_api import sync_playwright

    width, height = spec.viewport
    template_path = resolve_template(spec.template, template_dir=template_dir)
    html_text = render_html(template_path, spec.data or {}, width, height)

    output = spec.output
    output.parent.mkdir(parents=True, exist_ok=True)

    if html_output:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(html_text)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp_file:
        tmp_file.write(html_text)
        tmp_path = Path(tmp_file.name)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(tmp_path.as_uri())
            format_name = output_format(spec)

            if format_name == "pdf":
                page.pdf(
                    path=str(output),
                    width=f"{width}px",
                    height=f"{height}px",
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
            else:
                screenshot_args: dict[str, Any] = {
                    "path": str(output),
                    "type": format_name,
                    "full_page": False,
                }
                if format_name == "jpeg" and spec.quality:
                    screenshot_args["quality"] = spec.quality
                page.screenshot(**screenshot_args)
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    return output


def render_png(
    spec: RenderSpec,
    *,
    template_dir: Path | None = None,
    html_output: Path | None = None,
) -> Path:
    png_spec = RenderSpec(
        template=spec.template,
        output=spec.output,
        size=spec.size,
        format="png",
        quality=spec.quality,
        data=spec.data,
        width=spec.width,
        height=spec.height,
    )
    return render(png_spec, template_dir=template_dir, html_output=html_output)
