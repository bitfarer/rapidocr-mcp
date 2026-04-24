FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    RAPIDOCR_LOG_LEVEL=INFO

EXPOSE 8080 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["python", "-m", "rapidocr_mcp", "--mode", "fastapi"]
