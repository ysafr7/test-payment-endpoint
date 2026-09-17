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
