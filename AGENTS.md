# acp-tck

A Test Compatibility Kit for the [Agent Client Protocol](https://agentclientprotocol.com) (ACP).
It launches an agent implementation as a stdio subprocess and drives it through the protocol to
check conformance -- initialize, session lifecycle, prompt turns, cancellation, error handling,
and transport hygiene -- reporting which requirements pass, fail, are not applicable, or were
never exercised.

## Architecture

The codebase is split into a version-agnostic core and one package per protocol version:

- `src/tck/common/` -- harness, report model, requirement-tier vocabulary, and the pytest
  plugin's version-agnostic core, plus the `VersionSpec` glue that connects a version package to
  that core.
- `src/tck/v1/` -- ACP v1's protocol constants, vendored schema, requirement registry, schema
  validation, pytest plugin shim, and full conformance suite. v1 is the default and complete.
- `src/tck/v2/` -- the same shape for ACP v2 (Draft). Nothing under `v2/` imports from `v1/` or
  vice versa -- each version package is a self-contained, honestly-duplicated implementation
  sharing only `common/`. v2 is behind `--protocol-version 2` and still growing.

This split lets a new protocol version be added without duplicating or forking the harness,
report model, or plugin machinery. For the precise, current set of requirements each version
covers, read `src/tck/v{1,2}/requirements.py` (the registry, with citations) rather than this
file -- it's the source of truth and won't drift the way a prose summary would.

The repo holds three uv projects, with the product kept apart from the maintenance tooling:

- Root `acp-tck` -- the product (`src/tck/`, `tests/`). It is also the uv workspace root, but
  depends on no member.
- `spec-tracker/` -- a workspace member that depends on `acp-tck`: spec maps and the `spec-impact`
  CLI for following spec updates. Read `spec-tracker/README.md` before working on it or on a spec
  update.
- `cross-check/` -- a standalone uv project, excluded from the workspace, that runs the TCK
  against upstream agents and checks an expected baseline. Read `cross-check/README.md` before
  working on it.

Each version's `plugin.py` is a thin shim: it copies every hook/fixture from `tck.common.plugin`
into its own module namespace (via `vars()`, not `import *`, so underscore-named autouse
fixtures aren't skipped), then overrides `pytest_configure` to stash that version's `SPEC` before
delegating to `tck.common.plugin.pytest_configure`. **Footgun:** the copied functions keep
`__globals__` pointing at `tck.common.plugin`'s own namespace, so only a function pytest resolves
*by name as a hook* (like `pytest_configure`) can actually be overridden in a shim -- redefining
a plain helper (e.g. `_build_report`) in `tck.v1.plugin` would silently do nothing, since every
copied hook still calls `tck.common.plugin`'s original.

Mirroring this split, `tests/common/`, `tests/v1/`, `tests/v2/` hold unit/registry/CLI tests, and
`tests/fixtures/agents/v{1,2}/` hold pure-stdlib, deterministic, offline fixture agents: a
conforming baseline plus one fixture per defect, each designed to trip exactly the requirement(s)
named in its filename/docstring. Read a conformance test's own `@pytest.mark.requirement(...)`/
`@pytest.mark.capability(...)` markers, and a fixture's own docstring, for ground truth --
`tests/v{1,2}/test_cli.py` asserts each fixture's exact FAIL/PASS set (see
[Writing tests](docs/writing-tests.md#fixtures)).

## Running the TCK against an agent

```
uv run acp-tck -- python tests/fixtures/agents/v1/conforming.py
uv run acp-tck --protocol-version 2 -- python tests/fixtures/agents/v2/conforming.py
```

Key options: `--agent-cwd DIR`, `--agent-env KEY=VAL` (repeatable), `--timeout S` (per-response
deadline, default 30), `--startup-timeout S`, `--test-timeout S` (per-test watchdog),
`--cancel-prompt TEXT` (prompt text for cancellation tests -- needs to keep a real agent busy
long enough for `session/cancel` to land; SKIP with "cancellation not exercised" means the race
was inconclusive, not that the agent failed), `--report-json PATH`, `--close-grace S`, `-k EXPR`,
`--protocol-version {1,2}` (default 1), `--auth-method ID` (drives `authenticate`/`auth/login`
before session-dependent tests; without it, auth-gated agents SKIP those tests and the run is
forced NOT CONFORMANT via `Verdict.blocked_by_auth`), `--allow-logout` (opt-in to actually
calling `logout`/`auth/logout`, since it may revoke the operator's own credentials).

If the embedded login (`authenticate`/`auth/login`) never answers within the timeout -- an
interactive login may stay pending -- the test SKIPs with an `AUTH-GATED:` reason and a hint
(`tck.common.plugin.skip_if_login_times_out`) instead of FAILing, and the run is blocked by auth
like any other auth-gated SKIP. Use a non-interactive `--auth-method` or raise the timeouts.

If an agent negotiates down to a different protocol version than requested (e.g. a v1-only
agent run under `--protocol-version 2`), every requirement that judges the *result's shape*
against that version's rules SKIPs with a `"VERSION-MISMATCH:"`-prefixed message rather than
failing, and the run is forced NOT CONFORMANT (`Verdict.blocked_by_version_mismatch`) even with
zero FAILs. Requirements that judge only the negotiation *outcome* are judged normally and PASS
on an honest downgrade.

If the main `initialize` is instead *rejected* with `-32022` (unsupported protocol version --
e.g. a v2-only agent under the default v1 suite), the connection is not initialized, so
`tck.common.plugin`'s version-rejection gate SKIPs every test with `VERSION-MISMATCH:` and the
run is blocked the same way. Only tests marked `@pytest.mark.negotiation` still run (v2's
version-tolerant `ACP-INIT-*` rows); v1 marks none, because its negotiation rule ("respond with
the latest version it supports") predates `-32022` and cannot judge a v2-only agent.

**Exit code** is the four-status verdict, not pytest's own: `0` iff `verdict.conformant` (no
MANDATORY FAIL/NOT_TESTED, no CAPABILITY FAIL, no auth/version-mismatch block), `1` otherwise.

You can also run the suite directly with plain pytest to add pytest's own flags, e.g.:

```
uv run pytest src/tck/v1/conformance -p tck.v1.plugin --tck-agent-cmd 'python tests/fixtures/agents/v1/conforming.py'
```

The plugin shims are deliberately not auto-registered via `pytest11` entry points -- always pass
`-p tck.v1.plugin` / `-p tck.v2.plugin` explicitly.

## Running the repo's own tests

```
uv run pytest
```

Runs only `tests/` (`spec-tracker/` and `cross-check/` have their own suites, see their READMEs):
harness unit tests, registry meta-tests, and end-to-end CLI tests against every fixture for
both v1 and v2 (a few minutes -- most of it is v2's end-to-end subprocess runs). Some self-tests
scope themselves with `-k` to just the module(s) owning the id(s) they assert on, which flips the
printed verdict to NOT CONFORMANT for that run (expected -- they're checking specific per-id
statuses, not the overall verdict).

For local development run `uv sync --all-packages`. Plain `uv sync` is exact and removes the
`spec-tracker` member from the venv (`uv run --package spec-tracker ...` puts it back).

Editors: the root `.venv` covers the TCK and `spec-tracker`; `cross-check/` has its own env (see
its README).

## CI

`.github/workflows/ci.yml`: a required `test` job (`uv sync --locked && uv run pytest -q`, then the
spec-tracker tests against a fetched spec checkout) and an informational `cross-check` job
(`continue-on-error: true`). See each project's README for what its CI step checks.

## Contributor docs

The contracts live in [`docs/`](docs/README.md); read the page before changing what it covers.

- [Requirements](docs/requirements.md): id format, rule B and the id lifecycle, tiers, statuses, the verdict
  (`blocked_by_auth`/`blocked_by_version_mismatch`), citation rules, the ledger of deliberate non-requirements.
- [Writing tests](docs/writing-tests.md): how to add a requirement + test, markers, probes, the error-code
  policy, SKIP vs FAIL, fixtures.
- [Mock-client prompt driver](docs/mock-client.md): the `run_prompt` contract.
- [Harness API](docs/harness.md): `tck.common.harness`.
- [Spec updates](docs/spec-updates.md): the `/update-to-spec` procedure, id alignment, cross-check refresh.

## Vendored schema

`src/tck/v1/schema/schema.unstable.json`/`meta.unstable.json` and `src/tck/v2/schema/schema.unstable.json`/
`meta.unstable.json` are verbatim copies of the ACP JSON Schema from the spec repo. Both v1 and v2 (Draft) verify
entirely against the draft (unstable) superset. The RFD-gated fields and methods it adds are optional for agents,
but any an agent uses are validated against the draft shapes. Commit hash, vendor date and the refresh steps live
in each `schema/VENDORED.md`; the update procedure is in [`docs/spec-updates.md`](docs/spec-updates.md). Do not
hand-edit the JSON files.

`tck.v{1,2}.protocol` and `tck.v{1,2}.validation` derive their method-name tables and validation rules from these
files at import time, so a schema refresh mostly self-updates them -- but check each version's `validation.py`
docstring for hand-written carve-outs a refresh could invalidate (e.g. v1's `session/load` null-response quirk,
v2's any-array-is-one-issue rule and open-enum discriminator carve-out).

`tck.v{1,2}.validation` only validates messages the *agent under test* authors (its requests/
notifications to the client, and its responses to methods it implements) -- never a message the
TCK's own mock client writes. There is no `validate_client_message`; add one only if a future
requirement needs to assert on the harness's own outgoing traffic.

## Conventions

- Keep comments and docstrings concise and straightforward. Use plain language. Note non-obvious
  rationale, gotchas, and spec citations; skip narrating what the code already says, restating
  history slice-by-slice, or listing exhaustive cascades/examples that belong in tests, not prose.
- **Never reference anything under `.agents/`**  in the
  final code: not in comments, docstrings, `Requirement` citations, tests, or scripts. Those files are
  deleted before the PR merges, so such a reference would dangle. A temporary reference is fine
  while the work that needs it is in progress, but it must be removed or replaced with a permanent
  upstream citation or plain explanation by the time that work is done.
- Dependency management is `uv` only, with exact pins (`==`), never bare `pip` or hand-edited
  `pyproject.toml` dependency entries. Add to the product with `uv add ...`, to the member with
  `uv add --package spec-tracker ...`, and to cross-check with `uv add --project cross-check ...`.