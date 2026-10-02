"""Command-line interface for the check-audit demonstration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .adversaries import DEFAULT_ADVERSARIES
from .core import audit, check_full_goal, check_no_duplicate_ids
from .reporting import render_text_report, report_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check-audit",
        description="Audit whether a validation check catches supplied defects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the built-in audit demonstration")
    demo.add_argument(
        "--max-examples",
        type=int,
        default=500,
        help="maximum Hypothesis examples searched per adversary (default: 500)",
    )
    demo.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional Hypothesis seed for repeatable witness search",
    )
    demo.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help="also write a machine-readable JSON report to this path",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_examples < 1:
        raise SystemExit("--max-examples must be at least 1")

    naive = audit(
        check_no_duplicate_ids,
        DEFAULT_ADVERSARIES,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    tracking = audit(
        check_full_goal,
        DEFAULT_ADVERSARIES,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    render_text_report(naive, tracking, max_examples=args.max_examples)

    if args.json_report is not None:
        payload = report_payload(naive, tracking, max_examples=args.max_examples)
        args.json_report.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nJSON report written to {args.json_report}")

    return 0
