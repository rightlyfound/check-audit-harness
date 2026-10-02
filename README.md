# Check Audit Harness

A small Python tool for a practical verification problem: **does a validation check enforce its stated goal, or only a neighboring property?** It searches caller-supplied Hypothesis strategies for counterexamples from deliberately defective implementations, then reports which defects a check accepts.

The included example concerns deduplicating records by `id` while preserving the maximum `updated_at`. A weak check that only rejects duplicate IDs misses wrong-record and missing-key defects; a separately implemented full-goal check rejects the supplied adversaries.

> **Scope:** this is bounded adversarial testing, not a proof or certification. The audit cannot invent missing adversaries, and witness search cannot see inputs excluded by the supplied strategy.

## Quick start

Requires Python 3.10 or newer. From a checkout:

```bash
python -m pip install -e '.[dev]'
check-audit demo --max-examples 500
```

To write a machine-readable result as well:

```bash
check-audit demo --max-examples 500 --seed 17 --json-report audit.json
```

The CLI prints falsification results before its supporting adversary tables, states the known coverage gaps, and ends with a self-check. `--seed` is optional; without it, Hypothesis runs in derandomized mode for repeatability in the same environment. Changing Hypothesis versions or the input strategy can change generated examples. Use `--seed` to select an explicit run seed.

## Use the Python API

```python
from check_audit import Adversary, audit, check_full_goal, records_strategy


# Define an implementation with the same signature as the input-to-output
# transformation being checked.
def drops_everything(records):
    return []


adversaries = [Adversary("drops_all", "missing_key", drops_everything)]
results = audit(
    check_full_goal,
    adversaries,
    input_strategy=records_strategy,
    max_examples=500,
)
for result in results:
    print(result.to_dict())
```

Use `satisfies_goal(inputs, output)` to encode the reference property. Keep that specification independent of the candidate check; otherwise the audit can reproduce the same mistake in both places. In the bundled demo, `check_full_goal` independently computes each id's maximum by scanning the inputs, rather than calling the reference predicate. Custom checks take `(inputs, output)` and return `True` when they accept the output.

## What the bundled audit covers

The demonstration supplies four defect classes: `wrong_record_kept`, `missing_key`, `duplicate_key`, and `no_deduplication`. Its strategy generates lists of up to 25 records, IDs 1–4, timestamps 0–50, and payload strings up to six characters. The four named examples of gaps are tie-breaking ambiguity, input mutation, output aliasing, and partial key collision. These lists are illustrations, not exhaustive taxonomies.

The bundled goal does not specify a payload tie-break when records share the maximum `updated_at`, so either record is acceptable; this example demonstrates the audit method, not a complete specification of deduplication semantics.

A found witness is concrete evidence that the implementation violates the reference goal for that input. A clean result means only that the check rejected the supplied adversaries for which a witness was found. “No witness found” is unresolved; it does not establish that an implementation is correct.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
check-audit demo --max-examples 500
```

CI runs lint and tests on pushes and pull requests. The repository includes `.github/copilot-instructions.md`, `AGENTS.md`, and `skills/check-audit/SKILL.md` to help coding agents understand the project, validate changes, and report audit limits accurately.

## GitHub references

The CI workflow follows GitHub's [Python build and test guidance](https://docs.github.com/actions/guides/building-and-testing-python), including explicit Python setup and test execution. The repository's Copilot-specific instructions use the documented `.github/copilot-instructions.md` location described in [Adding repository custom instructions for GitHub Copilot](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot).
