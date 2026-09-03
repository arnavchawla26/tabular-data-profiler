import os
import tempfile

from tabprofiler.io_utils import load_csv_file, load_csv_text


def test_basic_load_with_header():
    text = "a,b,c\n1,2,3\n4,5,6\n"
    table = load_csv_text(text)
    assert table.columns == ["a", "b", "c"]
    assert table.rows == [["1", "2", "3"], ["4", "5", "6"]]
    assert table.n_rows == 2
    assert table.n_cols == 3
    assert table.warnings == []


def test_load_without_header():
    text = "1,2,3\n4,5,6\n"
    table = load_csv_text(text, has_header=False)
    assert table.columns == ["column_1", "column_2", "column_3"]
    assert table.rows == [["1", "2", "3"], ["4", "5", "6"]]


def test_custom_delimiter():
    text = "a;b\n1;2\n"
    table = load_csv_text(text, delimiter=";")
    assert table.columns == ["a", "b"]
    assert table.rows == [["1", "2"]]


def test_ragged_short_row_padded_with_warning():
    text = "a,b,c\n1,2,3\n4,5\n"
    table = load_csv_text(text)
    assert table.rows[1] == ["4", "5", ""]
    assert len(table.warnings) == 1
    assert "row 3" in table.warnings[0]


def test_ragged_long_row_truncated_with_warning():
    text = "a,b\n1,2\n3,4,5\n"
    table = load_csv_text(text)
    assert table.rows[1] == ["3", "4"]
    assert len(table.warnings) == 1


def test_empty_file():
    table = load_csv_text("")
    assert table.columns == []
    assert table.rows == []
    assert table.warnings


def test_column_values_helper():
    table = load_csv_text("a,b\n1,x\n2,y\n3,z\n")
    assert table.column_values("b") == ["x", "y", "z"]


def test_load_csv_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    table = load_csv_file(str(p))
    assert table.columns == ["a", "b"]
    assert table.rows == [["1", "2"], ["3", "4"]]


def test_load_csv_file_roundtrip_tempfile():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        f.write("x,y\n10,20\n")
        path = f.name
    try:
        table = load_csv_file(path)
        assert table.columns == ["x", "y"]
        assert table.rows == [["10", "20"]]
    finally:
        os.remove(path)
