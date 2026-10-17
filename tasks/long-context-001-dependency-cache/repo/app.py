"""Demo application."""

from cache import Cache


def main():
    cache = Cache()
    cache.set("user:1", {"name": "ada"})
    cache.set("feed:1", ["post"], depends_on=("user:1",))
    cache.invalidate("user:1")
    print(cache.get("feed:1"))


if __name__ == "__main__":
    main()
