from uuid import uuid4


class MpesaProvider:
    name = "mpesa"

    def charge(self, amount, currency, token, metadata=None):
        return {
            "status": "captured",
            "provider": self.name,
            "reference": f"mpesa_mock_{uuid4().hex}",
            "amount": str(amount),
            "currency": currency,
            "metadata": metadata or {},
        }
