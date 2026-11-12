# cross-check

Runs the ACP TCK against independently implemented upstream agents and compares their scorecards
with an expected baseline. A deviation points at either a TCK bug or new upstream behavior.

- v1: the Rust SDK's `testy` fixture agent, and the Python SDK's `examples/echo_agent.py`.
- v2: `testy` built with the `unstable_protocol_v2` feature, and the repo-owned
  `python_v2_agent.py` (no upstream v2 Python example agent exists yet).

A standalone uv project, excluded from the root workspace, with its own `uv.lock` and `.venv`. It
never imports `tck`; it runs the TCK as a CLI. Both Python agents run in this env, so the
`agent-client-protocol` pin in `pyproject.toml` is the SDK version they are checked at. Add
dependencies with `uv add --project cross-check ...`. For editor completion of its `acp` imports,
open `cross-check/` as its own editor root.

## Running

```
./cross-check/run.sh
```

Works from any directory. It needs a Rust toolchain and network access: both SDKs are
shallow-fetched at the SHAs pinned in `sdk-pins.sh` into `scratch/cross-check/sdks/{rust,python}-sdk`
(a checkout already at the pinned SHA is reused, which keeps its cargo `target/` warm).

- `ACP_RUST_SDK`, `ACP_PYTHON_SDK`: opt-in overrides pointing at your own SDK checkouts. `run.sh`
  warns when they are set, since the expected baseline below is defined for the pinned SHAs only.
- `OUT_DIR`: where the JSON reports go (default `scratch/cross-check/`).
- `ACP_CROSS_CHECK_V2=0`: skip both v2 legs.

`run.sh` exits 0 once every agent ran and its report was written; the agents' verdicts are data,
checked by `summary.py` below.

## SDK pins

`sdk-pins.sh` is the single source of truth: repo URL, release tag, and full commit SHA for each
SDK. `run.sh` sources it and CI keys its cargo cache on it. A test in `tests/` fails if the Python
tag differs from the `agent-client-protocol==` pin in `pyproject.toml`.

To bump an SDK: edit `sdk-pins.sh` (the SHA must be what the release tag points at, see
`git ls-remote --tags <url> <tag>^{}`); for Python also run
`uv add --project cross-check agent-client-protocol==<tag>`; re-run `run.sh`; then update the
`--expect` / `--expect-flaky` lines at the end of `run.sh` and in `.github/workflows/ci.yml` from the
observed results.

## Expected baseline

`summary.py` prints a requirement-by-requirement table and, with `--expect`, diffs each report's
MANDATORY FAILs against an expected set; `--expect-flaky LABEL=ID,...` leaves ids that PASS or FAIL
run to run out of one report's check. The baseline is the `--expect` lines at the end of
`run.sh`, mirrored in the CI workflow:

- v1 `testy`: fully conformant.
- `echo_agent`: only `ACP-INIT-003` (it echoes an unsupported requested version).
- v2 `testy`: `ACP-INIT-205` and `ACP-INIT-211` (its protocol router hands a below-v1 request
  and a first `initialize` without a valid version to its v1 implementation, which keeps the
  connection).
- `python_v2_agent`: a small set of known SDK limitations, explained above the `--expect` lines.
- `--expect-flaky` is available for ids that PASS or FAIL run to run (an upstream race); none
  are flaky today.

## Tests and CI

```
uv run --directory cross-check pytest
```

(`--directory`, not `--project`: pytest finds its config from the working directory.)

The informational CI `cross-check` job runs these tests, then `run.sh`, then re-checks the scorecard
with `summary.py` so a drifted baseline turns the job red.
