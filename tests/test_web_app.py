from pathlib import Path

import pytest

from banner_generator import web_app


def test_template_catalog_discovers_placeholders_without_viewport_fields():
    templates = {item["name"]: item for item in web_app.template_catalog()}

    assert "dtc-social" in templates
    assert "title" in templates["dtc-social"]["placeholders"]
    assert "width" not in templates["dtc-social"]["placeholders"]
    assert "height" not in templates["dtc-social"]["placeholders"]


def test_example_catalog_only_includes_render_specs():
    examples = web_app.example_catalog()

    assert examples
    assert all(not example["name"].startswith("lambda-") for example in examples)
    assert {example["template"] for example in examples} >= {"dtc-social", "lab-card"}


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
    assert list(tmp_path.iterdir()) == []
