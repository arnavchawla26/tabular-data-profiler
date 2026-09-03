from datetime import date

import pytest

from tabprofiler.types import ColumnType, infer_column, is_missing


def test_is_missing_variants():
    assert is_missing("")
    assert is_missing("  ")
    assert is_missing("NA")
    assert is_missing("n/a")
    assert is_missing("NULL")
    assert is_missing("None")
    assert is_missing("?")
    assert not is_missing("0")
    assert not is_missing("hello")


def test_infer_integer_column():
    col = infer_column("age", ["18", "25", "", "42"])
    assert col.dtype == ColumnType.INTEGER
    assert col.values == [18, 25, None, 42]
    assert col.missing_mask == [False, False, True, False]


def test_infer_float_column_mixed_with_ints():
    # A column with any true float among otherwise-integer-looking values
    # should be classified as float, and integers parse cleanly as floats.
    col = infer_column("price", ["1", "2.5", "3"])
    assert col.dtype == ColumnType.FLOAT
    assert col.values == [1.0, 2.5, 3.0]


def test_infer_boolean_column():
    col = infer_column("active", ["true", "false", "TRUE", "No", "yes"])
    assert col.dtype == ColumnType.BOOLEAN
    assert col.values == [True, False, True, False, True]


def test_boolean_does_not_swallow_zero_one_integers():
    # 0/1 must NOT be classified as boolean -- it's ambiguous with integer
    # and integer is the more useful interpretation.
    col = infer_column("flag", ["0", "1", "1", "0"])
    assert col.dtype == ColumnType.INTEGER


def test_infer_date_column_iso():
    col = infer_column("signup", ["2024-01-15", "2024-02-01", ""])
    assert col.dtype == ColumnType.DATE
    assert col.values[0] == date(2024, 1, 15)
    assert col.values[1] == date(2024, 2, 1)
    assert col.values[2] is None


def test_infer_date_column_us_format():
    col = infer_column("d", ["01/15/2024", "02/01/2024"])
    assert col.dtype == ColumnType.DATE
    assert col.values[0] == date(2024, 1, 15)


def test_infer_string_column_fallback():
    col = infer_column("city", ["Boston", "NYC", "42nd St"])
    assert col.dtype == ColumnType.STRING
    assert col.values == ["Boston", "NYC", "42nd St"]


def test_mixed_type_column_falls_back_to_string():
    col = infer_column("mixed", ["1", "hello", "3.5"])
    assert col.dtype == ColumnType.STRING


def test_all_missing_column_defaults_to_string():
    col = infer_column("empty", ["", "NA", "null"])
    assert col.dtype == ColumnType.STRING
    assert col.values == [None, None, None]
    assert col.missing_mask == [True, True, True]


def test_infinity_and_nan_tokens_are_not_parsed_as_float():
    col = infer_column("weird", ["1.0", "inf", "nan"])
    # "inf"/"nan" reject float parsing -> falls through to string.
    assert col.dtype == ColumnType.STRING


def test_negative_and_scientific_notation_floats():
    col = infer_column("x", ["-1.5", "2.5e3", "-3e-2"])
    assert col.dtype == ColumnType.FLOAT
    assert col.values == [-1.5, 2500.0, -0.03]


def test_custom_na_values():
    col = infer_column("x", ["1", "MISSING", "3"], na_values=["MISSING"])
    assert col.dtype == ColumnType.INTEGER
    assert col.values == [1, None, 3]
