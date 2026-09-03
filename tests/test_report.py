import json

from tabprofiler.io_utils import load_csv_text
from tabprofiler.profile import profile_table
from tabprofiler.report import render_html, render_json, render_text

CSV = """id,age,score,city
1,25,88.5,Boston
2,30,91.0,NYC
3,25,88.5,Boston
"""


def _profile():
    return profile_table(load_csv_text(CSV))


def test_render_text_contains_key_sections():
    text = render_text(_profile())
    assert "Tabular Data Profile" in text
    assert "Column: age" in text
    assert "Duplicate rows:" in text
    assert "Correlation" in text  # id/age/score are all numeric


def test_render_text_reports_missing_rate():
    csv = "a,b\n1,\n2,3\n"
    text = render_text(profile_table(load_csv_text(csv)))
    assert "missing: 1 (50.00%)" in text


def test_render_json_is_valid_and_structured():
    payload = render_json(_profile())
    data = json.loads(payload)
    assert data["n_rows"] == 3
    assert data["n_cols"] == 4
    names = [c["name"] for c in data["columns"]]
    assert names == ["id", "age", "score", "city"]
    assert "correlation" in data


def test_render_json_duplicate_rows_section():
    csv = "a,b\n1,2\n1,2\n"
    data = json.loads(render_json(profile_table(load_csv_text(csv))))
    assert data["duplicate_rows"]["total_duplicate_rows"] == 2
    assert len(data["duplicate_rows"]["groups"]) == 1


def test_render_html_is_well_formed_and_escapes_values():
    csv = 'name,note\n"<script>",hi\n'
    profile = profile_table(load_csv_text(csv))
    out = render_html(profile)
    assert out.startswith("<!doctype html>")
    assert "<title>Tabular Data Profile</title>" in out
    # The raw "<script>" value must be HTML-escaped in the top-values list.
    assert "<script>" not in out.split("<body>")[1].replace("&lt;script&gt;", "")
    assert "&lt;script&gt;" in out


def test_render_html_includes_row_and_column_counts():
    out = render_html(_profile())
    assert "3 rows" in out
    assert "4 columns" in out


def test_render_html_no_correlation_section_when_fewer_than_two_numeric_columns():
    csv = "name,city\nA,Boston\nB,NYC\n"
    profile = profile_table(load_csv_text(csv))
    out = render_html(profile)
    assert "Correlation" not in out
