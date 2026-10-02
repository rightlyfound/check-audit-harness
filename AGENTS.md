# Agent guidance

This repository is a Python package for bounded adversarial audits of validation checks. The goal predicate lives in `src/check_audit/core.py`; the bundled example defects are in `src/check_audit/adversaries.py`; reports and the CLI are in `reporting.py` and `cli.py`.

Install with `python -m pip install -e '.[dev]'`. Before considering a change complete, run `ruff check .` and `pytest`. Smoke-test the user command with `check-audit demo --max-examples 500`.

Keep the reference goal independent from the candidate check. Preserve explicit boundaries around adversary coverage and generated inputs. A PASS is not a proof; a missing witness is inconclusive. Add or update tests for behavior changes, and do not broaden claims beyond what the strategy and adversary set exercise. The CI workflow is `.github/workflows/tests.yml` and grants only read access to repository contents.
