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

## Migrations

`db/schema.sql` (via `db-setup`/`db-reset` above) provides the base tables. Everything built on top of it (e.g. `payments`) is a Flask-Migrate (Alembic) migration in `migrations/versions/`.

Apply migrations:

    docker compose exec app flask db upgrade

Revert the last migration:

    docker compose exec app flask db downgrade -1

Create a new migration:

    docker compose exec app flask db revision -m "description"

## Tests

    uv run pytest
