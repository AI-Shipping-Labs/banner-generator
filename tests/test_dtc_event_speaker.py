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
    "dtc-event-speaker-sponsor-luma.json",
    "dtc-event-speaker-sponsor-og.json",
    "dtc-event-speaker-podcast-youtube.json",
    "dtc-event-speaker-podcast-og.json",
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
    assert sizes == {(1000, 1000), (1200, 630), (1280, 720)}


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


def _headline(tmp_path, title, *, size=(1000, 1000), sponsor=None):
    data = {"kind": "webinar", "title": title, "date_label": "Mon 30 Nov 2026",
            "time_label": "17:00 CET", "speakers": [{"name": "Alexey Grigorev"}]}
    if sponsor:
        data["sponsor"] = sponsor
    page_file = tmp_path / "page.html"
    page_file.write_text(render_html(resolve_template("dtc-event-speaker"), data, *size))
    manager, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        page.goto(page_file.as_uri())
        report = page.evaluate("() => window.bannerReady")
        headline = page.evaluate("() => document.querySelector('h1').textContent")
    finally:
        browser.close()
        manager.stop()
    return headline, report


def test_sibling_titles_that_fit_large_keep_their_distinguishing_part(tmp_path):
    for title in (
        "Production AI Agents for Generative Media: Course Launch",
        "Production AI Agents for Generative Media: Pre-Course Live Q&A",
    ):
        headline, report = _headline(tmp_path, title)
        assert headline == title
        assert report[0]["size"] >= 72


def test_long_title_that_does_not_fit_large_keeps_the_main_part(tmp_path):
    title = ("Machine Learning Systems Design in Production Environments: Monitoring, "
             "Drift Detection, Retraining Pipelines, Feature Stores and Model Registries Explained")
    headline, _ = _headline(tmp_path, title)
    assert headline == "Machine Learning Systems Design in Production Environments"


def test_series_episode_headline_keeps_the_series_and_topic(tmp_path):
    title = ("Hireable With AI #2: Agentic Engineering: How I Build Software with Coding Agents, "
             "Review Loops, Context Engineering and Shipping Every Day")
    headline, _ = _headline(tmp_path, title)
    assert headline == "Hireable With AI #2: Agentic Engineering"


def test_sponsor_reaches_the_template_and_is_drawn(tmp_path):
    html = render_html(resolve_template("dtc-event-speaker"),
                       {"title": "T", "sponsor": {"name": "Acme", "logo_url": "https://example.test/l.png"}},
                       1000, 1000)
    assert 'data-sponsor="{&quot;name&quot;: &quot;Acme&quot;' in html
    assert 'data-sponsor=""' in render_html(resolve_template("dtc-event-speaker"), {"title": "T"}, 1000, 1000)
    for size in ((1000, 1000), (1200, 630)):
        headline, report = _headline(tmp_path, "Building AI Agent Workflows", size=size,
                                     sponsor={"name": "Acme Corp"})
        assert headline == "Building AI Agent Workflows"
        assert all(item["ok"] for item in report), report


@pytest.mark.parametrize("name", ("dtc-event-speaker-podcast-youtube.json", "dtc-event-speaker-podcast-og.json"))
def test_series_line_is_drawn_on_one_line_inside_the_canvas(name, tmp_path):
    spec = load_spec(EXAMPLES / name)
    width, height = spec.viewport
    page_file = tmp_path / "page.html"
    page_file.write_text(render_html(resolve_template("dtc-event-speaker"), spec.data, width, height))
    manager, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(page_file.as_uri())
        page.evaluate("() => window.bannerReady")
        box = page.evaluate(
            "() => { const r = document.querySelector('.series').getBoundingClientRect();"
            " return {right: r.right, height: r.height, text: document.querySelector('.series').textContent}; }"
        )
    finally:
        browser.close()
        manager.stop()
    assert box["text"] == spec.data["series"]
    assert box["right"] <= width - 40
    assert box["height"] < 60  # one line


def test_youtube_size_is_16_by_9():
    from banner_generator.renderer import SIZES

    assert SIZES["youtube"] == (1280, 720)
