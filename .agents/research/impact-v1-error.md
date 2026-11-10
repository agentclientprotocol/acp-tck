# v1 impact: `docs/protocol/v1/draft/error.mdx` (stub -> real content), beac4ba9 -> 3961af94

**Sources checked:** agent-client-protocol (spec) worktree, base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (read via `git show`, checkout untouched); acp-rust-sdk @ `e75d6f19fabb` (2026-11-09, pulled ff-only); acp-python-sdk @ `8a9940744d0a` (2026-11-09, pulled ff-only); acp-tck working tree on `eugenethedev/update-spec` (`200baba`).
**Confidence:** high for classification of the existing rows and the spec text. Medium for the new-requirement granularity and the core-doc section choice, which are judgment calls flagged DECISION NEEDED.

All `error.mdx:N` citations below are at target `3961af94fa62` unless marked base.

## Answer

At base `error.mdx` was only "_Documentation coming soon_" (base `error.mdx:6`). At target it is a normative page. It has the error-object shape (6-10), a code table (24-35), a MUST and a SHOULD on codes (37), and four "Common cases" (39-61): `-32601` SHOULD for unknown or unadvertised capability-gated methods; `-32602` for malformed or unsupported params; `-32002` + `data.sessionId` SHOULD for unknown or inactive sessions; `-32600` SHOULD for requests before `initialize`. A list of unstable-method error rules follows (63-68).

Effects on the registry:
- **ACP-INFO-UNKNOWNSESSION-001**: its premise ("v1 does not specify one") is now false. Recommend retiring it and replacing it with an ADVISORY row.
- **ACP-INFO-PARSE-001** and **ACP-INFO-INVALIDREQ-001**: they say "spec silent", which is now only half true. They need a text update, and their tier stays the same.
- **ACP-JSONRPC-002/004** and **ACP-ERROR-002**: semantically unchanged, but they gain a direct `error.mdx` citation.
- **ACP-JSONRPC-001**: its Rust citation (`agent-client-protocol-schema/src/rpc.rs:14-16`) points at code that moved to `src/v1/rpc.rs:11-13`. `spec-impact --fix` will not remap it, because it only handles `.mdx` files.

Five new observable ADVISORY agent-side rules are proposed (ACP-ERROR-003..007), plus one optional (ACP-ERROR-008).

`error.mdx` should become a core doc in `spec-tracker/maps/v1.toml`. It is the only place that states the `-32602` and `-32002` codes for `session/set_mode` and `session/set_config_option`, and neither `session-modes.mdx` nor `session-config-options.mdx` links to it.

## Summary table

