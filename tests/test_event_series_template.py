import json
from pathlib import Path

from banner_generator.renderer import load_spec, render_html, resolve_template

EXAMPLE = Path("examples/aisl/content-event-series.json")
LAMBDA_EXAMPLE = Path("examples/aisl/lambda-content-event-series.json")


def test_event_series_template_is_resolvable():
    path = resolve_template("asl-event-series")

    assert path.name == "template.html"
    assert path.parent.name == "asl-event-series"
    assert (path.parent / "style.css").exists()


def test_event_series_example_renders_series_slots():
    spec = load_spec(EXAMPLE)
    template_path = resolve_template(spec.template)

    html = render_html(template_path, spec.data or {}, 1200, 630)

    # Series-specific framing must reach the rendered markup.
    assert "Event Series" in html
    assert "Weekly series" in html
    assert "AI Shipping Labs Build Reviews" in html
    assert "Wednesdays / 18:00 CEST" in html
    assert "12 sessions / Members" in html
    assert "AI Shipping Labs Events" in html
    # Recurring-series visual cues defined by this template.
    assert "stack-card" in html
    assert "repeat-dots" in html


def test_event_series_example_uses_the_event_series_template():
    spec = load_spec(EXAMPLE)

    assert spec.template == "asl-event-series"


def test_lambda_event_series_example_matches_data_contract():
    payload = json.loads(LAMBDA_EXAMPLE.read_text())

    assert payload["template"] == "asl-event-series"
    data = payload["data"]
    assert data["kind"] == "Event Series"
    # The exact data field names the website auto-banner pipeline must send.
    assert set(data) >= {
        "kind",
        "kicker",
        "title",
        "subtitle",
        "meta_primary",
        "meta_secondary",
        "footer",
    }
