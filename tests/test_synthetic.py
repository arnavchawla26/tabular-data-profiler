from tabprofiler.io_utils import load_csv_text
from tabprofiler.profile import profile_table
from tabprofiler.synthetic import HEADER, generate_csv_text, generate_rows


def test_generate_rows_deterministic_with_same_seed():
    a = generate_rows(n=50, seed=7)
    b = generate_rows(n=50, seed=7)
    assert a == b


def test_generate_rows_different_seed_differs():
    a = generate_rows(n=50, seed=1)
    b = generate_rows(n=50, seed=2)
    assert a != b


def test_generate_rows_count_and_width():
    rows = generate_rows(n=30, seed=1)
    assert len(rows) == 30
    assert all(len(r) == len(HEADER) for r in rows)


def test_generate_rows_produces_duplicates():
    rows = generate_rows(n=100, seed=42, duplicate_every=10)
    # row index 10 (0-based) should exactly equal row index 9.
    assert rows[10] == rows[9]


def test_generate_rows_no_duplicates_when_disabled():
    rows = generate_rows(n=50, seed=42, duplicate_every=0)
    unique_rows = {tuple(r) for r in rows}
    # user_id column is unique per row, so all rows are distinct.
    assert len(unique_rows) == len(rows)


def test_generate_csv_text_parses_and_profiles_cleanly():
    csv_text = generate_csv_text(n=200, seed=42)
    table = load_csv_text(csv_text)
    assert table.columns == HEADER
    assert table.n_rows == 200
    assert table.warnings == []  # every row is well-formed (correct width)

    profile = profile_table(table)
    assert profile.column("age").numeric is not None
    assert profile.column("score").numeric is not None
    assert profile.column("is_active").categorical is not None
    # age/score should be positively correlated by construction.
    corr = profile.correlation["age"]["score"]
    assert corr is not None
    assert corr > 0.8


def test_generate_csv_text_has_some_missing_values():
    csv_text = generate_csv_text(n=200, seed=42)
    table = load_csv_text(csv_text)
    profile = profile_table(table)
    total_missing = sum(c.missing_count for c in profile.columns)
    assert total_missing > 0


def test_generate_csv_text_has_duplicates_by_default():
    csv_text = generate_csv_text(n=200, seed=42, duplicate_every=37)
    table = load_csv_text(csv_text)
    profile = profile_table(table)
    assert profile.duplicate_row_count > 0
