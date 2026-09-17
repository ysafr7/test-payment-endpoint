from dataclasses import dataclass

from app import db
from models import User
from repositories.cart import CartRepository
from repositories.payment import PaymentRepository
from repositories.user_payment_method import UserPaymentMethodRepository
from mock_services.payment_provider import ChargeDeclined, charge
from mock_services.payment_total import calculate_total


class CartNotFound(Exception):
    pass


class CartNotActive(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"cart is {status}, not active")


class CartEmpty(Exception):
    pass


class NoDefaultPaymentMethod(Exception):
    pass


@dataclass
class PaymentData:
    cart: object
    items: list
    user: object
    payment_method: object
    amount: object
    currency: str


class PaymentService:
    def __init__(self):
        self.cart_repo = CartRepository()
        self.payment_repo = PaymentRepository()
        self.payment_method_repo = UserPaymentMethodRepository()

    def build_payment_data(self, cart):
        """Collect everything needed to charge a cart: its items, the
        owning user, their default payment method, and the total.
        """
        items = self.cart_repo.get_items(cart.id)
        user = db.session.get(User, cart.user_id)
        payment_method = self.payment_method_repo.get_default(cart.user_id)
        amount = calculate_total(items)
        return PaymentData(
            cart=cart,
            items=items,
            user=user,
            payment_method=payment_method,
            amount=amount,
            currency="USD",
        )

    def process_payment(self, cart_id):
        """Charge a cart's default payment method and record the result.

        Locks the cart row for the duration of the transaction so a
        concurrent attempt on the same cart can't race this one.
        """
        cart = self.cart_repo.get_for_update(cart_id)
        if cart is None:
            raise CartNotFound(cart_id)
        if cart.status != "active":
            raise CartNotActive(cart.status)

        data = self.build_payment_data(cart)
        if not data.items:
            raise CartEmpty(cart_id)
        if data.payment_method is None:
            raise NoDefaultPaymentMethod(cart.user_id)

        payment = self.payment_repo.create(
            cart_id=cart.id,
            user_id=cart.user_id,
            amount=data.amount,
            currency=data.currency,
        )

        try:
            reference = charge(data.payment_method.provider_token, data.amount, data.currency)
        except ChargeDeclined as exc:
            self.payment_repo.update(payment, status="failed", failure_reason=str(exc))
            db.session.commit()
            return payment

        self.payment_repo.update(payment, status="succeeded", provider_reference=reference)
        cart.status = "checked_out"
        db.session.commit()
        return payment
