#!/usr/bin/env python3
"""Compute README badge values for coverage and CodeScene code-health.

Usage::

    # requires: uv sync --group dev
    uv run --group dev python scripts/compute_metrics.py coverage

    # then (via Claude + CodeScene MCP):
    uv run python scripts/compute_metrics.py codescene-plan

The coverage subcommand runs ``coverage run -m unittest`` against ``tests/``
and prints a ready-to-paste shields.io badge URL plus a Markdown snippet.

The codescene-plan subcommand lists every Python file under ``mcp_server/``
with its non-empty line-of-code weight, and tells the maintainer how to
aggregate per-file ``code_health_score`` values (LOC-weighted mean, one
decimal). It then prints the badge template once the aggregate is in hand.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "mcp_server"
TESTS_DIR = REPO_ROOT / "tests"


def _coverage_color(percent: float) -> str:
    if percent >= 90:
        return "brightgreen"
    if percent >= 80:
        return "green"
    if percent >= 60:
        return "yellow"
    if percent >= 40:
        return "orange"
    return "red"


def _codescene_color(score: float) -> str:
    if score >= 9.0:
        return "brightgreen"
    if score >= 7.0:
        return "green"
    if score >= 4.0:
        return "yellow"
    return "red"


def _iter_source_files() -> Iterable[Path]:
    for path in sorted(SOURCE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _non_empty_loc(path: Path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def _run(cmd: list[str]) -> Tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def cmd_coverage(_args: argparse.Namespace) -> int:
    code, stdout, stderr = _run(
        ["coverage", "run", "--rcfile=pyproject.toml", "-m", "unittest", "discover", "-s", "tests", "-q"],
    )
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    if code != 0:
        print("coverage run failed", file=sys.stderr)
        return code

    code, stdout, stderr = _run(["coverage", "report", "--format=total"])
    sys.stderr.write(stderr)
    if code != 0:
        print("coverage report --format=total failed", file=sys.stderr)
        return code

    try:
        percent = float(stdout.strip())
    except ValueError:
        print("Could not parse coverage total: {!r}".format(stdout), file=sys.stderr)
        return 1

    color = _coverage_color(percent)
    percent_int = int(round(percent))
    badge_url = "https://img.shields.io/badge/coverage-{pct}%25-{color}".format(
        pct=percent_int, color=color
    )
    markdown = "[![Coverage]({url})](#regenerating-badges)".format(url=badge_url)

    print()
    print("Coverage: {:.1f}% (color: {})".format(percent, color))
    print("Badge URL:   {}".format(badge_url))
    print("Markdown:    {}".format(markdown))
    return 0


def cmd_codescene_plan(_args: argparse.Namespace) -> int:
    files = list(_iter_source_files())
    if not files:
        print("No Python files under {}".format(SOURCE_DIR), file=sys.stderr)
        return 1

    rows = []
    total_loc = 0
    for path in files:
        loc = _non_empty_loc(path)
        total_loc += loc
        rows.append((path.relative_to(REPO_ROOT), loc))

    print("CodeScene code-health plan for {}".format(SOURCE_DIR.relative_to(REPO_ROOT)))
    print("Run mcp__codescene__code_health_score on each file below, then")
    print("compute LOC-weighted mean = sum(score * loc) / {}.".format(total_loc))
    print()
    print("{:<50} {:>10}".format("file", "non-empty LOC"))
    print("-" * 62)
    for rel, loc in rows:
        print("{:<50} {:>10}".format(str(rel), loc))
    print("-" * 62)
    print("{:<50} {:>10}".format("TOTAL", total_loc))
    print()
    print("Once the aggregate score is known (one decimal place), paste:")
    print("  [![CodeScene Code Health](https://img.shields.io/badge/CodeScene-<SCORE>%2F10-<COLOR>)](#regenerating-badges)")
    print("  color thresholds: >=9.0 brightgreen | >=7.0 green | >=4.0 yellow | <4.0 red")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_cov = sub.add_parser("coverage", help="Run coverage and emit a shields.io badge URL")
    p_cov.set_defaults(func=cmd_coverage)

    p_cs = sub.add_parser("codescene-plan", help="List files + LOC weights for CodeScene aggregation")
    p_cs.set_defaults(func=cmd_codescene_plan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
