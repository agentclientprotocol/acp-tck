# Pinned upstream SDK revisions the cross-check baseline is defined for. Sourced by `run.sh`
# (and read by the pin-consistency test in `tests/`); the single source of truth for both SDKs.
#
# Bump procedure: edit this file, run `uv add --project cross-check agent-client-protocol==<tag>`,
# re-run `run.sh`, then update the `--expect` lines (run.sh and .github/workflows/ci.yml).
#
# Each SHA must be the commit its release tag points at: `git ls-remote --tags <url> <tag>^{}`.

# Rust SDK `v5.3.0`: pins `agent-client-protocol-schema =1.18.0`, the schema release the vendored
# spec commit sits on (v5.4.0 moves to 1.19.0, ahead of it). Has the `unstable_protocol_v2` cargo
# feature (the v2 leg).
RUST_SDK_URL=https://github.com/agentclientprotocol/rust-sdk
RUST_SDK_TAG=v5.3.0
RUST_SDK_SHA=05fd3893cca2f1be2eb3a262b0f7da2c52abaa58

# Python SDK `1.0.0`. Its tag must equal the `agent-client-protocol==` pin in `pyproject.toml`
# (the version the agents actually run on); `echo_agent.py` is taken from this checkout.
PYTHON_SDK_URL=https://github.com/agentclientprotocol/python-sdk
PYTHON_SDK_TAG=1.0.0
PYTHON_SDK_SHA=9853d8b514d6340000bcbd01ec07808436db80cf
