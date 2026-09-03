"""Column type inference for raw string CSV values.

Every value read from a CSV file arrives as a string. This module decides,
per column, the "best" logical type that ALL of that column's non-missing
values conform to, using a fixed priority order:

    boolean > integer > float > date > string (categorical)

A column falls back to the next type in the chain as soon as a single
non-missing value fails to parse under the current candidate type. If every
value fails everything but string, the column is treated as categorical
text.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Iterable, Optional

# Values (case-insensitive, whitespace-stripped) treated as "missing".
DEFAULT_NA_VALUES = frozenset(
    {"", "na", "n/a", "null", "none", "nan", "nil", "-", "?"}
)

# Exact (case-insensitive) vocabulary accepted for a boolean column. Kept
# deliberately small and unambiguous -- "1"/"0" are NOT included here since
# they are indistinguishable from integers and would make every 0/1 integer
# column misclassify as boolean.
_BOOL_TRUE = frozenset({"true", "yes"})
_BOOL_FALSE = frozenset({"false", "no"})

# Date formats tried in order; the first one that parses ALL non-missing
# values in a column wins. Kept to common, unambiguous ISO-ish formats.
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


class ColumnType(str, Enum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    STRING = "string"


@dataclass(frozen=True)
class ParsedColumn:
    """Result of inferring + parsing one column."""

    name: str
    dtype: ColumnType
    raw_values: list  # original strings, same length/order as the CSV rows
    values: list  # parsed values (None for missing), aligned with raw_values
    missing_mask: list  # bool per row: True if that row's value is missing


def is_missing(raw: str, na_values: Iterable[str] = DEFAULT_NA_VALUES) -> bool:
    if raw is None:
        return True
    stripped = raw.strip()
    return stripped.lower() in {v.lower() for v in na_values}


def _try_bool(raw: str) -> Optional[bool]:
    token = raw.strip().lower()
    if token in _BOOL_TRUE:
        return True
    if token in _BOOL_FALSE:
        return False
    return None


def _try_int(raw: str) -> Optional[int]:
    token = raw.strip()
    if token == "":
        return None
    # Reject float-looking tokens (e.g. "3.0") so they fall through to float.
    try:
        return int(token)
    except ValueError:
        return None


def _try_float(raw: str) -> Optional[float]:
    token = raw.strip()
    if token == "":
        return None
    try:
        value = float(token)
    except ValueError:
        return None
    # Reject inf/nan tokens like "inf", "-infinity", "nan" -- treat as
    # unparsable rather than silently introducing non-finite floats.
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def _try_date(raw: str, fmt: str):
    token = raw.strip()
    try:
        parsed = datetime.strptime(token, fmt)
    except ValueError:
        return None
    if fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        return parsed.date()
    return parsed


def infer_column(
    name: str, raw_values: list, na_values: Iterable[str] = DEFAULT_NA_VALUES
) -> ParsedColumn:
    """Infer the type of a single column and parse its values accordingly."""
    missing_mask = [is_missing(v, na_values) for v in raw_values]
    non_missing = [v for v, m in zip(raw_values, missing_mask) if not m]

    if not non_missing:
        # All-missing column: nothing to infer from, default to string.
        return ParsedColumn(
            name=name,
            dtype=ColumnType.STRING,
            raw_values=list(raw_values),
            values=[None] * len(raw_values),
            missing_mask=missing_mask,
        )

    # --- boolean ---
    if all(_try_bool(v) is not None for v in non_missing):
        values = [
            (_try_bool(v) if not m else None)
            for v, m in zip(raw_values, missing_mask)
        ]
        return ParsedColumn(name, ColumnType.BOOLEAN, list(raw_values), values, missing_mask)

    # --- integer ---
    if all(_try_int(v) is not None for v in non_missing):
        values = [
            (_try_int(v) if not m else None)
            for v, m in zip(raw_values, missing_mask)
        ]
        return ParsedColumn(name, ColumnType.INTEGER, list(raw_values), values, missing_mask)

    # --- float ---
    if all(_try_float(v) is not None for v in non_missing):
        values = [
            (_try_float(v) if not m else None)
            for v, m in zip(raw_values, missing_mask)
        ]
        return ParsedColumn(name, ColumnType.FLOAT, list(raw_values), values, missing_mask)

    # --- date ---
    for fmt in _DATE_FORMATS:
        if all(_try_date(v, fmt) is not None for v in non_missing):
            values = [
                (_try_date(v, fmt) if not m else None)
                for v, m in zip(raw_values, missing_mask)
            ]
            return ParsedColumn(name, ColumnType.DATE, list(raw_values), values, missing_mask)

    # --- fallback: string / categorical ---
    values = [
        (v.strip() if not m else None) for v, m in zip(raw_values, missing_mask)
    ]
    return ParsedColumn(name, ColumnType.STRING, list(raw_values), values, missing_mask)
