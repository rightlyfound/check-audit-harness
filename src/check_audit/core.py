"""Core functions for auditing validation checks against adversarial programs."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import seed as hypothesis_seed
from hypothesis import strategies as st

Record = dict[str, Any]
Implementation = Callable[[list[Record]], list[Record]]
Check = Callable[[list[Record], list[Record]], bool]

record_strategy = st.fixed_dictionaries(
    {
        "id": st.integers(min_value=1, max_value=4),
        "updated_at": st.integers(min_value=0, max_value=50),
        "payload": st.text(max_size=6),
    }
)
records_strategy = st.lists(record_strategy, max_size=25)


@dataclass(frozen=True)
class Adversary:
    """A deliberately defective implementation and the defect it represents."""

    name: str
    defect_class: str
    implementation: Implementation


@dataclass
class AdversaryResult:
    """Outcome of testing one check against one supplied adversary."""

    name: str
    defect_class: str
    witness: list[Record] | None
    check_accepted: bool | None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


class _WitnessFound(Exception):
    def __init__(self, records: list[Record]) -> None:
        self.records = records


def satisfies_goal(inputs: Sequence[Record], output: Sequence[Record]) -> bool:
    """Return whether output has one max-timestamp record for every input id.

    Malformed records or outputs are treated as not satisfying the goal.
    Payloads are intentionally unconstrained: the goal is about id uniqueness
    and the maximum ``updated_at`` value only.
    """
    try:
        expected: dict[Any, Any] = {}
        for record in inputs:
            key = record["id"]
            timestamp = record["updated_at"]
            if key not in expected or timestamp > expected[key]:
                expected[key] = timestamp

        observed: dict[Any, Any] = {}
        for record in output:
            key = record["id"]
            if key in observed:
                return False
            observed[key] = record["updated_at"]
    except (KeyError, TypeError, AttributeError):
        return False

    return set(observed) == set(expected) and all(
        observed[key] == expected[key] for key in expected
    )


def find_witness(
    implementation: Implementation,
    *,
    input_strategy: st.SearchStrategy[list[Record]] = records_strategy,
    max_examples: int = 500,
    seed: int | None = None,
) -> list[Record] | None:
    """Find one input on which ``implementation`` violates the goal.

    Search is bounded by both ``input_strategy`` and ``max_examples``. A found
    example stops the run immediately; Hypothesis shrinking is intentionally
    skipped so the audit remains a witness finder rather than a full test run.
    """
    if max_examples < 1:
        raise ValueError("max_examples must be at least 1")

    @given(input_strategy)
    @settings(
        max_examples=max_examples,
        deadline=None,
        derandomize=True,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def probe(records: list[Record]) -> None:
        original = deepcopy(records)
        output = implementation(deepcopy(records))
        if not satisfies_goal(original, output):
            raise _WitnessFound(original)

    if seed is not None:
        probe = hypothesis_seed(seed)(probe)
    try:
        probe()
    except _WitnessFound as found:
        return found.records
    return None


def audit(
    check: Check,
    adversaries: Sequence[Adversary],
    *,
    input_strategy: st.SearchStrategy[list[Record]] = records_strategy,
    max_examples: int = 500,
    seed: int | None = None,
) -> list[AdversaryResult]:
    """Measure whether ``check`` accepts any supplied goal violators."""
    results: list[AdversaryResult] = []
    for adversary in adversaries:
        witness = find_witness(
            adversary.implementation,
            input_strategy=input_strategy,
            max_examples=max_examples,
            seed=seed,
        )
        if witness is None:
            results.append(
                AdversaryResult(
                    adversary.name,
                    adversary.defect_class,
                    None,
                    None,
                    f"no witness found within {max_examples} examples; not a proof",
                )
            )
            continue

        output = adversary.implementation(deepcopy(witness))
        accepted = check(deepcopy(witness), output)
        results.append(
            AdversaryResult(
                adversary.name,
                adversary.defect_class,
                witness,
                accepted,
                "check accepts violator" if accepted else "check rejects violator",
            )
        )
    return results


def check_no_duplicate_ids(_inputs: list[Record], output: list[Record]) -> bool:
    """A deliberately weak check that only enforces unique output ids."""
    try:
        ids = [record["id"] for record in output]
        return len(ids) == len(set(ids))
    except (KeyError, TypeError):
        return False


def check_full_goal(inputs: list[Record], output: list[Record]) -> bool:
    """Independently check the goal using per-id scans rather than accumulation."""
    try:
        input_ids = {record["id"] for record in inputs}
        output_ids = [record["id"] for record in output]
        if len(output_ids) != len(input_ids) or set(output_ids) != input_ids:
            return False

        for key in input_ids:
            expected_max = max(
                record["updated_at"] for record in inputs if record["id"] == key
            )
            actual = next(
                record["updated_at"] for record in output if record["id"] == key
            )
            if actual != expected_max:
                return False
    except (KeyError, TypeError, ValueError, StopIteration):
        return False
    return True
