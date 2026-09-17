from app import db
from models import Payment


class PaymentRepository:
    """Data access for the payments table.

    Methods flush (so generated fields like id/status defaults are
    available) but don't commit — the caller controls the transaction
    boundary.
    """

    def create(self, *, cart_id, user_id, amount, currency, status="pending"):
        payment = Payment(
            cart_id=cart_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=status,
        )
        db.session.add(payment)
        db.session.flush()
        return payment

    def get(self, payment_id):
        return db.session.get(Payment, payment_id)

    def list_for_cart(self, cart_id):
        return db.session.query(Payment).filter_by(cart_id=cart_id).all()

    def update(self, payment, **fields):
        for key, value in fields.items():
            setattr(payment, key, value)
        db.session.flush()
        return payment

    def delete(self, payment_id):
        payment = db.session.get(Payment, payment_id)
        if payment is None:
            return False
        db.session.delete(payment)
        db.session.flush()
        return True
