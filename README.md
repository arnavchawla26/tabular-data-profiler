# tabular-data-profiler

A dependency-free tabular (CSV) data profiler for Python -- a small,
`pandas-profiling`-style tool built entirely on the standard library. Point
it at a CSV file and get column type inference, missing-value rates,
numeric distributions, categorical cardinality, exact duplicate-row
detection, and pairwise correlation between numeric columns, rendered as
text, JSON, or a self-contained HTML report.

## Why

Most "quick look at my CSV" tools pull in pandas + numpy just to compute a
mean and a few quantiles. This one doesn't: every statistic (mean, sample
standard deviation, quartiles via linear interpolation matching numpy's
default method, Pearson correlation) is implemented from scratch on plain
Python floats and lists, and CSV parsing uses only the stdlib `csv` module.
The whole tool -- parsing, type inference, stats, duplicate detection,
report rendering, and CLI -- has zero third-party runtime dependencies.

## Features

- **Column type inference**: boolean, integer, float, date, or string
  (categorical), inferred per column with a fixed priority order
  (boolean > integer > float > date > string) and graceful fallback when a
  column doesn't cleanly fit a narrower type.
- **Missing-value handling**: a configurable set of "missing" tokens
  (`""`, `NA`, `N/A`, `null`, `None`, `NaN`, `-`, `?`, ...), with a
  per-column missing count and rate.
- **Numeric distributions**: count, mean, sample standard deviation, min,
  Q1, median, Q3, max -- quartiles use linear interpolation on the sorted
  sample, the same method `numpy.percentile` uses by default.
- **Categorical cardinality**: unique-value count and the top-N most
  common values with their counts.
- **Duplicate-row detection**: groups of exact-duplicate rows (compared on
  raw field values, independent of type inference), with row indices and
  occurrence counts.
- **Correlation**: a pairwise Pearson correlation matrix across every
  numeric column, using pairwise-complete rows (missing values in either
  column drop just that pair, not the whole column).
- **Three report formats**: `text` (terminal-friendly), `json`
  (machine-readable, fully structured), and `html` (a single
  self-contained styled page, no external assets).
- **Malformed-row handling**: rows with too few or too many fields are
  padded or truncated rather than silently dropped, with a warning
  surfaced in every report.

## Tech stack

Python 3.9+, standard library only (`csv`, `argparse`, `dataclasses`,
`json`, `html`, `math`, `random`, `datetime`). `pytest` is a dev-only
dependency for the test suite.

## Install

```bash
git clone https://github.com/arnavchawla26/tabular-data-profiler.git
cd tabular-data-profiler
pip install -e ".[dev]"
```

This installs the `tabprofile` console script.

## Usage

### Profile a CSV file

```bash
tabprofile profile data.csv
```

Options:

- `--format {text,json,html}` -- output format (default `text`)
- `--output PATH` / `-o PATH` -- write to a file instead of stdout
- `--delimiter CHAR` -- field delimiter (default `,`)
- `--no-header` -- treat the first row as data; columns are auto-named
  `column_1`, `column_2`, ...
- `--top-n N` -- number of most-common values to report per categorical
  column (default 5)

### Try it with no input file (`demo`)

`demo` generates a deterministic synthetic dataset in memory (seeded, so
it's reproducible) and profiles it -- useful for trying the tool with zero
setup:

```bash
tabprofile demo --rows 200 --format text
```

## Real example

Given this CSV (`example.csv`):

```csv
name,age,department,salary,active
Alice,29,Engineering,95000,true
Bob,34,Sales,72000,true
Carol,,Engineering,101000,false
Dave,41,Marketing,68000,true
Alice,29,Engineering,95000,true
Eve,25,Sales,,true
```

Running `tabprofile profile example.csv` produces (real output, copied
from an actual run):

```
Tabular Data Profile
=====================
Rows: 6    Columns: 5

Column: name  [string]
  missing: 0 (0.00%)
  categorical: unique=5 top=['Alice': 2, 'Bob': 1, 'Carol': 1, 'Dave': 1, 'Eve': 1]

Column: age  [integer]
  missing: 1 (16.67%)
  numeric: count=5 mean=31.6000 std=6.1482 min=25.0000 q1=29.0000 median=29.0000 q3=34.0000 max=41.0000

Column: department  [string]
  missing: 0 (0.00%)
  categorical: unique=3 top=['Engineering': 3, 'Sales': 2, 'Marketing': 1]

Column: salary  [integer]
  missing: 1 (16.67%)
  numeric: count=5 mean=86200.0000 std=15056.5600 min=68000.0000 q1=72000.0000 median=95000.0000 q3=95000.0000 max=101000.0000

Column: active  [boolean]
  missing: 0 (0.00%)
  categorical: unique=2 top=['True': 5, 'False': 1]

Duplicate rows: 2
  rows [0, 4] occur 2x

Correlation (Pearson, numeric columns):
             age   salary
     age    1.00    -0.92
  salary   -0.92     1.00
```

Note the exact-duplicate `Alice` row (index 0 and 4) got flagged, and the
tool correctly noticed a strong negative age/salary correlation in this
tiny sample -- with real data and more rows this becomes a genuinely
useful signal.

`tabprofile demo --rows 200 --format text` (real output, tail of a run --
200 synthetic rows with a real 2*age+noise relationship baked in) shows
the correlation section clearly picking that up:

```
Correlation (Pearson, numeric columns):
         user_id      age    score
 user_id    1.00     0.03     0.05
     age    0.03     1.00     0.99
   score    0.05     0.99     1.00
```

## As a library

```python
from tabprofiler.io_utils import load_csv_file
from tabprofiler.profile import profile_table
from tabprofiler.report import render_json

table = load_csv_file("data.csv")
profile = profile_table(table, top_n=10)

print(profile.n_rows, profile.n_cols)
print(profile.column("age").numeric.mean)
print(profile.duplicate_row_count)
print(render_json(profile))
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

79 tests cover type inference (including boolean/integer disambiguation,
scientific notation, date formats, all-missing columns), CSV loading
(ragged rows, custom delimiters, headerless files), statistics (percentile
values hand-checked against `numpy.percentile`'s linear-interpolation
method, correlation edge cases like zero variance and pairwise deletion of
missing values), duplicate detection, all three report renderers
(including HTML-escaping of unsafe cell values), the synthetic data
generator (determinism, injected duplicates/missing values/correlation),
and the CLI end-to-end -- including a real subprocess-level
`python -m tabprofiler.cli` invocation, not just in-process calls.

## Current status

v1 complete and functional: CSV loading, type inference (boolean / integer
/ float / date / string), missing-value handling, numeric distributions,
categorical cardinality, duplicate-row detection, pairwise Pearson
correlation, and three report formats (text / JSON / HTML) are all
implemented and tested. The `demo` subcommand lets you try the whole
pipeline with no input file.

Possible future extensions (not yet built): a `--sample` flag to profile
only the first N rows of very large files, outlier flagging per numeric
column, and a `--compare` mode to diff two profiles (useful for data-drift
checks between dataset versions).

## License

MIT -- see [LICENSE](LICENSE).
