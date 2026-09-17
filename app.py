import os
from pathlib import Path

import click
from flask import Flask, abort
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)
SCHEMA_FILE = Path(__file__).parent / "db" / "schema.sql"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.get("/health")
def index():
    return {"status": "ok"}


@app.get("/api/carts/<uuid:cart_id>/payment-preview")
def payment_preview(cart_id):
    """Build (without charging) the object a future payment would use."""
    from repositories.cart import CartRepository
    from services.payment import PaymentService

    cart = CartRepository().get(cart_id)
    if cart is None:
        abort(404, description="cart not found")

    data = PaymentService().build_payment_data(cart)

    return {
        "cart_id": str(cart.id),
        "cart_status": cart.status,
        "user": {
            "id": str(data.user.id),
            "email": data.user.email,
            "name": data.user.name,
        }
        if data.user
        else None,
        "items": [
            {
                "cart_item_id": str(item.id),
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
            }
            for item in data.items
        ],
        "amount": str(data.amount),
        "currency": data.currency,
        "payment_method": {
            "id": str(data.payment_method.id),
            "last_four": data.payment_method.last_four,
            "is_default": data.payment_method.is_default,
        }
        if data.payment_method
        else None,
    }


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
