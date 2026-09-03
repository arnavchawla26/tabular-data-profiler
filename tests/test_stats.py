import math

import pytest

from tabprofiler.stats import (
    categorical_summary,
    correlation_matrix,
    numeric_summary,
    pearson_correlation,
    percentile,
)


def test_percentile_matches_numpy_linear_method_hand_computed():
    # sorted [1,2,3,4,5,6,7,8,9,10]; numpy.percentile(..., 25) == 3.25
    data = list(range(1, 11))
    assert percentile(data, 25) == pytest.approx(3.25)
    assert percentile(data, 50) == pytest.approx(5.5)
    assert percentile(data, 75) == pytest.approx(7.75)
    assert percentile(data, 0) == 1
    assert percentile(data, 100) == 10


def test_percentile_single_value():
    assert percentile([42.0], 50) == 42.0
    assert percentile([42.0], 0) == 42.0
    assert percentile([42.0], 100) == 42.0


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        percentile([], 50)


def test_numeric_summary_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    summary = numeric_summary(values)
    assert summary.count == 5
    assert summary.missing == 0
    assert summary.mean == pytest.approx(3.0)
    assert summary.minimum == 1.0
    assert summary.maximum == 5.0
    assert summary.median == pytest.approx(3.0)
    # sample stdev of 1..5 is sqrt(2.5) ~= 1.5811
    assert summary.std == pytest.approx(math.sqrt(2.5))


def test_numeric_summary_with_missing():
    values = [1.0, None, 3.0, None, 5.0]
    summary = numeric_summary(values)
    assert summary.count == 3
    assert summary.missing == 2
    assert summary.mean == pytest.approx(3.0)


def test_numeric_summary_all_missing():
    summary = numeric_summary([None, None])
    assert summary.count == 0
    assert summary.missing == 2
    assert summary.mean is None
    assert summary.std is None


def test_numeric_summary_single_value_std_is_zero():
    summary = numeric_summary([7.0])
    assert summary.count == 1
    assert summary.std == 0.0
    assert summary.mean == 7.0


def test_categorical_summary_top_values_and_unique():
    values = ["a", "b", "a", "a", "c", None, "b"]
    summary = categorical_summary(values, top_n=2)
    assert summary.count == 6
    assert summary.missing == 1
    assert summary.unique == 3
    assert summary.top_values[0] == ("a", 3)
    assert len(summary.top_values) == 2


def test_pearson_correlation_perfect_positive():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert pearson_correlation(x, y) == pytest.approx(1.0)


def test_pearson_correlation_perfect_negative():
    x = [1.0, 2.0, 3.0, 4.0]
    y = [8.0, 6.0, 4.0, 2.0]
    assert pearson_correlation(x, y) == pytest.approx(-1.0)


def test_pearson_correlation_zero_variance_returns_none():
    x = [5.0, 5.0, 5.0]
    y = [1.0, 2.0, 3.0]
    assert pearson_correlation(x, y) is None


def test_pearson_correlation_too_few_points():
    assert pearson_correlation([1.0], [2.0]) is None
    assert pearson_correlation([], []) is None


def test_correlation_matrix_symmetry_and_diagonal():
    cols = {
        "a": [1.0, 2.0, 3.0, 4.0],
        "b": [4.0, 3.0, 2.0, 1.0],
        "c": [1.0, 1.0, 1.0, 1.0],  # zero variance
    }
    matrix = correlation_matrix(cols)
    assert matrix["a"]["a"] == 1.0
    assert matrix["a"]["b"] == pytest.approx(-1.0)
    assert matrix["b"]["a"] == pytest.approx(-1.0)  # symmetric
    assert matrix["a"]["c"] is None  # zero variance -> undefined


def test_correlation_matrix_pairwise_deletion_of_missing():
    cols = {
        "a": [1.0, 2.0, None, 4.0],
        "b": [10.0, 20.0, 30.0, None],
    }
    matrix = correlation_matrix(cols)
    # Only rows 0 and 1 have both present -> perfectly correlated pair.
    assert matrix["a"]["b"] == pytest.approx(1.0)
