#!/usr/bin/env bash
# Cross-check the ACP TCK against independently implemented agents:
#   v1 -- `testy` (Rust SDK's own test fixture agent, built from the pinned checkout) and
#         `examples/echo_agent.py` (Python SDK's example agent)
#   v2 -- `testy` again, this time built with the `unstable_protocol_v2` feature so it routes
#         v2 connections to its native v2 agent, and a repo-authored minimal v2 agent
#         (`python_v2_agent.py`) since no upstream v2 example agent exists yet
#
# Both Python agents run in this directory's own uv project, whose `agent-client-protocol`
# pin (see `pyproject.toml`) is the SDK version they are checked at. The TCK itself runs as a
# CLI from the repo-root project.
#
# Both SDKs are shallow-fetched at the SHAs pinned in `sdk-pins.sh` (a checkout already at the
# pinned SHA is reused). This is a manual/CI cross-check, NOT part of `uv run pytest` -- it needs
# a Rust toolchain and network access. See `README.md` in this directory.
#
# Set ACP_CROSS_CHECK_V2=0 to skip both v2 legs and run only the v1 comparison (e.g. if the
# local Rust toolchain lacks the v2 feature, or to keep a quick v1-only smoke run).
#
# Exits 0 iff the script itself completed (every enabled agent run happened and its JSON report
# was written). The agents' own conformance verdicts are data, not the script's success -- read
# the printed table(s) and verdict lines.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=sdk-pins.sh
source "$SCRIPT_DIR/sdk-pins.sh"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/scratch/cross-check}"
CROSS_CHECK_V2="${ACP_CROSS_CHECK_V2:-1}"

# Sync both envs once up front and run everything with --no-sync, so uv never touches a venv
# while the TCK is using it. --inexact keeps the root sync from pruning other workspace members.
uv sync --locked --inexact --project "$REPO_ROOT"
uv sync --locked --project "$SCRIPT_DIR"
TCK=(uv run --no-sync --project "$REPO_ROOT" acp-tck)
AGENT_PYTHON=(uv run --no-sync --project "$SCRIPT_DIR" python)

mkdir -p "$OUT_DIR"
# Canonicalize to absolute: downstream cargo builds run in a subshell `cd`'d into
# $ACP_RUST_SDK, and a relative OUT_DIR would then resolve --target-dir against that
# directory instead of the repo root, building the binary somewhere this script never checks.
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

# fetch_sdk DIR URL SHA: shallow-fetch SHA into DIR, unless DIR is already a checkout at SHA
# (keeps the cargo target dir inside it warm).
fetch_sdk() {
  local dir="$1" url="$2" sha="$3"
  # Test for DIR/.git itself: DIR sits inside this repo, so a bare `git -C DIR` would find ours.
  if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$sha" ]; then
    echo "== Reusing $dir at $sha ==" >&2
    return
  fi
  echo "== Fetching $url at $sha into $dir ==" >&2
  mkdir -p "$dir"
  [ -d "$dir/.git" ] || git -C "$dir" init -q
  git -C "$dir" remote remove origin 2>/dev/null || true
  git -C "$dir" remote add origin "$url"
  git -C "$dir" fetch -q --depth 1 origin "$sha"
  git -C "$dir" checkout -q --force FETCH_HEAD
}

# ACP_RUST_SDK / ACP_PYTHON_SDK are explicit opt-in overrides (e.g. to try a local SDK change).
if [ -n "${ACP_RUST_SDK:-}" ]; then
  echo "warning: using ACP_RUST_SDK=$ACP_RUST_SDK; the baseline is defined for the pinned Rust SDK $RUST_SDK_TAG ($RUST_SDK_SHA)" >&2
else
  ACP_RUST_SDK="$OUT_DIR/sdks/rust-sdk"
  fetch_sdk "$ACP_RUST_SDK" "$RUST_SDK_URL" "$RUST_SDK_SHA"
fi
if [ -n "${ACP_PYTHON_SDK:-}" ]; then
  echo "warning: using ACP_PYTHON_SDK=$ACP_PYTHON_SDK; the baseline is defined for the pinned Python SDK $PYTHON_SDK_TAG ($PYTHON_SDK_SHA)" >&2
else
  ACP_PYTHON_SDK="$OUT_DIR/sdks/python-sdk"
  fetch_sdk "$ACP_PYTHON_SDK" "$PYTHON_SDK_URL" "$PYTHON_SDK_SHA"
