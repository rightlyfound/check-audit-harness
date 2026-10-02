# Repository instructions

This is a small Python package that audits validation checks by searching caller-supplied Hypothesis strategies for examples where seeded adversarial implementations violate a declared goal. A passing audit is bounded evidence, not a correctness proof.

## Layout and commands

- `src/check_audit/core.py`: goal predicate, witness search, and audit API.
- `src/check_audit/adversaries.py`: demonstration implementations and named coverage gaps.
- `src/check_audit/reporting.py` and `cli.py`: text/JSON output and `check-audit` CLI.
- `tests/`: unit and end-to-end tests.
- `.github/workflows/tests.yml`: CI on pushes and pull requests.
- `skills/check-audit/SKILL.md`: reusable workflow for AI coding agents.

Use Python 3.10 or newer. From the repository root, bootstrap with `python -m pip install -e '.[dev]'`. Validate changes with `ruff check .` and `pytest`. Run the demonstration with `check-audit demo --max-examples 500`; add `--json-report audit.json` to save structured results.

Keep the declared goal separate from the check under audit. Do not claim completeness from a PASS: report the adversary set, input strategy, and example budget. Add a focused test whenever goal semantics or report behavior changes. Keep workflow permissions least-privilege and avoid adding publishing credentials or external side effects to CI.
