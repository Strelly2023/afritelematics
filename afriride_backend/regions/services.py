from .models import RegionPolicy


def get_region_policy(country_code):
    return RegionPolicy.objects.get(
        country_code=country_code.upper(),
        active=True,
    )


def example_region_policies():
    """Documentation helper for seed data; not used as runtime truth."""

    return [
        {
            "country_code": "AU",
            "currency": "AUD",
            "tax_name": "GST",
            "default_payment_provider": "stripe",
        },
        {
            "country_code": "RW",
            "currency": "RWF",
            "tax_name": "VAT",
            "default_payment_provider": "flutterwave",
        },
        {
            "country_code": "KE",
            "currency": "KES",
            "tax_name": "VAT",
            "default_payment_provider": "mpesa",
        },
        {
            "country_code": "CD",
            "currency": "CDF",
            "tax_name": "VAT",
            "default_payment_provider": "flutterwave",
        },
    ]
