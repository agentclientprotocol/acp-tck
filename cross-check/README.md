# cross-check

Runs the ACP TCK against independently implemented upstream agents and compares their scorecards
with an expected baseline. A deviation points at either a TCK bug or new upstream behavior.

Agents checked:

- v1: the Rust SDK's `testy` fixture agent, and the Python SDK's `examples/echo_agent.py`.
- v2: `testy` built with the `unstable_protocol_v2` feature, and the repo-owned
  `python_v2_agent.py` (no upstream v2 Python example agent exists yet).

## Project layout

A standalone uv project with its own `uv.lock` and `.venv`. The root workspace excludes it
(`[tool.uv.workspace] exclude`). It never imports `tck`: it runs the TCK as a CLI from the repo-root
project. Both Python agents run in this project's env, so the `agent-client-protocol` pin in
`pyproject.toml` is the SDK version they are checked at.

Add dependencies with `uv add --project cross-check ...` (exact `==` pins).

Editors: open `cross-check/` as its own editor/IDE root to get completion for its `acp` imports.
Pyright/Pylance opened at the repo root resolve it against the root `.venv`, which has no `acp`.

## Running

```
./cross-check/run.sh
```

Works from any directory. It needs a Rust toolchain and local checkouts of both SDKs:

- `ACP_RUST_SDK`, `ACP_PYTHON_SDK`: SDK checkout paths. They default to the `.repo` files of the
  `check-rust-sdk`/`check-python-sdk` skills.
- `OUT_DIR`: where the JSON reports and the v2 `testy` build go (default `scratch/cross-check/`).
  The v1 `testy` builds into the Rust SDK checkout's own `target/`.
- `ACP_CROSS_CHECK_V2=0`: skip both v2 legs.

`run.sh` exits 0 once every enabled agent ran and its report was written. The agents' verdicts are
data, not the script's result: read the printed tables, or the `summary.py` check below.

## Expected baseline

`summary.py` prints a requirement-by-requirement table across the reports and, with `--expect`,
diffs each report's MANDATORY FAILs against an expected set (see its docstring). The baseline lives
in the `--expect` lines at the end of `run.sh`, mirrored in the CI workflow:

- v1 `testy`: fully conformant (it answers 1 from rust-sdk `53dd268`).
- `echo_agent`: only `ACP-INIT-003` (it echoes an unsupported requested version).
- v2 `testy`: only `ACP-INIT-205`/`206`. It exits right after rejecting `initialize`, usually
  before the error reply is flushed to stdout (a known upstream race).
- `python_v2_agent`: a small set tied to known SDK limitations, each explained in the comment
  above the `--expect` lines.

## Tests and CI

```
uv run --directory cross-check pytest
```

Use `--directory`, not `--project`: pytest finds its config and tests from the working directory,
so `--project` from the repo root would collect the root suite instead.

In CI, the informational `cross-check` job (`continue-on-error: true`) runs these tests, then
`run.sh`, then re-checks the scorecard with `summary.py` so a drifted baseline turns the job red.
