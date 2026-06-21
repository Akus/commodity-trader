# syntax=docker/dockerfile:1
# Multi-stage build, runs as non-root. Built with Podman locally and in CI.

FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Non-root runtime user.
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /opt/venv /opt/venv
COPY app ./app

USER appuser
EXPOSE 8080

# Honour container CPU limits when sizing the worker count is left to operators;
# a single uvicorn worker keeps Prometheus counters consistent per replica.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
