# State: move maintenance tooling out of the `tck` package into uv workspace members
## Settings
mode: single · branch: orchestrator-skills · reviews: off
(Carried over from the previous goal; re-confirm with the user before delegating.)

## Context
The spec tooling built in the previous goal (below) lives inside the product package:
`src/tck/common/{citations,spec_map,spec_repo}.py`, `src/tck/v{1,2}/spec_map.py`,
`src/tck/v{1,2}/spec_map.toml`, plus `scripts/spec-impact.py`. Nothing in the product imports
them; only tests and the script do. The user sees this as a separation-of-concerns violation:
`tck` is the shipped product, the tooling only maintains it. The user also wants `scripts/` grouped
by purpose, and one tool, uv, managing dependencies for every script, even one-off ones.

## Decisions (final)
- Use a uv workspace. The root is the current `pyproject.toml` (`acp-tck`, the `tck` package),
  unchanged except for `[tool.uv.workspace] members`. The root depends on no member.
- Two members: cross-check and spec-tools. Each has its own `pyproject.toml`, its own
  dependencies and its own tests, kept apart from the root package. Each depends on
  `acp-tck = { workspace = true }`, never the other way round.

## Proposal (not yet decided; discuss each question with the user)
```
pyproject.toml            # acp-tck root + [tool.uv.workspace] members
src/tck/ ...              # product only
tests/ ...                # product tests only
tools/
  cross-check/  pyproject.toml, src/cross_check/ (summary.py, python_v2_agent.py),
                cross-check.sh, tests/ (test_cross_check_summary.py)
  spec-tools/   pyproject.toml, src/spec_tools/ (citations, spec_map, spec_repo, impact CLI),
                maps/v1.toml, maps/v2.toml, tests/ (spec-map/ledger checks, spec_doc fixture,
                test_spec_map, test_citations, test_spec_impact)
```
- Members are real packages (uv_build, `src/` layout, editable), with `[project.scripts]` entry
  points, e.g. `spec-impact = "spec_tools.impact:main"`.
- Members carry `classifiers = ["Private :: Do Not Upload"]` so PyPI rejects an accidental upload.
  `uv build` at the root builds only `acp-tck`.
- Each member has its own `[tool.pytest.ini_options]`. Root `uv run pytest` runs only `tests/`.
  CI uses `uv sync --locked --all-packages`, with one test step per project. The spec-repo fetch
  moves to the spec-tools step: the root tests no longer need the spec checkout.
- `citations.py`: the product registry tests get their own pointer helpers back (as before S2),
  and spec-tools keeps its own copy. That's a little duplication, in exchange for a strictly
  one-way dependency.
- Cross-check: the Python SDK agents under test keep running in ephemeral
  `uv run --no-project --with 'agent-client-protocol==…'` environments, outside the TCK's
  environment (v1 uses `1.0.0rc1`, v2 `1.0.0rc2`; a single workspace lock can't hold both without
  `tool.uv.conflicts`). The member's own dependencies are only what its Python code needs:
  `summary.py` is stdlib, and `python_v2_agent.py` is itself an agent under test. The SDK checkouts
  (Python example agents, Rust `testy`) are still needed.
- Limits the user knows: one `uv.lock` and one `.venv` for all members. Isolation is by
  declaration only, so members must agree on versions.

## Open questions (waiting on the user)
1. Parent folder: `tools/` or keep `scripts/`.
2. Member and package names, e.g. `acp-tck-spec-tools` / `spec_tools`, and
   `acp-tck-cross-check` / `cross_check`.
3. Cross-check SDK agents: keep the `--with` ephemeral runs (recommended), or lock both SDK
   versions in the member through conflicting groups.
4. Members as packages (`src/` layout, entry points; recommended), or as non-package projects
   (`tool.uv.package = false`, scripts run by path).
5. Whether to rename `cross-check.sh` (e.g. `run.sh`) and `cross-check-summary.py` (`summary.py`).

## Plan (draft, once the questions are settled)
- S1 workspace skeleton + cross-check member (move the scripts and their test; fix `cross-check.sh`'s
  `REPO_ROOT`/`SCRIPT_DIR` paths, CI calls, docs).
- S2 spec-tools member (move the modules, maps and tests; drop `src/tck/v{1,2}/spec_map.py` and
  the spec-map checks from `tests/v{1,2}/test_registry.py`; entry point for the impact CLI).
- S3 CI and docs: per-project test steps, spec fetch in the spec-tools step; `AGENTS.md`, both
  `VENDORED.md`, `update-to-spec/SKILL.md`, orchestrator skill grep paths (`src tests tools`).

## Other open items (the user's call, not part of this goal)
- The full suite takes ~15.5 min locally vs the CI `test` job's `timeout-minutes: 20`. Cause: CLI
  self-tests run the whole conformance suite per fixture (97 v2 + 68 v1), with timeouts on defect
  fixtures, and nothing runs in parallel. The user will tackle it later.
- The local spec checkout is on `eugenethedev/end-turn-token-rfd-update`. Put it back on `main`
  before running `/update-to-spec`.
- `/orchestrator` can now be invoked by the model, with no restriction on when. Its
  `description` could say "use only when the user asks or another skill invokes it".

## Done (previous goal: spec-impact tooling, complete)
- Core-docs research — 4a9df3c — reports core-docs-v1.md, core-docs-v2.md
- S1 spec maps — 551d497 — maps, loader, registry checks
- S1b section addressing — 369799f — heading paths, `(intro)`, `resolve_section()`
- S1c CI spec fetch — 0cff7c4 — fetch the pin in the test job; spec_doc fails under CI
- S2 spec-impact report — 408efbe — `scripts/spec-impact.py` + `tck.common.citations`/`spec_repo`
- S3 --fix remap — 1d39ae8 — in-place line remap, needs-review list
- S3b --fix guard — dcab871 — base must equal the pin
- S4 docs — 56387a5 — AGENTS.md spec-map section, narrowed orchestrator grep, VENDORED.md pointer
- Cleanup — 0235c6f — python_v2_agent.py research reference rewritten

## Before merging the PR
Delete `.agents/state.md`, `.agents/prompt.md` (if present) and `.agents/research/`.
