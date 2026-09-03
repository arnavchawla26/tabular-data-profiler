"""Render a TableProfile as text, JSON, or a self-contained HTML report."""
from __future__ import annotations

import html
import json

from .profile import TableProfile


def _fmt(value, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_text(profile: TableProfile) -> str:
    lines = []
    lines.append("Tabular Data Profile")
    lines.append("=" * 21)
    lines.append(f"Rows: {profile.n_rows}    Columns: {profile.n_cols}")
    if profile.warnings:
        lines.append(f"Warnings: {len(profile.warnings)}")
        for w in profile.warnings:
            lines.append(f"  - {w}")
    lines.append("")

    for col in profile.columns:
        lines.append(f"Column: {col.name}  [{col.dtype.value}]")
        lines.append(f"  missing: {col.missing_count} ({col.missing_rate:.2%})")
        if col.numeric is not None:
            n = col.numeric
            lines.append(
                "  numeric: "
                f"count={n.count} mean={_fmt(n.mean)} std={_fmt(n.std)} "
                f"min={_fmt(n.minimum)} q1={_fmt(n.q1)} median={_fmt(n.median)} "
                f"q3={_fmt(n.q3)} max={_fmt(n.maximum)}"
            )
        if col.categorical is not None:
            c = col.categorical
            top = ", ".join(f"{v!r}: {cnt}" for v, cnt in c.top_values)
            lines.append(f"  categorical: unique={c.unique} top=[{top}]")
        lines.append("")

    lines.append(f"Duplicate rows: {profile.duplicate_row_count}")
    for group in profile.duplicate_groups:
        lines.append(f"  rows {group.row_indices} occur {group.count}x")
    lines.append("")

    if profile.correlation:
        lines.append("Correlation (Pearson, numeric columns):")
        names = list(profile.correlation.keys())
        header = "        " + " ".join(f"{n[:8]:>8}" for n in names)
        lines.append(header)
        for a in names:
            row = f"{a[:8]:>8}" + " ".join(
                f"{_fmt(profile.correlation[a][b], 2):>8}" for b in names
            )
            lines.append(row)

    return "\n".join(lines)


def render_json(profile: TableProfile, indent: int = 2) -> str:
    return json.dumps(profile.to_dict(), indent=indent, sort_keys=False)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Tabular Data Profile</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
         margin: 2rem; color: #1a1a1a; background: #fafafa; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .meta {{ color: #555; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem;
           background: #fff; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left;
            font-size: 0.9rem; }}
  th {{ background: #f0f0f0; }}
  .dtype {{ font-family: monospace; color: #7a1fa2; }}
  .warn {{ color: #a15c00; }}
  .section {{ margin-top: 2rem; }}
</style>
</head>
<body>
<h1>Tabular Data Profile</h1>
<p class="meta">{n_rows} rows &times; {n_cols} columns</p>
{warnings_html}
<div class="section">
<h2>Columns</h2>
<table>
<tr><th>Name</th><th>Type</th><th>Missing</th><th>Details</th></tr>
{column_rows}
</table>
</div>
<div class="section">
<h2>Duplicate rows</h2>
<p>{dup_count} duplicate rows across {dup_groups} group(s).</p>
{dup_table}
</div>
{corr_section}
</body>
</html>
"""


def _column_details_html(col) -> str:
    if col.numeric is not None:
        n = col.numeric
        return (
            f"count={n.count}, mean={_fmt(n.mean)}, std={_fmt(n.std)}, "
            f"min={_fmt(n.minimum)}, q1={_fmt(n.q1)}, median={_fmt(n.median)}, "
            f"q3={_fmt(n.q3)}, max={_fmt(n.maximum)}"
        )
    if col.categorical is not None:
        c = col.categorical
        top = ", ".join(
            f"{html.escape(str(v))} ({cnt})" for v, cnt in c.top_values
        )
        return f"unique={c.unique}, top values: {top}"
    return ""


def render_html(profile: TableProfile) -> str:
    warnings_html = ""
    if profile.warnings:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in profile.warnings)
        warnings_html = f'<p class="warn">Warnings:</p><ul class="warn">{items}</ul>'

    column_rows = []
    for col in profile.columns:
        column_rows.append(
            "<tr>"
            f"<td>{html.escape(col.name)}</td>"
            f'<td class="dtype">{col.dtype.value}</td>'
            f"<td>{col.missing_count} ({col.missing_rate:.1%})</td>"
            f"<td>{_column_details_html(col)}</td>"
            "</tr>"
        )

    dup_table = ""
    if profile.duplicate_groups:
        rows = "".join(
            f"<tr><td>{g.row_indices}</td><td>{g.count}</td></tr>"
            for g in profile.duplicate_groups
        )
        dup_table = (
            "<table><tr><th>Row indices</th><th>Occurrences</th></tr>"
            f"{rows}</table>"
        )

    corr_section = ""
    if profile.correlation:
        names = list(profile.correlation.keys())
        header = "".join(f"<th>{html.escape(n)}</th>" for n in names)
        rows = ""
        for a in names:
            cells = "".join(
                f"<td>{_fmt(profile.correlation[a][b], 3)}</td>" for b in names
            )
            rows += f"<tr><th>{html.escape(a)}</th>{cells}</tr>"
        corr_section = (
            '<div class="section"><h2>Correlation (Pearson)</h2>'
            f"<table><tr><th></th>{header}</tr>{rows}</table></div>"
        )

    return _HTML_TEMPLATE.format(
        n_rows=profile.n_rows,
        n_cols=profile.n_cols,
        warnings_html=warnings_html,
        column_rows="\n".join(column_rows),
        dup_count=profile.duplicate_row_count,
        dup_groups=len(profile.duplicate_groups),
        dup_table=dup_table,
        corr_section=corr_section,
    )


RENDERERS = {
    "text": render_text,
    "json": render_json,
    "html": render_html,
}
