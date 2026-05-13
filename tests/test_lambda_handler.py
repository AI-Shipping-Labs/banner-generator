from pathlib import Path

from banner_generator import lambda_handler


def test_spec_from_event_supports_data_and_inline_fields(tmp_path: Path):
    event = {
        "template": "asl-content-card",
        "format": "png",
        "size": "og",
        "data": {"title": "From data"},
        "kind": "Article",
    }

    spec = lambda_handler.spec_from_event(event, output=tmp_path / "rendered.png")

    assert spec.template == "asl-content-card"
    assert spec.output == tmp_path / "rendered.png"
    assert spec.format == "png"
    assert spec.data == {"title": "From data", "kind": "Article"}


def test_spec_from_event_supports_api_gateway_body(tmp_path: Path):
    event = {
        "body": """
        {
          "template": "ai-hero-certificate",
          "format": "pdf",
          "width": 1536,
          "height": 1024,
          "data": {"name": "Jane Doe"}
        }
        """
    }

    spec = lambda_handler.spec_from_event(event, output=tmp_path / "rendered.pdf")

    assert spec.template == "ai-hero-certificate"
    assert spec.format == "pdf"
    assert spec.width == 1536
    assert spec.height == 1024
    assert spec.data == {"name": "Jane Doe"}


def test_handler_returns_base64_response(monkeypatch, tmp_path: Path):
    rendered = tmp_path / "rendered.png"
    rendered.write_bytes(b"fake-png")

    def fake_spec_from_event(event, output=None):
        return lambda_handler.RenderSpec(
            template="asl-content-card",
            output=rendered,
            format="png",
        )

    def fake_render(spec):
        return spec.output

    monkeypatch.setattr(lambda_handler, "spec_from_event", fake_spec_from_event)
    monkeypatch.setattr(lambda_handler, "render", fake_render)

    response = lambda_handler.handler({"template": "asl-content-card"})

    assert response["statusCode"] == 200
    assert response["isBase64Encoded"] is True
    assert response["headers"]["Content-Type"] == "image/png"
    assert response["body"] == "ZmFrZS1wbmc="
