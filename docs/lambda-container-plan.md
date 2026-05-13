# Lambda Container Plan

Do this after the local templates are accepted.

## Runtime Shape

Keep one rendering core and two entrypoints:

- CLI: reads a JSON spec from disk and writes to `output`.
- Lambda handler: receives a render spec event, renders in `/tmp`, then returns bytes or uploads.

Initial Lambda event shape:

```json
{
  "template": "asl-content-card",
  "format": "png",
  "size": "og",
  "data": {
    "kind": "Article",
    "title": "Example title",
    "subtitle": "Example subtitle"
  }
}
```

Production event shape can add publishing:

```json
{
  "template": "asl-content-card",
  "format": "png",
  "size": "og",
  "data": {},
  "s3": {
    "bucket": "aishippinglabs-assets",
    "key": "banners/example.png",
    "content_type": "image/png"
  }
}
```

## Docker Setup

1. Base image: `python:3.12-slim-bookworm`.
2. Install the package, `awslambdaric`, and Playwright Chromium with system dependencies.
3. Remove the full Chromium and ffmpeg payloads after dependency installation,
   leaving the Chromium headless shell that Playwright launches for this renderer.
4. Set the handler as the container command.
5. Test locally by importing the handler in Docker.
6. For Lambda-style HTTP invocation, run the image with the Lambda Runtime Interface
   Emulator mounted as the entrypoint.
7. Invoke with sample PNG, JPEG, and PDF events and confirm the rendered bytes are valid.

The slim image is larger than a normal Python service because Chromium and browser
system libraries are required, but it avoids the full Playwright base image and
keeps only the Chromium path needed by the renderer.

Measured image sizes:

- Playwright base image with duplicate browser install: `4.49GB`
- Pinned Playwright base image, no duplicate browser install: `3.56GB`
- `python:3.12-slim-bookworm` with full Chromium install: `1.78GB`
- `python:3.12-slim-bookworm` keeping only Chromium headless shell: `1.22GB`

The `playwright install --with-deps --only-shell chromium` path was tested and
would also land around `1.23GB`, but it segfaulted during local Docker rendering.
Installing full Chromium first and then deleting the unused full browser payload
keeps the smaller runtime image while preserving the working dependency set.
Multi-stage and single-stage builds measured the same final size for this setup,
so the Dockerfile stays single-stage.

Build:

```bash
make docker-build
```

Direct local smoke test:

```bash
make docker-smoke
```

Lambda Runtime Interface Emulator test, after downloading `aws-lambda-rie`:

```bash
docker run --rm -p 9000:8080 \
  --entrypoint /aws-lambda/aws-lambda-rie \
  -v "$PWD/.aws-lambda-rie:/aws-lambda:ro" \
  banner-generator-lambda \
  python -m awslambdaric banner_generator.lambda_handler.handler

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d @examples/lambda-content-event.json
```

## Validation Before Publishing

1. `make test`
2. `make lint`
3. `make render-content-examples`
4. `make render-content-variants`
5. `make render-certificate-example`
6. Build Docker image.
7. Invoke Docker image locally with PNG, JPEG, and PDF events.
8. Push to ECR only after local Docker rendering works.