fi

echo "== Building testy (--no-default-features) from $ACP_RUST_SDK ==" >&2
(
  cd "$ACP_RUST_SDK"
  cargo build -p agent-client-protocol-test --bin testy --no-default-features
)

TESTY="$ACP_RUST_SDK/target/debug/testy"
if [ ! -x "$TESTY" ]; then
  echo "error: expected testy binary at $TESTY after build, not found" >&2
  exit 1
fi

echo "== Running acp-tck against testy ($TESTY) ==" >&2
set +e
"${TCK[@]}" --cancel-prompt wait_for_cancel --report-json "$OUT_DIR/testy.json" -- "$TESTY"
TESTY_EXIT=$?
set -e
echo "testy exit code: $TESTY_EXIT" >&2

echo "== Running acp-tck against echo_agent.py ==" >&2
set +e
"${TCK[@]}" --cancel-prompt wait_for_cancel --report-json "$OUT_DIR/echo_agent.json" -- \
  "${AGENT_PYTHON[@]}" "$ACP_PYTHON_SDK/examples/echo_agent.py"
ECHO_EXIT=$?
set -e
echo "echo_agent exit code: $ECHO_EXIT" >&2

TESTY_V2_EXIT=""
PYTHON_V2_EXIT=""
if [ "$CROSS_CHECK_V2" = "1" ]; then
  # Built into an isolated --target-dir, never the checkout's own target/debug/testy: a
  # *dual*-feature build (v1 + unstable_protocol_v2, picking the route per-connection from the
  # client's own `initialize`) does NOT reproduce the v1-only build's ACP-INIT-003 baseline
  # unchanged. The v1 ACP-INIT-003 probe sends an `info` object alongside the unsupported
  # `protocolVersion: 65535`, which a dual-feature router accepts as valid v2 params and happily
  # routes to (and correctly answers from) its v2 agent -- so the same probe that FAILs against
  # a strict v1-only build actually PASSes against the dual build, for an entirely different
  # reason having nothing to do with the v1 agent's own conformance. Building the v2 leg into
  # its own --target-dir keeps the v1 leg's binary (and its documented baseline) untouched.
  echo "== Building testy (--no-default-features --features unstable_protocol_v2) from $ACP_RUST_SDK ==" >&2
  TESTY_V2_TARGET_DIR="$OUT_DIR/target-v2"
  (
    cd "$ACP_RUST_SDK"
    cargo build -p agent-client-protocol-test --bin testy --no-default-features \
      --features unstable_protocol_v2 --target-dir "$TESTY_V2_TARGET_DIR"
  )

  TESTY_V2="$TESTY_V2_TARGET_DIR/debug/testy"
  if [ ! -x "$TESTY_V2" ]; then
    echo "error: expected testy binary at $TESTY_V2 after build, not found" >&2
    exit 1
  fi

  echo "== Running acp-tck --protocol-version 2 against testy ($TESTY_V2) ==" >&2
  set +e
  "${TCK[@]}" --protocol-version 2 --cancel-prompt wait_for_cancel \
    --report-json "$OUT_DIR/testy-v2.json" -- "$TESTY_V2"
  TESTY_V2_EXIT=$?
  set -e
  echo "testy (v2) exit code: $TESTY_V2_EXIT" >&2

  echo "== Running acp-tck --protocol-version 2 against python_v2_agent.py ==" >&2
  set +e
  "${TCK[@]}" --protocol-version 2 --cancel-prompt wait_for_cancel \
    --report-json "$OUT_DIR/python-v2.json" -- \
    "${AGENT_PYTHON[@]}" "$SCRIPT_DIR/python_v2_agent.py"
  PYTHON_V2_EXIT=$?
  set -e
  echo "python_v2_agent exit code: $PYTHON_V2_EXIT" >&2
else
  echo "== ACP_CROSS_CHECK_V2=0 -- skipping the v2 legs ==" >&2
fi

