"""tabprofiler: a dependency-free tabular (CSV) data profiler.

Inspired by tools like pandas-profiling / ydata-profiling, but implemented
entirely with the Python standard library -- no pandas, no numpy. Infers
column types, reports missing-value rates, numeric distributions, categorical
cardinality, duplicate rows, and pairwise correlation between numeric
columns, then renders the result as text, JSON, or a self-contained HTML
report.
"""

__version__ = "0.1.0"
