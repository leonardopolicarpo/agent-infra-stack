FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
COPY api/ ./api/
COPY shared/ ./shared/

RUN pip install uv && uv sync --no-dev

ENV PYTHONPATH=/app

RUN useradd -m apiuser && chown -R apiuser:apiuser /app
USER apiuser

CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]