from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from banner_generator.renderer import RenderSpec, render, slugify

DEFAULT_TEMPLATE = "asl-event-stage"
MAX_BYTES = 100_000
WORKSHOPS_DIR = Path("/home/alexey/tmp/aisl-workshops-raw")
CONTENT_DIR = Path("/home/alexey/git/ai-shipping-labs-content")
PYTHON_COURSE_DIR = Path("/home/alexey/git/python-course")
OUTPUT_DIR = Path("output/source-banners")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_scalar_yaml(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []

    def flush_block() -> None:
        nonlocal current_key, block_lines
        if current_key:
            values[current_key] = " ".join(line.strip() for line in block_lines if line.strip())
        current_key = None
        block_lines = []

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if current_key and (raw_line.startswith(" ") or raw_line.startswith("\t")):
            block_lines.append(raw_line)
            continue
        flush_block()

        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw_line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if value in {"|", ">"}:
            current_key = key
            block_lines = []
        elif value and not value.startswith("[") and not value.startswith("{"):
            values[key] = value.strip("\"'")

    flush_block()
    return values


def markdown_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = read_text(path)
    if text.startswith("---\n"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parse_scalar_yaml(parts[1]), parts[2]
    return {}, text


def first_paragraph(markdown: str) -> str:
    cleaned = re.sub(r"```.*?```", "", markdown, flags=re.S)
    for paragraph in re.split(r"\n\s*\n", cleaned):
        paragraph = paragraph.strip()
        if not paragraph or paragraph.startswith("#") or paragraph.startswith("!["):
            continue
        paragraph = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", paragraph)
        paragraph = re.sub(r"[*_`>#-]+", "", paragraph)
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if paragraph:
            return paragraph
    return ""


def clamp_text(value: str, max_chars: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def title_size(title: str) -> int:
    length = len(title)
    if length > 82:
        return 50
    if length > 66:
        return 56
    if length > 52:
        return 62
    return 70


def subtitle_size(subtitle: str) -> int:
    return "24" if len(subtitle) > 130 else "27"


def selected_template(default: str) -> str:
    feedback_path = Path(".tmp/review-board/feedback.json")
    if not feedback_path.exists():
        return default
    payload = json.loads(feedback_path.read_text())
    liked = payload.get("liked", [])
    variants = [item.get("variantSlug") for item in liked if item.get("variantSlug")]
    if not variants:
        return default
    return Counter(variants).most_common(1)[0][0]


def base_data(
    *,
    kind: str,
    title: str,
    subtitle: str,
    meta_primary: str,
    meta_secondary: str,
    footer: str,
) -> dict[str, str]:
    subtitle = clamp_text(subtitle, 170)
    return {
        "brand": "AI Shipping Labs",
        "kind": kind,
        "kicker": kind,
        "title": clamp_text(title, 95),
        "subtitle": subtitle,
        "meta_primary": meta_primary,
        "meta_secondary": meta_secondary,
        "footer": footer,
        "tag_one": kind,
        "tag_two": meta_primary,
        "tag_three": "AI Shipping Labs",
        "step_one": "Learn",
        "step_two": "Build",
        "step_three": "Ship",
        "stat_label": meta_primary,
        "stat_value": meta_secondary.split("/")[0].strip() or kind,
        "title_size": str(title_size(title)),
        "subtitle_size": subtitle_size(subtitle),
    }


def workshop_items() -> list[dict[str, Any]]:
    items = []
    for yaml_path in sorted(WORKSHOPS_DIR.glob("*/workshop.yaml")):
        meta = parse_scalar_yaml(read_text(yaml_path))
        readme = yaml_path.parent / "README.md"
        subtitle = first_paragraph(read_text(readme)) if readme.exists() else ""
        title = meta.get("title") or yaml_path.parent.name.replace("-", " ").title()
        date = meta.get("date") or yaml_path.parent.name[:10]
        slug = meta.get("slug") or slugify(title)
        items.append(
            {
                "source": "workshops",
                "slug": slug,
                "data": base_data(
                    kind="Workshop",
                    title=title,
                    subtitle=subtitle or "A hands-on AI Shipping Labs workshop.",
                    meta_primary=date,
                    meta_secondary=meta.get("instructor_name", "Alexey Grigorev"),
                    footer="AI Shipping Labs Workshops",
                ),
            }
        )
    return items


def content_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for path in sorted((CONTENT_DIR / "blog").glob("*.md")):
        meta, body = markdown_frontmatter(path)
        title = meta.get("title") or path.stem.replace("-", " ").title()
        items.append(
            {
                "source": "content/blog",
                "slug": path.stem,
                "data": base_data(
                    kind="Article",
                    title=title,
                    subtitle=meta.get("description") or first_paragraph(body),
                    meta_primary="Blog",
                    meta_secondary="/".join((meta.get("tags") or "AI Engineering").split()[:3]),
                    footer="aishippinglabs.com/blog",
                ),
            }
        )

    for path in sorted((CONTENT_DIR / "curated-links").glob("*.md")):
        meta, body = markdown_frontmatter(path)
        title = meta.get("title") or path.stem.replace("-", " ").title()
        items.append(
            {
                "source": "content/curated-links",
                "slug": path.stem,
                "data": base_data(
                    kind="Resource",
                    title=title,
                    subtitle=meta.get("description") or first_paragraph(body),
                    meta_primary="Curated link",
                    meta_secondary="AI / Agents / Engineering",
                    footer="AI Shipping Labs Resources",
                ),
            }
        )

    for path in sorted((CONTENT_DIR / "projects").glob("*.md")):
        meta, body = markdown_frontmatter(path)
        title = meta.get("title") or path.stem.replace("-", " ").title()
        items.append(
            {
                "source": "content/projects",
                "slug": path.stem,
                "data": base_data(
                    kind="Project",
                    title=title,
                    subtitle=meta.get("description") or first_paragraph(body),
                    meta_primary=meta.get("difficulty", "Project"),
                    meta_secondary="OpenAI / Pydantic / Tool Use",
                    footer="AI Shipping Labs Projects",
                ),
            }
        )

    for path in sorted((CONTENT_DIR / "events").glob("*.yaml")):
        meta = parse_scalar_yaml(read_text(path))
        title = meta.get("title") or path.stem.replace("-", " ").title()
        items.append(
            {
                "source": "content/events",
                "slug": meta.get("slug") or path.stem,
                "data": base_data(
                    kind="Live Event",
                    title=title,
                    subtitle=meta.get("description") or "An AI Shipping Labs live session.",
                    meta_primary=(meta.get("start_datetime") or "Live online")[:10],
                    meta_secondary=meta.get("location", "Online"),
                    footer="aishippinglabs.com/events",
                ),
            }
        )

    for path in sorted((CONTENT_DIR / "courses").glob("*/course.yaml")):
        meta = parse_scalar_yaml(read_text(path))
        title = meta.get("title") or path.parent.name.replace("-", " ").title()
        items.append(
            {
                "source": "content/courses",
                "slug": meta.get("slug") or path.parent.name,
                "data": base_data(
                    kind="Course",
                    title=title,
                    subtitle=meta.get("description") or "A practical AI Shipping Labs course.",
                    meta_primary="Free" if meta.get("is_free") == "true" else "Course",
                    meta_secondary="RAG / Agents / Evaluation",
                    footer="aishippinglabs.com/courses",
                ),
            }
        )

    return items


def python_course_items() -> list[dict[str, Any]]:
    items = []
    for path in sorted(PYTHON_COURSE_DIR.glob("[0-9]*-*/module.yaml")):
        meta = parse_scalar_yaml(read_text(path))
        readme = path.parent / "README.md"
        title = meta.get("title") or path.parent.name.replace("-", " ").title()
        module_number = path.parent.name.split("-", 1)[0]
        items.append(
            {
                "source": "python-course",
                "slug": path.parent.name,
                "data": base_data(
                    kind="Python Course",
                    title=title if title.lower().startswith("module") else f"Module {int(module_number)}: {title}",
                    subtitle=first_paragraph(read_text(readme)) if readme.exists() else "",
                    meta_primary=f"Module {int(module_number)}",
                    meta_secondary="Python / Data / AI",
                    footer="AI Shipping Labs Python Course",
                ),
            }
        )
    return items


def render_jpeg_with_cap(template: str, item: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    output = OUTPUT_DIR / item["source"] / f"{item['slug']}.jpg"
    output.parent.mkdir(parents=True, exist_ok=True)

    attempts = []
    for quality in [82, 74, 66, 58, 50, 42, 36, 30]:
        render(
            RenderSpec(
                template=template,
                output=output,
                format="jpeg",
                quality=quality,
                size="og",
                data=item["data"],
            )
        )
        size = output.stat().st_size
        attempts.append({"quality": quality, "size_bytes": size})
        if size <= max_bytes:
            break

    return {
        "source": item["source"],
        "slug": item["slug"],
        "title": item["data"]["title"],
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "quality": attempts[-1]["quality"],
        "under_limit": output.stat().st_size <= max_bytes,
        "attempts": attempts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default=None)
    parser.add_argument("--max-kb", type=int, default=100)
    args = parser.parse_args()

    template = args.template or selected_template(DEFAULT_TEMPLATE)
    max_bytes = args.max_kb * 1000
    items = [*workshop_items(), *content_items(), *python_course_items()]
    manifest = {
        "template": template,
        "max_bytes": max_bytes,
        "count": len(items),
        "items": [],
    }

    for item in items:
        result = render_jpeg_with_cap(template, item, max_bytes)
        manifest["items"].append(result)
        print(f"{result['output']} {result['size_bytes']} bytes q={result['quality']}")

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
