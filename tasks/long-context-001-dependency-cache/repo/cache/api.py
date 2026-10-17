"""Public cache interface."""

import time

from cache.deps import DependencyGraph
from cache.store import Store


class Cache:
    def __init__(self, clock=time.monotonic):
        self._graph = DependencyGraph()
        self._store = Store(self._graph, clock)

    def set(self, key, value, ttl=None, depends_on=()):
        self._store.set(key, value, ttl=ttl, depends_on=depends_on)

    def get(self, key):
        return self._store.get(key)

    def invalidate(self, key):
        self._store.invalidate(key)
