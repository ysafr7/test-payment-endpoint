from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True)


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.Text, nullable=False)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey("carts.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)


class UserPaymentMethod(db.Model):
    __tablename__ = "user_payment_methods"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    provider_token = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, nullable=False)


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey("carts.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.CHAR(3), nullable=False)
    status = db.Column(db.Text, nullable=False, default="pending")
    provider_reference = db.Column(db.Text)
    failure_reason = db.Column(db.Text)
