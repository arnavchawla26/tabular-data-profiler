import pytest

from tabprofiler.io_utils import load_csv_text
from tabprofiler.profile import profile_table
from tabprofiler.types import ColumnType


CSV = """id,age,score,active,city
1,25,88.5,true,Boston
2,30,91.0,false,NYC
3,25,88.5,true,Boston
4,,75.2,true,Chicago
5,40,,false,NYC
"""


def test_profile_table_basic_shape():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    assert profile.n_rows == 5
    assert profile.n_cols == 5
    assert [c.name for c in profile.columns] == ["id", "age", "score", "active", "city"]


def test_profile_table_column_types():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    assert profile.column("id").dtype == ColumnType.INTEGER
    assert profile.column("age").dtype == ColumnType.INTEGER
    assert profile.column("score").dtype == ColumnType.FLOAT
    assert profile.column("active").dtype == ColumnType.BOOLEAN
    assert profile.column("city").dtype == ColumnType.STRING


def test_profile_table_missing_values():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    age_col = profile.column("age")
    assert age_col.missing_count == 1
    assert age_col.missing_rate == pytest.approx(0.2)
    score_col = profile.column("score")
    assert score_col.missing_count == 1


def test_profile_table_numeric_summary_present_for_numeric_columns():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    age_col = profile.column("age")
    assert age_col.numeric is not None
    assert age_col.categorical is None
    assert age_col.numeric.count == 4  # 5 rows, 1 missing


def test_profile_table_categorical_summary_for_string_and_boolean():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    city_col = profile.column("city")
    assert city_col.categorical is not None
    assert city_col.categorical.unique == 3  # Boston, NYC, Chicago
    active_col = profile.column("active")
    assert active_col.categorical is not None


def test_profile_table_duplicate_rows_detected():
    table = load_csv_text(CSV)
    profile = profile_table(table)
    # rows[0] = (1,25,88.5,true,Boston), rows[2] = (3,25,88.5,true,Boston)
    # -- different id, so NOT a duplicate row.
    assert profile.duplicate_row_count == 0


def test_profile_table_actual_duplicates():
    csv = "a,b\n1,2\n1,2\n3,4\n"
    table = load_csv_text(csv)
    profile = profile_table(table)
    assert profile.duplicate_row_count == 2
    assert len(profile.duplicate_groups) == 1


def test_profile_table_correlation_between_numeric_columns():
    csv = "x,y\n1,10\n2,20\n3,30\n4,40\n"
    table = load_csv_text(csv)
    profile = profile_table(table)
    assert profile.correlation["x"]["y"] == pytest.approx(1.0)


def test_profile_table_no_correlation_section_with_fewer_than_two_numeric_columns():
    csv = "name,age\nA,10\nB,20\n"
    table = load_csv_text(csv)
    profile = profile_table(table)
    assert profile.correlation == {}


def test_profile_table_empty_table():
    table = load_csv_text("")
    profile = profile_table(table)
    assert profile.n_rows == 0
    assert profile.n_cols == 0
    assert profile.columns == []


def test_profile_table_to_dict_roundtrips_json_serializable():
    import json

    table = load_csv_text(CSV)
    profile = profile_table(table)
    d = profile.to_dict()
    # Should not raise -- confirms every value is JSON-serializable.
    serialized = json.dumps(d)
    assert '"id"' in serialized


def test_profile_table_warnings_propagate_from_raw_table():
    csv = "a,b\n1,2\n3\n"  # second row is short -> padding warning
    table = load_csv_text(csv)
    profile = profile_table(table)
    assert len(profile.warnings) == 1
