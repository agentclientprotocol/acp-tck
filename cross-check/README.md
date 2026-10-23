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

Works from any directory. It needs a Rust toolchain and local checkouts of both SDKs:

- `ACP_RUST_SDK`, `ACP_PYTHON_SDK`: SDK checkout paths (default: the `check-rust-sdk`/
  `check-python-sdk` skills' `.repo` files).
- `OUT_DIR`: where the JSON reports go (default `scratch/cross-check/`).
- `ACP_CROSS_CHECK_V2=0`: skip both v2 legs.

`run.sh` exits 0 once every agent ran and its report was written; the agents' verdicts are data,
checked by `summary.py` below.

## Expected baseline

`summary.py` prints a requirement-by-requirement table and, with `--expect`, diffs each report's
MANDATORY FAILs against an expected set. The baseline is the `--expect` lines at the end of
`run.sh`, mirrored in the CI workflow:

- v1 `testy`: fully conformant.
- `echo_agent`: only `ACP-INIT-003` (it echoes an unsupported requested version).
- v2 `testy`: only `ACP-INIT-205`/`206` (it exits before flushing its `initialize` error reply, a
  known upstream race).
- `python_v2_agent`: a small set of known SDK limitations, explained above the `--expect` lines.

## Tests and CI

```
uv run --directory cross-check pytest
```

(`--directory`, not `--project`: pytest finds its config from the working directory.)

The informational CI `cross-check` job runs these tests, then `run.sh`, then re-checks the scorecard
with `summary.py` so a drifted baseline turns the job red.
