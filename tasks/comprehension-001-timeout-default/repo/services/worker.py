"""Background worker."""

from services.http_client import HttpClient


def build_worker():
    # The worker uses a short timeout of its own and is unrelated to app defaults.
    return HttpClient(10)
