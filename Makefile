.PHONY: setup test lint render-example render-content-examples render-certificate-example docker-build docker-smoke install-browser

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
	uv run banner-generator render examples/content-workshop.json
	uv run banner-generator render examples/content-blog.json
	uv run banner-generator render examples/content-course.json
	uv run banner-generator render examples/content-project.json
	uv run banner-generator render examples/content-resource.json
	uv run banner-generator render examples/content-long-title.json

render-certificate-example:
	uv run banner-generator render examples/ai-hero-certificate.json

docker-build:
	docker build -t banner-generator-lambda .

docker-smoke:
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/lambda-content-event.json
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/lambda-ai-hero-certificate.json
