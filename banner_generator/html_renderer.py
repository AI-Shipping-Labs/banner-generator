from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FORMATS = {"pdf", "png", "jpeg"}
PAGE_FORMATS = {"A4", "Letter"}


@dataclass(frozen=True)
class S3Object:
    bucket: str
    key: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "S3Object":
        return cls(bucket=value["bucket"], key=value["key"])

    def as_dict(self) -> dict[str, str]:
        return {"bucket": self.bucket, "key": self.key}


@dataclass(frozen=True)
class RenderJob:
    job_id: str
    input: S3Object
    output: S3Object
    format: str
    viewport: dict[str, int] = field(default_factory=lambda: {"width": 1200, "height": 630})
    image: dict[str, Any] = field(default_factory=dict)
    pdf: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RenderJob":
        if payload.get("schema") != "html-renderer.job.v1":
            raise ValueError("schema must be html-renderer.job.v1")
        format_name = str(payload["format"]).lower()
        if format_name not in FORMATS:
            raise ValueError(f"Unsupported output format: {format_name}")
        job = cls(
            job_id=str(payload["job_id"]),
            input=S3Object.from_dict(payload["input"]),
            output=S3Object.from_dict(payload["output"]),
            format=format_name,
            viewport=dict(payload.get("viewport", {"width": 1200, "height": 630})),
            image=dict(payload.get("image", {})),
            pdf=dict(payload.get("pdf", {})),
            context=dict(payload.get("context", {})),
        )
        job.validate()
        return job

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", self.job_id):
            raise ValueError("job_id must contain 1-128 safe identifier characters")
        for dimension in ("width", "height"):
            if not 1 <= int(self.viewport.get(dimension, 0)) <= 4096:
                raise ValueError(f"viewport.{dimension} must be between 1 and 4096")
        if self.format == "jpeg":
            quality = int(self.image.get("quality", 80))
            if not 1 <= quality <= 100:
                raise ValueError("image.quality must be between 1 and 100")
        output_size = self.image.get("output_size")
        if output_size:
            for dimension in ("width", "height"):
                value = int(output_size.get(dimension, 0))
                if value <= 0 or value > int(self.viewport[dimension]):
                    raise ValueError(
                        f"image.output_size.{dimension} must be positive and within viewport"
                    )
        if self.format == "pdf":
            page_format = self.pdf.get("page_format")
            has_dimensions = "width" in self.pdf or "height" in self.pdf
            if page_format and page_format not in PAGE_FORMATS:
                raise ValueError("pdf.page_format must be A4 or Letter")
            if has_dimensions and not {"width", "height"} <= self.pdf.keys():
                raise ValueError("pdf.width and pdf.height must be supplied together")
            if page_format and has_dimensions:
                raise ValueError("use pdf.page_format or explicit dimensions, not both")


def render_document(html: str, job: RenderJob, output: Path) -> Path:
    """Render untrusted self-contained HTML with secure defaults."""
    from playwright.sync_api import sync_playwright

    output.parent.mkdir(parents=True, exist_ok=True)
    viewport = {key: int(job.viewport[key]) for key in ("width", "height")}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-javascript",
                "--no-sandbox",
                "--single-process",
            ]
        )
        context = browser.new_context(java_script_enabled=False, viewport=viewport)
        page = context.new_page()
        # Self-contained data URLs are allowed; network and file URLs are not.
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.url.startswith(("data:", "about:"))
                else route.abort("blockedbyclient")
            ),
        )
        page.set_default_timeout(30_000)
        page.set_content(html, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_function("Array.from(document.images).every(image => image.complete)")

        if job.format == "pdf":
            options: dict[str, Any] = {
                "path": str(output),
                "print_background": bool(job.pdf.get("print_background", True)),
                "margin": job.pdf.get(
                    "margin", {"top": "0", "right": "0", "bottom": "0", "left": "0"}
                ),
            }
            if job.pdf.get("page_format"):
                options["format"] = job.pdf["page_format"]
            elif "width" in job.pdf:
                options.update(width=str(job.pdf["width"]), height=str(job.pdf["height"]))
            else:
                options.update(width=f"{viewport['width']}px", height=f"{viewport['height']}px")
            page.pdf(**options)
        else:
            screenshot: dict[str, Any] = {
                "path": str(output),
                "type": job.format,
                "full_page": False,
            }
            output_size = job.image.get("output_size")
            if output_size:
                screenshot["clip"] = {
                    "x": 0,
                    "y": 0,
                    "width": int(output_size["width"]),
                    "height": int(output_size["height"]),
                }
            if job.format == "jpeg":
                screenshot["quality"] = int(job.image.get("quality", 80))
            page.screenshot(**screenshot)
        browser.close()

    return output
