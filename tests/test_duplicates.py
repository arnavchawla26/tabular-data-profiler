from tabprofiler.duplicates import duplicate_row_count, find_duplicate_rows


def test_no_duplicates():
    rows = [["1", "a"], ["2", "b"], ["3", "c"]]
    assert find_duplicate_rows(rows) == []
    assert duplicate_row_count(rows) == 0


def test_simple_duplicate_pair():
    rows = [["1", "a"], ["2", "b"], ["1", "a"]]
    groups = find_duplicate_rows(rows)
    assert len(groups) == 1
    assert groups[0].row_indices == [0, 2]
    assert groups[0].count == 2
    assert duplicate_row_count(rows) == 2


def test_triple_duplicate():
    rows = [["x"], ["x"], ["x"]]
    groups = find_duplicate_rows(rows)
    assert len(groups) == 1
    assert groups[0].row_indices == [0, 1, 2]
    assert groups[0].count == 3


def test_multiple_duplicate_groups_ordered_by_first_occurrence():
    rows = [
        ["a"],  # idx 0
        ["b"],  # idx 1
        ["a"],  # idx 2 (dup of 0)
        ["c"],  # idx 3
        ["b"],  # idx 4 (dup of 1)
    ]
    groups = find_duplicate_rows(rows)
    assert [g.row_indices for g in groups] == [[0, 2], [1, 4]]


def test_similar_but_not_identical_rows_are_not_duplicates():
    rows = [["1", "a"], ["1", "A"], ["1 ", "a"]]
    assert find_duplicate_rows(rows) == []


def test_empty_rows_list():
    assert find_duplicate_rows([]) == []
    assert duplicate_row_count([]) == 0
