"""CSV loading helpers.

Reads a CSV file (or any iterable of text lines) into a column-oriented
structure: a list of column names plus, for each column, the list of raw
string values in row order. Ragged rows (too few/many fields) are padded or
truncated with a loud warning rather than silently dropped, since a profiler
that hides malformed rows would misreport missing-value rates.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import List


@dataclass
class RawTable:
    columns: List[str]
    rows: List[List[str]]  # row-oriented raw strings, each len == len(columns)
    warnings: List[str] = field(default_factory=list)

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return len(self.columns)

    def column_values(self, name: str) -> List[str]:
        idx = self.columns.index(name)
        return [row[idx] for row in self.rows]


def _normalize_rows(header: List[str], raw_rows, warnings: List[str]) -> List[List[str]]:
    width = len(header)
    fixed = []
    for i, row in enumerate(raw_rows):
        row = list(row)
        if len(row) < width:
            warnings.append(
                f"row {i + 2}: expected {width} fields, got {len(row)} -- padded with missing values"
            )
            row = row + [""] * (width - len(row))
        elif len(row) > width:
            warnings.append(
                f"row {i + 2}: expected {width} fields, got {len(row)} -- extra fields dropped"
            )
            row = row[:width]
        fixed.append(row)
    return fixed


def load_csv_text(text: str, delimiter: str = ",", has_header: bool = True) -> RawTable:
    """Parse CSV content already held in memory as a string."""
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    all_rows = list(reader)
    # Skip fully blank lines (common trailing-newline artifact).
    all_rows = [r for r in all_rows if r != []]

    if not all_rows:
        return RawTable(columns=[], rows=[], warnings=["empty file: no rows found"])

    warnings: List[str] = []
    if has_header:
        header = all_rows[0]
        body = all_rows[1:]
    else:
        header = [f"column_{i + 1}" for i in range(len(all_rows[0]))]
        body = all_rows

    rows = _normalize_rows(header, body, warnings)
    return RawTable(columns=header, rows=rows, warnings=warnings)


def load_csv_file(path: str, delimiter: str = ",", has_header: bool = True) -> RawTable:
    with open(path, "r", newline="", encoding="utf-8") as f:
        text = f.read()
    return load_csv_text(text, delimiter=delimiter, has_header=has_header)
