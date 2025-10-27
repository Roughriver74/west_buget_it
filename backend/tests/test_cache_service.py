import time

from app.services.cache import CacheService


def test_cache_service_local_get_set_and_copy():
    cache = CacheService(ttl_seconds=60, enable_redis=False)
    namespace = "test"
    key = cache.build_key("user", 1, None, True)

    assert cache.get(namespace, key) is None

    payload = {"value": 42, "items": [1, 2, 3]}
    cache.set(namespace, key, payload)

    cached = cache.get(namespace, key)
    assert cached == payload

    # Ensure cached value is a copy (mutating result should not affect stored data)
    cached["value"] = 100
    cached["items"].append(4)
    cached_again = cache.get(namespace, key)
    assert cached_again == payload


def test_cache_service_invalidation():
    cache = CacheService(ttl_seconds=60, enable_redis=False)
    namespace = "alpha"
    key1 = cache.build_key("one")
    key2 = cache.build_key("two")

    cache.set(namespace, key1, {"foo": "bar"})
    cache.set(namespace, key2, {"foo": "baz"})

    cache.invalidate(namespace, key1)
    assert cache.get(namespace, key1) is None
    assert cache.get(namespace, key2) == {"foo": "baz"}

    cache.invalidate_namespace(namespace)
    assert cache.get(namespace, key2) is None


def test_cache_service_respects_ttl():
    cache = CacheService(ttl_seconds=60, enable_redis=False)
    namespace = "beta"
    key = cache.build_key("temp")

    cache.set(namespace, key, {"value": 1}, ttl_seconds=1)
    assert cache.get(namespace, key) == {"value": 1}

    time.sleep(1.1)
    assert cache.get(namespace, key) is None
