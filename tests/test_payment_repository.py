from unittest.mock import patch

import pytest

from models import Payment
from repositories.payment import PaymentRepository


@pytest.fixture
def repo():
    return PaymentRepository()


@patch("repositories.payment.db")
def test_create_adds_payment_and_flushes(mock_db, repo):
    payment = repo.create(cart_id="cart-1", user_id="user-1", amount=10, currency="USD")

    mock_db.session.add.assert_called_once_with(payment)
    mock_db.session.flush.assert_called_once()
    assert payment.cart_id == "cart-1"
    assert payment.user_id == "user-1"
    assert payment.amount == 10
    assert payment.currency == "USD"
    assert payment.status == "pending"


@patch("repositories.payment.db")
def test_create_accepts_explicit_status(mock_db, repo):
    payment = repo.create(cart_id="cart-1", user_id="user-1", amount=10, currency="USD", status="failed")

    assert payment.status == "failed"


@patch("repositories.payment.db")
def test_get_delegates_to_session_get(mock_db, repo):
    mock_db.session.get.return_value = "a-payment"

    result = repo.get("payment-1")

    mock_db.session.get.assert_called_once_with(Payment, "payment-1")
    assert result == "a-payment"


@patch("repositories.payment.db")
def test_list_for_cart_filters_by_cart_id(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.all.return_value = ["payment-a", "payment-b"]

    result = repo.list_for_cart("cart-1")

    mock_db.session.query.assert_called_once_with(Payment)
    query.filter_by.assert_called_once_with(cart_id="cart-1")
    assert result == ["payment-a", "payment-b"]


@patch("repositories.payment.db")
def test_update_sets_fields_and_flushes(mock_db, repo):
    payment = Payment(cart_id="cart-1", user_id="user-1", amount=10, currency="USD")

    result = repo.update(payment, status="succeeded", provider_reference="ch_123")

    assert payment.status == "succeeded"
    assert payment.provider_reference == "ch_123"
    mock_db.session.flush.assert_called_once()
    assert result is payment


@patch("repositories.payment.db")
def test_delete_removes_existing_payment(mock_db, repo):
    payment = Payment(cart_id="cart-1", user_id="user-1", amount=10, currency="USD")
    mock_db.session.get.return_value = payment

    result = repo.delete("payment-1")

    mock_db.session.get.assert_called_once_with(Payment, "payment-1")
    mock_db.session.delete.assert_called_once_with(payment)
    mock_db.session.flush.assert_called_once()
    assert result is True


@patch("repositories.payment.db")
def test_delete_returns_false_when_not_found(mock_db, repo):
    mock_db.session.get.return_value = None

    result = repo.delete("missing-id")

    mock_db.session.delete.assert_not_called()
    assert result is False
