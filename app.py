import os
import uuid
from pathlib import Path

import click
from flask import Flask, abort, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)
SCHEMA_FILE = Path(__file__).parent / "db" / "schema.sql"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.errorhandler(HTTPException)
def handle_http_exception(exc):
    return {"error": exc.description}, exc.code


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


def _serialize_payment(payment):
    return {
        "id": str(payment.id),
        "cart_id": str(payment.cart_id),
        "user_id": str(payment.user_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "provider_reference": payment.provider_reference,
        "failure_reason": payment.failure_reason,
    }


@app.post("/api/payments/process")
def create_payment():
    """Charge a cart's default payment method for its current total."""
    from services.payment import (
        CartEmpty,
        CartNotActive,
        CartNotFound,
        NoDefaultPaymentMethod,
        PaymentService,
    )

    body = request.get_json(silent=True) or {}
    cart_id_raw = body.get("cart_id")
    if not cart_id_raw:
        abort(400, description="cart_id is required")
    try:
        cart_id = uuid.UUID(cart_id_raw)
    except (ValueError, AttributeError, TypeError):
        abort(400, description="cart_id must be a valid UUID")

    try:
        payment = PaymentService().process_payment(cart_id)
    except CartNotFound:
        abort(404, description="cart not found")
    except CartNotActive as exc:
        abort(409, description=str(exc))
    except CartEmpty:
        abort(422, description="cart is empty")
    except NoDefaultPaymentMethod:
        abort(422, description="no default payment method")

    status_code = 201 if payment.status == "succeeded" else 402
    return _serialize_payment(payment), status_code


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
