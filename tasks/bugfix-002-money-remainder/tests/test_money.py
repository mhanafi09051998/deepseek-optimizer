import pytest

from money import split_bill


def test_remainder_is_distributed_first():
    assert split_bill(1000, 3) == [334, 333, 333]


def test_sum_is_preserved():
    for total, people in [(1, 3), (99, 7), (100, 3), (123456, 13), (5, 5)]:
        shares = split_bill(total, people)
        assert sum(shares) == total
        assert len(shares) == people
        assert max(shares) - min(shares) <= 1


def test_more_people_than_cents():
    assert split_bill(2, 5) == [1, 1, 0, 0, 0]


def test_zero_total():
    assert split_bill(0, 4) == [0, 0, 0, 0]


def test_rejects_invalid_input():
    with pytest.raises(ValueError):
        split_bill(100, 0)
    with pytest.raises(ValueError):
        split_bill(-1, 3)
