# test-payment-endpoint

## Install

    uv sync

## Run

    uv run python app.py

## Run with Docker (app + Postgres)

    cp .env.example .env
    docker compose up --build

## Endpoints

App runs on `localhost:5000` (`uv run`) or `localhost:4000` (Docker).

- `GET /health` — app liveness check

## Database CLI

Requires Postgres to be running — use Docker:

    docker compose up -d --build

- `docker compose exec app flask --app app db-setup` — applies `schema.sql` to an empty database (tables + sample data).
- `docker compose exec app flask --app app db-reset` — drops and recreates the `public` schema, then applies `schema.sql`.
