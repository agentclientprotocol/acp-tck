# Cross-check run: `eugenethedev/v2-draft` vs `main` (2026-09-29)

## Result

All four agent legs match the `--expect` baselines in `scripts/cross-check.sh` on the branch
(`cross-check-summary.py expectations exit code: 0`). The per-requirement status for all four
reports is **identical between the branch and `main`**, down to the FAIL assertion messages. No
deviation on the branch, and no change caused by the switch to the draft schema.

| Agent (proto) | Verdict (branch) | MANDATORY FAILs | Other FAILs | Baseline | Same on main |
|---|---|---|---|---|---|
| testy (v1) | NOT CONFORMANT, exit 1 | ACP-INIT-003 | ACP-INIT-004 (ADVISORY) | match | yes |
| echo_agent (v1, `agent-client-protocol==1.0.0rc1`) | NOT CONFORMANT, exit 1 | ACP-INIT-003 | ACP-INIT-004, ACP-JSONRPC-004 (ADVISORY) | match | yes |
| testy_v2 (v2, `unstable_protocol_v2`) | CONFORMANT, exit 0 | none | none | match | yes |
| python_v2_agent (v2, `agent-client-protocol==1.0.0rc2`) | NOT CONFORMANT, exit 1 | ACP-BATCH-201, ACP-BATCH-202, ACP-INIT-003, ACP-INIT-201, ACP-INIT-202, ACP-JSONRPC-001, ACP-JSONRPC-003 | ACP-BATCH-203, ACP-BATCH-204, ACP-BATCH-205, ACP-JSONRPC-005 (ADVISORY) | match | yes |

Tier counts (identical on both trees):

- testy: MANDATORY 20 PASS / 1 FAIL; CAPABILITY 17 PASS / 2 SKIP; ADVISORY 10 PASS / 1 FAIL / 1 SKIP; INFORMATIONAL 4 PASS
- echo_agent: MANDATORY 18 PASS / 1 FAIL / 2 SKIP; CAPABILITY 19 SKIP; ADVISORY 8 PASS / 2 FAIL / 2 SKIP; INFORMATIONAL 4 PASS
- testy_v2: MANDATORY 17 PASS / 2 SKIP; CAPABILITY 31 PASS / 20 SKIP; ADVISORY 15 PASS / 5 SKIP; INFORMATIONAL 10 PASS / 6 SKIP
- python_v2_agent: MANDATORY 10 PASS / 7 FAIL / 2 SKIP; CAPABILITY 30 PASS / 21 SKIP; ADVISORY 11 PASS / 4 FAIL / 5 SKIP; INFORMATIONAL 10 PASS / 6 SKIP

`schema_revision` in the v2 reports: branch `9af0e9f748db9f4cc4c410a7b212ead4f98ae78c` (draft),
main `d8805733cca4ef0d92e5135b50d5bfc2ea4fbdf3`. v1 reports: `6d08f412…` on both.

## Setup (reproduces the CI `cross-check` job)

- TCK trees: `git archive HEAD` (183ee5a, branch tip; working tree has only untracked
  `.agents/` files, so HEAD == working tree) and `git archive main` (b15c7bd), each extracted
  into the scratchpad, `uv sync --locked`, run via their own `./scripts/cross-check.sh`.
  `scripts/cross-check.sh` and `.github/workflows/ci.yml` are identical between main and branch.
- SDKs at CI's pinned SHAs, exported via `git archive` from the local skill checkouts (the
  checkouts themselves were not touched):
  - rust-sdk `28688b2d97a81975ff875180c3a3e46e6cad0161` (local checkout is at b55cdc7, 6 commits
    ahead, so the pin was used, not the checkout HEAD)
  - python-sdk `9d07d7871ef4b220b8507e15fc4b1560f0950a64` (== local checkout HEAD)
- Env as in CI: `CARGO_PROFILE_DEV_DEBUG=0`, `ACP_RUST_SDK`, `ACP_PYTHON_SDK`, `OUT_DIR` set to
  scratch dirs; `ACP_CROSS_CHECK_V2` default (1).
- Toolchain: macOS arm64 (CI is ubuntu-latest), cargo/rustc 1.97.1 stable, uv 0.12.11,
  Python 3.14 (`.python-version`). Both testy builds succeeded.
- Runs were sequential (branch, then main) to avoid timing interference with cancel tests.

## FAIL details (branch; main identical)

- testy / echo_agent **ACP-INIT-003** (`test_unsupported_version_still_succeeds`):
  `protocolVersion must not echo the client's unsupported requested version verbatim ... assert 65535 != 65535`
- testy / echo_agent **ACP-INIT-004** (ADVISORY, `test_agent_info_present`): `agentInfo is not present in the initialize result`
- echo_agent **ACP-JSONRPC-004** (ADVISORY, `test_unknown_method_yields_method_not_found`):
  `expected an error response, got {'jsonrpc': '2.0', 'id': 2, 'result': None}`
- python_v2_agent **ACP-INIT-003 / ACP-INIT-201**: `an unsupported version must still yield a successful result, got
  {'jsonrpc':'2.0','id':1,'error':{'code':-32602,'message':'Invalid params','data':{'expectedProtocolVersion':2,'receivedProtocolVersion':65535}}}`
- python_v2_agent **ACP-INIT-202** (`test_downgrade_request_still_succeeds`): same `-32602` error with
  `receivedProtocolVersion: 1`.
- python_v2_agent **ACP-BATCH-201/202/203/204/205, ACP-JSONRPC-001/003/005**: all
  `AgentExited: agent process exited while waiting for a line (exit_code=1)`. Agent stderr:
  ```
  File ".../acp/connection.py", line 153, in _process_message
    method = message.get("method")
  AttributeError: 'list' object has no attribute 'get'
  ERROR:root:Receive loop failed
  ```
  i.e. the rc2 SDK's receive loop crashes on any JSON array (batch) input. JSONRPC-001/003/005
  fail via the batch-shaped tests bound to them.

v1 cancel tests on echo_agent: `SKIPPED [2] ... cancellation not exercised: prompt turn completed
before session/cancel could be sent` on both trees (expected; echo_agent completes instantly).

## Observations (not deviations)

- The `python_v2_agent` comment in `scripts/cross-check.sh` says ACP-INIT-003/201/202 fail
  because the fixture "echoes back whatever protocol_version it's given". The fixture's
  `initialize()` does echo, but the observed failure is a `-32602 Invalid params` error with
  `expectedProtocolVersion: 2` -- the rc2 SDK rejects the non-2 version before the handler is
  reached. The comment's rationale is inaccurate; the FAIL set is unaffected.
- The same comment attributes ACP-JSONRPC-001/003 to "id echoing, cancel-on-idle-session
  handling"; in this run they fail purely because the SDK's receive loop crashes on batch input
  (see above).
- The `--expect` baselines only constrain MANDATORY FAILs; the ADVISORY FAILs above are not
  checked by CI.
- `CLAUDE.md` refers to a `docs/cross-check.md` baseline document; no `docs/` directory exists.
  The baseline actually lives only in the `--expect` lines of `scripts/cross-check.sh` (which
  `AGENTS.md` describes correctly).

## Raw artifacts (scratchpad)

`/private/tmp/claude-501/-Users-eugene-Documents-JetBrains-projects-acp-tck/12df2688-46e5-4ddc-ae68-125af21d9b0b/scratchpad/`:
`branch.log`, `main.log` (full script output), `out-branch/*.json`, `out-main/*.json` (reports),
`fails.txt` (extracted FAIL assertion lines for both trees).
