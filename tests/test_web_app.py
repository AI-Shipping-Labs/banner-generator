from pathlib import Path

import pytest

from banner_generator import web_app


def test_template_catalog_discovers_placeholders_without_viewport_fields():
    templates = {item["name"]: item for item in web_app.template_catalog()}

    assert "dtc-social" in templates
    assert "title" in templates["dtc-social"]["placeholders"]
    assert "width" not in templates["dtc-social"]["placeholders"]
    assert "height" not in templates["dtc-social"]["placeholders"]
    assert templates["dtc-social"]["path"] == "banner_generator/templates/dtc-social/template.html"
    assert "${title}" in templates["dtc-social"]["definition"]


def test_template_catalog_exposes_spec_canvas_recommendations():
    templates = {item["name"]: item for item in web_app.template_catalog()}

    content_canvas = templates["asl-content-card"]["recommended_canvas"]
    assert content_canvas["size"] == "og"
    assert content_canvas["width"] == 1200
    assert content_canvas["height"] == 630

    certificate_canvas = templates["ai-hero-certificate"]["recommended_canvas"]
    assert certificate_canvas["size"] == "certificate"
    assert certificate_canvas["width"] == 1536
    assert certificate_canvas["height"] == 1024
    assert certificate_canvas["format"] == "pdf"
    assert certificate_canvas["source"] == "examples/ai-hero-certificate.json"


def test_example_catalog_only_includes_render_specs():
    examples = web_app.example_catalog()

    assert examples
    assert all(not example["name"].startswith("lambda-") for example in examples)
    assert {example["template"] for example in examples} >= {"dtc-social", "lab-card"}
    assert "asl-blueprint-path" in {example["template"] for example in examples}


def test_build_render_spec_accepts_custom_viewport(tmp_path: Path):
    spec = web_app.build_render_spec(
        {
            "template": "dtc-social",
            "size": "og",
            "width": 900,
            "height": 500,
            "data": {"title": "Preview"},
        },
        tmp_path / "preview.png",
    )

    assert spec.viewport == (900, 500)
    assert spec.format == "png"
    assert spec.data == {"title": "Preview"}


def test_build_render_spec_rejects_unknown_templates(tmp_path: Path):
    with pytest.raises(ValueError, match="bundled templates"):
        web_app.build_render_spec(
            {"template": "../outside", "data": {}},
            tmp_path / "preview.png",
        )


def test_render_preview_returns_data_url_and_cleans_scratch_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(web_app, "PREVIEW_ROOT", tmp_path)

    def fake_render(spec):
        spec.output.write_bytes(b"fake-png")
        return spec.output

    monkeypatch.setattr(web_app, "render", fake_render)

    result = web_app.render_preview(
        {
            "template": "dtc-social",
            "size": "og",
            "data": {"title": "Preview"},
        }
    )

    assert result["image"] == "data:image/png;base64,ZmFrZS1wbmc="
    assert result["width"] == 1200
    assert result["height"] == 630
    assert result["download"] == result["image"]
    assert result["download_format"] == "png"
    assert result["download_name"] == "dtc-social-1200x630.png"
    assert list(tmp_path.iterdir()) == []


def test_render_preview_returns_pdf_download_for_pdf_template(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(web_app, "PREVIEW_ROOT", tmp_path)
    rendered_formats = []

    def fake_render(spec):
        rendered_formats.append(spec.format)
        spec.output.write_bytes(
            b"fake-pdf" if spec.format == "pdf" else b"fake-png"
        )

    monkeypatch.setattr(web_app, "render", fake_render)

    result = web_app.render_preview(
        {
            "template": "ai-hero-certificate",
            "size": "certificate",
            "data": {"name": "Preview"},
        }
    )

    assert rendered_formats == ["png", "pdf"]
    assert result["width"] == 1536
    assert result["height"] == 1024
    assert result["download"] == "data:application/pdf;base64,ZmFrZS1wZGY="
    assert result["download_format"] == "pdf"
    assert result["download_name"] == "ai-hero-certificate-1536x1024.pdf"
    assert list(tmp_path.iterdir()) == []
