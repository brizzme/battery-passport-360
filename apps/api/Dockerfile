FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /bin/uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY app app
# HOST=:: for IPv6 private networks (Railway); defaults suit Docker Compose.
CMD ["sh", "-c", "exec .venv/bin/uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
