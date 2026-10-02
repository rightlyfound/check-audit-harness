"""Human-readable and machine-readable rendering for audit outcomes."""

from __future__ import annotations

from typing import Any

from .adversaries import DEFAULT_ADVERSARIES, UNCOVERED_CLASSES
from .core import AdversaryResult


def _print_check(name: str, results: list[AdversaryResult]) -> None:
    missed = [result for result in results if result.check_accepted is True]
    found = [result for result in results if result.witness is not None]
    print(f"\n=== FALSIFICATION: check '{name}' ===")
    if missed:
        classes = ", ".join(result.defect_class for result in missed)
        print("STATUS: FAIL")
        print(
            f"  The check accepts {len(missed)} of {len(results)} supplied violators."
        )
        print(f"  Defect classes missed: {classes}")
        print("  -> The check tracks a neighbor of the goal, not the goal.")
    else:
        print("STATUS: PASS (on covered classes)")
        print(f"  The check rejects all {len(found)} violators with found witnesses.")
        print("  This does NOT mean the check is complete. See bounds below.")


def render_text_report(
    naive_results: list[AdversaryResult],
    tracking_results: list[AdversaryResult],
    *,
    max_examples: int,
) -> None:
    """Print the demo outcome, with falsification results before detail."""
    print("GOAL:")
    print("  For each input id, output exactly one record with the maximum updated_at.")
    print("\nSTATUS: PARTIAL")
    print(f"  Adversaries supplied: {len(DEFAULT_ADVERSARIES)}")
    print(f"  Named demo coverage gaps: {len(UNCOVERED_CLASSES)}")
    print(f"  Max {max_examples} generated examples per adversary")

    _print_check("naive (no duplicate ids)", naive_results)
    _print_check("tracking (full goal)", tracking_results)

    for check_name, results in (
        ("naive", naive_results),
        ("tracking", tracking_results),
    ):
        print(f"\n=== Supporting: {check_name} adversary table ===")
        print(
            f"{'adversary':<22}{'defect class':<24}{'witness':<10}{'check':<10}verdict"
        )
        print("-" * 80)
        for result in results:
            if result.witness is None:
                check = "-"
                witness = "none"
                verdict = "UNRESOLVED"
            else:
                check = "accepts" if result.check_accepted else "rejects"
                witness = "found"
                verdict = "DEFECT" if result.check_accepted else "OK"
            print(
                f"{result.name:<22}{result.defect_class:<24}"
                f"{witness:<10}{check:<10}{verdict}"
            )

    print("\n=== Bounds on the negative ===")
    covered = ", ".join(adversary.defect_class for adversary in DEFAULT_ADVERSARIES)
    print(f"  Covered by supplied demo adversaries: {covered}")
    print("  Example gaps not covered by this demo:")
    for defect_class in UNCOVERED_CLASSES:
        print(f"    - {defect_class}")
    print(
        "  Passing means surviving these supplied adversaries, not proving correctness."
    )

    naive_misses = sum(result.check_accepted is True for result in naive_results)
    tracking_misses = sum(result.check_accepted is True for result in tracking_results)
    print("\n=== Harness self-check ===")
    if naive_misses == 2 and tracking_misses == 0:
        print("OK: the harness flags the weak check and clears the full-goal check.")
    else:
        print("FAILED: the observed demo results differ from the expected behavior.")
        print(
            f"  weak-check misses: {naive_misses}; full-goal misses: {tracking_misses}"
        )


def report_payload(
    naive_results: list[AdversaryResult],
    tracking_results: list[AdversaryResult],
    *,
    max_examples: int,
) -> dict[str, Any]:
    """Build the machine-readable report payload."""
    return {
        "status": "PARTIAL",
        "max_examples_per_adversary": max_examples,
        "covered_defect_classes": [item.defect_class for item in DEFAULT_ADVERSARIES],
        "uncovered_example_classes": list(UNCOVERED_CLASSES),
        "checks": {
            "naive": [result.to_dict() for result in naive_results],
            "tracking": [result.to_dict() for result in tracking_results],
        },
    }
