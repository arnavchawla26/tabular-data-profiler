"""Descriptive statistics: numeric distributions, categorical cardinality,
and pairwise Pearson correlation between numeric columns.

No numpy/pandas -- everything here is plain Python floats, lists, and
dicts. Percentiles use linear interpolation on the sorted sample, matching
numpy's default ('linear') interpolation method, so results are directly
comparable to `numpy.percentile`.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """p-th percentile (0 <= p <= 100) of an already-sorted sequence, using
    linear interpolation between closest ranks (numpy's default method)."""
    if not sorted_values:
        raise ValueError("percentile of empty sequence")
    n = len(sorted_values)
    if n == 1:
        return float(sorted_values[0])
    index = (p / 100.0) * (n - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[int(index)])
    frac = index - lower
    return float(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * frac)


@dataclass
class NumericSummary:
    count: int
    missing: int
    mean: Optional[float]
    std: Optional[float]
    minimum: Optional[float]
    q1: Optional[float]
    median: Optional[float]
    q3: Optional[float]
    maximum: Optional[float]

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "missing": self.missing,
            "mean": self.mean,
            "std": self.std,
            "min": self.minimum,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "max": self.maximum,
        }


def numeric_summary(values: List[Optional[float]]) -> NumericSummary:
    """`values` is one entry per row; None means missing."""
    missing = sum(1 for v in values if v is None)
    present = sorted(v for v in values if v is not None)
    n = len(present)

    if n == 0:
        return NumericSummary(0, missing, None, None, None, None, None, None, None)

    mean = sum(present) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in present) / (n - 1)
        std = math.sqrt(variance)
    else:
        std = 0.0

    return NumericSummary(
        count=n,
        missing=missing,
        mean=mean,
        std=std,
        minimum=present[0],
        q1=percentile(present, 25),
        median=percentile(present, 50),
        q3=percentile(present, 75),
        maximum=present[-1],
    )


@dataclass
class CategoricalSummary:
    count: int
    missing: int
    unique: int
    top_values: List[Tuple[str, int]]  # sorted most-common first

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "missing": self.missing,
            "unique": self.unique,
            "top_values": [{"value": v, "count": c} for v, c in self.top_values],
        }


def categorical_summary(values: List[Optional[str]], top_n: int = 5) -> CategoricalSummary:
    missing = sum(1 for v in values if v is None)
    present = [v for v in values if v is not None]
    counts = Counter(present)
    top = counts.most_common(top_n)
    return CategoricalSummary(
        count=len(present), missing=missing, unique=len(counts), top_values=top
    )


def pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """Pearson correlation coefficient between two equal-length numeric
    sequences with pairwise-complete rows already removed (no Nones). Returns
    None if fewer than 2 points remain or either series has zero variance."""
    n = len(x)
    if n != len(y) or n < 2:
        return None
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    var_x = sum((a - mean_x) ** 2 for a in x)
    var_y = sum((b - mean_y) ** 2 for b in y)
    if var_x == 0 or var_y == 0:
        return None
    return cov / math.sqrt(var_x * var_y)


def correlation_matrix(
    numeric_columns: Dict[str, List[Optional[float]]]
) -> Dict[str, Dict[str, Optional[float]]]:
    """Pairwise Pearson correlation between every pair of numeric columns,
    using rows where BOTH columns are non-missing (pairwise deletion).
    Returns a nested dict `matrix[a][b]`, symmetric, with 1.0 on the
    diagonal (or None if the column has zero variance / <2 valid rows)."""
    names = list(numeric_columns.keys())
    matrix: Dict[str, Dict[str, Optional[float]]] = {a: {} for a in names}

    for i, a in enumerate(names):
        for b in names[i:]:
            col_a = numeric_columns[a]
            col_b = numeric_columns[b]
            paired_a, paired_b = [], []
            for va, vb in zip(col_a, col_b):
                if va is not None and vb is not None:
                    paired_a.append(va)
                    paired_b.append(vb)
            if a == b:
                corr = 1.0 if len(paired_a) >= 1 else None
            else:
                corr = pearson_correlation(paired_a, paired_b)
            matrix[a][b] = corr
            matrix[b][a] = corr

    return matrix
