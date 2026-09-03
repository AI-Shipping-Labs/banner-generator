# Banner Generator

Generate branded social banners, document headers, and certificate-style PDFs from HTML templates.

This project is intentionally separate from the AI Shipping Labs Django app. It starts as a local CLI tool and can later become a Lambda, GitHub Action, or standalone render worker without making the production Django image carry Chromium.

## Install

```bash
uv sync --dev
uv run playwright install chromium
```

## Local Preview App

Run the local browser-based studio:

```bash
uv run banner-generator-web
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765), choose a bundled template, edit its
placeholders, and click **Generate preview**. The app renders locally with the same
Playwright renderer used by the CLI; it does not call the Lambda service or upload data.

## Render the Example

```bash
uv run banner-generator render examples/workshop.json
```

The example writes:

```text
output/workshop.png
```

Render the AI Hero certificate example:

```bash
uv run banner-generator render examples/ai-hero-certificate.json
```

Render the content banner examples:

```bash
make render-content-examples
```

Render the DataTalks.Club social kit examples:

```bash
uv run python scripts/render_dtc_examples.py
```

The `dtc-social` template follows the supplied DataTalks.Club canvas: Quicksand type,
cream/lavender/mint surfaces, ink outlines, offset shadows, and separate cadence layouts
for Luma/Meetup, Open Graph, YouTube, and website previews. Use `channel: "luma"` with
the `luma` size for the 1000 x 1000 event artwork.

You can also render with inline arguments:

```bash
uv run banner-generator render \
  --template lab-card \
  --size og \
  --label "Live Workshop" \
  --title "Build Reliable AI Agents" \
  --subtitle "A hands-on session for shipping agentic workflows people can actually use." \
  --meta "May 28, 2026 / Online" \
  --output output/reliable-ai-agents.png
```

## Render Specs

Specs are JSON files:

```json
{
  "template": "lab-card",
  "size": "og",
  "format": "png",
  "output": "output/workshop.png",
  "label": "Live Workshop",
  "title": "Build Reliable AI Agents",
  "subtitle": "A hands-on session for shipping agentic workflows people can actually use.",
  "meta": "May 28, 2026 / Online"
}
```

## Output Formats

The renderer supports:

- `png`
- `jpeg` with optional quality
- `pdf`

The format is inferred from the output extension unless `format` or `--format` is provided.

```bash
uv run banner-generator render examples/workshop.json --output output/workshop.jpg --format jpeg --quality 90
uv run banner-generator render examples/workshop.json --output output/workshop.pdf --format pdf
```

For certificates, use a document-shaped viewport:

```json
{
  "template": "ai-hero-certificate",
  "size": "certificate",
  "format": "pdf",
  "output": "output/ai-hero-certificate.pdf",
  "name": "Jane Doe",
  "course_name": "7-Day AI Agents Crash-Course",
  "dates": "20 January 2026",
  "certificate_id": "example1",
  "certificate_url": "https://certificates.aishippinglabs.com/ai-hero/example1.pdf"
}
```

Supported built-in sizes:

| Size | Dimensions |
|---|---:|
| `og` | 1200 x 630 |
| `certificate` | 1536 x 1024 |
| `linkedin` | 1200 x 627 |
| `wide` | 1600 x 900 |
| `square` | 1080 x 1080 |
| `luma` | 1000 x 1000 |

Use `width` and `height` in the spec, or `--width` and `--height`, for custom sizes.

## Templates

Bundled templates live in `banner_generator/templates/`. Custom templates can be passed by path:

```bash
uv run banner-generator render \
  --template ./my-template.html \
  --output output/custom.png \
  --title "Custom Card"
```

Or from a custom template directory:

```bash
uv run banner-generator render examples/workshop.json --template-dir ./templates
```

Templates use Python `string.Template` placeholders:

```html
<h1>${title}</h1>
<p>${subtitle}</p>
```

The renderer provides `${width}` and `${height}` automatically.

## Publishing Generated Images

The CLI only writes files. Publishing is a separate concern.

Good targets for generated banners:

- S3 plus a CDN URL
- a GitHub repository that stores generated assets
- a local output directory while iterating on styles

This keeps Django, Studio, and production workers independent from browser rendering.

## AWS Lambda Deployment

Terraform for the AWS deployment lives in `infra/`. It creates:

- ECR for the Lambda container image
- a private S3 bucket for templates synced from `banner_generator/templates`
- a private S3 bucket for rendered outputs
- a Lambda Function URL protected by a bearer token from Terraform state or `auth_token`

See `infra/README.md` for the deploy and invoke commands. Do not hardcode the
Function URL or token into the Remix app; pass them through that app's
environment variables or secret manager.

Note: this in-repo Terraform is temporary. After the renderer is redeployed in
the other AWS account, the long-lived infrastructure definition should live in
the dedicated infra repository. Once that migration is complete, destroy the
stack managed from this repo.

## Roadmap

- Add more AI Shipping Labs templates and Canva-inspired style variants.
- Add batch rendering from a directory of specs.
- Add optional upload commands for S3 or GitHub.
- Package the renderer for Lambda once the CLI workflow settles.
- Add certificate-oriented templates and batch input helpers.
