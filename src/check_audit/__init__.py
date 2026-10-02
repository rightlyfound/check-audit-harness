"""Audit validation checks against seeded, goal-violating implementations."""

from .core import (
    Adversary,
    AdversaryResult,
    audit,
    check_full_goal,
    check_no_duplicate_ids,
    find_witness,
    records_strategy,
    satisfies_goal,
)

__all__ = [
    "Adversary",
    "AdversaryResult",
    "audit",
    "check_full_goal",
    "check_no_duplicate_ids",
    "find_witness",
    "records_strategy",
    "satisfies_goal",
]
