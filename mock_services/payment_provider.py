import uuid


class ChargeDeclined(Exception):
    pass


def charge(provider_token, amount, currency):
    """Stand-in for the real payment provider client.

    Declines when given the magic token 'tok_decline', so the failure
    path can be exercised without a real provider.
    """
    if provider_token == "tok_decline":
        raise ChargeDeclined("card declined")
    return f"ch_{uuid.uuid4().hex}"
