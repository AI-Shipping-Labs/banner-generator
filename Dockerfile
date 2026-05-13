FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

WORKDIR /var/task

ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY pyproject.toml README.md ./
COPY banner_generator ./banner_generator
COPY scripts ./scripts

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir awslambdaric . \
    && python -m playwright install chromium

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["banner_generator.lambda_handler.handler"]
