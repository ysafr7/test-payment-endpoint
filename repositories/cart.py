from app import db
from models import Cart, CartItem


class CartRepository:
    def get(self, cart_id):
        return db.session.get(Cart, cart_id)

    def get_for_update(self, cart_id):
        """Fetch a cart with a row lock (SELECT ... FOR UPDATE).

        Use this before starting a payment, so a concurrent payment
        attempt on the same cart blocks until the first one commits
        instead of racing it.
        """
        return db.session.query(Cart).filter_by(id=cart_id).with_for_update().first()

    def get_items(self, cart_id):
        return db.session.query(CartItem).filter_by(cart_id=cart_id).all()

    def mark_checked_out(self, cart):
        cart.status = "checked_out"
        db.session.flush()
        return cart
