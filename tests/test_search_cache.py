
import time

from app.services.search_cache import SearchCache


def test_cache():

    cache = SearchCache(
        max_size=10,
        ttl_seconds=2,
    )

    cache.set("player", ["ABDO007"])

    assert cache.get("player") == ["ABDO007"]

    print("Cache hit test passed.")

    time.sleep(2.1)

    assert cache.get("player") is None

    print("Cache expiration test passed.")

    cache.set("team", ["Team A"])

    cache.clear()

    assert cache.get("team") is None

    print("Cache invalidation test passed.")


if __name__ == "__main__":
    test_cache()
