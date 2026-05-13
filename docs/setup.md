# Setup and Agent Handoff

Use this note when continuing work on the project with another coding agent.

## Project

Work in:

```text
/home/alexey/git/banner-generator
```

GitHub repository:

```text
https://github.com/AI-Shipping-Labs/banner-generator
```

This is a standalone AI Shipping Labs project for generating branded banners, social images, headers, and certificate-style PDFs from HTML templates. Keep it independent from the AI Shipping Labs Django app.

Related local repositories:

```text
/home/alexey/git/ai-shipping-labs
/home/alexey/git/ai-shipping-labs-content
/home/alexey/git/certificate-creator
```

The main website lives in `/home/alexey/git/ai-shipping-labs`. It is a Django app for `aishippinglabs.com`. It has content models for articles, workshops, events, courses, projects, downloads, and certificates. Many of those models have a `cover_image_url` field that currently points to an external image URL.

The content repository lives in `/home/alexey/git/ai-shipping-labs-content`. The website can sync content from there. Generated banners may eventually be referenced from content metadata or model fields, but this generator should not need to know the website database schema.

The older certificate rendering project lives in `/home/alexey/git/certificate-creator`. It is useful as historical context: it renders HTML templates through a browser and outputs PDFs. This project should absorb the generic part of that idea, but avoid certificate-specific APIs or upload flows in the core renderer.

## Intended Use

The first use case is local generation of visual assets for AI Shipping Labs:

- workshop banners
- article cover images
- event promo images
- social sharing cards
- card headers
- certificate-style PDFs

The operator should be able to run a CLI command, inspect the generated file, and then publish it wherever the website expects public assets.

Example:

```bash
uv run banner-generator render examples/workshop.json --output output/agent-workshop.png
```

Then the generated file can be uploaded or committed separately, and the resulting public URL can be used as `cover_image_url` in the website.

Important: generated assets should not be assumed to live inside the Django repo's `static/` directory. That might be convenient for local experiments, but it is not the production publishing model.

Likely publishing targets:

- S3 bucket plus CDN URL
- a GitHub repository that stores generated assets
- a future asset pipeline triggered by GitHub Actions

Longer term, the AI Shipping Labs Studio UI may have actions such as:

- generate a banner for one article/workshop/event
- find all content without `cover_image_url`
- enqueue banner generation for missing assets
- regenerate a banner after content metadata changes

If that happens, the Django app should call a separate rendering boundary rather than carrying Chromium in the production web or worker image. Good future boundaries are a Lambda function, a separate render worker, or a GitHub Action.

## Current State

- Python package: `banner_generator`
- CLI entrypoint: `banner-generator`
- Renderer: `banner_generator/renderer.py`
- CLI: `banner_generator/cli.py`
- Built-in template: `banner_generator/templates/lab-card.html`
- Example spec: `examples/workshop.json`
- Docs: `README.md` and `docs/architecture.md`
- Supported outputs: `png`, `jpeg` with quality, and `pdf`
- Rendering engine: Playwright/Chromium

## Setup

```bash
uv sync --dev
uv run playwright install chromium
```

Run checks:

```bash
uv run pytest
uv run ruff check .
```

Render the example:

```bash
uv run banner-generator render examples/workshop.json
```

## Design Constraints

- Do not assume generated files go into Django `static/`.
- Outputs should be arbitrary local paths.
- Uploading and publishing should stay separate from rendering for now.
- Future publishing targets may include S3, GitHub Actions, Lambda, or a standalone render worker.
- Keep the core renderer generic enough for both social banners and certificates.
- Avoid adding Django dependencies.

## Good Next Tasks

1. Add batch rendering from a directory or multiple JSON specs.
2. Add a certificate-oriented example template and spec.
3. Improve template variable handling and document available fields.
4. Add `--list-sizes` or richer CLI help.
5. Add `--html-output` examples for debugging templates.
6. Consider an S3 publishing command only as a separate command, not part of `render`.

Before changing behavior, inspect:

```text
README.md
docs/architecture.md
banner_generator/renderer.py
banner_generator/cli.py
```

After changes, run:

```bash
uv run pytest
uv run ruff check .
```

## Template Work Priority

If the next task is visual design, create another polished AI Shipping Labs template inspired by the Canva banner style. Keep it pure HTML/CSS, render correctly at fixed viewport dimensions, and add an example JSON spec.
