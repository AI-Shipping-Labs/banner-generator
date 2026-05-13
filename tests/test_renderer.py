from pathlib import Path

import pytest

from banner_generator.renderer import (
    RenderSpec,
    load_spec,
    output_format,
    render_html,
    resolve_template,
)


def test_load_spec_supports_inline_data(tmp_path: Path):
    spec_path = tmp_path / "card.json"
    spec_path.write_text(
        """
        {
          "template": "lab-card",
          "size": "og",
          "format": "jpeg",
          "quality": 90,
          "output": "output/card.png",
          "title": "Ship It",
          "label": "Workshop"
        }
        """
    )

    spec = load_spec(spec_path)

    assert spec == RenderSpec(
        template="lab-card",
        output=Path("output/card.png"),
        size="og",
        format="jpeg",
        quality=90,
        data={"title": "Ship It", "label": "Workshop"},
        width=None,
        height=None,
    )


def test_resolve_template_finds_bundled_template():
    path = resolve_template("lab-card")

    assert path.name == "lab-card.html"
    assert path.exists()


def test_render_html_escapes_user_content(tmp_path: Path):
    template = tmp_path / "template.html"
    template.write_text("<h1>${title}</h1><p>${width}x${height}</p>")

    html = render_html(template, {"title": "<script>alert(1)</script>"}, 1200, 630)

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "1200x630" in html


def test_render_html_adds_base_url_for_relative_assets(tmp_path: Path):
    template = tmp_path / "template.html"
    template.write_text("<!doctype html><html><head></head><body></body></html>")

    html = render_html(template, {}, 1200, 630)

    assert f'<base href="{tmp_path.as_uri()}/">' in html


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("card.png", "png"),
        ("card.jpg", "jpeg"),
        ("card.jpeg", "jpeg"),
        ("card.pdf", "pdf"),
    ],
)
def test_output_format_infers_from_extension(output: str, expected: str):
    spec = RenderSpec(template="lab-card", output=Path(output))

    assert output_format(spec) == expected


def test_output_format_prefers_explicit_format():
    spec = RenderSpec(template="lab-card", output=Path("card.bin"), format="pdf")

    assert output_format(spec) == "pdf"
