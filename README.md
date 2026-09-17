# test-payment-endpoint

## Demo

<video src="docs/demo.mov" controls></video>

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
- `GET /api/carts/<uuid:cart_id>/payment-preview` — builds (without charging) the object a future payment for this cart would use: items, total, currency, user, and default payment method. 404 if the cart doesn't exist.
- `POST /api/payments/process` — charges a cart's default payment method for its current total. Takes `{"cart_id": "<uuid>"}` in the JSON body. Retries a declined charge up to `PAYMENT_CHARGE_MAX_ATTEMPTS` times before giving up.
  - `201` charge succeeded
  - `402` charge declined after all retries
  - `400` missing/malformed `cart_id`
  - `404` cart not found
  - `409` cart isn't `active` (already checked out or abandoned)
  - `422` cart is empty, or the user has no default payment method

## Configuration

- `PAYMENT_CHARGE_MAX_ATTEMPTS` (default `3`) — how many times `PaymentService` retries a declined charge against the payment provider before recording the payment as `failed`.

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
