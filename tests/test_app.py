import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest

from app import app as flask_app
from models import Cart, CartItem, User, UserPaymentMethod


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_payment_preview_returns_preview_object(
    mock_cart_db, mock_pm_db, mock_service_db, client
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart = Cart(id=cart_id, user_id=user_id, status="active")
    mock_cart_db.session.get.return_value = cart

    items = [
        CartItem(id=uuid.uuid4(), cart_id=cart_id, quantity=2, unit_price=Decimal("12.50")),
        CartItem(id=uuid.uuid4(), cart_id=cart_id, quantity=1, unit_price=Decimal("45.00")),
    ]
    mock_cart_db.session.query.return_value.filter_by.return_value.all.return_value = items

    user = User(id=user_id, email="alice@example.com", name="Alice")
    mock_service_db.session.get.return_value = user

    payment_method = UserPaymentMethod(
        id=uuid.uuid4(),
        user_id=user_id,
        provider_token="tok_x",
        last_four="4242",
        is_default=True,
    )
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = (
        payment_method
    )

    response = client.get(f"/api/carts/{cart_id}/payment-preview")

    assert response.status_code == 200
    body = response.get_json()
    assert body == {
        "cart_id": str(cart_id),
        "cart_status": "active",
        "user": {"id": str(user_id), "email": "alice@example.com", "name": "Alice"},
        "items": [
            {"cart_item_id": str(items[0].id), "quantity": 2, "unit_price": "12.50"},
            {"cart_item_id": str(items[1].id), "quantity": 1, "unit_price": "45.00"},
        ],
        "amount": "70.00",
        "currency": "USD",
        "payment_method": {
            "id": str(payment_method.id),
            "last_four": "4242",
            "is_default": True,
        },
    }


@patch("repositories.cart.db")
def test_payment_preview_404_when_cart_missing(mock_cart_db, client):
    mock_cart_db.session.get.return_value = None

    response = client.get(f"/api/carts/{uuid.uuid4()}/payment-preview")

    assert response.status_code == 404
