.PHONY: setup test lint render-example render-content-examples render-dtc-examples render-content-variants render-content-matrix render-source-banners render-certificate-example docker-build docker-smoke docker-benchmark-certificates install-browser

COUNT ?= 10
MAX_KB ?= 100
TEMPLATE ?=

setup:
	uv sync --dev

install-browser:
	uv run playwright install chromium

test:
	uv run pytest

lint:
	uv run ruff check .

render-example:
	uv run banner-generator render examples/workshop.json --output output/workshop.png

render-content-examples:
	uv run banner-generator render examples/content-event.json
	uv run banner-generator render examples/content-event-jpeg.json
	uv run banner-generator render examples/content-workshop.json
	uv run banner-generator render examples/content-blog.json
	uv run banner-generator render examples/content-course.json
	uv run banner-generator render examples/content-project.json
	uv run banner-generator render examples/content-resource.json
	uv run banner-generator render examples/content-long-title.json

render-dtc-examples:
	uv run banner-generator render examples/dtc-event-webinar-luma.json
	uv run banner-generator render examples/dtc-event-webinar-og.json
	uv run banner-generator render examples/dtc-event-webinar-youtube.json
	uv run banner-generator render examples/dtc-event-podcast-luma.json
	uv run banner-generator render examples/dtc-event-podcast-og.json
	uv run banner-generator render examples/dtc-event-podcast-youtube.json
	uv run banner-generator render examples/dtc-event-workshop-luma.json
	uv run banner-generator render examples/dtc-event-workshop-og.json
	uv run banner-generator render examples/dtc-event-workshop-youtube.json
	uv run banner-generator render examples/dtc-article-preview.json
	uv run banner-generator render examples/dtc-book-preview.json
	uv run banner-generator render examples/dtc-course-preview.json

render-content-variants:
	uv run banner-generator render examples/content-variants/blueprint-path-course.json
	uv run banner-generator render examples/content-variants/editorial-pulse-blog.json
	uv run banner-generator render examples/content-variants/event-stage-live.json
	uv run banner-generator render examples/content-variants/event-series-long-title.json
	uv run banner-generator render examples/content-event-series.json
	uv run banner-generator render examples/content-variants/project-dossier-showcase.json
	uv run banner-generator render examples/content-variants/resource-stack-download.json

render-content-matrix:
	uv run python scripts/render_content_variant_matrix.py

render-source-banners:
	uv run python scripts/generate_source_banners.py $(if $(TEMPLATE),--template $(TEMPLATE),) --max-kb $(MAX_KB)

render-certificate-example:
	uv run banner-generator render examples/ai-hero-certificate.json

docker-build:
	docker build -t banner-generator-lambda .

docker-smoke:
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/lambda-content-event.json
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/lambda-content-event-jpeg.json
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/lambda-ai-hero-certificate.json

docker-benchmark-certificates:
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/benchmark_lambda_event.py /tmp/examples/lambda-ai-hero-certificate.json --count $(COUNT) --warmup 1 --unique-certificates
