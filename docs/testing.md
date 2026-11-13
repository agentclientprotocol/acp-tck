# Testing

How to run the repo's own tests and how they work. Adding a requirement and its test is in
[Writing tests](writing-tests.md); how to run the TCK against an agent is in the [top-level README](../README.md).

## The suites

The repo holds three uv projects, each with its own pytest suite:

- **Product** (`tests/`, the root project): unit tests for the harness, report model and plugin, the registry
  meta-tests, and end-to-end CLI tests that run `acp-tck` against every fixture agent for both versions. Run it
  for any change under `src/`, `tests/`, or the root `pyproject.toml`.
- **spec-tracker** (`spec-tracker/tests`): checks the spec maps against the spec docs. Run it when you touch
  `spec-tracker/`, a requirement's citation, or a spec update. Commands, including `--spec-repo`, are in
  [`spec-tracker/README.md`](../spec-tracker/README.md).
- **cross-check** (`cross-check/tests`): tests the cross-check tooling (not the upstream agents). Run it when you
  touch `cross-check/`. Commands are in [`cross-check/README.md`](../cross-check/README.md).

The product suite:

```
uv run pytest
```

## Parallel by default

The root `pyproject.toml` sets `addopts = ["-n", "auto"]` (pytest-xdist, a dev dependency), so `uv run pytest`
spreads the end-to-end CLI tests, which mostly wait on agent subprocesses, across cores. Pass `-n 0` for a
serial run, which you want when debugging with `pdb` or reading interleaved output.

The addopts apply only to the repo's own tests. The TCK's own conformance runs (`acp-tck`, and plain pytest on
`src/tck/v{1,2}/conformance`) never inherit them, or any other outer pytest config. `acp-tck` passes the
conformance `pytest.ini` explicitly with `-c`; do the same for plain pytest (see
[Development](development.md#running-the-tck-from-source)). Relying on pytest's config discovery is not enough:
it resolves the config before the plugin registers its `--tck-*` options, so option values that are existing paths
(an agent command that is a single file, `--tck-agent-cwd`) count as path arguments, and a path inside the repo (or,
in an installed copy, inside the project around the virtual environment) pulls in that project's config. The
`pytest.ini` files also stop the upward walk as a second line of defense.
`tests/common/test_cli_isolation.py` pins this. The `PYTEST_ADDOPTS` environment variable still applies, but
`acp-tck` blocks xdist (`-p no:xdist`) because its report needs a single process, so `-n` in `PYTEST_ADDOPTS` makes
it fail with a usage error instead of reporting nothing.

## Narrow runs

```
uv run pytest tests --ignore tests/v1/test_cli.py --ignore tests/v2/test_cli.py
uv run pytest tests/v1/test_cli.py -k conforming
```

- The first runs only the unit and registry tests, skipping the two end-to-end `test_cli.py` files.
- The second runs the CLI tests whose name matches `-k`, usually a fixture agent's name.

Some CLI tests scope the inner `acp-tck` run with its own `-k` to the modules that own the ids they assert on. A
scoped run leaves every unselected MANDATORY row NOT TESTED, so it prints NOT CONFORMANT; that is expected, and
the tests assert on the per-id statuses, not the verdict (see [Writing tests](writing-tests.md#fixtures)).

## What catches what

- The registry tests (`tests/v{1,2}/test_registry.py`) fail if a registered id has no test, if a test references an
  unregistered id, or if the pinned id set or per-tier id sets were not updated by hand.
- `tests/v{1,2}/test_cli.py` runs each fixture agent through `acp-tck`, asserts its exact FAIL set, and keeps its
  own hand-written tier sets that must match the registry too.

[Writing tests](writing-tests.md) covers how to add the fixtures and assertions these check.

## CI

`.github/workflows/ci.yml` runs two independent parts side by side:

- `test` (required): `uv sync --locked && uv run pytest -q` (the product suite, parallel via addopts), then the
  spec-tracker tests against a fetched spec checkout.
- The cross-check (informational, `continue-on-error: true`): one `cross-check <agent>` job per upstream agent,
  each running the TCK against it on its own runner, then a `cross-check` job that runs the cross-check tests and
  checks the four reports against the expected baseline.

Each project's README says what its CI step checks.
