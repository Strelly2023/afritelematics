from uuid import uuid4


class StripeProvider:
    name = "stripe"

    def charge(self, amount, currency, token, metadata=None):
        return {
            "status": "captured",
            "provider": self.name,
            "reference": f"stripe_mock_{uuid4().hex}",
            "amount": str(amount),
            "currency": currency,
            "metadata": metadata or {},
        }
