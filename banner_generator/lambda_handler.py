from __future__ import annotations

import base64
import json
import mimetypes
import tempfile
from pathlib import Path
from typing import Any

from banner_generator.renderer import DEFAULT_SIZE, RenderSpec, output_format, render


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    return event


def spec_from_event(event: dict[str, Any], output: Path | None = None) -> RenderSpec:
    payload = _event_payload(event)
    data = payload.get("data", {})
    known_keys = {
        "template",
        "output",
        "size",
        "format",
        "quality",
        "width",
        "height",
        "data",
        "s3",
    }
    inline_data = {key: value for key, value in payload.items() if key not in known_keys}
    data = {**data, **inline_data}

    format_name = payload.get("format", "png")
    suffix = "jpg" if format_name == "jpeg" else format_name
    output_path = output or Path(tempfile.gettempdir()) / f"rendered.{suffix}"

    return RenderSpec(
        template=payload["template"],
        output=output_path,
        size=payload.get("size", DEFAULT_SIZE),
        format=format_name,
        quality=payload.get("quality"),
        data=data,
        width=payload.get("width"),
        height=payload.get("height"),
    )


def _content_type(path: Path, format_name: str) -> str:
    if format_name == "pdf":
        return "application/pdf"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _upload_to_s3(path: Path, target: dict[str, Any], content_type: str) -> dict[str, Any]:
    import boto3

    bucket = target["bucket"]
    key = target["key"]
    boto3.client("s3").upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={"ContentType": target.get("content_type", content_type)},
    )
    return {"bucket": bucket, "key": key}


def handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    payload = _event_payload(event)
    spec = spec_from_event(payload)
    output = render(spec)
    format_name = output_format(spec)
    content_type = _content_type(output, format_name)

    if "s3" in payload:
        uploaded = _upload_to_s3(output, payload["s3"], content_type)
        return {
            "ok": True,
            "format": format_name,
            "content_type": content_type,
            "s3": uploaded,
        }

    body = base64.b64encode(output.read_bytes()).decode("ascii")
    return {
        "statusCode": 200,
        "isBase64Encoded": True,
        "headers": {"Content-Type": content_type},
        "body": body,
    }