| Id | Classification | One-line note |
|----|----------------|---------------|
| ACP-INFO-UNKNOWNSESSION-001 | **retired** (DECISION NEEDED) | Premise stale: `error.mdx:51-55` now gives a SHOULD (`-32002` + `data.sessionId`). Replace it with new ACP-ERROR-003. Its citation `error.mdx:6 (stub)` now lands on unrelated text. |
| ACP-INFO-PARSE-001 | changed text (tier unchanged) | "Spec silent" is now partly wrong: `error.mdx:28` assigns `-32700` but doesn't require a reply. Stays INFORMATIONAL. |
| ACP-INFO-INVALIDREQ-001 | changed text (tier unchanged) | Same: `error.mdx:29` assigns `-32600` to "not a valid request object" with no SHOULD to reply. Stays INFORMATIONAL. |
| ACP-JSONRPC-001 | citation-only change (non-mdx, **manual**) | `agent-client-protocol-schema/src/rpc.rs:14-16` -> `agent-client-protocol-schema/src/v1/rpc.rs:11-13`. Not remapped by `--fix`. |
| ACP-JSONRPC-002 | citation-only change (add) | `overview.mdx:235-239` is still correct at target. Add `error.mdx:6-10` as the primary prose citation. `error.rs:25-49` unchanged. |
| ACP-JSONRPC-003 | unchanged | `overview.mdx:239` and `error.rs:9` unchanged. |
| ACP-JSONRPC-004 | citation-only change (add) | Add `error.mdx:41-43` (explicit **SHOULD** `-32601`). ADVISORY confirmed. |
| ACP-JSONRPC-005 | unchanged | Not touched by error.mdx. |
| ACP-JSONRPC-006 | unchanged (from this doc's angle) | Cancellation hunks are owned by the cancellation/transport researcher. |
| ACP-JSONRPC-007 | unchanged (from this doc's angle) | `error.mdx:33` restates `-32800`. `ErrorCode` description change is wording only. |
| ACP-ERROR-001 | unchanged (optional citation add) | `error.mdx:9` ("a short human-readable description") is consistent. `error.rs:40-42` unchanged. |
| ACP-ERROR-002 | citation-only change (add) | Add `error.mdx:31,47`. Its "malformed parameters ... get `-32602`" has no RFC keyword, so it stays ADVISORY. |
| ACP-EXT-001 | unchanged | `error.mdx:43` is consistent with "some response, `-32601` only SHOULD". |
| ACP-SCHEMA-002 | unchanged | error.mdx adds no `Error` fields. `data` "shape depends on the code" (`error.mdx:10`). |
| ACP-AUTH-001..006 | unchanged | `error.mdx:34` (`-32000`) is consistent. |
| ACP-SYSPROMPT-002 | unchanged (from this doc's angle) | `error.mdx:49` matches `session-setup.mdx:422` (`-32602` RECOMMENDED). The stale "Unstable feature" wording belongs to the session-setup owner. |
| ACP-DELETE-002 | unchanged | `error.mdx:55` ("deleting a session that does not exist still succeeds") is consistent with `session-delete.mdx:86`. |
| ACP-CLOSE-001/002 | unchanged | A new close-idempotency SHOULD exists (`session-setup.mdx:347-350`, restated at `error.mdx:55`). See cross-ref X1. Owned by the session-setup researcher. |
| ACP-INIT-003 | unchanged | Its `-32602` reasoning is consistent with `error.mdx:31`. |
| *new* ACP-ERROR-003 | **new** ADVISORY | `session/prompt` on an unknown or closed session gets `-32002` with `data.sessionId` set to the requested id. |
| *new* ACP-ERROR-004 | **new** ADVISORY (test-level gates) | Same rule for `session/set_mode`, `session/set_config_option`, `session/load`, `session/resume`. |
| *new* ACP-ERROR-005 | **new** ADVISORY | A request other than `initialize` before initialization gets `-32600`. |
| *new* ACP-ERROR-006 | **new** ADVISORY | An unadvertised capability-gated stable method gets `-32601`. |
| *new* ACP-ERROR-007 | **new** ADVISORY (inferred gates) | An unknown `modeId`, `configId`, or config value gets `-32602`. |
| *new* ACP-ERROR-008 | **new, optional** ADVISORY (DECISION NEEDED) | Agent-returned codes inside the reserved ranges are ACP-defined ones. |
| ledger L1-L3 | new non-requirements | Receivers MUST treat unknown codes as generic failure; client `-32002` for fs/terminal; client treats `-32002` on close/delete as success. |
| unstable U1-U4 | deferred (DECISION NEEDED) | fork/status/archive/set_title error rules. They depend on whether v1 starts testing those methods at all (`spec-diff-v1.md` open question). |

## Requirements (spec statements in error.mdx and their tiers)

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| E1 | Error object has integer `code`, `message`, and optional `data` | MUST (JSON-RPC, already ACP-JSONRPC-002) | `error.mdx:6-10`; `schema/v1/schema.unstable.json#/$defs/Error` |
| E2 | Receivers MUST treat an unrecognized code as a generic failure | MUST, receiver-side, unobservable | `error.mdx:37` |
| E3 | Implementation-specific errors SHOULD use codes outside `-32768..-32000` and `-32899..-32800` | SHOULD | `error.mdx:37` |
| E4 | Unimplemented method, or capability-gated method not advertised, SHOULD get `-32601` | SHOULD | `error.mdx:41-43` |
| E5 | Malformed params or unsupported values get `-32602`, e.g. invalid list cursor, unknown `configId`/value, unknown mode | indicative, no keyword -> treat as SHOULD | `error.mdx:45-47` |
| E6 | `systemPrompt` the agent cannot apply gets an error, with `-32602` recommended | MUST error / RECOMMENDED code (owned by session-setup) | `error.mdx:49`; `session-setup.mdx:422` |
| E7 | Session-scoped request naming a session that doesn't exist or isn't active SHOULD get `-32002` with `data.sessionId` set to the requested id. Applies to prompt, set_mode, set_config_option, and to load/resume of a nonexistent session | SHOULD | `error.mdx:51-55` |
| E8 | Closing or deleting a session that does not exist still succeeds | indicative (backed by SHOULDs at `session-setup.mdx:347-349`, `session-delete.mdx:86`) | `error.mdx:55` |
| E9 | Clients SHOULD reply `-32002` for missing file on `fs/read_text_file` or unknown terminal | SHOULD, client-side | `error.mdx:57` |
| E10 | Agents SHOULD reject any request other than `initialize` before initialization completes with `-32600` | SHOULD | `error.mdx:59-61` (also table row `error.mdx:29`) |
| E11 | Unstable: fork/status/archive/unarchive/set_title of an unknown session get `-32002` (status: with `data.sessionId`; exists-but-not-loaded is not an error). Unsupported `archived` filter and rejected title get `-32602` | indicative; capability:`sessionCapabilities.{fork,status,archive,title}` | `error.mdx:63-68` |

## Details

### Existing rows: changed text

**ACP-INFO-UNKNOWNSESSION-001: retire (DECISION NEEDED; recommendation: retire, replace with ACP-ERROR-003).**
- Old: INFORMATIONAL, "...recorded, never asserted -- v1 does not specify one...", citation `docs/protocol/v1/draft/error.mdx:6 (stub)` (`src/tck/v1/requirements.py:1079-1090`).
- New spec: `error.mdx:53`, "the Agent **SHOULD** respond with `-32002` and set `data.sessionId` to the requested ID", and `error.mdx:55`, "This applies to `session/prompt`, ...". The rule is now specified at SHOULD level, so the INFORMATIONAL premise (spec silent) is gone. Target `error.mdx:6` is now the "Failed requests return a JSON-RPC 2.0 error object" sentence, so the existing citation silently points at unrelated text.
- Why retire rather than re-tier in place: the `ACP-INFO-*` prefix is used only for INFORMATIONAL "spec silent" probes (`requirements.py:1046-1090`). An ADVISORY row under that prefix would mislead readers. The alternative is to keep the id, flip it to ADVISORY, and assert. It is cheaper but leaves the misleading prefix.
- Test impact: `src/tck/v1/conformance/test_informational.py:123-166` (`test_unknown_session_id_behaviour`) is removed or rebound to ACP-ERROR-003 and gains assertions. The module docstring (`test_informational.py:1-10`) says "The spec is silent on all three behaviours" and must change either way.

**ACP-INFO-PARSE-001: changed text, tier unchanged (INFORMATIONAL).**
- Old text: "Spec silent; reference SDKs disagree" (`requirements.py:1054`).
- New: `error.mdx:28` defines `-32700` "Parse error: The message is not valid JSON", but no sentence requires a receiver to reply to an unparseable line. `transports.mdx` still says the client MUST NOT write it (target line 24, base 27, which `--fix` remaps).
- Proposed text: replace "Spec silent" with "The spec assigns `-32700` to non-JSON input (error.mdx code table) but does not require a reply, and the client MUST NOT send it". Add citation `docs/protocol/v1/draft/error.mdx:28`. No test change; the probe already records `-32700`.

**ACP-INFO-INVALIDREQ-001: changed text, tier unchanged (INFORMATIONAL).**
- `error.mdx:29` gives `-32600` for "not a valid request object". There is no SHOULD to reply, and `{"foo":"bar"}` is still forbidden client traffic (`transports.mdx:24`). Same text edit as PARSE-001, plus citation `error.mdx:29`. No test change.
- Do not confuse this with E10: E10 is about a *valid* request arriving before `initialize`, which is a separate new row (ACP-ERROR-005).

### Existing rows: citation-only

- **ACP-JSONRPC-001**: `agent-client-protocol-schema/src/rpc.rs:14-16` (base) is now `pub use crate::v1::{Request, RequestId, Response};` at target (`rpc.rs:12-13`). The RequestId doc comment ("The Server MUST reply with the same value...") moved to `agent-client-protocol-schema/src/v1/rpc.rs:11-13` (identical text). This is a `.rs` citation, so `spec-impact --fix` won't touch it. Fix it by hand.
- **ACP-JSONRPC-002**: `overview.mdx:235-239` is the same content at target. Only the heading at 233 was recased and line 241 added the link to Errors. Recommend adding `docs/protocol/v1/draft/error.mdx:6-10`. `error.rs:25-49` unchanged (the diff only touched lines 11, 130-135, 146-195).
- **ACP-JSONRPC-004**: add `docs/protocol/v1/draft/error.mdx:41-43`. This is the first bold **SHOULD** for `-32601`; `extensibility.mdx:84` says only lowercase "should". The tier is confirmed and the test (`test_jsonrpc.py:86-100`) is unchanged.
- **ACP-ERROR-002**: add `docs/protocol/v1/draft/error.mdx:31,45-47`. Missing required `cwd` counts as "malformed parameters". The test (`test_diagnostics.py:58-75`) is unchanged.
- **ACP-ERROR-001**: optional, add `error.mdx:9`.

### New requirements (agent-side, client-observable)

All are ADVISORY because the source wording is SHOULD or indicative. ADVISORY rows use `capability=None` in the registry plus a test-level `@pytest.mark.capability(...)` where needed. This is the same pattern as ACP-DELETE-002 (`requirements.py:464-471`, `test_session_capabilities.py:271-284`). They must not be CAPABILITY tier, because a CAPABILITY FAIL breaks the verdict and a SHOULD must not do that. Every probe should SKIP on `-32000`, as ACP-ERROR-002 does (`test_diagnostics.py:71-72`).

**ACP-ERROR-003 (ADVISORY, no gate).**
- Text: "`session/prompt` naming a session that does not exist, or that was closed on this connection, gets error `-32002` with `data.sessionId` equal to the requested id."
- Citation: `docs/protocol/v1/draft/error.mdx:51-55 @ 3961af94fa62`; `schema/v1/schema.unstable.json#/$defs/ErrorCode`.
- How to observe:
  - Test A, ungated, replaces the INFO probe: after `session/new`, send `session/prompt` with `sessionId: "tck-does-not-exist"`. Assert `error.code == -32002`, that `error.data` is an object, and that `data.sessionId == "tck-does-not-exist"`. Report the code and data failures separately.
  - Test B, gated by `@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")`: create a session, `session/close` it, then prompt it. Expect the same result. This covers "not active on the connection" (`error.mdx:53`: "active once it is created, loaded or resumed ... until it is closed").
  - Keep the existing "outstanding client request" handling from `test_informational.py:141-153`.
- Reference evidence: the Rust reference test agent `testy` returns exactly this for prompt on a missing or closed session (`src/agent-client-protocol-test/src/testy/v1.rs:169-175`, via `session_not_found` at `:1666-1667`). It uses the schema crate helper `Error::session_not_found` (spec repo `agent-client-protocol-schema/src/v1/error.rs:130-135`, new in this diff). The Python SDK has only `RequestError.resource_not_found(uri)`, which yields `data: {"uri": ...}` (`src/acp/exceptions.py:40-43`), and no session-id helper. A Python-SDK agent using it would fail the `data.sessionId` half. That is an SDK gap, not a spec conflict.
- Fixture: `unknown_session_wrong_code.py` (unknown-session prompt gets `-32602`, which is exactly what `_base.py:336-345` does today). Optionally also `unknown_session_no_data.py` (`-32002` without `data`).
- **Fixture impact:** the shared base (`tests/fixtures/agents/v1/_base.py:344`) currently answers `-32602 "unknown sessionId"`. It must switch to `-32002` + `data.sessionId`, or `conforming.py` will FAIL the new row. Its comment at `_base.py:336-342` cites the INFO probe as the reason no code is asserted, and that becomes stale.

**ACP-ERROR-004 (ADVISORY, per-test gates).**
- Text: "`session/set_mode`, `session/set_config_option` naming an unknown session, and `session/load`/`session/resume` of a session that does not exist, get `-32002` with `data.sessionId` equal to the requested id."
- Citation: `docs/protocol/v1/draft/error.mdx:53-55 @ 3961af94fa62`.
- Observe with one test per method:
  - set_mode is gated on `inferred:modes`, i.e. `session/new` returned `modes`. Send `{sessionId:"tck-does-not-exist", modeId:<an advertised id>}`. Use a valid modeId so the check isolates the session rule from `-32602`.
  - set_config_option is gated on `inferred:configOptions`. Use a real `configId` and value.
  - load is gated on `agentCapabilities.loadSession` (`boolean=True`). Send `{sessionId:"tck-never-created", cwd, mcpServers:[]}`.
  - resume is gated on `agentCapabilities.sessionCapabilities.resume`, with the same params.
- Reference evidence: Rust testy does this for set_mode (`testy/v1.rs:431-438`) and set_config_option (`:466-473`). Load/resume behavior in testy was not traced (hypothesis that it matches).
- Fixtures: `load_upserts_unknown_session.py`. **Fixture impact:** `_base.py:61-62`/`:339` document "upsert/silent-success semantics" for load/resume. `conforming_full.py` would FAIL ACP-ERROR-004 unless that changes. DECISION NEEDED: one id vs. splitting into ERROR-004 (set_mode/config) and ERROR-00x (load/resume). Recommendation: one id. It is one SHOULD sentence, and the per-test failure messages name the method.

**ACP-ERROR-005 (ADVISORY, no gate).**
- Text: "A request other than `initialize` sent before initialization gets error `-32600`."
- Citation: `docs/protocol/v1/draft/error.mdx:29,59-61 @ 3961af94fa62`.
- Observe: on a fresh `connected_agent(handshake=False)`, send `session/new` (valid params) as the first message and assert `error.code == -32600`. Don't assert recovery afterwards; the spec says nothing on it. Rust's router leaves the connection open for a later `initialize` (`src/agent-client-protocol/src/role/acp.rs:461-464`), but that is SDK behavior.
- SDK evidence:
  - Rust v1 agents that register an `initialize` handler reject pre-init requests with `-32600` (`tests/protocol_negotiation.rs:276-297`).
  - Rust v1 agents without one serve the request (`:299-318`). Rust and Python v2/negotiating routers return `-32600 "first ACP request must be initialize"` (Rust `role/acp.rs:692-700`, `tests/error_wire_format.rs:296`; Python `src/acp/experimental/negotiation.py:95-97`).
  - The plain Python v1 `AgentSideConnection` has no gating. This is negative evidence only: there is no initialize-state check under `src/acp/agent/` or in `src/acp/connection.py`.
  - So real agents will often fail this. ADVISORY is right.
- Fixture: `serves_before_initialize.py`. **Fixture and harness impact:** if `_base.py` gains the gate, `tests/common/test_harness.py:196,218,264` call `_tck/big`/`_tck/env` on `conforming.py` *without* initializing first and would break. Exempt the `_tck/*` harness probes from the gate, or have those tests initialize first. All current conformance tests send `initialize` first (checked every `handshake=False` site), so the TCK's own traffic already follows the rule.

**ACP-ERROR-006 (ADVISORY, gate = capability absent).**
- Text: "A stable capability-gated method the agent did not advertise (`session/load` without `loadSession`; `session/list`/`resume`/`close`/`delete` without the matching `sessionCapabilities` key) gets error `-32601`."
- Citation: `docs/protocol/v1/draft/error.mdx:41-43 @ 3961af94fa62`.
- Observe: pick each such method whose capability is *not* advertised, send well-formed params, and assert `-32601`. SKIP if every one is advertised. This is an inverted gate, so the test computes it with `capability_is_supported` itself, not with the marker.
- Fixture: `implements_unadvertised_list.py` (answers `session/list` with a result while not advertising `list`).
- Note: this is not the existing ACP-JSONRPC-004, which only probes an unknown `_`-prefixed method. Could be folded into JSONRPC-004 as a second test; recommendation is a separate id, because the second half of the sentence is new text.

**ACP-ERROR-007 (ADVISORY, inferred gates).**
- Text: "`session/set_mode` with an unknown `modeId`, and `session/set_config_option` with an unknown `configId` or an unsupported value, get error `-32602`."
- Citation: `docs/protocol/v1/draft/error.mdx:45-47 @ 3961af94fa62`.
- Tier: the sentence has no RFC keyword ("get `-32602`"). ADVISORY matches ACP-ERROR-002's treatment of the same kind of sentence. `session-modes.mdx` and `session-config-options.mdx` contain no `-32602` text at target, so error.mdx is the only source.
- Observe: on a real session, use `modeId:"_tck_unknown_mode"` and `configId:"_tck_unknown"`. The `_` prefix avoids colliding with real ids.
- Fixture: `set_mode_unknown_accepts.py`.
- The `session/list` invalid-cursor example (`error.mdx:47`) restates `session-list.mdx:174` (**SHOULD**, new in this diff). Leave that to the session-list owner; see cross-ref X2.

**ACP-ERROR-008 (optional, ADVISORY). DECISION NEEDED. Recommendation: add, low priority.**
- Text: "Every error code the agent returns in the run that lies in `-32768..-32000` or `-32899..-32800` is one of the ACP-defined codes (`ErrorCode` consts)."
- Citation: `docs/protocol/v1/draft/error.mdx:37 @ 3961af94fa62`; `schema/v1/schema.unstable.json#/$defs/ErrorCode`.
- Observe: sample passively over the error replies the other probes provoke, like ACP-ERROR-001's sampling (`test_diagnostics.py:16-55`). It passes vacuously when no sample exists.
- Caveat: JSON-RPC 2.0 itself leaves `-32000..-32099` to implementations, and ACP now reserves the whole `-32768..-32000` block (`error.mdx:37`; `ErrorCode` description). Agents with legacy `-32001`-style codes will trip it.
- Alternative: put it in the ledger as "observable only opportunistically".

### New deliberate non-requirements (ledger candidates for `[[not_requirement]]`)

| # | citation | statement | reason |
|---|----------|-----------|--------|
| L1 | `docs/protocol/v1/draft/error.mdx:37 @ 3961af94fa62` | Receivers MUST treat an unrecognized error code as a generic failure. | Unobservable: the agent's internal handling of an unknown code in a client's error reply has no defined wire effect. For clients, it is a client-side rule. |
| L2 | `docs/protocol/v1/draft/error.mdx:57 @ 3961af94fa62` | Clients SHOULD respond `-32002` when `fs/read_text_file` names a missing file or a `terminal/*` method names an unknown terminal. | Client-side rule. The TCK tests agents, and its mock client advertises no fs/terminal capabilities. |
| L3 | `docs/protocol/v1/draft/session-setup.mdx:349-350`, `docs/protocol/v1/draft/session-delete.mdx:87 @ 3961af94fa62` | Clients SHOULD treat a `-32002` response to `session/close`/`session/delete` as success. | Client-side rule. (Owned by the session-setup/session-delete researchers; listed here only because `error.mdx:55` restates it. Dedupe.) |

### Unstable-method rules (U1-U4): deferred, DECISION NEEDED

`error.mdx:63-68` (also `schema.mdx:530,1402,1428,1483,1556` and `session-list.mdx:252,260`):
- **U1:** fork of a nonexistent session gets `-32002`.
- **U2:** status of an unknown session gets `-32002` with `data.sessionId`, and status of an existing but unloaded session is *not* an error.
- **U3:** archive/unarchive of a nonexistent session gets `-32002`, "unlike `session/delete`" (no silent success). An unsupported `archived` filter gets `-32602`.
- **U4:** set_title of a nonexistent session gets `-32002`, and a rejected title gets `-32602`.

All would be ADVISORY rows with test-level gates on `agentCapabilities.sessionCapabilities.{fork,status,archive,title}` (all present in the target `SessionCapabilities`).

The v1 registry has no rows for fork/status/archive/title at all today, so these only make sense together with the scoping decision in `spec-diff-v1.md` ("Should the v1 TCK start exercising any of the new unstable methods..."). Recommendation: don't add error-only rows for features without positive-path coverage. Route them with that scoping decision.

### Cross-references for other owners (no action here)

- **X1 (session-setup owner):** `session-setup.mdx:347-350` (new; there is no idempotency text at base) says closing a nonexistent or inactive session SHOULD return the same empty result. `error.mdx:55` restates it. This is a candidate ACP-CLOSE-003, ADVISORY and test-gated on `close`; the probe is `session/close` on a never-created id expecting `{}`. It has the same shape as ACP-DELETE-002.
- **X2 (session-list owner):** `session-list.mdx:174` "Agents **SHOULD** return `-32602` if the cursor is invalid" (new at target; there is no `-3260x` text in base session-list.mdx). It is restated as an example at `error.mdx:47`.
- **X3 (session-setup owner):** ACP-SYSPROMPT-002 can stay as-is. Its "`-32602` is only RECOMMENDED" matches both `error.mdx:49` and `session-setup.mdx:422`.

## Spec map: make `error.mdx` a core doc? Yes.

Rationale: error.mdx is the only place that gives error codes for `session/set_mode`/`session/set_config_option` (grep of target `session-modes.mdx` and `session-config-options.mdx`: no `-326xx`/`-32002` text and no link to `error`), and for unknown sessions on `session/prompt`/`load`/`resume`. Only `overview.mdx:241` and `session-setup.mdx:350` link to it. So a change there would not be flagged through the docs that rely on it.

Proposed entry:

```toml
[[core_doc]]
path = "docs/protocol/v1/draft/error.mdx"
sections = ["(intro)", "Error codes", "Common cases"]
code = [
    "src/tck/v1/protocol.py",
    "src/tck/v1/conformance/test_jsonrpc.py",
    "src/tck/v1/conformance/test_diagnostics.py",
    "src/tck/v1/conformance/test_informational.py",
    "src/tck/v1/conformance/test_session_capabilities.py",
    "src/tck/v1/conformance/_helpers.py",
]
reason = "the error object, the code table and the -32601/-32602/-32002/-32600 rules that session-scoped feature docs (session-modes, session-config-options, prompt-turn, session-setup) apply without linking here"
```

- Section choice (DECISION NEEDED; recommendation as above): leave "Unstable features" (63-68) out. It holds per-feature rules for methods the TCK doesn't test, and as unstable it will churn. It is still diffed as a normal doc. If U1-U4 rows are ever added, switch to whole-doc (drop `sections`). Headings at target: intro 6-22, `## Error codes` 24, `## Common cases` 39 (subsections `### Unknown methods` 41, `### Invalid parameters` 45, `### Unknown sessions` 51, `### Requests before initialization` 59), `## Unstable features` 63.
- Code list: `protocol.py:31-38` holds the code constants. `_helpers.py` has the `-32000` auth-gate (`skip_if_auth_gated`) and the mock client's `-32601` replies (`_helpers.py:425`). Add the module(s) that will host ACP-ERROR-003..007 if they land elsewhere.
- `core_defs` already includes `ErrorCode`. `Error` sits in its `$ref` closure, which spec-impact already reports, so it need not be added.

## Testability notes

- Every new row is a pure client-side request/response check against an error code, plus `data.sessionId` for 003/004. A conforming agent returns exactly the code. A non-conforming one returns another code, a result, or silence (silence on a request is already ACP-EXT-001/MANDATORY territory for custom methods; for these probes treat a timeout as FAIL of the ADVISORY row).
- Interference to guard against:
  - `-32000` from auth-gated agents: SKIP, as ERROR-002 does.
  - For 004 and 007, use otherwise-valid params, so `-32602` vs `-32002` isolates one rule. When a request is both bad-session and bad-params, the spec doesn't define precedence.
  - For 005, use a throwaway connection.
  - For 006, the inverted capability gate.
- Unobservable: "not active on the connection" can only be probed via close (Test B of 003). A session created on another process is simply nonexistent to a fresh process. E2 (receiver handling) is unobservable, and E9 is client-side.
- `tests/v1/test_cli.py` asserts each fixture's exact FAIL/PASS set. Changing `_base.py` (unknown-session code, load/resume upsert, pre-init gate) will shift expectations for many fixtures at once. Plan it as a dedicated slice.

## Discrepancies

1. **Tier conflict, `archived` filter:** `error.mdx:67` says an unsupported `archived` value "gets `-32602`" (indicative). `session-list.mdx:252` says "Agents **MUST** reject a value they don't support with `-32602`". The Rust doc comment/schema text agrees with MUST (`schema.mdx:6639` "return `-32602` ..."). It only matters if U3 is scoped in; then the MUST in session-list.mdx should win, but the user/orchestrator should confirm.
2. **ErrorCode `-32600` description vs doc:** the schema says "The JSON sent is not a valid Request object" (`$defs/ErrorCode`, unchanged). `error.mdx:29` extends the meaning to "or a request other than `initialize` arrived before initialization". The schema lags the doc; there is no conflict in values. Minor.
3. **Reserved range vs JSON-RPC 2.0:** `error.mdx:37` and the `ErrorCode` description (`agent-client-protocol-schema/src/v1/error.rs:146-150`) reserve `-32768..-32000` (including JSON-RPC's implementation-defined server-error block `-32000..-32099`) for JSON-RPC+ACP. JSON-RPC 2.0 gives that block to implementations. Doc and schema are consistent with each other; ACP deliberately narrows JSON-RPC. This matters for ERROR-008's false-positive risk.
4. **SDKs on E7 `data`:** Rust schema crate `Error::session_not_found` puts `data.sessionId` (spec repo `agent-client-protocol-schema/src/v1/error.rs:130-135`). Python SDK offers only `resource_not_found(uri)` -> `data.uri` (`acp-python-sdk src/acp/exceptions.py:40-43`). This is an implementation gap, not a spec conflict.
5. **SDKs on E10:** Rust v1 agents reject pre-init requests only when an `initialize` handler is registered (`tests/protocol_negotiation.rs:276-318`). The plain Python v1 agent connection doesn't gate (negative evidence). Both routers gate. This is consistent with SHOULD, not a conflict.

None found between `error.mdx`, the target schema, and the restating docs (session-setup, session-delete, overview) on the rules ACP-ERROR-003..007 would assert. The close/delete success carve-out (`error.mdx:55`) matches `session-setup.mdx:347-349` and `session-delete.mdx:86`.

## Open questions

- DECISION NEEDED: retire ACP-INFO-UNKNOWNSESSION-001 (recommended) vs re-tier it in place.
- DECISION NEEDED: ERROR-004 as one id vs split. ERROR-006 separate vs folded into JSONRPC-004. ERROR-008 add vs ledger.
- DECISION NEEDED: core-doc sections (exclude "Unstable features", recommended) vs whole doc.
- Route to the scoping decision: U1-U4 (unstable fork/status/archive/title error rules).
- Route to other researchers: X1 (close idempotency, session-setup), X2 (list cursor `-32602`, session-list).
- Programmer planning: base-fixture changes (unknown-session code, load/resume upsert, pre-init gate with the `_tck/*` harness exemption) cascade into `tests/v1/test_cli.py` expectations.
