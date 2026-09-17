FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY app.py models.py ./
COPY db/ ./db/
COPY migrations/ ./migrations/
COPY repositories/ ./repositories/
COPY services/ ./services/
COPY mock_services/ ./mock_services/

EXPOSE 5000

CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0"]
