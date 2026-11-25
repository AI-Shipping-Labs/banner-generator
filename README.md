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
uv run banner-generator render examples/dtc/dtc-article-preview.json
```

The example writes:

```text
output/dtc/article-preview.png
```

Render the AI Hero certificate example:

```bash
uv run banner-generator render examples/certificates/ai-hero-certificate.json
```

Render the DataTalks.Club social kit examples:

```bash
uv run python scripts/render_dtc_examples.py
```

The `dtc-social` template follows the supplied DataTalks.Club canvas: Quicksand type,
cream/lavender/mint surfaces, ink outlines, offset shadows, and separate cadence layouts
for Luma/Meetup, Open Graph, YouTube, and website previews. Use `channel: "luma"` with
the `luma` size for the 1000 x 1000 event artwork.

### DataTalks.Club event pictures (`dtc-event-speaker`)

`dtc-event-speaker` is the speaker-led picture for DataTalks.Club events: big speaker
portrait(s), name(s), type pill, weekday + date, local time, and the title. It is made
to be read where it is shown: about 290px wide on the event page and about 500px in
social feeds, so no text on the canvas is smaller than 40px. It has no DTC logo, edge
strip, or inner border; the host page draws the frame. A sponsored event can add the
sponsor's logo (`sponsor`).

One template serves both canvases. The layout is chosen by aspect ratio:

- `size: "luma"` (1000 x 1000): the event page and Luma/Meetup artwork.
- `size: "og"` (1200 x 630): Open Graph, LinkedIn, X, and Slack previews.
- `size: "youtube"` (1280 x 720): YouTube thumbnail and video poster; the extra height goes to larger portraits.

```bash
uv run banner-generator render examples/dtc/dtc-event-speaker-luma.json
uv run banner-generator render examples/dtc/dtc-event-speaker-og.json
```

Spec fields:

| Field | Meaning |
|---|---|
| `kind` | `webinar`, `workshop`, `podcast`, or `conference` (sets the colours and the pill) |
| `title` | Event title. The whole title is kept when it fits at 72px or more (60px on `og`), so sibling events such as `Course: Launch` and `Course: Live Q&A` keep their own headlines. A longer title with a colon falls back to the part before the colon (a series episode, `Series #2: Topic: details`, keeps `Series #2: Topic`); set `headline` to override |
| `date_label` | For example `Tue 19 Jan 2021`, in the event's own timezone |
| `time_label` | For example `17:00 CET` |
| `speakers` | List of `{"name", "image_url", "crop"}`. Up to four portraits are shown; four or more show "N speakers". An empty list shows the date in a large disc |
| `sponsor` | Optional `{"name", "logo_url", "label"}`: draws "Sponsored by" (or `label`) and the logo on a white plate under the title (the name in bold when there is no logo). `logo_url` is any image URL, a `file://` URL, or a data URL |
| `series` | Optional line under the speaker names, e.g. `DataTalks.Club Podcast · S15 E6`, kept on one line (landscape sizes shrink the portraits to make room) |

`crop` is optional, `{"zoom": 1.5, "x": 65, "y": 20}`: it zooms a portrait and sets
the focus point (in percent) to hide stray edge content in the source photo. Title
and name sizes are fitted automatically in the page (`window.bannerReady`); the
renderer waits for that before the screenshot, so the CLI, web app, and Lambda all
produce the fitted result.

More examples: `examples/dtc/dtc-event-speaker-two-speakers-luma.json`,
`examples/dtc/dtc-event-speaker-no-speakers-luma.json`, and the sponsored
`examples/dtc/dtc-event-speaker-sponsor-luma.json` / `-sponsor-og.json`.

## Render Specs

Specs are JSON files. See `examples/dtc/dtc-article-preview.json` for a complete
DataTalks.Club card spec, `examples/certificates/dtc-data-engineering-zoomcamp-certificate.json`
for the Zoomcamp certificate spec, and `examples/certificates/ai-hero-certificate.json` for the
AI Hero certificate spec.

## Output Formats

The renderer supports:

- `png`
- `jpeg` with optional quality
- `pdf`

The format is inferred from the output extension unless `format` or `--format` is provided.

```bash
uv run banner-generator render examples/dtc/dtc-article-preview.json --output output/dtc/article-preview.jpg --format jpeg --quality 90
uv run banner-generator render examples/dtc/dtc-article-preview.json --output output/dtc/article-preview.pdf --format pdf
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

The DataTalks.Club Zoomcamp certificate uses the same fields with the
`zoomcamp-certificate` size. Its bundled course examples intentionally use one lead
instructor signature, including Data Engineering and MLOps Zoomcamp, rather than
including every historical course contributor.

Supported built-in sizes:

| Size | Dimensions |
|---|---:|
| `og` | 1200 x 630 |
| `certificate` | 1536 x 1024 |
| `zoomcamp-certificate` | 1920 x 1080 |
| `linkedin` | 1200 x 627 |
| `wide` | 1600 x 900 |
| `square` | 1080 x 1080 |
| `luma` | 1000 x 1000 |

Use `width` and `height` in the spec, or `--width` and `--height`, for custom sizes.

## Templates

Bundled templates live in `banner_generator/templates/`. Custom templates can be passed by path:

Certificate templates currently include:

- `ai-hero-certificate` — AI Hero dark certificate
- `ai-buildcamp-certificate` — AI Engineering Buildcamp dark certificate
- `dtc-zoomcamp-certificate` — reusable DataTalks.Club Zoomcamp certificate

```bash
uv run banner-generator render \
  --template ./my-template.html \
  --output output/custom.png \
  --title "Custom Card"
```

Or from a custom template directory:

```bash
uv run banner-generator render examples/dtc/dtc-article-preview.json --template-dir ./templates
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
