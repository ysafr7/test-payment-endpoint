def calculate_total(cart_items):
    """Stand-in for the existing payment total calculation service."""
    return sum(item.unit_price * item.quantity for item in cart_items)
