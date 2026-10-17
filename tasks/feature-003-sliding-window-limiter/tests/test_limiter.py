import threading

import pytest

from limiter import SlidingWindowLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_allows_up_to_limit():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(limit=3, window_seconds=10, clock=clock)

    assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]


def test_window_slides():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(limit=2, window_seconds=10, clock=clock)

    assert limiter.allow("k") is True
    clock.now = 1.0
    assert limiter.allow("k") is True
    clock.now = 5.0
    assert limiter.allow("k") is False

    clock.now = 11.0
    assert limiter.allow("k") is True


def test_boundary_is_exclusive():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(limit=1, window_seconds=10, clock=clock)

    assert limiter.allow("k") is True
    clock.now = 9.999
    assert limiter.allow("k") is False
    clock.now = 10.0
    assert limiter.allow("k") is True


def test_keys_are_independent():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(limit=1, window_seconds=10, clock=clock)

    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        SlidingWindowLimiter(limit=0, window_seconds=10)
    with pytest.raises(ValueError):
        SlidingWindowLimiter(limit=1, window_seconds=0)


def test_concurrent_calls_allow_exactly_limit():
    limiter = SlidingWindowLimiter(limit=25, window_seconds=60, clock=lambda: 100.0)
    results = []
    lock = threading.Lock()
    start = threading.Barrier(100)

    def worker():
        start.wait()
        allowed = limiter.allow("shared")
        with lock:
            results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(results) == 25
