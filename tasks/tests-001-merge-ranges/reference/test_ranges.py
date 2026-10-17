from ranges import merge_ranges


def test_touching_ranges_merge():
    assert merge_ranges([(1, 3), (4, 6)]) == [(1, 6)]
    assert merge_ranges([(5, 7), (1, 4)]) == [(1, 7)]


def test_overlap_and_separation():
    assert merge_ranges([(1, 5), (4, 8)]) == [(1, 8)]
    assert merge_ranges([(1, 2), (10, 12)]) == [(1, 2), (10, 12)]


def test_empty_and_single():
    assert merge_ranges([]) == []
    assert merge_ranges([(2, 4)]) == [(2, 4)]
