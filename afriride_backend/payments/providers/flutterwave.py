from uuid import uuid4


class FlutterwaveProvider:
    name = "flutterwave"

    def charge(self, amount, currency, token, metadata=None):
        return {
            "status": "captured",
            "provider": self.name,
            "reference": f"flutterwave_mock_{uuid4().hex}",
            "amount": str(amount),
            "currency": currency,
            "metadata": metadata or {},
        }
