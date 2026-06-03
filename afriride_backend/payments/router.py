from payments.providers.flutterwave import FlutterwaveProvider
from payments.providers.mpesa import MpesaProvider
from payments.providers.stripe import StripeProvider


PROVIDERS = {
    "stripe": StripeProvider,
    "flutterwave": FlutterwaveProvider,
    "mpesa": MpesaProvider,
}


def get_payment_provider(region_policy):
    provider_class = PROVIDERS.get(region_policy.default_payment_provider)

    if provider_class is None:
        raise ValueError("Unsupported payment provider")

    return provider_class()
