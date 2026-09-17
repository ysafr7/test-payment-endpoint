import os
from pathlib import Path

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)
SCHEMA_FILE = Path(__file__).parent / "db" / "schema.sql"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

db = SQLAlchemy(app)


@app.get("/health")
def index():
    return {"status": "ok"}


def _apply_schema():
    schema_sql = SCHEMA_FILE.read_text()
    with db.engine.begin() as conn:
        conn.exec_driver_sql(schema_sql)


@app.cli.command("db-setup")
def db_setup():
    """Apply schema.sql to an empty database."""
    _apply_schema()
    click.echo("Schema applied.")


@app.cli.command("db-reset")
def db_reset():
    """Drop all tables and recreate the schema from schema.sql."""
    with db.engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    _apply_schema()
    click.echo("Database reset and schema applied.")


if __name__ == "__main__":
    app.run(debug=True)
