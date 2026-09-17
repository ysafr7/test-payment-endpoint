from unittest.mock import patch

import pytest

from models import Cart, CartItem
from repositories.cart import CartRepository


@pytest.fixture
def repo():
    return CartRepository()


@patch("repositories.cart.db")
def test_get_for_update_locks_and_returns_cart(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.with_for_update.return_value.first.return_value = "a-cart"

    result = repo.get_for_update("cart-1")

    mock_db.session.query.assert_called_once_with(Cart)
    query.filter_by.assert_called_once_with(id="cart-1")
    assert result == "a-cart"


@patch("repositories.cart.db")
def test_get_for_update_returns_none_when_missing(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.with_for_update.return_value.first.return_value = None

    result = repo.get_for_update("missing-id")

    assert result is None


@patch("repositories.cart.db")
def test_get_items_filters_by_cart_id(mock_db, repo):
    query = mock_db.session.query.return_value
    query.filter_by.return_value.all.return_value = ["item-a", "item-b"]

    result = repo.get_items("cart-1")

    mock_db.session.query.assert_called_once_with(CartItem)
    query.filter_by.assert_called_once_with(cart_id="cart-1")
    assert result == ["item-a", "item-b"]
