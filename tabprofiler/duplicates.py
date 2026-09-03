"""Exact duplicate-row detection.

Two rows are duplicates if every raw (pre-type-inference) field matches
exactly. Detection runs on the raw string values rather than parsed values
so that it doesn't depend on -- or get confused by -- type inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class DuplicateGroup:
    row_indices: List[int]  # 0-based indices into the data rows (header excluded)
    values: Tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.row_indices)


def find_duplicate_rows(rows: List[List[str]]) -> List[DuplicateGroup]:
    """Group row indices by identical field tuples; only groups with more
    than one member are returned (unique rows are omitted)."""
    seen = {}
    for idx, row in enumerate(rows):
        key = tuple(row)
        seen.setdefault(key, []).append(idx)

    groups = [
        DuplicateGroup(row_indices=indices, values=key)
        for key, indices in seen.items()
        if len(indices) > 1
    ]
    # Deterministic ordering: by first occurrence.
    groups.sort(key=lambda g: g.row_indices[0])
    return groups


def duplicate_row_count(rows: List[List[str]]) -> int:
    """Total number of rows that are part of a duplicate group, counting
    every occurrence (so a group of 3 identical rows contributes 3)."""
    return sum(g.count for g in find_duplicate_rows(rows))
