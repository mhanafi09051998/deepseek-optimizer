import pytest

from store import ITEMS, paginate


def walk(limit):
    collected = []
    cursor = None
    pages = 0
    while True:
        page, cursor = paginate(ITEMS, limit=limit, cursor=cursor)
        assert len(page) <= limit
        collected.extend(page)
        pages += 1
        if cursor is None:
            return collected, pages
        assert pages < 100, "cursor never terminates"


def test_walk_collects_every_item_once():
    collected, pages = walk(10)
    assert collected == ITEMS
    assert pages == 3


def test_last_page_has_no_cursor():
    page, cursor = paginate(ITEMS, limit=10)
    assert len(page) == 10
    assert cursor is not None

    page, cursor = paginate(ITEMS, limit=10, cursor=cursor)
    assert len(page) == 10
    assert cursor is not None

    page, cursor = paginate(ITEMS, limit=10, cursor=cursor)
    assert len(page) == 5
    assert cursor is None


def test_limit_larger_than_collection():
    page, cursor = paginate(["a", "b"], limit=50)
    assert page == ["a", "b"]
    assert cursor is None


def test_limit_one_walk():
    collected, pages = walk(1)
    assert collected == ITEMS
    assert pages == len(ITEMS)


def test_invalid_arguments():
    with pytest.raises(ValueError):
        paginate(ITEMS, limit=0)
    with pytest.raises(ValueError):
        paginate(ITEMS, limit=-3)
    with pytest.raises(ValueError):
        paginate(ITEMS, limit=5, cursor="not-a-cursor")
