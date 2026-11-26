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
    "dtc-article-picture-square.json",
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
    if spec.data.get("picture") and spec.viewport == (1000, 1000):
        assert report == []  # the square picture stands alone, with no text to fit
        return
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


LAYOUT = """() => {
  const box = (sel) => { const e = document.querySelector(sel); return e && e.getBoundingClientRect(); };
  const avatar = box('.avatar'), title = box('h1'), byline = box('.byline');
  return {pill: !!document.querySelector('.pill'), brand: !!document.querySelector('.brand img[src$="dtc-mark.svg"]'),
          avatar: avatar && avatar.width, titleTop: title && title.top, bylineTop: byline && byline.top,
          picture: !!document.querySelector('.picture img'), h1: !!title};
}"""
AUTHOR = {"title": "Benefits of Learning in Public and Why It Works", "date_label": "Jan 25, 2026",
          "reading_time": "8 min read", "authors": [{"name": "Alexey Grigorev"}]}


@pytest.mark.parametrize(("width", "height", "brand"), [(1000, 1000, False), (1200, 630, True)])
def test_author_card_is_title_first_with_a_small_byline_portrait(width, height, brand, tmp_path):
    _, parts = _evaluate(AUTHOR, width, height, tmp_path, LAYOUT)
    assert not parts["pill"]  # no type pill: the palette tells the types apart
    assert parts["brand"] is brand  # the social card carries the DataTalks.Club logo
    assert parts["avatar"] <= 160  # a byline portrait, not the event's big circle
    assert parts["titleTop"] < parts["bylineTop"]  # the title leads, the byline closes


def test_picture_is_a_cover_panel_beside_the_title_on_the_social_card(tmp_path):
    picture = {"url": (EXAMPLES / "assets" / "mlops-with-databricks.jpg").as_uri(), "fit": "cover", "frame": True}
    _, parts = _evaluate({**AUTHOR, "picture": picture}, 1200, 630, tmp_path, LAYOUT)
    assert parts["picture"] and parts["h1"] and parts["brand"] and not parts["pill"]


def test_square_picture_is_the_picture_alone(tmp_path):
    picture = {"url": (EXAMPLES / "assets" / "mlops-with-databricks.jpg").as_uri(), "fit": "cover"}
    _, parts = _evaluate({"title": "Short title", "picture": picture}, 1000, 1000, tmp_path,
                         "() => [document.body.classList.contains('picture-only'), !!document.querySelector('h1')]")
    assert parts == [True, False]
