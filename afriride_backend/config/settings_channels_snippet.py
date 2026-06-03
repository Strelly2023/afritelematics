"""Settings snippet for enabling AfriRide realtime dispatch.

Merge these values into the concrete Django settings module used by deployment.
"""

INSTALLED_APPS_ADDITIONS = [
    "channels",
    "rest_framework",
    "accounts",
    "rides",
    "evidence",
    "replay",
    "dispatch",
    "realtime",
    "gps",
    "route_replay",
    "pricing",
    "payments",
    "earnings",
    "receipts",
    "regions",
    "currency",
    "tax",
    "organizations",
    "fleets",
    "subscriptions",
    "billing",
    "zones",
    "analytics",
    "trust",
    "regulatory",
    "government",
    "public_transport",
    "pilot",
    "certification",
    "network.apps.NetworkConfig",
    "operations.apps.OperationsConfig",
    "mos.mobility_graph.apps.MobilityGraphConfig",
    "mos.scheduling.apps.SchedulingConfig",
    "mos.policies.apps.PoliciesConfig",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

REDIS_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}
