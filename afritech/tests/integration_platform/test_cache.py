from __future__ import annotations

from afritech.integration_platform import CachePolicy, IntegrationCache


def test_integration_cache_respects_ttl_and_prefix_invalidation() -> None:
    cache = IntegrationCache()
    policy = CachePolicy(
        policy_id="reference-data",
        ttl_seconds=60,
        stale_while_revalidate_seconds=0,
        cache_location="memory",
        tenant_scoped=True,
        user_scoped=False,
        allow_persistent_storage=False,
        invalidate_on=("providers",),
        classification_limit="INTERNAL",
    )

    cache.set("novaride:tenant-a:country-list", ["AU"], policy, tenant_id="tenant-a")
    assert cache.get("novaride:tenant-a:country-list") == ["AU"]
    cache.invalidate("novaride:tenant-a")
    assert cache.get("novaride:tenant-a:country-list") is None

