FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py ./

EXPOSE 5000

CMD ["uv", "run", "flask", "--app", "app", "run", "--host", "0.0.0.0"]
