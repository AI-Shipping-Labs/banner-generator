# Architecture

`banner-generator` starts as a CLI, but the core boundary is deliberately small enough to reuse from other environments.

## Current Flow

1. Read a JSON render spec.
2. Resolve an HTML template.
3. Substitute text variables.
4. Open the rendered HTML with Playwright.
5. Capture a PNG, JPEG, or PDF at a fixed viewport size.

The CLI writes only to the path you provide. It does not assume a Django project, a `static/` directory, or a production storage backend.

## Future Boundaries

The same renderer can later sit behind:

- a GitHub Action that renders banners from content metadata and commits or uploads the images
- a Lambda function that accepts render specs and writes to S3
- a separate worker service that receives render jobs from another app

The main AI Shipping Labs Django app should not need Chromium in its production image. If Studio eventually triggers banner generation, it can call a separate rendering boundary instead of running browser automation inside the web or worker container.

## Storage

Generated files are artifacts. Reasonable storage targets:

- S3 bucket plus CDN URL
- GitHub repository for committed generated assets
- local `output/` directory during design iteration

The renderer itself does not upload. Publishing is a separate step so storage can evolve independently.

## Certificates

Certificates fit the same model: HTML template in, PDF out. The generator should stay generic and let certificate-specific tools prepare the data, QR codes, verification URLs, and publishing workflow.
