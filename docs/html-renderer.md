# Private HTML renderer

Deploy the Banner Generator image with command override
`banner_generator.html_renderer_handler.handler`. Invoke using the IAM Lambda
Invoke API or an SQS event source; do not create a public Function URL.

The caller stores self-contained UTF-8 HTML (maximum 8 MiB) in private S3,
then submits:

```json
{
  "schema": "html-renderer.job.v1",
  "job_id": "stable-card-job-hash",
  "input": {"bucket": "private-files", "key": "input.html"},
  "output": {"bucket": "private-files", "key": "banner.png"},
  "format": "png",
  "viewport": {"width": 2400, "height": 1350}
}
```

Supported formats are PNG, JPEG and PDF. Each viewport dimension is 1-4096.
JPEG accepts `image.quality` (1-100). PDF accepts `pdf.page_format` (A4/Letter)
or both explicit CSS width and height, plus margins and print_background.

JavaScript, external HTTP and local file requests are blocked. Embed required
images and fonts as data URLs. Fonts and images finish loading before capture.

Use stable job IDs and immutable output keys. Output carries render-job-id and
sha256 metadata. Existing output from the same job is reused; another job cannot
overwrite it. Concurrent writes use conditional S3 PutObject. The execution role
needs GetObject on allowed inputs and GetObject/PutObject on allowed outputs;
no ListBucket permission is required.

Success returns html-renderer.completed.v1 with job_id, input/output, format,
content_type, size_bytes, checksum and reused. Failure returns
html-renderer.failed.v1 with error type/message. SQS uses partial batch failures;
an optional HTML_RENDERER_COMPLETION_QUEUE_URL receives successful events.

The banner-specific compatibility handler remains unchanged. This private
entrypoint is additive; it does not replace or disable existing deployments.
