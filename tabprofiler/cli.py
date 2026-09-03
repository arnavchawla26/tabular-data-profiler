"""Command-line interface for tabprofiler.

    tabprofile profile data.csv --format html --output report.html
    tabprofile demo --format text
"""
from __future__ import annotations

import argparse
import sys

from .io_utils import load_csv_file, load_csv_text
from .profile import profile_table
from .report import RENDERERS
from .synthetic import generate_csv_text


def _write_output(text: str, output_path: str | None) -> None:
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=sorted(RENDERERS.keys()),
        default="text",
        help="Output report format (default: text)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write the report to this file instead of stdout",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of most-common values to report per categorical column (default: 5)",
    )


def cmd_profile(args: argparse.Namespace) -> int:
    delimiter = args.delimiter
    has_header = not args.no_header
    table = load_csv_file(args.csv_path, delimiter=delimiter, has_header=has_header)
    profile = profile_table(table, top_n=args.top_n)
    renderer = RENDERERS[args.format]
    text = renderer(profile)
    _write_output(text, args.output)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    csv_text = generate_csv_text(n=args.rows, seed=args.seed)
    table = load_csv_text(csv_text, delimiter=",", has_header=True)
    profile = profile_table(table, top_n=args.top_n)
    renderer = RENDERERS[args.format]
    text = renderer(profile)
    _write_output(text, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tabprofile",
        description="Dependency-free tabular (CSV) data profiler.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile_parser = subparsers.add_parser(
        "profile", help="Profile a CSV file"
    )
    profile_parser.add_argument("csv_path", help="Path to the CSV file to profile")
    profile_parser.add_argument(
        "--delimiter", default=",", help="Field delimiter (default: ',')"
    )
    profile_parser.add_argument(
        "--no-header",
        action="store_true",
        help="Treat the first row as data, not a header (columns are auto-named)",
    )
    _add_common_args(profile_parser)
    profile_parser.set_defaults(func=cmd_profile)

    demo_parser = subparsers.add_parser(
        "demo", help="Generate a synthetic dataset in-memory and profile it"
    )
    demo_parser.add_argument(
        "--rows", type=int, default=200, help="Number of synthetic rows to generate (default: 200)"
    )
    demo_parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    _add_common_args(demo_parser)
    demo_parser.set_defaults(func=cmd_demo)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
