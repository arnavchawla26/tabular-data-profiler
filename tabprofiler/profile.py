"""Top-level orchestration: turn a RawTable into a full profile report.

`profile_table()` is the single entry point used by both the CLI and the
test suite. It ties together type inference (types.py), descriptive
statistics (stats.py), and duplicate-row detection (duplicates.py) into one
structured `TableProfile` dataclass that the report renderers consume.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .duplicates import DuplicateGroup, find_duplicate_rows
from .io_utils import RawTable
from .stats import (
    CategoricalSummary,
    NumericSummary,
    categorical_summary,
    correlation_matrix,
    numeric_summary,
)
from .types import ColumnType, ParsedColumn, infer_column


@dataclass
class ColumnProfile:
    name: str
    dtype: ColumnType
    missing_count: int
    missing_rate: float
    numeric: Optional[NumericSummary] = None
    categorical: Optional[CategoricalSummary] = None

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "dtype": self.dtype.value,
            "missing_count": self.missing_count,
            "missing_rate": self.missing_rate,
        }
        if self.numeric is not None:
            d["numeric"] = self.numeric.to_dict()
        if self.categorical is not None:
            d["categorical"] = self.categorical.to_dict()
        return d


@dataclass
class TableProfile:
    n_rows: int
    n_cols: int
    columns: List[ColumnProfile]
    duplicate_groups: List[DuplicateGroup]
    correlation: Dict[str, Dict[str, Optional[float]]]
    warnings: List[str] = field(default_factory=list)

    @property
    def duplicate_row_count(self) -> int:
        return sum(g.count for g in self.duplicate_groups)

    def column(self, name: str) -> ColumnProfile:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def to_dict(self) -> dict:
        return {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "columns": [c.to_dict() for c in self.columns],
            "duplicate_rows": {
                "total_duplicate_rows": self.duplicate_row_count,
                "groups": [
                    {"row_indices": g.row_indices, "count": g.count}
                    for g in self.duplicate_groups
                ],
            },
            "correlation": self.correlation,
            "warnings": self.warnings,
        }


def profile_table(table: RawTable, top_n: int = 5) -> TableProfile:
    if table.n_cols == 0:
        return TableProfile(0, 0, [], [], {}, warnings=list(table.warnings))

    parsed_columns: Dict[str, ParsedColumn] = {}
    for name in table.columns:
        raw_values = table.column_values(name)
        parsed_columns[name] = infer_column(name, raw_values)

    column_profiles: List[ColumnProfile] = []
    numeric_for_corr: Dict[str, List[Optional[float]]] = {}

    for name in table.columns:
        parsed = parsed_columns[name]
        n = len(parsed.raw_values)
        missing_count = sum(parsed.missing_mask)
        missing_rate = (missing_count / n) if n else 0.0

        numeric_stats = None
        categorical_stats = None

        if parsed.dtype in (ColumnType.INTEGER, ColumnType.FLOAT):
            numeric_values = [float(v) if v is not None else None for v in parsed.values]
            numeric_stats = numeric_summary(numeric_values)
            numeric_for_corr[name] = numeric_values
        elif parsed.dtype == ColumnType.BOOLEAN:
            # Booleans are summarized categorically (True/False counts),
            # not folded into numeric correlation.
            categorical_stats = categorical_summary(
                [str(v) if v is not None else None for v in parsed.values], top_n=top_n
            )
        elif parsed.dtype == ColumnType.DATE:
            categorical_stats = categorical_summary(
                [v.isoformat() if v is not None else None for v in parsed.values],
                top_n=top_n,
            )
        else:  # STRING
            categorical_stats = categorical_summary(parsed.values, top_n=top_n)

        column_profiles.append(
            ColumnProfile(
                name=name,
                dtype=parsed.dtype,
                missing_count=missing_count,
                missing_rate=missing_rate,
                numeric=numeric_stats,
                categorical=categorical_stats,
            )
        )

    duplicate_groups = find_duplicate_rows(table.rows)
    corr = correlation_matrix(numeric_for_corr) if len(numeric_for_corr) >= 2 else {}

    return TableProfile(
        n_rows=table.n_rows,
        n_cols=table.n_cols,
        columns=column_profiles,
        duplicate_groups=duplicate_groups,
        correlation=corr,
        warnings=list(table.warnings),
    )
