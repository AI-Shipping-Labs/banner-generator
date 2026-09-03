from pathlib import Path

import pytest

from banner_generator.renderer import (
    RenderSpec,
    load_spec,
    output_format,
    render_html,
    resolve_template,
)

DTC_EXAMPLE_SPECS = (
    "dtc-event-webinar-luma.json",
    "dtc-event-webinar-og.json",
    "dtc-event-webinar-youtube.json",
    "dtc-event-podcast-luma.json",
    "dtc-event-workshop-luma.json",
    "dtc-article-preview.json",
    "dtc-book-preview.json",
    "dtc-course-preview.json",
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

    assert path.name == "template.html"
    assert path.parent.name == "lab-card"
    assert path.exists()


def test_luma_size_matches_the_public_event_artwork_contract():
    spec = RenderSpec(template="lab-card", output=Path("card.png"), size="luma")

    assert spec.viewport == (1000, 1000)


def test_dtc_social_template_contains_the_public_brand_and_data_slots():
    template = resolve_template("dtc-social")

    assert template.parent.name == "dtc-social"
    assert (template.parent / "style.css").is_file()
    assert (template.parent / "assets" / "quicksand-latin-var.woff2").is_file()

    html = render_html(
        template,
        {
            "brand": "DataTalks.Club",
            "kind": "Webinar",
            "title": "A <safe> title",
            "meta_primary": "Mon 31 Aug",
            "meta_secondary": "17:00 CEST",
        },
        1000,
        1000,
    )

    assert 'class="poster"' in html
    assert "DataTalks.Club" in html
    assert "A &lt;safe&gt; title" in html
    assert "Mon 31 Aug" in html
    assert "17:00 CEST" in html


def test_dtc_example_specs_cover_the_published_size_contracts():
    examples_dir = Path(__file__).parents[1] / "examples"

    for filename in DTC_EXAMPLE_SPECS:
        spec = load_spec(examples_dir / filename)

        assert spec.template == "dtc-social"
        assert spec.data["brand"] == "DataTalks.Club"

    luma_specs = [
        load_spec(examples_dir / filename) for filename in DTC_EXAMPLE_SPECS if "luma" in filename
    ]
    assert luma_specs
    assert {spec.viewport for spec in luma_specs} == {(1000, 1000)}
    assert load_spec(examples_dir / "dtc-event-webinar-og.json").viewport == (1200, 630)
    assert load_spec(examples_dir / "dtc-event-webinar-youtube.json").viewport == (1280, 720)


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
