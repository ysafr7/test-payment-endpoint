from unittest.mock import patch

import pytest

from models import UserPaymentMethod
from repositories.user_payment_method import UserPaymentMethodRepository


@pytest.fixture
def repo():
    return UserPaymentMethodRepository()


@patch("repositories.user_payment_method.db")
def test_get_default_filters_by_user_and_default_flag(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.first.return_value = "a-payment-method"

    result = repo.get_default("user-1")

    mock_db.session.query.assert_called_once_with(UserPaymentMethod)
    query.filter_by.assert_called_once_with(user_id="user-1", is_default=True)
    assert result == "a-payment-method"


@patch("repositories.user_payment_method.db")
def test_get_default_returns_none_when_missing(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.first.return_value = None

    result = repo.get_default("user-without-method")

    assert result is None
