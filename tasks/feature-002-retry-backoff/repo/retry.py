"""Retry helper."""

import time


class RetryableError(Exception):
    """A transient failure that may succeed on a later attempt."""


class FatalError(Exception):
    """A failure that must never be retried."""


def call_with_retry(fn, max_attempts=3):
    last = None
    for _ in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last
