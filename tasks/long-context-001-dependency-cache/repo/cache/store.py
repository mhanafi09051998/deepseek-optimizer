"""Storage layer."""

from dataclasses import dataclass


@dataclass
class Entry:
    value: object
    expires_at: float | None = None


class Store:
    def __init__(self, graph, clock):
        self._data: dict[str, Entry] = {}
        self._graph = graph
        self._clock = clock

    def set(self, key, value, ttl=None, depends_on=()):
        expires_at = None if ttl is None else self._clock() + ttl
        self._data[key] = Entry(value, expires_at)
        self._graph.add(key, tuple(depends_on))

    def raw(self, key):
        return self._data.get(key)

    def get(self, key):
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and self._clock() >= entry.expires_at:
            self.invalidate(key)
            return None
        return entry.value

    def invalidate(self, key):
        self._data.pop(key, None)
        self._graph.discard(key)
