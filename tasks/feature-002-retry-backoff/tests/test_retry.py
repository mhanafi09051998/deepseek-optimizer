import pytest

from retry import FatalError, RetryableError, call_with_retry


class Recorder:
    def __init__(self):
        self.delays = []

    def __call__(self, seconds):
        self.delays.append(seconds)


def test_retries_until_success():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RetryableError("later")
        return "ok"

    sleep = Recorder()
    assert call_with_retry(flaky, max_attempts=4, sleep=sleep) == "ok"
    assert calls["n"] == 3
    assert len(sleep.delays) == 2


def test_backoff_bounds():
    def always():
        raise RetryableError("nope")

    sleep = Recorder()
    with pytest.raises(RetryableError):
        call_with_retry(always, max_attempts=4, base_delay=0.01, max_delay=0.02, sleep=sleep)

    assert len(sleep.delays) == 3
    expected_caps = [0.01, 0.02, 0.02]
    for delay, cap in zip(sleep.delays, expected_caps):
        assert cap / 2 <= delay <= cap


def test_fatal_error_is_not_retried():
    calls = {"n": 0}

    def fatal():
        calls["n"] += 1
        raise FatalError("stop")

    with pytest.raises(FatalError):
        call_with_retry(fatal, max_attempts=5, sleep=Recorder())
    assert calls["n"] == 1


def test_rejects_bad_attempt_count():
    with pytest.raises(ValueError):
        call_with_retry(lambda: 1, max_attempts=0)


def test_success_on_first_call():
    sleep = Recorder()
    assert call_with_retry(lambda: 42, sleep=sleep) == 42
    assert sleep.delays == []
