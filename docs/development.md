# Development

Repo layout, setup, the commands for running the TCK from source, the vendored schema, and coding
conventions. How to run the TCK against an agent, its options and its report are in the
[top-level README](../README.md).

## Layout

The codebase is a version-agnostic core plus one package per protocol version:

- `src/tck/common/` -- the harness, the report model, the requirement-tier vocabulary, the pytest plugin's
  version-agnostic core, and the `VersionSpec` glue that connects a version package to that core.
- `src/tck/v1/` -- ACP v1's protocol constants, vendored schema, requirement registry, schema validation,
  pytest plugin shim, and conformance suite. v1 is the default.
- `src/tck/v2/` -- the same shape for ACP v2 (Draft), behind `--protocol-version 2`.

Nothing under `v2/` imports from `v1/` or the other way round. Each version package is self-contained and
deliberately duplicated, sharing only `common/`, so a new protocol version needs no fork of the harness, report
model or plugin. For the requirements each version covers, read `src/tck/v{1,2}/requirements.py` (the registry,
with citations); it is the source of truth.

Tests mirror the split. `tests/common/`, `tests/v1/` and `tests/v2/` hold unit, registry and CLI tests, and
`tests/fixtures/agents/v{1,2}/` hold the fixture agents (see [Writing tests](writing-tests.md#fixtures)).

The repo holds three uv projects, keeping the product apart from the maintenance tooling:

- Root `acp-tck` -- the product (`src/tck/`, `tests/`). It is also the uv workspace root, but depends on no
  member.
- `spec-tracker/` -- a workspace member that depends on `acp-tck`: the spec maps and the `spec-impact` CLI for
  following spec updates. See [`spec-tracker/README.md`](../spec-tracker/README.md).
- `cross-check/` -- a standalone uv project, excluded from the workspace, that runs the TCK against upstream
  agents and checks an expected baseline. See [`cross-check/README.md`](../cross-check/README.md).

### Plugin shims

Each version's `plugin.py` is a thin shim. It copies every hook and fixture from `tck.common.plugin` into its
own module namespace (via `vars()`, not `import *`, so underscore-named autouse fixtures are not skipped), then
overrides `pytest_configure` to stash that version's `SPEC` before delegating to
`tck.common.plugin.pytest_configure`.

**Footgun:** the copied functions keep `__globals__` pointing at `tck.common.plugin`'s namespace. Only a
function pytest resolves by name as a hook (like `pytest_configure`) can be overridden in a shim. Redefining a
plain helper (e.g. `_build_report`) in `tck.v1.plugin` silently does nothing, because every copied hook still
calls `tck.common.plugin`'s original.

## Setup

```
uv sync --all-packages
```

Plain `uv sync` is exact and removes the `spec-tracker` member from the venv (`uv run --package spec-tracker ...`
puts it back). In editors, the root `.venv` covers the TCK and `spec-tracker`; `cross-check/` has its own
environment (see its README).

## Running the TCK from source

```
uv run acp-tck -- python tests/fixtures/agents/v1/conforming.py
uv run acp-tck --protocol-version 2 -- python tests/fixtures/agents/v2/conforming.py
```

To add pytest's own flags, run a suite with plain pytest:

```
uv run pytest src/tck/v1/conformance -p tck.v1.plugin --tck-agent-cmd 'python tests/fixtures/agents/v1/conforming.py'
```

The plugin shims are deliberately not auto-registered through `pytest11` entry points, so always pass
`-p tck.v1.plugin` or `-p tck.v2.plugin`. Either way the run uses the `pytest.ini` beside the conformance suite,
not the repo's pytest config (see [Testing](testing.md#parallel-by-default)).

## Tests and CI

How to run the repo's own tests and what CI runs are in [Testing](testing.md).

## Vendored schema

`src/tck/v{1,2}/schema/schema.unstable.json` and `meta.unstable.json` are verbatim copies of the ACP JSON Schema
from the spec repo. Do not hand-edit them. Both versions verify against the draft (unstable) superset: the
RFD-gated fields and methods it adds are optional for agents, but any an agent uses are validated against the
draft shapes. The commit hash, vendor date and refresh steps are in each `schema/VENDORED.md`; the update procedure
is in [Spec updates](spec-updates.md).

`tck.v{1,2}.protocol` and `tck.v{1,2}.validation` derive their method tables and validation rules from these files
at import time, so a refresh mostly updates them by itself. Check each `validation.py` docstring for hand-written
carve-outs a refresh could invalidate (e.g. v1's `session/load` null-response quirk, v2's any-array-is-one-issue
rule and open-enum discriminator carve-out).

`tck.v{1,2}.validation` validates only messages the agent under test authors: its requests and notifications to
the client, and its responses to methods it implements. It never validates the mock client's own messages. There
is no `validate_client_message`; add one only if a requirement needs to assert on the TCK's outgoing traffic.

## Conventions

- Keep comments and docstrings concise and plain. Note non-obvious rationale, gotchas and spec citations. Don't
  narrate what the code already says, retell its history, or list exhaustive cases that belong in tests.
- Dependencies are managed with `uv` only, with exact pins (`==`). Never use bare `pip` or hand-edit dependency
  entries in `pyproject.toml`. Add to the product with `uv add ...`, to spec-tracker with
  `uv add --package spec-tracker ...`, and to cross-check with `uv add --project cross-check ...`.
