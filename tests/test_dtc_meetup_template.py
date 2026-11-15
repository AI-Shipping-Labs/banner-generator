from pathlib import Path

from banner_generator import web_app
from banner_generator.renderer import SIZES, load_spec, render_html, resolve_template

EXAMPLE = Path("examples/dtc-meetup/meetup-online.json")


def test_dtc_meetup_template_is_resolvable():
    path = resolve_template("dtc-meetup")

    assert path.name == "template.html"
    assert path.parent.name == "dtc-meetup"
    assert (path.parent / "style.css").exists()
    assert (path.parents[1] / "shared" / "logo_main.svg").is_file()
    assert (path.parents[1] / "dtc-social" / "assets" / "quicksand-latin-var.woff2").is_file()


def test_meetup_size_preset_is_16_by_9():
    assert SIZES["meetup"] == (1200, 675)


def test_dtc_meetup_example_renders_all_fields():
    spec = load_spec(EXAMPLE)
    template_path = resolve_template(spec.template)

    html = render_html(template_path, spec.data or {}, *spec.viewport)

    assert spec.template == "dtc-meetup"
    assert spec.viewport == (1200, 675)
    assert "MEETUP" in html
    assert "ONLINE" in html
    assert "AI engineering vs agentic engineering" in html
    assert "Mon, 23 Nov 2026 | 17:00 Berlin" in html
    assert "Alexey Grigorev" in html
    assert 'src="../shared/logo_main.svg"' in html
    assert '<svg class="dtc-logo"' not in html


def test_dtc_meetup_appears_in_web_catalog():
    templates = {item["name"]: item for item in web_app.template_catalog()}

    assert "dtc-meetup" in templates
    assert set(templates["dtc-meetup"]["placeholders"]) == {
        "format",
        "title",
        "datetime",
        "speaker",
    }
    canvas = templates["dtc-meetup"]["recommended_canvas"]
    assert canvas is not None
    assert canvas["size"] == "meetup"
    assert canvas["width"] == 1200
    assert canvas["height"] == 675
