from __future__ import annotations

import argparse
import base64
import json
import re
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from banner_generator.renderer import SIZES, RenderSpec, load_spec, render

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples"
WEB_INDEX = REPOSITORY_ROOT / "web" / "index.html"
PREVIEW_ROOT = REPOSITORY_ROOT / ".tmp" / "web-previews"
PLACEHOLDER_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_REQUEST_BYTES = 512_000
MAX_VIEWPORT = 4_000


def template_placeholders(template_path: Path) -> list[str]:
    placeholders: list[str] = []
    for name in PLACEHOLDER_PATTERN.findall(template_path.read_text(encoding="utf-8")):
        if name not in {"width", "height"} and name not in placeholders:
            placeholders.append(name)
    return placeholders


def canonical_template_name(template: str) -> str:
    path = Path(template)
    if path.name == "template.html":
        return path.parent.name
    return path.name


def render_example_specs() -> list[tuple[Path, RenderSpec]]:
    specs = []
    for example_path in sorted(EXAMPLE_ROOT.rglob("*.json")):
        payload = json.loads(example_path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or not payload.get("template")
            or not payload.get("output")
        ):
            continue
        specs.append((example_path, load_spec(example_path)))
    return specs


def recommended_canvas(
    template: str,
    examples: list[tuple[Path, RenderSpec]],
) -> dict[str, Any] | None:
    matching = [
        (path, spec)
        for path, spec in examples
        if canonical_template_name(spec.template) == template
    ]
    if not matching:
        return None

    viewport_counts = Counter(spec.viewport for _, spec in matching)
    recommended_viewport, _ = viewport_counts.most_common(1)[0]
    source_path, source_spec = next(
        (path, spec)
        for path, spec in matching
        if spec.viewport == recommended_viewport
    )
    source_format = source_spec.format
    if source_format is None:
        suffix = source_spec.output.suffix.lower().lstrip(".")
        source_format = "jpeg" if suffix in {"jpg", "jpeg"} else suffix

    return {
        "width": recommended_viewport[0],
        "height": recommended_viewport[1],
        "size": (
            source_spec.size
            if source_spec.width is None and source_spec.height is None
            else None
        ),
        "format": source_format,
        "source": str(source_path.relative_to(REPOSITORY_ROOT)),
        "definition": source_path.read_text(encoding="utf-8"),
    }


def template_catalog() -> list[dict[str, Any]]:
    examples = render_example_specs()
    templates = []
    for template_path in sorted(TEMPLATE_ROOT.glob("*/template.html")):
        templates.append(
            {
                "name": template_path.parent.name,
                "placeholders": template_placeholders(template_path),
                "recommended_canvas": recommended_canvas(template_path.parent.name, examples),
                "path": str(template_path.relative_to(REPOSITORY_ROOT)),
                "definition": template_path.read_text(encoding="utf-8"),
            }
        )
    return templates


def example_catalog() -> list[dict[str, Any]]:
    examples = []
    for example_path, spec in render_example_specs():
        examples.append(
            {
                "name": example_path.name,
                "template": canonical_template_name(spec.template),
                "size": spec.size,
                "width": spec.width,
                "height": spec.height,
                "data": spec.data or {},
                "path": str(example_path.relative_to(REPOSITORY_ROOT)),
                "definition": example_path.read_text(encoding="utf-8"),
            }
        )
    return examples


def catalog() -> dict[str, Any]:
    return {
        "templates": template_catalog(),
        "examples": example_catalog(),
        "sizes": [
            {"name": name, "width": width, "height": height}
            for name, (width, height) in SIZES.items()
        ],
    }


def _viewport_value(payload: dict[str, Any], name: str) -> int | None:
    value = payload.get(name)
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not 1 <= value <= MAX_VIEWPORT:
        raise ValueError(f"{name} must be between 1 and {MAX_VIEWPORT}")
    return value


def build_render_spec(
    payload: dict[str, Any],
    output: Path,
    *,
    format_name: str = "png",
) -> RenderSpec:
    template = payload.get("template")
    template_names = {item["name"] for item in template_catalog()}
    if not isinstance(template, str) or template not in template_names:
        raise ValueError("template must be one of the bundled templates")

    size = payload.get("size", "og")
    if not isinstance(size, str) or size not in SIZES:
        raise ValueError(f"size must be one of: {', '.join(SIZES)}")

    width = _viewport_value(payload, "width")
    height = _viewport_value(payload, "height")
    if (width is None) != (height is None):
        raise ValueError("width and height must be provided together")

    data = payload.get("data", {})
    if not isinstance(data, dict):
        raise ValueError("data must be an object")
    for key, value in data.items():
        if not isinstance(key, str) or not FIELD_NAME_PATTERN.fullmatch(key):
            raise ValueError(f"invalid placeholder name: {key!r}")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"placeholder {key!r} must be a scalar value")

    return RenderSpec(
        template=template,
        output=output,
        size=size,
        format=format_name,
        data=data,
        width=width,
        height=height,
    )


def render_preview(payload: dict[str, Any]) -> dict[str, Any]:
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    preview_output = PREVIEW_ROOT / f"{uuid4().hex}.png"
    spec = build_render_spec(payload, preview_output)
    download_output: Path | None = None
    try:
        render(spec)
        image = base64.b64encode(preview_output.read_bytes()).decode("ascii")
        width, height = spec.viewport
        result = {
            "image": f"data:image/png;base64,{image}",
            "template": spec.template,
            "width": width,
            "height": height,
            "download": f"data:image/png;base64,{image}",
            "download_format": "png",
            "download_name": f"{spec.template}-{width}x{height}.png",
        }
        recommended = next(
            (
                item["recommended_canvas"]
                for item in template_catalog()
                if item["name"] == spec.template
            ),
            None,
        )
        download_format = recommended.get("format") if recommended else "png"
        if download_format == "pdf":
            download_output = PREVIEW_ROOT / f"{uuid4().hex}.pdf"
            download_spec = build_render_spec(
                payload,
                download_output,
                format_name="pdf",
            )
            render(download_spec)
            encoded = base64.b64encode(download_output.read_bytes()).decode("ascii")
            result.update(
                {
                    "download": f"data:application/pdf;base64,{encoded}",
                    "download_format": "pdf",
                    "download_name": f"{spec.template}-{width}x{height}.pdf",
                }
            )
        return result
    finally:
        preview_output.unlink(missing_ok=True)
        if download_output:
            download_output.unlink(missing_ok=True)


class PreviewServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class PreviewRequestHandler(BaseHTTPRequestHandler):
    server_version = "BannerGeneratorPreview/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_file(WEB_INDEX, "text/html; charset=utf-8")
        elif path == "/api/catalog":
            self._send_json(HTTPStatus.OK, catalog())
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/render":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            payload = self._read_json()
            result = render_preview(payload)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Rendering failed"})
            return
        self._send_json(HTTPStatus.OK, result)

    def _read_json(self) -> dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            raise ValueError("Content-Length is required")
        try:
            length = int(content_length)
        except ValueError as exc:
            raise ValueError("Content-Length must be an integer") from exc
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ValueError(f"request body must be at most {MAX_REQUEST_BYTES} bytes")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError("request body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Web app not found"})
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def create_server(host: str = "127.0.0.1", port: int = 8765) -> PreviewServer:
    return PreviewServer((host, port), PreviewRequestHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Banner Generator preview app.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
    parser.add_argument("--port", default=8765, type=int, help="Bind port (default: 8765).")
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    host, bound_port = server.server_address[:2]
    print(f"Banner Generator preview app: http://{host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
