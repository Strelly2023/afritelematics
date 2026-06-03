from uuid import uuid4


class PaymentGateway:
    """Mock gateway for controlled testing.

    This class is intentionally not a production payment processor. It preserves
    the service boundary while keeping field-test capture deterministic.
    """

    provider = "mock"

    def authorize(self, rider, amount, currency="AUD"):
        return {
            "status": "authorized",
            "provider": self.provider,
            "provider_reference": f"mock_auth_{uuid4().hex}",
            "currency": currency,
            "amount": amount,
        }

    def capture(self, provider_reference):
        return {
            "status": "captured",
            "provider_reference": provider_reference,
        }
