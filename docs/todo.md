# TODO

## Phase 1: Local Templates

1. Keep certificate rendering working as `html + css + assets`.
2. Add AI Shipping Labs banner templates for core content types:
   - events
   - workshops
   - blog posts / articles
   - courses
   - projects
   - downloads / resources
   - certificates
3. Use real-ish AI Shipping Labs content fields and long-title examples.
4. Render every example locally and visually inspect the generated images.
5. Add a JPEG render check alongside PNG and PDF examples.
6. Keep all templates packageable: HTML, CSS, and assets must be included in the wheel.

## Phase 2: Render Contract

1. Keep the CLI contract stable for local rendering.
2. Define a Lambda-compatible JSON event shape.
3. Reuse the same renderer from CLI and Lambda.
4. Add tests for asset resolution and render-spec loading.
5. Add certificate QR-code generation so callers provide a verification URL or
   certificate ID, while QR style/defaults live with the certificate template.

## Phase 3: Lambda Container

1. Add a Dockerfile with Python, package dependencies, and Playwright Chromium.
2. Add a Lambda handler entrypoint.
3. Support local Docker invocation.
4. Decide the output boundary:
   - return rendered bytes for local/dev smoke tests
   - write to S3 for production jobs
5. Add documentation for building, running, and publishing the Lambda container.

## Phase 4: Publishing

1. Push the image to ECR.
2. Create or update the Lambda function.
3. Test a real invocation that renders a banner.
4. Wire future publishing to S3/CDN without coupling it to template rendering.
