# syntax=docker/dockerfile:1

# Build stage: resolve dependencies from the committed uv.lock into a virtualenv
# that carries its own copy of the interpreter, so the runtime stage needs no uv.
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY uv.lock pyproject.toml .python-version ./
RUN uv sync --frozen --no-dev

# Runtime stage: non-root, production mode, Waitress.
FROM python:3.12-slim
ENV APP_ENV=production \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY cetak_kira.py cli.py ./
COPY modules/ modules/
COPY sources/ sources/
COPY static/ static/
COPY templates/ templates/

# SECRET_KEY is deliberately not set here. sources/config.py refuses to start in
# production while the placeholder key is in place, so it must be supplied at
# runtime: docker run -e SECRET_KEY=... (never a value baked into the image).
USER 1000:1000
EXPOSE 5000
CMD ["python", "cetak_kira.py"]
