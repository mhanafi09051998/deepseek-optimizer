"""Application entry point."""

from services.http_client import HttpClient
from settings import load_settings


def main() -> None:
    settings = load_settings()
    client = HttpClient(settings["network"]["timeout"])
    print(client.describe())


if __name__ == "__main__":
    main()
