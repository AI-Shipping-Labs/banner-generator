.PHONY: setup install-browser docker-build docker-smoke docker-benchmark-certificates

COUNT ?= 10

setup:
	uv sync --dev

install-browser:
	uv run playwright install chromium

docker-build:
	docker build -t banner-generator-lambda .

docker-smoke:
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/aisl/lambda-content-event.json
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/aisl/lambda-content-event-jpeg.json
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/invoke_lambda_event.py /tmp/examples/aisl/lambda-ai-hero-certificate.json

docker-benchmark-certificates:
	docker run --rm --entrypoint python -v "$$PWD/examples:/tmp/examples:ro" banner-generator-lambda scripts/benchmark_lambda_event.py /tmp/examples/aisl/lambda-ai-hero-certificate.json --count $(COUNT) --warmup 1 --unique-certificates
