from __future__ import annotations

import json

import pytest
from hypothesis import strategies as st

from check_audit.adversaries import DEFAULT_ADVERSARIES, correct, first_wins
from check_audit.cli import main
from check_audit.core import (
    audit,
    check_full_goal,
    check_no_duplicate_ids,
    find_witness,
    satisfies_goal,
)

EXAMPLE = [
    {"id": 1, "updated_at": 2, "payload": "old"},
    {"id": 1, "updated_at": 5, "payload": "new"},
    {"id": 2, "updated_at": 4, "payload": "two"},
]


def test_correct_implementation_satisfies_goal() -> None:
    assert satisfies_goal(EXAMPLE, correct(EXAMPLE))


def test_goal_rejects_wrong_timestamp_missing_key_and_duplicate() -> None:
    assert not satisfies_goal(EXAMPLE, first_wins(EXAMPLE))
    assert not satisfies_goal(EXAMPLE, correct(EXAMPLE)[:-1])
    output = correct(EXAMPLE)
    assert not satisfies_goal(EXAMPLE, output + [output[0]])


def test_empty_input_has_empty_output() -> None:
    assert satisfies_goal([], [])
    assert not satisfies_goal([], [{"id": 1, "updated_at": 0}])


def test_malformed_output_is_not_accepted() -> None:
    assert not satisfies_goal(EXAMPLE, [{"id": 1}])
    assert not satisfies_goal(EXAMPLE, None)  # type: ignore[arg-type]


def test_find_witness_respects_a_fixed_input_strategy() -> None:
    witness = find_witness(
        first_wins,
        input_strategy=st.just(EXAMPLE),
        max_examples=1,
        seed=7,
    )
    assert witness == EXAMPLE


def test_audit_distinguishes_neighbor_check_from_full_goal_check() -> None:
    naive_results = audit(check_no_duplicate_ids, DEFAULT_ADVERSARIES, max_examples=500)
    tracking_results = audit(check_full_goal, DEFAULT_ADVERSARIES, max_examples=500)

    naive_misses = {
        result.defect_class for result in naive_results if result.check_accepted
    }
    assert naive_misses == {"wrong_record_kept", "missing_key"}
    assert all(result.witness is not None for result in tracking_results)
    assert all(result.check_accepted is False for result in tracking_results)


def test_cli_emits_text_and_json_report(tmp_path, capsys) -> None:
    report_path = tmp_path / "audit.json"
    exit_code = main(
        [
            "demo",
            "--max-examples",
            "500",
            "--seed",
            "17",
            "--json-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "STATUS: FAIL" in output
    assert "Harness self-check" in output
    assert "OK: the harness flags" in output
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["status"] == "PARTIAL"
    assert len(data["checks"]["tracking"]) == 4


def test_find_witness_rejects_nonpositive_example_budget() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        find_witness(first_wins, max_examples=0)
