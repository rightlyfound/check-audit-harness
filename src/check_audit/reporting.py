"""Human-readable and machine-readable rendering for audit outcomes."""

from __future__ import annotations

from typing import Any

from .adversaries import DEFAULT_ADVERSARIES, UNCOVERED_CLASSES
from .core import AdversaryResult


def _print_check(name: str, results: list[AdversaryResult]) -> None:
    missed = [result for result in results if result.check_accepted is True]
    errors = [result for result in results if result.check_raised is not None]
    found = [
        result
        for result in results
        if result.witness is not None and result.check_raised is None
    ]
    print(f"\n=== FALSIFICATION: check '{name}' ===")
    if missed:
        classes = ", ".join(result.defect_class for result in missed)
        print("STATUS: FAIL")
        print(
            f"  The check accepts {len(missed)} of {len(results)} supplied violators."
        )
        print(f"  Defect classes missed: {classes}")
        print("  -> The check tracks a neighbor of the goal, not the goal.")
        if errors:
            print(f"  Additional check errors (not verdicts): {len(errors)}")
    elif errors:
        print("STATUS: ERROR")
        print(f"  The check raised on {len(errors)} supplied witnesses.")
        print("  Those cases have no accept/reject verdict.")
    else:
        print("STATUS: PASS (on covered classes)")
        print(f"  The check rejects all {len(found)} violators with found witnesses.")
        print("  This does NOT mean the check is complete. See bounds below.")


def _self_check_passes(
    naive_results: list[AdversaryResult],
    tracking_results: list[AdversaryResult],
) -> bool:
    expected_naive_misses = {"wrong_record_kept", "missing_key"}
    naive_misses = {
        result.defect_class for result in naive_results if result.check_accepted is True
    }
    tracking_misses = {
        result.defect_class
        for result in tracking_results
        if result.check_accepted is True
    }
    check_errors = any(
        result.check_raised is not None
        for result in (*naive_results, *tracking_results)
    )
    return (
        naive_misses == expected_naive_misses
        and not tracking_misses
        and not check_errors
    )


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
            elif result.check_raised is not None:
                check = "error"
                witness = "found"
                verdict = "ERROR"
            else:
                check = "accepts" if result.check_accepted else "rejects"
                witness = "found"
                verdict = "DEFECT" if result.check_accepted else "OK"
            print(
                f"{result.name:<22}{result.defect_class:<24}"
                f"{witness:<10}{check:<10}{verdict}"
            )
            if result.check_raised is not None:
                print(f"  exception: {result.check_raised}")

    print("\n=== Bounds on the negative ===")
    covered = ", ".join(adversary.defect_class for adversary in DEFAULT_ADVERSARIES)
    print(f"  Covered by supplied demo adversaries: {covered}")
    print("  Example gaps not covered by this demo:")
    for defect_class in UNCOVERED_CLASSES:
        print(f"    - {defect_class}")
    print(
        "  Passing means surviving these supplied adversaries, not proving correctness."
    )

    naive_misses = {
        result.defect_class for result in naive_results if result.check_accepted is True
    }
    tracking_misses = {
        result.defect_class
        for result in tracking_results
        if result.check_accepted is True
    }
    print("\n=== Harness self-check ===")
    if _self_check_passes(naive_results, tracking_results):
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
