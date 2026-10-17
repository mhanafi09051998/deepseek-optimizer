"""Dependency graph for cache entries."""


class DependencyGraph:
    """Tracks which keys depend on which other keys."""

    def __init__(self):
        self._dependents: dict[str, set[str]] = {}

    def add(self, key: str, depends_on: tuple[str, ...]) -> None:
        for parent in depends_on:
            self._dependents.setdefault(parent, set()).add(key)

    def dependents(self, key: str) -> set[str]:
        return set(self._dependents.get(key, ()))

    def discard(self, key: str) -> None:
        self._dependents.pop(key, None)
