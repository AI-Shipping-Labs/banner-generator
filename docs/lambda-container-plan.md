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

## Docker Steps

1. Base image: Playwright Python image with Chromium system dependencies.
2. Install the package and `awslambdaric`.
3. Set the handler as the container command.
4. Test locally by importing the handler in Docker.
5. For Lambda-style HTTP invocation, run the image with the Lambda Runtime Interface
   Emulator mounted as the entrypoint.
6. Invoke with a sample content-card event and confirm the rendered image is valid.

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
4. `make render-certificate-example`
5. Build Docker image.
6. Invoke Docker image locally with one PNG banner event.
7. Invoke Docker image locally with one PDF certificate event.
8. Push to ECR only after local Docker rendering works.
