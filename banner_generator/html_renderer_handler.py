from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from banner_generator.html_renderer import RenderJob, render_document


def _event(event_type: str, job: RenderJob, **details: Any) -> dict[str, Any]:
    return {
        "schema": f"html-renderer.{event_type}.v1",
        "job_id": job.job_id,
        "input": job.input.as_dict(),
        "output": job.output.as_dict(),
        "format": job.format,
        "timestamp": datetime.now(UTC).isoformat(),
        "context": job.context,
        **details,
    }


def _publish_completion(event: dict[str, Any]) -> None:
    queue_url = os.environ.get("HTML_RENDERER_COMPLETION_QUEUE_URL")
    if not queue_url:
        return
    import boto3

    boto3.client("sqs").send_message(QueueUrl=queue_url, MessageBody=json.dumps(event))


def process_job(payload: dict[str, Any], s3: Any | None = None) -> dict[str, Any]:
    if s3 is None:
        import boto3

        s3 = boto3.client("s3")
    job = RenderJob.from_dict(payload)

    try:
        existing = s3.head_object(Bucket=job.output.bucket, Key=job.output.key)
    except s3.exceptions.ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {
            "403",
            "AccessDenied",
            "404",
            "NoSuchKey",
            "NotFound",
        }:
            raise
    else:
        existing_job_id = existing.get("Metadata", {}).get("render-job-id")
        if existing_job_id == job.job_id:
            return _event(
                "completed",
                job,
                content_type=existing.get("ContentType"),
                size_bytes=existing.get("ContentLength"),
                checksum=existing.get("Metadata", {}).get("sha256"),
                reused=True,
            )
        raise ValueError(f"output key already belongs to job {existing_job_id or '(unknown)'}")

    suffix = "jpg" if job.format == "jpeg" else job.format
    output = Path(tempfile.gettempdir()) / f"html-render-{job.job_id}.{suffix}"
    source = s3.get_object(Bucket=job.input.bucket, Key=job.input.key)["Body"].read(
        8 * 1024 * 1024 + 1
    )
    if len(source) > 8 * 1024 * 1024:
        raise ValueError("input HTML exceeds 8 MiB")
    html = source.decode("utf-8")
    try:
        render_document(html, job, output)
        output_bytes = output.read_bytes()
        checksum = hashlib.sha256(output_bytes).hexdigest()
        content_type = mimetypes.types_map.get(f".{suffix}", "application/octet-stream")
        if job.format == "pdf":
            content_type = "application/pdf"
        try:
            s3.put_object(
                Bucket=job.output.bucket,
                Key=job.output.key,
                Body=output_bytes,
                ContentType=content_type,
                Metadata={"render-job-id": job.job_id, "render-schema": "v1", "sha256": checksum},
                IfNoneMatch="*",
            )
        except s3.exceptions.ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in {
                "PreconditionFailed",
                "412",
                "ConditionalRequestConflict",
                "409",
            }:
                raise
            existing = s3.head_object(Bucket=job.output.bucket, Key=job.output.key)
            if existing.get("Metadata", {}).get("render-job-id") != job.job_id:
                raise ValueError("output key belongs to a different render job") from exc
            return _event(
                "completed",
                job,
                content_type=existing.get("ContentType"),
                size_bytes=existing.get("ContentLength"),
                checksum=existing.get("Metadata", {}).get("sha256"),
                reused=True,
            )
    finally:
        output.unlink(missing_ok=True)
    return _event(
        "completed",
        job,
        content_type=content_type,
        size_bytes=len(output_bytes),
        checksum=checksum,
        reused=False,
    )


def _payload(record_or_event: dict[str, Any]) -> dict[str, Any]:
    body = record_or_event.get("body")
    return json.loads(body) if isinstance(body, str) else record_or_event


def handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    records = event.get("Records")
    if not records:
        try:
            return process_job(_payload(event))
        except Exception as exc:
            return {
                "schema": "html-renderer.failed.v1",
                "job_id": event.get("job_id"),
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }

    failures = []
    for record in records:
        try:
            _publish_completion(process_job(_payload(record)))
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
