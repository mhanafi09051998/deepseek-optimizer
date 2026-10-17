"""Sliding window rate limiter."""

import time


class SlidingWindowLimiter:
    def __init__(self, limit, window_seconds, clock=time.monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._events = {}

    def allow(self, key):
        now = self._clock()
        events = self._events.setdefault(key, [])
        events.append(now)
        return len(events) <= self.limit
