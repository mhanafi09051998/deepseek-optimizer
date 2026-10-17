"""HTTP client used by the application."""


class HttpClient:
    def __init__(self, timeout):
        self.timeout = timeout

    def describe(self):
        return f"http client timeout={self.timeout}s"
