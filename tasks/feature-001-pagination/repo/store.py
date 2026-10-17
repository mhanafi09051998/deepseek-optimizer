"""In-memory item store."""

ITEMS = [f"item-{index:03d}" for index in range(1, 26)]


def list_items() -> list[str]:
    return list(ITEMS)
