from app import db
from models import Cart


class CartRepository:
    def get_for_update(self, cart_id):
        """Fetch a cart with a row lock (SELECT ... FOR UPDATE).

        Use this before starting a payment, so a concurrent payment
        attempt on the same cart blocks until the first one commits
        instead of racing it.
        """
        return db.session.query(Cart).filter_by(id=cart_id).with_for_update().first()
