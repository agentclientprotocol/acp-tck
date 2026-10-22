# State: move maintenance tooling out of the `tck` package (spec-tracker workspace member, standalone cross-check)
## Settings
mode: single · branch: orchestrator-skills · reviews: off (confirmed 2026-10-22)

## Context
The spec tooling built in the previous goal lives inside the product package:
`src/tck/common/{citations,spec_map,spec_repo}.py`, `src/tck/v{1,2}/spec_map.py`,
`src/tck/v{1,2}/spec_map.toml`, plus `scripts/spec-impact.py`. Nothing in the product imports
them; only tests and the script do. The user sees this as a separation-of-concerns violation:
`tck` is the shipped product, the tooling only maintains it. The user also wants scripts grouped
by purpose, and one tool, uv, managing dependencies for every script, even one-off ones.

## Decisions (final)
- The repo root stays where it is and becomes the uv workspace root: the current
  `pyproject.toml` (`acp-tck`, the `tck` package), unchanged except for `[tool.uv.workspace]`.
  The root depends on no member.
- `[tool.uv.workspace]`: `members = ["spec-tracker"]`, `exclude = ["cross-check"]`. Explicit, no globs.
- `spec-tracker` (package `spec_tracker`) is a nested workspace member with its own
  `pyproject.toml`, dependencies and tests. It depends on `acp-tck = { workspace = true }`, never
  the other way round. Declare that source in the member's own `pyproject.toml` (IntelliJ bug
  PY-89867). Real package (uv_build, `src/` layout, editable), entry point
  `spec-impact = "spec_tracker.impact:main"`, run as `uv run --package spec-tracker spec-impact ...`,
  `classifiers = ["Private :: Do Not Upload"]`. `uv build` at the root builds only `acp-tck`.
- `cross-check` is a standalone nested uv project, not a workspace member: own `pyproject.toml`
  (`tool.uv.package = false`), `uv.lock` and `.venv`. It doesn't depend on `acp-tck`; it runs the
  TCK as a CLI (`uv run --project "$REPO_ROOT" acp-tck`).
- Cross-check deps: `agent-client-protocol==1.0.0rc2` (regular dependency, locked) and dev
  `pytest`. Both Python agents (SDK checkout's `examples/echo_agent.py` for v1, repo-owned
  `python_v2_agent.py` for v2) run in cross-check's own env. No `--with`, no `rc1`.
  Why: echo_agent gives identical results on rc1 and rc2 (probe 2026-10-22: FAIL `ACP-INIT-003`
  MANDATORY + `ACP-INIT-004`, `ACP-JSONRPC-004`, `ACP-SESSION-004` ADVISORY on both; the baseline
  checks MANDATORY only). rc1 was just the latest release when the script was written (a080fee).
- Both projects sit at the repo root (no `tools/` parent). `scripts/` goes away.
- Renames: `cross-check.sh` -> `run.sh`, `cross-check-summary.py` -> `summary.py`.
- Each project has its own `[tool.pytest.ini_options]`. Root `uv run pytest` runs only `tests/`.
- `citations.py`: the product registry tests get their own pointer helpers back (as before the
  previous goal's S2), and spec-tracker keeps its own copy. A little duplication for a strictly
  one-way dependency.
- CI: root `test` job `uv sync --locked` + `uv run pytest`; a spec-tracker step
  `uv run --locked --package spec-tracker pytest spec-tracker/tests` takes over the spec-repo
  fetch (root tests no longer need the spec checkout); the cross-check job syncs and tests in its
  own dir.
- Docs: `uv sync --all-packages` (not plain `uv sync`) for local dev; editor note: open
  `cross-check/` as its own editor root for completion there.
- Rejected: cross-check as a member (shared venv, isolation only declared); moving the TCK into
  a subdir (no root `uv run acp-tck`: uv has no config key for it, and README/LICENSE must be
  symlinked into the project dir for uv_build).

Layout:
```
pyproject.toml   # acp-tck root + [tool.uv.workspace] members/exclude
src/tck/         # product only
tests/           # product tests only
cross-check/     # standalone: pyproject.toml, uv.lock, run.sh, summary.py, python_v2_agent.py,
                 # tests/test_summary.py
spec-tracker/    # member: pyproject.toml, src/spec_tracker/ (citations, spec_map, spec_repo,
                 # impact CLI), maps/v1.toml, maps/v2.toml, tests/ (spec-map/ledger checks,
                 # spec_doc fixture, test_spec_map, test_citations, test_spec_impact)
```

## Facts checked (uv 0.13)
- A non-member nested project gets its own `.venv` and `uv.lock`; `uv sync --all-packages` at
  the root never touches it.
- `uv sync` is exact by default (removes other members' packages unless `--all-packages` or
  `--inexact`); `uv run` is inexact unless `--exact`.
- Editors: IntelliJ's pyproject-based project model gives each project its own env (PyCharm docs;
  not verified in IntelliJ IDEA). Pyright/Pylance at the repo root use the root `.venv` for
  cross-check too, so `acp` in `python_v2_agent.py` won't resolve unless cross-check is opened as
  its own editor root.
- No Python SDK is attached to `acp-tck` in the user's IntelliJ (`.idea` is a bare `JAVA_MODULE`).

## Plan (approved)
- S1 standalone cross-check project: move `scripts/cross-check.sh` -> `cross-check/run.sh`,
  `scripts/cross-check-summary.py` -> `cross-check/summary.py`,
  `scripts/cross-check/python_v2_agent.py` -> `cross-check/python_v2_agent.py`,
  `tests/common/test_cross_check_summary.py` -> `cross-check/tests/test_summary.py`; pyproject +
  lock; fix `REPO_ROOT`/`SCRIPT_DIR` and `uv run` calls; CI cross-check job paths.
- S2 spec-tracker member + root `[tool.uv.workspace]`: move the modules, maps, tests and
  `scripts/spec-impact.py` (as the entry point); drop `src/tck/v{1,2}/spec_map.py` and the
  spec-map checks from `tests/v{1,2}/test_registry.py`; restore registry pointer helpers; CI step.
- S3 docs: `AGENTS.md`/`CLAUDE.md`, README, both `VENDORED.md`, `update-to-spec/SKILL.md`,
  orchestrator skill grep paths (`src tests cross-check spec-tracker`), editor + `--all-packages`
  notes. Then the `.agents/` reference check.

## Done
(none yet)

## Next
- S1 (programmer, single mode).

## Open questions (waiting on the user)
None.

## Other open items (the user's call, not part of this goal)
- The full suite takes ~15.5 min locally vs the CI `test` job's `timeout-minutes: 20`. Cause: CLI
  self-tests run the whole conformance suite per fixture, nothing runs in parallel.
- The local spec checkout is on `eugenethedev/end-turn-token-rfd-update`. Put it back on `main`
  before running `/update-to-spec`.
- `/orchestrator` can be invoked by the model with no restriction. Its `description` could say
  "use only when the user asks or another skill invokes it".
- `examples/echo_agent.py` runs from the SDK checkout's HEAD, not the tag matching the pin; `rc3`
  exists (bumping may move the v2 cross-check baseline).

## Done (previous goal: spec-impact tooling, complete)
- Core-docs research 4a9df3c · S1 spec maps 551d497 · S1b section addressing 369799f ·
  S1c CI spec fetch 0cff7c4 · S2 spec-impact report 408efbe · S3 --fix remap 1d39ae8 ·
  S3b --fix guard dcab871 · S4 docs 56387a5 · Cleanup 0235c6f

## Before merging the PR
Delete `.agents/state.md`, `.agents/prompt.md` (if present) and `.agents/research/`.
