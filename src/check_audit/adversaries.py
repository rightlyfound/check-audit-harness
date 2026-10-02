"""Built-in adversaries used by the runnable demonstration."""

from __future__ import annotations

from .core import Adversary, Record


def correct(records: list[Record]) -> list[Record]:
    best: dict[int, Record] = {}
    for record in records:
        key = record["id"]
        if key not in best or record["updated_at"] > best[key]["updated_at"]:
            best[key] = record
    return list(best.values())


def first_wins(records: list[Record]) -> list[Record]:
    seen: set[int] = set()
    output: list[Record] = []
    for record in records:
        key = record["id"]
        if key not in seen:
            seen.add(key)
            output.append(record)
    return output


def drops_one_id(records: list[Record]) -> list[Record]:
    output = correct(records)
    return output[:-1] if len(output) > 1 else []


def duplicates_one_id(records: list[Record]) -> list[Record]:
    output = correct(records)
    return output + [output[0]] if output else []


def returns_all(records: list[Record]) -> list[Record]:
    return list(records)


DEFAULT_ADVERSARIES = (
    Adversary("first_wins", "wrong_record_kept", first_wins),
    Adversary("drops_one_id", "missing_key", drops_one_id),
    Adversary("duplicates_one_id", "duplicate_key", duplicates_one_id),
    Adversary("returns_all", "no_deduplication", returns_all),
)

# These are examples of gaps in the demo, not an exhaustive taxonomy.
UNCOVERED_CLASSES = (
    "tie_breaking_ambiguity",
    "input_mutation",
    "output_aliasing",
    "partial_key_collision",
)
