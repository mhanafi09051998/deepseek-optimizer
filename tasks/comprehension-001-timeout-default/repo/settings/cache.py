"""Cache settings."""

# Kept for backwards compatibility with the old cache client.
DEFAULT_TIMEOUT_SECONDS = 5

DEFAULTS = {
    "ttl": 60,
    "timeout": DEFAULT_TIMEOUT_SECONDS,
}
