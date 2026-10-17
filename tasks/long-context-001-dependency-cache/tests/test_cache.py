from cache import Cache


def make_cache():
    now = [0.0]
    return Cache(clock=lambda: now[0]), now


def test_direct_dependent_is_invalidated():
    cache, _ = make_cache()
    cache.set("user:1", {"name": "ada"})
    cache.set("feed:1", ["post"], depends_on=("user:1",))

    cache.invalidate("user:1")

    assert cache.get("user:1") is None
    assert cache.get("feed:1") is None


def test_transitive_dependents_are_invalidated():
    cache, _ = make_cache()
    cache.set("a", 1)
    cache.set("b", 2, depends_on=("a",))
    cache.set("c", 3, depends_on=("b",))

    cache.invalidate("a")

    assert cache.get("a") is None
    assert cache.get("b") is None
    assert cache.get("c") is None


def test_unrelated_entries_survive():
    cache, _ = make_cache()
    cache.set("a", 1)
    cache.set("b", 2, depends_on=("a",))
    cache.set("other", 3)

    cache.invalidate("a")

    assert cache.get("other") == 3


def test_ttl_expiry_cascades():
    cache, now = make_cache()
    cache.set("a", 1, ttl=5)
    cache.set("b", 2, depends_on=("a",))

    now[0] = 5
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_cycle_terminates():
    cache, _ = make_cache()
    cache.set("a", 1, depends_on=("b",))
    cache.set("b", 2, depends_on=("a",))

    cache.invalidate("a")

    assert cache.get("a") is None
    assert cache.get("b") is None
