from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from banner_generator.renderer import load_spec, render

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DTC_EXAMPLE_SPECS = (
    "examples/dtc-event-webinar-luma.json",
    "examples/dtc-event-webinar-og.json",
    "examples/dtc-event-webinar-youtube.json",
    "examples/dtc-event-podcast-luma.json",
    "examples/dtc-event-podcast-og.json",
    "examples/dtc-event-podcast-youtube.json",
    "examples/dtc-event-workshop-luma.json",
    "examples/dtc-event-workshop-og.json",
    "examples/dtc-event-workshop-youtube.json",
    "examples/dtc-article-preview.json",
    "examples/dtc-book-preview.json",
    "examples/dtc-course-preview.json",
)


def render_dtc_examples() -> None:
    for spec_name in DTC_EXAMPLE_SPECS:
        spec = load_spec(REPOSITORY_ROOT / spec_name)
        output = spec.output if spec.output.is_absolute() else REPOSITORY_ROOT / spec.output
        rendered = render(replace(spec, output=output))
        print(rendered.relative_to(REPOSITORY_ROOT))


if __name__ == "__main__":
    render_dtc_examples()
