"""Settings package."""

from settings.cache import DEFAULTS as CACHE_DEFAULTS
from settings.network import DEFAULTS as NETWORK_DEFAULTS


def load_settings():
    return {"cache": dict(CACHE_DEFAULTS), "network": dict(NETWORK_DEFAULTS)}
