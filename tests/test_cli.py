import json
import subprocess
import sys

import pytest

from tabprofiler.cli import build_parser, main


CSV = "id,age,score\n1,25,88.5\n2,30,91.0\n3,25,88.5\n"


def test_build_parser_requires_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_profile_text_to_stdout(tmp_path, capsys):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(CSV)
    rc = main(["profile", str(csv_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Tabular Data Profile" in out
    assert "Column: age" in out


def test_cli_profile_json_to_file(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(CSV)
    out_path = tmp_path / "report.json"
    rc = main(["profile", str(csv_path), "--format", "json", "--output", str(out_path)])
    assert rc == 0
    data = json.loads(out_path.read_text())
    assert data["n_rows"] == 3
    assert data["n_cols"] == 3


def test_cli_profile_html_to_file(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(CSV)
    out_path = tmp_path / "report.html"
    rc = main(["profile", str(csv_path), "--format", "html", "--output", str(out_path)])
    assert rc == 0
    content = out_path.read_text()
    assert content.startswith("<!doctype html>")


def test_cli_profile_custom_delimiter_and_no_header(tmp_path, capsys):
    csv_path = tmp_path / "data.tsv"
    csv_path.write_text("1\t2\n3\t4\n")
    rc = main(["profile", str(csv_path), "--delimiter", "\t", "--no-header"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "column_1" in out
    assert "column_2" in out


def test_cli_demo_default_text(capsys):
    rc = main(["demo", "--rows", "50"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Tabular Data Profile" in out
    assert "50 rows" not in out  # text renderer doesn't use this exact phrase
    assert "Rows: 50" in out


def test_cli_demo_json_deterministic(capsys):
    main(["demo", "--rows", "40", "--seed", "1", "--format", "json"])
    first = capsys.readouterr().out
    main(["demo", "--rows", "40", "--seed", "1", "--format", "json"])
    second = capsys.readouterr().out
    assert first == second
    data = json.loads(first)
    assert data["n_rows"] == 40


def test_cli_demo_top_n_limits_categorical_values(capsys):
    main(["demo", "--rows", "200", "--seed", "42", "--format", "json", "--top-n", "1"])
    data = json.loads(capsys.readouterr().out)
    plan_col = next(c for c in data["columns"] if c["name"] == "plan")
    assert len(plan_col["categorical"]["top_values"]) == 1


def test_cli_module_entrypoint_subprocess():
    # End-to-end sanity check that `python -m tabprofiler.cli demo` works as
    # a real subprocess, not just via the in-process `main()` function.
    result = subprocess.run(
        [sys.executable, "-m", "tabprofiler.cli", "demo", "--rows", "20", "--format", "text"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "Tabular Data Profile" in result.stdout


def test_cli_profile_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        main(["profile", "/nonexistent/path/does-not-exist.csv"])
