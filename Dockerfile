FROM python:3.12-slim-bookworm

WORKDIR /var/task

ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY pyproject.toml README.md ./
COPY banner_generator ./banner_generator
COPY scripts ./scripts

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir awslambdaric . \
    && python -m playwright install --with-deps chromium \
    && rm -rf /ms-playwright/chromium-* /ms-playwright/ffmpeg-* \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["banner_generator.lambda_handler.handler"]
