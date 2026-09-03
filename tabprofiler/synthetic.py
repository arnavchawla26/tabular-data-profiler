"""Deterministic synthetic dataset generator, used by the `demo` CLI
subcommand and by the test suite. Uses `random.Random` with a fixed seed so
output is bit-for-bit reproducible across runs and machines.

The generated table intentionally exercises every feature of the profiler:
an integer column, a float column correlated with it, a boolean column, a
date column, a categorical column, missing values scattered across columns,
and a handful of exact duplicate rows.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import List

HEADER = ["user_id", "age", "score", "is_active", "signup_date", "plan"]

_PLANS = ["free", "pro", "enterprise"]


def generate_rows(n: int = 200, seed: int = 42, duplicate_every: int = 37) -> List[List[str]]:
    """Return `n` synthetic data rows (as raw string fields, matching
    HEADER). `score` is generated as a noisy linear function of `age` so the
    correlation report has something real to show. Every `duplicate_every`-th
    row exactly repeats the previous row (to exercise duplicate detection).
    Roughly 5% of individual cells are blanked out to exercise missing-value
    handling.
    """
    rng = random.Random(seed)
    start_date = date(2024, 1, 1)
    rows: List[List[str]] = []

    for i in range(n):
        if duplicate_every and i > 0 and i % duplicate_every == 0:
            rows.append(list(rows[-1]))
            continue

        age = rng.randint(18, 75)
        noise = rng.gauss(0, 5)
        score = round(2.0 * age + 10.0 + noise, 2)
        is_active = "true" if rng.random() < 0.7 else "false"
        signup = start_date + timedelta(days=rng.randint(0, 700))
        plan = rng.choice(_PLANS)

        row = [
            str(i + 1),
            str(age),
            str(score),
            is_active,
            signup.isoformat(),
            plan,
        ]

        # Scatter ~5% missing cells across non-id columns.
        for col_idx in range(1, len(row)):
            if rng.random() < 0.05:
                row[col_idx] = ""

        rows.append(row)

    return rows


def generate_csv_text(n: int = 200, seed: int = 42, duplicate_every: int = 37) -> str:
    rows = generate_rows(n=n, seed=seed, duplicate_every=duplicate_every)
    lines = [",".join(HEADER)]
    lines.extend(",".join(row) for row in rows)
    return "\n".join(lines) + "\n"
