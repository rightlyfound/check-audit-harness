from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

import check_audit.core as core
from check_audit.adversaries import (
    DEFAULT_ADVERSARIES,
    UNCOVERED_CLASSES,
    correct,
    first_wins,
    returns_all,
)
from check_audit.cli import main
from check_audit.core import (
    Adversary,
    AdversaryResult,
    audit,
    check_full_goal,
    check_no_duplicate_ids,
    find_witness,
    records_strategy,
    satisfies_goal,
)
from check_audit.reporting import render_text_report, report_payload

EXAMPLE = [
    {"id": 1, "updated_at": 2, "payload": "old"},
    {"id": 1, "updated_at": 5, "payload": "new"},
    {"id": 2, "updated_at": 4, "payload": "two"},
]


def test_correct_implementation_satisfies_goal() -> None:
    assert satisfies_goal(EXAMPLE, correct(EXAMPLE))


def test_uncovered_classes_do_not_overlap_demo_adversaries() -> None:
    covered_classes = {adversary.defect_class for adversary in DEFAULT_ADVERSARIES}
    assert covered_classes.isdisjoint(UNCOVERED_CLASSES)


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


@given(records_strategy, records_strategy)
def test_independent_check_matches_reference(inputs, output) -> None:
    assert check_full_goal(inputs, output) == satisfies_goal(inputs, output)


def test_full_goal_check_does_not_call_reference(monkeypatch) -> None:
    monkeypatch.setattr(
        core,
        "satisfies_goal",
        lambda *_args: pytest.fail("candidate check called the reference predicate"),
    )
    assert check_full_goal(EXAMPLE, correct(EXAMPLE))
    assert not check_full_goal(EXAMPLE, first_wins(EXAMPLE))


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


def test_audit_reports_check_exception_as_error(capsys) -> None:
    def raising_check(_inputs, _output):
        raise RuntimeError("checker boom")

    result = audit(
        raising_check,
        [DEFAULT_ADVERSARIES[0]],
        input_strategy=st.just(EXAMPLE),
        max_examples=1,
    )[0]

    assert result.check_accepted is None
    assert result.check_raised == "RuntimeError: checker boom"
    payload = report_payload([result], [], max_examples=1)
    assert payload["checks"]["naive"][0]["check_raised"] == result.check_raised

    render_text_report([result], [], max_examples=1)
    output = capsys.readouterr().out
    assert "STATUS: ERROR" in output
    assert "ERROR" in output
    assert "RuntimeError: checker boom" in output


def test_self_check_rejects_two_misses_from_unexpected_classes(capsys) -> None:
    synthetic_adversaries = [
        Adversary("fake_first", "unexpected_a", first_wins),
        Adversary("fake_all", "unexpected_b", returns_all),
    ]
    synthetic_results = audit(
        lambda _inputs, _output: True,
        synthetic_adversaries,
        input_strategy=st.just(EXAMPLE),
        max_examples=1,
    )

    render_text_report(synthetic_results, [], max_examples=1)
    assert "FAILED: the observed demo results differ" in capsys.readouterr().out


def test_api_dict_matches_cli_json_item_shape() -> None:
    result = AdversaryResult(
        name="sample",
        defect_class="missing_key",
        witness=EXAMPLE,
        check_accepted=False,
        note="check rejects violator",
    )
    payload = report_payload([result], [], max_examples=1)

    api_value = json.loads(json.dumps(result.to_dict()))
    cli_report_value = payload["checks"]["naive"][0]
    assert cli_report_value == api_value


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
