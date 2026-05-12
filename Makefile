.PHONY: setup test lint render-example install-browser

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
