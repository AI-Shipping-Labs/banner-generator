import html as html_lib
import json
from pathlib import Path

import pytest

from banner_generator.renderer import load_spec, render_html, resolve_template

EXAMPLES = Path(__file__).parents[1] / "examples" / "dtc"
ARTICLE_SPECS = (
    "dtc-article-square.json",
    "dtc-article-og.json",
    "dtc-article-two-authors-square.json",
    "dtc-article-survey-og.json",
    "dtc-article-picture-og.json",
)


def test_authors_reach_the_template_as_escaped_json():
    authors = [{"name": 'Ann "A" <O\'Neil>', "image_url": "https://example.test/a.jpg?x=1&y=2"}]
    page = render_html(
        resolve_template("dtc-article"),
        {"kind": "Survey", "title": "T & Q", "date_label": "10 Apr 2025", "reading_time": "6 min read",
         "authors": authors},
        1000,
        1000,
    )
    start = page.index('data-authors="') + len('data-authors="')
    assert json.loads(html_lib.unescape(page[start:page.index('"', start)])) == authors
    assert 'data-title="T &amp; Q"' in page
    assert 'data-reading="6 min read"' in page
    assert "${" not in page


def test_missing_fields_default_to_empty():
    page = render_html(resolve_template("dtc-article"), {"title": "No authors"}, 1000, 1000)
    assert 'data-authors="[]"' in page
    assert 'data-tone=""' in page


def test_dtc_article_examples_cover_square_and_social_sizes():
    sizes = set()
    for name in ARTICLE_SPECS:
        spec = load_spec(EXAMPLES / name)
        assert spec.template == "dtc-article"
        assert spec.data["title"] and spec.data["date_label"] and spec.data["reading_time"]
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


def _evaluate(data, width, height, tmp_path, script):
    page_file = tmp_path / "page.html"
    page_file.write_text(render_html(resolve_template("dtc-article"), data, width, height))
    manager, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(page_file.as_uri())
        report = page.evaluate("() => window.bannerReady")
        return report, page.evaluate(script)
    finally:
        browser.close()
        manager.stop()


SMALLEST_TEXT = """() => Math.min(...[...document.querySelectorAll('body *')]
     .filter(e => e.childNodes.length && [...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()))
     .map(e => parseFloat(getComputedStyle(e).fontSize)))"""


@pytest.mark.parametrize("name", ARTICLE_SPECS)
def test_dtc_article_text_fits_at_a_readable_size(name, tmp_path):
    spec = load_spec(EXAMPLES / name)
    report, smallest = _evaluate(spec.data, *spec.viewport, tmp_path, SMALLEST_TEXT)
    assert report and all(item["ok"] for item in report), report
    assert smallest >= 40


def test_long_title_falls_back_to_the_part_before_the_colon(tmp_path):
    title = ("Customer Segmentation with RFM+ and K-Means: 7 Segments from Champions to Lost, "
             "with Python Code and a Retention Playbook for Each")
    _, headline = _evaluate({"title": title, "date_label": "29 Nov 2020", "reading_time": "14 min read",
                             "authors": [{"name": "Nishant Mohan"}]}, 1000, 1000, tmp_path,
                            "() => document.querySelector('h1').textContent")
    assert headline == "Customer Segmentation with RFM+ and K-Means"


@pytest.mark.parametrize(("kind", "tone"), [("Article", "t-coral"), ("Guide", "t-teal"), ("Survey", "t-plum")])
def test_kind_picks_the_palette(kind, tone, tmp_path):
    _, classes = _evaluate({"kind": kind, "title": "Short title", "authors": []}, 1000, 1000, tmp_path,
                           "() => document.body.className")
    assert tone in classes.split()


def test_picture_takes_the_portraits_place_on_the_social_card(tmp_path):
    picture = {"url": (EXAMPLES / "assets" / "mlops-with-databricks.jpg").as_uri(), "fit": "contain", "frame": True}
    data = {"title": "Short title", "date_label": "Mar 3, 2026", "reading_time": "5 min read",
            "authors": [{"name": "Maria Vechtomova"}], "picture": picture}
    _, parts = _evaluate(data, 1200, 630, tmp_path,
                         "() => [!!document.querySelector('.picture img'), !!document.querySelector('.faces'), "
                         "!!document.querySelector('h1')]")
    assert parts == [True, False, True]


def test_square_picture_is_the_picture_alone(tmp_path):
    picture = {"url": (EXAMPLES / "assets" / "mlops-with-databricks.jpg").as_uri(), "fit": "cover"}
    _, parts = _evaluate({"title": "Short title", "picture": picture}, 1000, 1000, tmp_path,
                         "() => [document.body.classList.contains('picture-only'), !!document.querySelector('h1')]")
    assert parts == [True, False]
