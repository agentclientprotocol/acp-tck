# Review: M6 (mcp-over-acp P1), range 932c719..9156383

Reviewed in a detached worktree at 9156383. Spec read with `git show 3961af94:<path>` (no pull).
Full suite `uv run pytest -n auto`: **932 passed** (318 s).

Counts: blocker 0, should-fix 1, nit 3.

## Verdict on the programmer's call (fold into ACP-JSONRPC-003, ungated)

**The call is right.**

- The docs state the rule for every agent and every notification: v1 `overview.mdx:239` and v2
  `overview.mdx:227`, "Notifications never receive responses (success or error)". Under docs
  precedence (`docs/requirements.md` "Docs take precedence") the tier and text come from the docs.
  So the row is MANDATORY and ungated. The brief's CAPABILITY row gated on `acp` would have let
  an agent that does not advertise `acp` but answers `mcp/message` escape a docs MUST. Rule B
  holds: the rule ("no reply to a notification") is the same one ACP-JSONRPC-003 already states
  in both versions, so no new id is needed.
- **Probe rules** (`docs/writing-tests.md` "Probes"). The `_`-prefix bullet is about custom names
  and does not apply: `mcp/message` is a spec-defined (unstable-schema) method. The second bullet
  allows breaking a client rule only where the spec defines the agent's answer to that exact
  input. Here the client rules broken are "send only for an active request on a declared `acp`
  server" (`MessageMcpNotification` description) and "`requestId`/`method` required". The answer
  is defined by the overview rule for any notification, and for an `acp` agent also by RFD:225
  ("receives no response") and RFD:257 ("malformed notifications do not receive synthetic
  replies"). Compliant. The docstring could name the broken rule more explicitly (nit 3).
- **False-FAIL risk.** None for a *reply* that I can construct. Both probes are valid JSON-RPC
  notifications (`method`, no `id`), so JSON-RPC 2.0's -32600/`id:null` path does not apply.
  The params fault is a method-level fault, and JSON-RPC still forbids replying to it. An `acp`
  agent's only legitimate reaction to an unknown or late notification is to drop it (RFD:225). Any
  agent-initiated message (`$/cancel_request`, `session/update`, requests) is excluded by
  `is_response_line`. SDK behaviour I checked agrees. The Rust SDK v5.1.0 logs notification
  handler errors without a wire reply (`agent-client-protocol/src/jsonrpc.rs:577-579,1617`), and
  the MCP-over-ACP polyfill's `parse_notification(...)?` (`polyfill/src/mcp_over_acp/mod.rs:316`)
  therefore produces no reply. Python SDK 1.0.0 logs and swallows (`acp/connection.py:288-295`).
  The one false-FAIL shape is an agent that *exits*, see should-fix 1.
- **Is a gated row still needed?** Not at P1. The RFD-only extras in R12 are either unobservable
  ("must not deliver to a different operation"), have no MUST behind them ("a following request
  still succeeds"), or need the P2 provider stub (a *late* notification after a real final
  result). Record the late-notification probe as a P2 follow-up, not a P1 gap.

## Findings

### 1. should-fix: v2 FAILs MANDATORY ACP-JSONRPC-003 when the agent exits, v1 PASSes the same probe

- `src/tck/v2/conformance/test_jsonrpc.py:142` (with `:121-131`, the docstring) vs
  `src/tck/v1/conformance/test_jsonrpc.py:143-150,194`.
- **Defect:** the v2 `mcp/message` probe lets `AgentExited` escape, so an agent that crashes on
  the malformed notification FAILs MANDATORY ACP-JSONRPC-003. It never replied, and the docstring
  itself says "Only a reply fails this". The v1 sibling goes through
  `_assert_no_reply_to_notification`, which treats an exit as "no reply" and PASSes.
- **Scenario (confirmed by running):** a throwaway fixture that does `os._exit(1)` on an
  `mcp/message` without `requestId`. v1 `-k mcp_message` reports `ACP-JSONRPC-003 PASS`. v2
  reports `FAIL` with `AgentExited: agent process exited while waiting for a line (exit_code=1)`,
  a MANDATORY failure, so NOT CONFORMANT. That is a stricter-than-spec MANDATORY FAIL in v2, and
  the same probe under the same shared id gives opposite results in the two versions. The v1 side
  has its own hole: the helper's docstring says survival "is judged by ACP-EXT-002/ACP-JSONRPC-006",
  but neither row sends `mcp/message`, so in v1 a crash on this probe is never judged at all.
- The pre-existing v2 `session/cancel` probe (`:116`) has the same uncaught-exit shape. The new
  probe is far more likely to hit it, because it feeds malformed params to a *defined* method.
- **Fix direction (not applied):** handle `AgentExited` in v2 as v1 does, or say in the v2
  docstring and row text that an exit FAILs too. If survival after `mcp/message` should be judged,
  that belongs in a separate row (follow-up).
- Confidence: confirmed by running.

### 2. nit: stale docstring on the MCP-203 defect-fixture test

- `tests/v2/test_cli.py:4800`: "One fixture per probe: `sse` accepted, or a `_`-prefixed custom
  type accepted." The loop now also covers `accepts_unadvertised_acp_mcp.py`.
- Scenario: a reader trusting the docstring misses the `acp` fixture when updating the set.
  Confirmed by reading.

### 3. nit: neither `answers_mcp_notification` fixture pins either probe on its own

- `tests/fixtures/agents/v1/answers_mcp_notification.py:19-21`,
  `tests/fixtures/agents/v2/answers_mcp_notification.py:21-23`: both reply `-32602` to *every*
  `mcp/message` notification.
- Scenario: deleting the malformed second probe (`send_notification("mcp/message", {"serverId":
  ...})`, the RFD:257 "synthetic reply" case), or the well-formed first one, leaves every test
  green. A fixture that answers only an envelope missing `requestId`/`method` would pin the
  malformed probe. Confirmed by reading.

### 4. nit: probe docstring and row text describe the deviations but do not name them as broken client rules

- `src/tck/v1/conformance/test_jsonrpc.py:175-182`, `src/tck/v2/conformance/test_jsonrpc.py:122-131`,
  `src/tck/v1/requirements.py:65-83`, `src/tck/v2/requirements.py:1429-1444`.
- `docs/writing-tests.md` "Probes" asks the row text and docstring to say which client rule is
  broken. Here: `MessageMcpNotification` is sent only "for an active request" on a declared `acp`
  server, to an agent that advertised `acp`, and `requestId`/`method` are required. The text says
  "for a request nothing is waiting on", "missing the required ..." and "not gated". The substance
  is there, but not in the form the rule asks for. No failure scenario beyond reader confusion.
  Confirmed by reading.

## Checked, no finding

- **`acp` probe shape** `{type:"acp", name:"tck-acp", serverId:"tck-acp-1"}` matches
  `#/$defs/McpServerAcp` (required `name`, `serverId`) in the vendored v2 schema. v2
  `session-setup.mdx:545` at 3961af94 names `session.mcp.acp` explicitly and requires `-32602`
  "including a transport they did not advertise". Citation and tier (CAPABILITY on
  `capabilities.session`, as before) are right.
- **Skip logic**: `capability_is_supported(..., "capabilities.session.mcp.acp")` uses object-marker
  semantics. `{}` skips the probe. Absent, `null` and `false` send it. A malformed `acp: true`
  also skips it, and ACP-INIT-204 catches that shape. Both directions are pinned:
  `advertises_acp_mcp.py` PASSes, and an inverted or always-sent probe would FAIL it.
  `accepts_unadvertised_acp_mcp.py` FAILs, and a never-sent probe would PASS it.
- **Fixture FAIL sets, unscoped full runs (confirmed):** v1 `answers_mcp_notification.py` gives
  {ACP-JSONRPC-003}. v2 `answers_mcp_notification.py` gives {ACP-JSONRPC-003}. v2
  `accepts_unadvertised_acp_mcp.py` gives {ACP-MCP-203}. v2 `advertises_acp_mcp.py` is
  CONFORMANT. All match the docstrings. The v2 `_base.py` change (adding `acp` to the advertised
  set) affects no existing fixture: the full suite is green.
- **Cross-check baselines (confirmed by running** the pinned binaries and SDKs already built in
  the main checkout's `scratch/cross-check/`, rust-sdk 026fe25, python-sdk 9853d8b, with
  `-k "mcp_message or unsupported_mcp_transport"`): testy v1 JSONRPC-003 PASS. echo_agent
  JSONRPC-003 PASS. testy_v2 JSONRPC-003 PASS and MCP-203 PASS (it rejects the `acp` probe).
  python_v2_agent JSONRPC-003 PASS and MCP-203 FAIL. That FAIL is pre-existing (it now also
  accepts `acp`), it is CAPABILITY, and it is already listed in the `run.sh` comment. The
  MANDATORY-only `--expect` lines in `cross-check/run.sh:196-199` and
  `.github/workflows/ci.yml:105-108` are unaffected.
- **v1 INFORMATIONAL unadvertised-`acp` record skipped.** It is P3 in the research (v1 plan
  item 3), outside M6's P1 scope, so skipping it is correct. v1 has no `ACP-MCP-*` family yet, so
  it would need a new id anyway. The real reason is scope.
- **Citations**: overview line numbers, RFD:225/257 and the `(Active RFD)` labels check out at
  3961af94, and the schema pointers resolve (registry tests pass). No `.agents/` references in
  the diff. No v1/v2 cross-imports.

## Follow-ups (not M6 defects)

- P2: a *late* `mcp/message` notification (after a real final result) once the provider stub
  exists. Possibly a survival check after `mcp/message` (no spec MUST today, so ADVISORY at most).
