import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest

from mock_services.payment_provider import ChargeDeclined
from models import Cart, CartItem, User, UserPaymentMethod
from services.payment import PaymentService


@pytest.fixture
def service():
    return PaymentService()


def _active_cart_with_items(cart_id, user_id, mock_cart_db):
    cart = Cart(id=cart_id, user_id=user_id, status="active")
    mock_cart_db.session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = (
        cart
    )
    items = [CartItem(id=uuid.uuid4(), cart_id=cart_id, quantity=1, unit_price=Decimal("10.00"))]
    mock_cart_db.session.query.return_value.filter_by.return_value.all.return_value = items
    return cart, items


def _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id):
    mock_service_db.session.get.return_value = User(id=user_id, email="a@x.com", name="Alice")
    payment_method = UserPaymentMethod(
        id=uuid.uuid4(), user_id=user_id, provider_token="tok_x", is_default=True
    )
    mock_pm_db.session.query.return_value.filter_by.return_value.first.return_value = (
        payment_method
    )
    return payment_method


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_succeeds_on_first_attempt(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, service
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id)
    mock_charge.return_value = "ch_ref"

    payment = service.process_payment(cart_id)

    assert mock_charge.call_count == 1
    assert payment.status == "succeeded"
    assert payment.provider_reference == "ch_ref"
    assert cart.status == "checked_out"


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_recovers_after_retrying(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, service
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id)
    mock_charge.side_effect = [ChargeDeclined("try again"), ChargeDeclined("try again"), "ch_ref"]

    payment = service.process_payment(cart_id)

    assert mock_charge.call_count == 3
    assert payment.status == "succeeded"
    assert payment.provider_reference == "ch_ref"
    assert cart.status == "checked_out"


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_exhausts_all_attempts_then_fails(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, service
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id)
    mock_charge.side_effect = ChargeDeclined("card declined")

    payment = service.process_payment(cart_id)

    import services.payment as payment_module

    assert mock_charge.call_count == payment_module.MAX_CHARGE_ATTEMPTS
    assert payment.status == "failed"
    assert payment.failure_reason == "card declined"
    assert cart.status == "active"


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_respects_non_default_attempt_count(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, service
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    _cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id)
    mock_charge.side_effect = ChargeDeclined("card declined")

    with patch("services.payment.MAX_CHARGE_ATTEMPTS", 1):
        payment = service.process_payment(cart_id)

    assert mock_charge.call_count == 1
    assert payment.status == "failed"


@patch("services.payment.charge")
@patch("repositories.payment.db")
@patch("services.payment.db")
@patch("repositories.user_payment_method.db")
@patch("repositories.cart.db")
def test_unexpected_exception_is_not_retried(
    mock_cart_db, mock_pm_db, mock_service_db, mock_payment_db, mock_charge, service
):
    cart_id = uuid.uuid4()
    user_id = uuid.uuid4()
    _cart, _items = _active_cart_with_items(cart_id, user_id, mock_cart_db)
    _setup_user_and_payment_method(mock_service_db, mock_pm_db, user_id)
    mock_charge.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        service.process_payment(cart_id)

    assert mock_charge.call_count == 1
