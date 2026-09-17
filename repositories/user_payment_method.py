from app import db
from models import UserPaymentMethod


class UserPaymentMethodRepository:
    def get_default(self, user_id):
        return (
            db.session.query(UserPaymentMethod)
            .filter_by(user_id=user_id, is_default=True)
            .first()
        )
