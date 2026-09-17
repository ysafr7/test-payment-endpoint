import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest

from app import app as flask_app
from mock_services.payment_provider import ChargeDeclined
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


def _active_cart_with_items(cart_id, user_id, mock_cart_db):
    cart = Cart(id=cart_id, user_id=user_id, status="active")
    mock_cart_db.session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = (
        cart
    )
    items = [CartItem(id=uuid.uuid4(), cart_id=cart_id, quantity=2, unit_price=Decimal("12.50"))]
    mock_cart_db.session.query.return_value.filter_by.return_value.all.return_value = items
    return cart, items


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_create_payment_succeeds(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, client
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)

    mock_service_db.session.get.return_value = User(id=user_id, email="a@x.com", name="Alice")

    payment_method = UserPaymentMethod(
        id=uuid.uuid4(), user_id=user_id, provider_token="tok_x", is_default=True
    )
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = (
        payment_method
    )

    payment_id = uuid.uuid4()
    mock_payment_db.session.add.side_effect = lambda payment: setattr(payment, "id", payment_id)
    mock_charge.return_value = "ch_test123"

    response = client.post("/api/payments/process", json={"cart_id": str(cart_id)})

    assert response.status_code == 201
    assert response.get_json() == {
        "id": str(payment_id),
        "cart_id": str(cart_id),
        "user_id": str(user_id),
        "amount": "25.00",
        "currency": "USD",
        "status": "succeeded",
        "provider_reference": "ch_test123",
        "failure_reason": None,
    }
    assert cart.status == "checked_out"


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_create_payment_declined_returns_402(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, client
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)

    mock_service_db.session.get.return_value = User(id=user_id, email="a@x.com", name="Alice")

    payment_method = UserPaymentMethod(
        id=uuid.uuid4(), user_id=user_id, provider_token="tok_decline", is_default=True
    )
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = (
        payment_method
    )

    payment_id = uuid.uuid4()
    mock_payment_db.session.add.side_effect = lambda payment: setattr(payment, "id", payment_id)
    mock_charge.side_effect = ChargeDeclined("card declined")

    response = client.post("/api/payments/process", json={"cart_id": str(cart_id)})

    assert response.status_code == 402
    body = response.get_json()
    assert body["status"] == "failed"
    assert body["failure_reason"] == "card declined"
    assert body["provider_reference"] is None
    assert cart.status == "active"


def test_create_payment_400_when_cart_id_missing(client):
    response = client.post("/api/payments/process", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "cart_id is required"}


def test_create_payment_400_when_cart_id_malformed(client):
    response = client.post("/api/payments/process", json={"cart_id": "not-a-uuid"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "cart_id must be a valid UUID"}


@patch("repositories.cart.db")
def test_create_payment_404_when_cart_missing(mock_cart_db, client):
    mock_cart_db.session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = (
        None
    )

    response = client.post("/api/payments/process", json={"cart_id": str(uuid.uuid4())})

    assert response.status_code == 404
    assert response.get_json() == {"error": "cart not found"}


@patch("repositories.cart.db")
def test_create_payment_409_when_cart_not_active(mock_cart_db, client):
    cart = Cart(id=uuid.uuid4(), user_id=uuid.uuid4(), status="checked_out")
    mock_cart_db.session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = (
        cart
    )

    response = client.post("/api/payments/process", json={"cart_id": str(cart.id)})

    assert response.status_code == 409
    assert response.get_json() == {"error": "cart is checked_out, not active"}


@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_create_payment_422_when_cart_empty(mock_cart_db, mock_pm_db, mock_service_db, client):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart = Cart(id=cart_id, user_id=user_id, status="active")
    mock_cart_db.session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = (
        cart
    )
    mock_cart_db.session.query.return_value.filter_by.return_value.all.return_value = []
    mock_service_db.session.get.return_value = User(id=user_id, email="a@x.com", name="Alice")
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = None

    response = client.post("/api/payments/process", json={"cart_id": str(cart_id)})

    assert response.status_code == 422
    assert response.get_json() == {"error": "cart is empty"}


@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_create_payment_422_when_no_default_payment_method(
    mock_cart_db, mock_pm_db, mock_service_db, client
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    _cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    mock_service_db.session.get.return_value = User(id=user_id, email="a@x.com", name="Alice")
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = None

    response = client.post("/api/payments/process", json={"cart_id": str(cart_id)})

    assert response.status_code == 422
    assert response.get_json() == {"error": "no default payment method"}
