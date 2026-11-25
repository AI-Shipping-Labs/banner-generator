import json
from pathlib import Path

import pytest

from banner_generator.renderer import load_spec, render_html, resolve_template

EXAMPLES = Path(__file__).parents[1] / "examples" / "dtc"
EVENT_SPECS = (
    "dtc-event-speaker-luma.json",
    "dtc-event-speaker-og.json",
    "dtc-event-speaker-two-speakers-luma.json",
    "dtc-event-speaker-no-speakers-luma.json",
)


def test_speakers_reach_the_template_as_escaped_json():
    speakers = [{"name": 'Ann "A" <O\'Neil>', "image_url": "https://example.test/a.jpg?x=1&y=2"}]
    html = render_html(
        resolve_template("dtc-event-speaker"),
        {"kind": "Workshop", "title": "T & Q", "date_label": "Tue 19 Jan 2021", "time_label": "17:00 CET",
         "speakers": speakers},
        1000,
        1000,
    )
    start = html.index('data-speakers="') + len('data-speakers="')
    raw = html[start:html.index('"', start)]
    import html as html_lib

    assert json.loads(html_lib.unescape(raw)) == speakers
    assert 'data-title="T &amp; Q"' in html
    assert 'data-date="Tue 19 Jan 2021"' in html
    assert "${" not in html


def test_missing_speakers_default_to_an_empty_list():
    html = render_html(resolve_template("dtc-event-speaker"), {"title": "No speakers"}, 1000, 1000)
    assert 'data-speakers="[]"' in html


def test_dtc_event_speaker_template_bundles_its_script_style_and_font():
    template = resolve_template("dtc-event-speaker")
    for name in ("event.js", "style.css", "assets/quicksand-latin-var.woff2"):
        assert (template.parent / name).is_file(), name
    script = (template.parent / "event.js").read_text()
    assert "window.bannerReady" in script
    assert "crop" in script


def test_dtc_event_speaker_examples_cover_square_and_social_sizes():
    sizes = set()
    for name in EVENT_SPECS:
        spec = load_spec(EXAMPLES / name)
        assert spec.template == "dtc-event-speaker"
        assert spec.data["title"] and spec.data["date_label"]
        sizes.add(spec.viewport)
    assert sizes == {(1000, 1000), (1200, 630)}


def _browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    manager = sync_api.sync_playwright().start()
    try:
        return manager, manager.chromium.launch()
    except Exception as exc:  # Chromium is not installed in every environment (e.g. CI)
        manager.stop()
        pytest.skip(f"Chromium unavailable: {exc}")


@pytest.mark.parametrize("name", EVENT_SPECS)
def test_dtc_event_speaker_text_fits_at_a_readable_size(name, tmp_path):
    spec = load_spec(EXAMPLES / name)
    width, height = spec.viewport
    page_file = tmp_path / "page.html"
    page_file.write_text(render_html(resolve_template("dtc-event-speaker"), spec.data, width, height))
    manager, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(page_file.as_uri())
        report = page.evaluate("() => window.bannerReady")
        smallest = page.evaluate(
            """() => Math.min(...[...document.querySelectorAll('body *')]
                 .filter(e => e.childNodes.length && [...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()))
                 .map(e => parseFloat(getComputedStyle(e).fontSize)))"""
        )
    finally:
        browser.close()
        manager.stop()
    assert report and all(item["ok"] for item in report), report
    assert smallest >= 40


def test_series_episode_headline_keeps_the_series_and_topic(tmp_path):
    title = "Hireable With AI #2: Agentic Engineering: How I Build Software with Coding Agents"
    page_file = tmp_path / "page.html"
    page_file.write_text(render_html(resolve_template("dtc-event-speaker"),
                                     {"kind": "webinar", "title": title, "date_label": "Mon 30 Nov 2026",
                                      "time_label": "17:00 CET", "speakers": [{"name": "Alexey Grigorev"}]}, 1000, 1000))
    manager, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1000, "height": 1000})
        page.goto(page_file.as_uri())
        page.evaluate("() => window.bannerReady")
        headline = page.evaluate("() => document.querySelector('h1').textContent")
    finally:
        browser.close()
        manager.stop()
    assert headline == "Hireable With AI #2: Agentic Engineering"
