from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any

from banner_generator.renderer import DEFAULT_SIZE, RenderSpec, output_format, render

_TEMPLATE_CACHE_SIGNATURE: str | None = None
_TEMPLATE_CACHE_DIR = Path(tempfile.gettempdir()) / "banner-generator-templates"


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    return event


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _header(event: dict[str, Any], name: str) -> str | None:
    headers = event.get("headers") or {}
    if not isinstance(headers, dict):
        return None
    lower_name = name.lower()
    for key, value in headers.items():
        if key.lower() == lower_name:
            return str(value)
    return None


def _is_authorized(event: dict[str, Any]) -> bool:
    expected = os.environ.get("BANNER_GENERATOR_AUTH_TOKEN")
    if not expected:
        return True

    authorization = _header(event, "authorization") or ""
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        token = _header(event, "x-api-token") or ""
    return token == expected


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

    bucket = target.get("bucket") or os.environ["BANNER_GENERATOR_OUTPUT_BUCKET"]
    key = target["key"]
    boto3.client("s3").upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={"ContentType": target.get("content_type", content_type)},
    )
    return {"bucket": bucket, "key": key}


def _template_cache_signature(objects: list[dict[str, Any]]) -> str:
    payload = [
        {
            "key": obj["Key"],
            "etag": obj.get("ETag"),
            "size": obj.get("Size"),
            "last_modified": obj.get("LastModified", "").isoformat()
            if obj.get("LastModified")
            else None,
        }
        for obj in objects
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _template_dir_from_s3() -> Path | None:
    global _TEMPLATE_CACHE_SIGNATURE

    bucket = os.environ.get("BANNER_GENERATOR_TEMPLATE_BUCKET")
    if not bucket:
        return None

    import boto3

    prefix = os.environ.get("BANNER_GENERATOR_TEMPLATE_PREFIX", "templates/").strip("/")
    list_prefix = f"{prefix}/" if prefix else ""
    client = boto3.client("s3")
    paginator = client.get_paginator("list_objects_v2")
    objects: list[dict[str, Any]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=list_prefix):
        objects.extend(page.get("Contents", []))

    signature = _template_cache_signature(objects)
    if signature == _TEMPLATE_CACHE_SIGNATURE and _TEMPLATE_CACHE_DIR.exists():
        return _TEMPLATE_CACHE_DIR

    _TEMPLATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for obj in objects:
        key = obj["Key"]
        if key.endswith("/"):
            continue
        relative_key = key.removeprefix(list_prefix)
        target = _TEMPLATE_CACHE_DIR / relative_key
        target.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(target))

    _TEMPLATE_CACHE_SIGNATURE = signature
    return _TEMPLATE_CACHE_DIR


def handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    if not _is_authorized(event):
        return _response(401, {"ok": False, "error": "unauthorized"})

    payload = _event_payload(event)
    spec = spec_from_event(payload)
    template_dir = _template_dir_from_s3()
    output = render(spec, template_dir=template_dir) if template_dir else render(spec)
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
