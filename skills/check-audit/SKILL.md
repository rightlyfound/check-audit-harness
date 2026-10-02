---
name: check-audit
description: Audit a validation check against supplied goal-violating implementations using bounded property-based witness search.
---

# Check Audit Skill

Use this workflow when a developer wants to know whether a validator tracks its stated goal or only a nearby property.

## Procedure

1. Write the intended goal independently of the candidate check. Prefer a precise predicate over prose alone.
2. Define an input strategy that reflects the domain and state its boundaries.
3. Supply adversarial implementations, each labeled with a defect class and a short rationale. Include a known-correct implementation when practical.
4. Run `check-audit demo --max-examples N` for the bundled example, or call `check_audit.audit(check_fn, adversaries, input_strategy=..., max_examples=N)` from Python for a custom audit.
5. Treat any supplied adversary accepted by the check as a falsification of the check's claim for that defect class.
6. Report falsification before supporting examples. Name the tested adversaries, strategy, and budget.
7. Treat “no witness found” as unresolved, not proof. Explicitly list defect classes and input regions that were not covered.

## Interpretation

- A witness establishes a concrete counterexample within the tested setup.
- A clean run only shows that the check rejected the supplied adversaries for which witnesses were found.
- The harness cannot invent missing adversaries and cannot cover values excluded by the input strategy.
- Do not describe a partial audit as a formal proof, exhaustive test, or certification.

## Project validation

From the repository root, install with `python -m pip install -e '.[dev]'`, then run `ruff check .` and `pytest`. The demonstration command is `check-audit demo --max-examples 500`.
