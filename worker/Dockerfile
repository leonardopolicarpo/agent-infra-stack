FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

COPY worker/ ./worker/
COPY shared/ ./shared/

RUN pip install uv && uv sync --no-dev
ENV PYTHONPATH=/app

CMD [".venv/bin/celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]