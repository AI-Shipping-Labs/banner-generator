# Lambda TODO

## Goal

Package the same renderer for two execution paths:

- CLI for local development and one-off renders.
- Lambda container for programmatic banner/certificate rendering.

## Checklist

1. Add a Lambda handler that converts an event into a `RenderSpec`.
2. Return base64-encoded render bytes when no publishing target is provided.
3. Optionally upload to S3 when the event includes an `s3` target.
4. Add certificate QR-code generation with template-level defaults for style/size.
5. Add sample events for:
   - content banner PNG
   - content banner JPEG
   - AI Hero certificate PDF
6. Add tests for event parsing and response shape.
7. Add Dockerfile with Chromium/Playwright support.
8. Add local Docker invocation docs.
9. Verify:
   - `make test`
   - `make lint`
   - `make render-content-examples`
   - `make render-certificate-example`
   - package build contains templates/assets
   - Docker image builds
   - Docker image can render a sample event locally