echo
echo "== Comparison table =="
set +e
if [ "$CROSS_CHECK_V2" = "1" ]; then
  # Baselines (MANDATORY FAILs only), observed against the SDKs pinned in `sdk-pins.sh`.
  # Every expected FAIL is a genuine upstream deviation from the cited rule, not a TCK bug.
  #
  # echo_agent ACP-INIT-003: it echoes the client's unsupported probe version (65535) verbatim
  # instead of returning its own latest supported version. testy (v1) answers 1, so it is
  # fully conformant.
  #
  # testy_v2: built with `unstable_protocol_v2`, testy serves v1 and v2 behind a protocol router
  # that hands anything not requesting v2 (a version below v1, or a first `initialize` without a
  # valid `protocolVersion`) to its v1 implementation, which then owns the connection
  # (rust-sdk `AgentProtocolRouter` docs). That is deliberate v1 compatibility, and it breaks
  # two v2 rules:
  #   - ACP-INIT-205: `initialize(0)` gets a v1 result selecting 1; v2 requires -32022 when no
  #     supported version is <= the request (a result must not select a higher version).
  #   - ACP-INIT-211: after a rejected `initialize` (no `protocolVersion`), the corrected retry
  #     requesting 2 is answered by the v1 implementation selecting 1 instead of 2.
  # Both are deterministic (6/6 runs). The old ACP-INIT-205/206 flakiness (testy exiting before
  # flushing its error reply) is gone: the router keeps the connection open after a rejection.
  #
  # python_v2_agent (repo-authored fixture, see `python_v2_agent.py` docstring), all from the
  # Python SDK's v2 runtime, which the fixture delegates framing and validation to:
  #   - ACP-INIT-003/205/214: the SDK rejects every `protocolVersion` other than 2 with -32602.
  #     65535 must select 2 (and keep ignoring unparseable params such as `capabilities: 42`,
  #     ACP-INIT-214), and 0 must get -32022 with `{requested, supported}` data.
  #   - ACP-INIT-202: `initialize(1)` is validated as v2 params first and gets -32602 (missing
  #     `info`); an unsupported-but-well-formed version must get -32022.
  #   - ACP-INIT-206: the SDK coerces a string `protocolVersion` such as "2" to an integer and
  #     accepts it, where a non-integer value must get -32602.
  #   - ACP-INIT-212: the SDK rejects a repeated `initialize` with -32600 ("may only be
  #     initialized once"); the spec has the agent handle each repeat like the first.
  #   Not in the MANDATORY-only `--expect` set below: the SDK no longer crashes on JSON arrays
  #   (ACP-JSONRPC-001/003 now PASS), but still never answers one (ADVISORY ACP-BATCH-209), and
  #   the SDK's default-on-error `replayFrom` parsing lets a malformed value through (CAPABILITY
  #   ACP-RESUME-208). The fixture itself skips validation the spec requires (CAPABILITY
  #   ACP-ERROR-003/004, ACP-LIST-003/205, ACP-MCP-203, ACP-PROMPT-211, ACP-PROMPTCAP-201,
  #   ACP-SESSION-204, ADVISORY ACP-RESUME-214), so those FAIL too.
  "${AGENT_PYTHON[@]}" "$SCRIPT_DIR/summary.py" \
    "$OUT_DIR/testy.json" testy \
    "$OUT_DIR/echo_agent.json" echo_agent \
    --report "$OUT_DIR/testy-v2.json" testy_v2 \
    --report "$OUT_DIR/python-v2.json" python_v2_agent \
    --expect "testy=" \
    --expect "echo_agent=ACP-INIT-003" \
    --expect "testy_v2=ACP-INIT-205,ACP-INIT-211" \
    --expect "python_v2_agent=ACP-INIT-003,ACP-INIT-202,ACP-INIT-205,ACP-INIT-206,ACP-INIT-212,ACP-INIT-214"
else
  # Baselines: see the matching comment in the CROSS_CHECK_V2 branch above.
  "${AGENT_PYTHON[@]}" "$SCRIPT_DIR/summary.py" \
    "$OUT_DIR/testy.json" testy \
    "$OUT_DIR/echo_agent.json" echo_agent \
    --expect "testy=" \
    --expect "echo_agent=ACP-INIT-003"
fi
SUMMARY_EXIT=$?
set -e

echo
echo "testy exit code: $TESTY_EXIT"
echo "echo_agent exit code: $ECHO_EXIT"
if [ "$CROSS_CHECK_V2" = "1" ]; then
  echo "testy (v2) exit code: $TESTY_V2_EXIT"
  echo "python_v2_agent exit code: $PYTHON_V2_EXIT"
fi
echo "summary.py expectations exit code: $SUMMARY_EXIT"

exit 0
