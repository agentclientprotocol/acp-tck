# Impact of `docs/protocol/v2/draft/initialization.mdx` (beac4ba -> 3961af9) on the v2 registry

**Sources checked:** agent-client-protocol @ `3961af94fa62` (target) vs `beac4ba96190` (base), read via `git show`/`git diff` in `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` (not pulled, per brief); acp-rust-sdk @ `e75d6f19fabb` (2026-11-09, `pull --ff-only`: already up to date); acp-python-sdk @ `8a9940744d0a` (2026-11-09). **The Python `pull --ff-only` failed** ("Cannot fast-forward to multiple branches"). Local `main` equals the last-fetched `origin/main`, but I can't vouch that this is current.
**Confidence:** high for the classifications and line remaps (I read the whole doc at target plus the diff, the `$defs`, and every bound test). Medium for the tier calls on the new rows: three of them rest on indicative wording or on a client-side MAY, not on an explicit agent MUST (marked DECISION NEEDED).

## Answer

None of the 16 ids citing this doc is retired, and none changes text, tier or gate. All of them get **citation-only** changes. Three need a manual remap, because the `-32602` sentence moved out of the old line 117: `ACP-INIT-206` goes to `:108`, `ACP-INIT-003` to `:108,110,112`, and `ACP-INIT-202` to `:108,110,112`. `ACP-INIT-205` should also cite the new `$defs/UnsupportedProtocolVersionErrorData`.

The doc adds real, client-observable agent obligations that the TCK does not test:
- `-32600` for any non-`initialize` request before initialization completes (MUST, error.mdx:60);
- agents send nothing while uninitialized (MUST, :91);
- a failed `initialize` can be retried on the same connection (:92);
- `initialize` may be repeated before any other request (:137-139);
- `-32600` for an `initialize` repeated after another request (error.mdx:60);
- unparseable params of a newer-version request are ignored (MUST, :131).

I propose six new ids, `ACP-INIT-209`..`214`. Several existing fixtures and two test docstrings conflict with the new text:
- `_base.py` has no pre-init gate and does not support retry.
- `pushes_status_notifications.py` pushes after a failed `initialize`.
- `test_initialize.py`'s module docstring says retry is "implementation-specific" and that a second `initialize` is "forbidden".

The `-32022` version-rejection gate in `tck.common.plugin` and the `@pytest.mark.negotiation` set (INIT-201/003/202/208) are still correct. The TCK's mock-client `initialize` params (`capabilities: {}`, `info: {name, version}`) validate against the target `ClientCapabilities`/`Implementation`.

## Requirements

Summary table, as the brief asks (id -> classification -> note). Targets are `docs/protocol/v2/draft/initialization.mdx` (`init`) unless prefixed. "TCK-observable" is the only lens used.

| id | classification | note |
|---|---|---|
| ACP-INIT-001 | unchanged | `init:24,51` same lines, same text |
| ACP-INIT-201 | citation-only | `:98` -> `:110` |
| ACP-INIT-003 | citation-only (**meaning moved**, manual) | `:98,117` -> `:108,110,112`. Old `:117` was the `-32602` sentence, which is now `:108`; mechanical remap would land on `:129` (wrong) |
| ACP-INIT-202 | citation-only (**meaning moved**, manual; rule strengthened) | `:98,100,117` -> `:108,110,112`. `:108` "read `protocolVersion` before validating any other parameter" now directly backs FAILing `-32602` for the `info`-less v1 request |
| ACP-INIT-205 | citation-only (+ new `$def`) | `:100-115` -> `:112-127`; add `schema/v2/schema.unstable.json#/$defs/UnsupportedProtocolVersionErrorData` |
| ACP-INIT-206 | citation-only (**meaning moved**, manual) | `:117` -> `:108` |
| ACP-INIT-207 | citation-only | `:117` -> `:129`. Stays scoped to "no version-specific operations"; the broader new rules go to INIT-209/210 |
| ACP-INIT-208 | citation-only | `:98` -> `:110` (one of the 13 "unflagged" ids) |
| ACP-INIT-203 | citation-only | `:293` -> `:360` (optionally `:360-376`; the doc now marks `name`/`version` required and says omitted == `null` for `title`) |
| ACP-INIT-204 | unchanged | cites schema only; the marker walk self-updates for the new `session.archive/status/title` and `auth.status` |
| ACP-SCHEMA-001 | unchanged (row); **test needs review** (B1) | the test's batch-flattening rationale cites ACP-BATCH-207, which batching removal invalidates (transports owner) |
| ACP-PROMPT-206 | citation-only | `:248` -> `:308`; `ContentBlock::Text`/`ResourceLink` reworded to `text`/`resource_link` blocks, same rule |
| ACP-PROMPTCAP-001/002/003 | citation-only | `:246-271` -> `:306-331` |
| ACP-SYSPROMPT-202 | citation-only | `:238-244` -> `:298-304`; "**Unstable.**" label dropped (system prompt stabilized), no rule change |
| ACP-EXT-204 | citation-only | `:134` -> `:156` (one of the 13 "unflagged" ids); extensibility.mdx parts belong to that doc's owner |
| ACP-CONFIG-202 (not citing this doc) | citation add suggested | `init:239-240` "advertise config options MUST also support `session/set_config_option`"; already enforced (the test FAILs on any error, `-32601` included). Duplicates session-config-options.mdx:234 -> route to the config owner |
| ACP-AUTH-203 / ACP-AUTH-204 (not citing this doc) | citation add suggested | `init:82` wording changed from "one or more valid entries" to "a non-empty list". Consistent with `inferred:authMethods`. Route to the authentication owner |
| ACP-AUTH-202 (not citing this doc) | repoint (B3) | `#/$defs/AuthCapabilities` -> `#/$defs/ClientAuthCapabilities` (same shape). Authentication owner |
| **ACP-INIT-209** | new, MANDATORY | non-`initialize` request before init completes -> `-32600` |
| **ACP-INIT-210** | new, MANDATORY | agent sends no request/notification while uninitialized |
| **ACP-INIT-211** | new, DECISION NEEDED (rec. MANDATORY) | a failed `initialize` can be retried on the same connection |
| **ACP-INIT-212** | new, DECISION NEEDED (rec. MANDATORY) | a repeated `initialize` before any other request is handled like the first; a failed repeat keeps the previous one |
| **ACP-INIT-213** | new, DECISION NEEDED (rec. MANDATORY) | `initialize` repeated after another request -> `-32600` |
| **ACP-INIT-214** | new, MANDATORY | newer-version request with unparseable params is not rejected |
| ledger x4 | new non-requirements | see "Ledger" below |
| `-32022` gate (`tck.common.plugin`) | still correct | comment cite `:100` -> `:112` |
| `negotiation` marker set | still correct | do not add it to any new row |

Requirement tier table (the role's standard table):

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | Agents MUST reject any request other than `initialize` that arrives before initialization completes with `-32600` | MUST | `docs/protocol/v2/draft/error.mdx:60`; `init:88-90` @ 3961af94fa62 |
| 2 | Agents ignore notifications before initialization | MUST (same sentence as #1) | `error.mdx:60`; `init:90` |
| 3 | Agents MUST NOT send requests or notifications before initialization completes | MUST | `init:91` |
| 4 | After a failed `initialize` the connection is uninitialized; the Client MAY send `initialize` again | client MAY, so agent-side support is implied (RFC 2119 "MAY": an implementation must interoperate with a peer that uses the option) | `init:92` |
| 5 | Repeat before first other request: the Agent handles each like the first; latest successful is authoritative; a failed repeat keeps the previous one | indicative (no keyword); client MAY | `init:137-139` |
| 6 | `initialize` after another request is rejected with `-32600` | indicative, in a MUST paragraph | `error.mdx:29,60`; client side `init:139` MUST NOT |
| 7 | Read `protocolVersion` before validating other params; malformed -> `-32602` | MUST | `init:108` |
| 8 | Select highest supported <= requested; MUST NOT exceed it; use the selected version's response shape | MUST | `init:110` |
| 9 | No supported version <= requested -> `-32022` with `data: {requested, supported}` | MUST | `init:112`; `#/$defs/UnsupportedProtocolVersionErrorData` |
| 10 | After `-32022` the Agent MUST NOT begin version-specific operations | MUST | `init:129` |
| 11 | Newer requested version: the Agent MUST ignore params it can't parse under the selected version instead of rejecting | MUST | `init:131` |
| 12 | Non-empty `authMethods` -> MUST implement `auth/login` and `auth/logout` | MUST, gated by `inferred:authMethods` | `init:82` |
| 13 | Advertising config options -> MUST support `session/set_config_option` | MUST, gated by `inferred:configOptions` | `init:239-240` |
| 14 | `session` advertised -> MUST support `text` and `resource_link` prompt blocks | capability:`capabilities.session` | `init:308` |
| 15 | Agent MUST provide `info` (`name`, `version` required) | MUST | `init:360-376`; `#/$defs/Implementation` |
| 16 | Receivers MUST ignore unknown capability fields at every level | MUST | `init:156` |
| 17 | Omitted capabilities MUST be treated as unsupported | MUST (agent side observable only through specific capabilities: AUTH-202, CLIENTCAP-201) | `init:149` |

## Details

### Line remap, base -> target (`initialization.mdx`)

| base line | content | target line |
|---|---|---|
| 24, 51 | Client MUST call `initialize`; Agent MUST respond with version/capabilities/info | 24, 51 |
| 82 | `authMethods` obligations (reworded) | 82 |
| 98 | select highest <= requested; response shape | 110 |
| 100-115 | `-32022` + data + example | 112-127 |
| 117 | (a) mismatch does not initialize / MUST NOT begin version-specific ops; (b) malformed `protocolVersion` -> `-32602` | (a) 129; **(b) 108** |
| 134 | unknown capability fields MUST be ignored | 156 |
| 238-244 | `systemPrompt` capability field | 298-304 |
| 246-271 | Session prompt capabilities | 306-331 |
| 248 | baseline `text` + `resource_link` | 308 |
| 293 | Implementation information MUST | 360 |
| new | Before initialization completes | 86-94 |
| new | `protocolVersion` read first | 108 |
| new | ignore unparseable params on newer version | 131 |
| new | Repeating initialization | 135-141 |
| new | config-option MUST | 239-240 |
| new | `auth.status`, `session.archive/fork/status/title`, `mcp.acp` entries | 215-220, 261-287, 347-352 |

`fork` and `mcp.acp` were already in the base schema (`SessionCapabilities.fork`, `McpCapabilities.acp`); only their documentation is new. The schema additions are `SessionCapabilities.{archive,status,title}` and `AgentAuthCapabilities.status` (Appendix B of the inventory, which I confirmed). `InitializeRequest`, `InitializeResponse`, `AgentCapabilities`, `PromptCapabilities`, `Session*SystemPrompt*`, `ErrorCode` and `Implementation` are structurally identical at base and target, ignoring descriptions. `ClientCapabilities` differs only by the `auth` `$ref` rename (B3).

### Target `$defs` relevant here (structure, descriptions ignored)

- `InitializeRequest`: `protocolVersion` (`ProtocolVersion`, uint16 0..65535), `info` (`Implementation`), `capabilities` (`ClientCapabilities`, `default: {}`, `x-deserialize-default-on-error: true`), `_meta`. Required: `protocolVersion`, `info`.
- `ClientCapabilities`: `auth` -> `ClientAuthCapabilities | null` (`terminal` -> `TerminalAuthCapabilities | null`, `_meta`), `elicitation` -> `ElicitationCapabilities | null` (`form`, `url`, `_meta`), `_meta`.
- `UnsupportedProtocolVersionErrorData`: `requested` (`ProtocolVersion`), `supported` (array of `ProtocolVersion`), `_meta`. Required: `requested`, `supported`.
- `Error.data`: `ErrorData | null`, where `ErrorData` = `anyOf [UnsupportedProtocolVersionErrorData, SessionNotFoundErrorData, {}]`. Schema validation alone therefore never rejects a bad `-32022` `data`, so INIT-205's hand-written check stays necessary.

### The TCK's own `initialize` params against the target `ClientCapabilities`

`src/tck/v2/__init__.py:17-24` sends `{protocolVersion: 2, info: {name: "acp-tck", version}, capabilities: {}}`. `test_authentication.py:121` sends `capabilities: {auth: {terminal: {}}}`. Both are valid under target `ClientCapabilities`/`ClientAuthCapabilities`. `test_extensibility.py:192` sends unknown non-`_` fields on purpose (EXT-204). `init:168-170` now says "Extension-specific capabilities belong in `_meta`". That is a client rule; the EXT-204 probe deliberately stands in for a *future ACP* field, as its text already says, so no change is needed. `_V1_SHAPED_PARAMS` (`{protocolVersion: 1, clientCapabilities: {}}`, no `info`) is now explicitly protected by `init:108`: a v2-only agent must answer `-32022`, not `-32602`.

### Existing rows: what the tests must change

- **INIT-003, INIT-201, INIT-202, INIT-208**: test logic unchanged. Update the `initialization.mdx:98..117` references in docstrings to the new lines.
- **INIT-205**: unchanged. Optional strengthening of `init:108`: also probe `{protocolVersion: 0}` with **no `info`** and expect `-32022`, not `-32602`. That is my suggestion, not a required change.
- **INIT-206**: unchanged.
- **INIT-207**: unchanged logic. It accepts any error, or silence, for the post-`-32022` `session/new`. The tighter `-32600` code and the "no message of any method" rule go into new rows INIT-209/210, so INIT-207 keeps its narrower "no version-specific operations" scope (`init:129`). Alternative: widen INIT-207 itself. DECISION NEEDED; I recommend new rows, to keep `starts_session_after_mismatch.py`'s "FAILs exactly ACP-INIT-207" readable.
- **`test_initialize.py` module docstring (lines 4-8)**: "whether a rejected `initialize` can be retried is implementation-specific, and a second `initialize` on an initialized connection is forbidden" is **now wrong**. A retry after failure is permitted (`init:92`), and so is a repeat before any other request (`init:137-139`). Running each probe in its own process is still a fine design choice; only the stated reason is outdated. The same applies to `_helpers.py:688-689` ("never send a second `initialize`").
- **SCHEMA-001**: the row is fine. Its test flattens agent-sent array lines "because ACP-BATCH-207 permits" batches. Under B1 an array line from the agent is itself non-conforming. Route to the transports/batch owner.

### Proposed new requirements

All of them bind agents implementing v2. Each SKIPs with `VERSION-MISMATCH:` unless the cached main handshake selected 2 (reuse `_skip_unless_v2_endpoint`), and **none** carries `@pytest.mark.negotiation`. Each runs in a fresh process with `connected_agent(handshake=False)`. Citations are `@ 3961af94fa62`.

**ACP-INIT-209: MANDATORY, no capability gate.**
- Text: "A request other than `initialize` that arrives before initialization completes is answered with `-32600`, on a fresh connection and after a failed `initialize` (`-32602` or `-32022`); a notification sent then gets no response."
- Citation: `docs/protocol/v2/draft/error.mdx:29,60; docs/protocol/v2/draft/initialization.mdx:88-90`.
- Tier: error.mdx:60 says "Agents **MUST** reject ... with `-32600`, and ignore notifications". init:90 says the same without the keyword.
- Observation, three connections:
  1. Fresh: send a pre-init request and expect `-32600`.
  2. Send `initialize` with `protocolVersion` omitted, expect `-32602`, then send the request again and expect `-32600`.
  3. Send `initialize(0)`; if the reply is `-32022`, send the request and expect `-32600`.
- Which method to probe: use a standard method such as `session/new` with a valid `cwd`. A `_tck/...` probe would muddy `-32601` vs `-32600`, but the spec says "any request", so a `_tck/...` probe is acceptable as a second probe.
- Also send `session/cancel` (a notification) on the fresh connection first, and check that no line answers it. The ignore-part overlaps JSONRPC-003; fold it in or drop it.
- Fixture: `serves_before_initialize.py` answers `session/new` before `initialize`. **`_base.py` must change first**: it gates only after `-32022` (`_init_rejected`, `_base.py:135-136,192-195`), not on a fresh connection or after `-32602`. Today the conforming baseline would FAIL this row. `starts_session_after_mismatch.py` will also FAIL INIT-209: by design its `session/new` succeeds after `-32022`. Its expected FAIL set becomes {207, 209}, so update its docstring and the `test_cli.py` expectation.

**ACP-INIT-210: MANDATORY, no capability gate.**
- Text: "While the connection is uninitialized (before `initialize` is answered successfully, including after a failed `initialize`) the agent sends no JSON-RPC request or notification."
- Citation: `docs/protocol/v2/draft/initialization.mdx:88,91`.
- Tier: "Agents **MUST NOT** send requests or notifications".
- Observation:
  - **(a)** Spawn, wait a short quiet period, and assert that no `method`-bearing message arrived before `initialize` was sent.
  - **(b)** In the transcript, no `method`-bearing message from the agent precedes the successful `initialize` response.
  - **(c)** After `-32602` and after `-32022`, a quiet period with no `method`-bearing message. This is a superset of INIT-207's `session/*`/`elicitation/*` filter.
  - Startup output that is not JSON is TRANSPORT's concern, not this row's.
- Fixture: `notifies_before_initialize.py` writes a `_fixture/hello` notification at startup.
- **Conflict**: `pushes_status_notifications.py:32-38` sets `_initialized = True` after *any* `initialize` request, including a failed one, and then pushes on an uninitialized connection. So this "conforming" fixture, and anything that subclasses it (`pushes_status_and_answers_notifications.py`, `pushes_status_and_splits_batch_replies.py`; please verify), would FAIL INIT-210. Fix: set the flag only after a successful `initialize`.

**ACP-INIT-211: DECISION NEEDED, recommend MANDATORY (alternative ADVISORY).**
- Text: "After an `initialize` that failed (`-32602` for an omitted `protocolVersion`, or `-32022`), a corrected `initialize(2)` on the same connection succeeds and the connection is then usable."
- Citation: `docs/protocol/v2/draft/initialization.mdx:92`.
- Tier rationale: the text gives the *client* a MAY ("the Client **MAY** send `initialize` again, for example after correcting invalid params"). The only agent-side reading that makes that MAY meaningful is that the agent accepts the retry. RFC 2119 says an implementation must interoperate with a peer that uses an option. There is no explicit agent MUST, hence the decision.
- Observation: same connection; failed `initialize`, then valid `initialize(2)`. Expect a result selecting 2. Optionally follow with a `_tck/...` probe and expect `-32601` (not `-32600`), which proves the connection is now initialized.
- Fixture: `no_retry_after_failed_initialize.py` keeps refusing everything with `-32600` after any failed `initialize`.
- **Conflict**: `_base.py` today never clears `_init_rejected` on a later successful `initialize`, so the conforming baseline would FAIL the `-32022` leg.
- Rust SDK implements retry. Python SDK partly: a version `!= 2` raises `-32602` before the phase changes, so retry works there, but a handler failure moves the state to `failed` and a retry is then rejected. See Discrepancies.

**ACP-INIT-212: DECISION NEEDED, recommend MANDATORY (alternative ADVISORY).**
- Text: "A second `initialize(2)` sent after the first succeeded and before any other request is handled like the first (a result selecting 2); a repeat that fails (`protocolVersion` omitted -> `-32602`) leaves the previous initialization in effect (a following `_tck/...` probe gets `-32601`, not `-32600`)."
- Citation: `docs/protocol/v2/draft/initialization.mdx:137-139`.
- Tier rationale: "The Agent handles each one like the first and treats the latest successful `initialize` as authoritative. A repeat that fails leaves the previous successful initialization in effect." This is indicative, normative-sounding text with no keyword, combined with a client MAY. `init:141` exempts only v1-only agents, and the VERSION-MISMATCH skip handles those.
- Optional conditional sub-check of "latest is authoritative": first `initialize` with `auth.terminal: {}`, repeat without it. If the first result listed a `type: "terminal"` method, the second must not (AUTH-202 logic applied to the repeat). SKIP that sub-check otherwise.
- Fixture: `rejects_repeated_initialize.py` answers any second `initialize` with `-32600`. The Python SDK behaves exactly like this today.

**ACP-INIT-213: DECISION NEEDED, recommend MANDATORY (alternative ADVISORY).**
- Text: "An `initialize` sent after another request on an initialized connection is rejected with `-32600`."
- Citation: `docs/protocol/v2/draft/error.mdx:29,60; docs/protocol/v2/draft/initialization.mdx:139`.
- Tier rationale: error.mdx:60 says "They also reject an `initialize` repeated after another request with `-32600`". That sentence follows a MUST in the same paragraph but has no keyword of its own. The error table (`:29`) lists this case under `-32600`. `init:139` is the client-side MUST NOT, which the TCK deliberately violates here, as INIT-206 already does with malformed versions.
- Observation: `initialize(2)` OK, then `_tck/probe` (any answer), then `initialize(2)`; expect error code `-32600`. A success FAILs.
- The spec says "any other request", so a `-32601`'d `_tck/...` probe counts. The Rust SDK closes the repeat window on any incoming request that passes the initialization gate, before dispatch (`protocol_compat.rs:654-666`). If the orchestrator prefers a request that succeeds, use `session/list` when `capabilities.session` is advertised; that may hit `-32000` on auth-gated agents.
- Fixture: `accepts_initialize_after_request.py`. Note that `_base.py` today answers every `initialize` with success, so the baseline would FAIL until it is updated.

**ACP-INIT-214: MANDATORY.**
- Text: "An `initialize` requesting a version above the selected one (`protocolVersion: 65535`) whose `capabilities` is unparseable under v2 (a non-object, e.g. `42`) is not rejected: it gets a result, not an error."
- Citation: `docs/protocol/v2/draft/initialization.mdx:131`.
- Tier: "the Agent **MUST** ignore parameters it can't parse under the selected version instead of rejecting the request".
- Observation: one probe, fresh process. Assert only "result, not error". INIT-003 owns version correctness, which keeps `echoes_any_version.py`'s FAIL set unchanged. The schema's `x-deserialize-default-on-error: true` on `InitializeRequest.capabilities` supports this.
- Probe choice: I did not choose an `info` that is missing or malformed. The Rust SDK tolerates that too (`acp.rs:406-412`), but whether a missing required field counts as a parameter it "can't parse" is arguable. Hypothesis: keep to `capabilities`.
- Fixture: `rejects_unparseable_newer_params.py` validates `capabilities` strictly and returns `-32602`.
- Check that `_base._client_wants_terminal_auth` does not crash on a non-object `capabilities`.

### Ledger (deliberate non-requirements) proposed for `spec-tracker/maps/v2.toml`

1. `docs/protocol/v2/draft/initialization.mdx:88-90 @ 3961af94fa62`.
   - Statement: a request arriving while `initialize` is in flight (sent, not yet answered) is rejected with `-32600`.
   - Reason: unobservable. Whether a pipelined request "arrives before initialization completes" depends on agent scheduling, so a client cannot provoke it deterministically.
2. `docs/protocol/v2/draft/initialization.mdx:147 @ 3961af94fa62`.
   - Statement: Agents SHOULD support all possible combinations of their peer's capabilities.
   - Reason: combinatorial and unobservable in general. Specific combinations are covered by AUTH-202 and CLIENTCAP-201.
3. `docs/protocol/v2/draft/initialization.mdx:200 @ 3961af94fa62`.
   - Statement: the Agent SHOULD specify whether it supports each listed capability.
   - Reason: unobservable. Omission is defined as "unsupported" (`:149`), so omitting and not supporting look identical on the wire.
4. `docs/protocol/v2/draft/initialization.mdx:139 @ 3961af94fa62` (the "authoritative" clause).
   - Statement: the Agent treats the latest successful `initialize` as authoritative.
   - Reason: observable only through capability-dependent behaviour the agent may not have. Partially covered by INIT-212's optional terminal-auth sub-check. Ledger only the general clause.

Client-only rules (`:24`, `:90` first half, `:106`, `:129` SHOULD close, `:133`, `:139` MUST NOT, `:225` providers MUST NOT, `:370` display SHOULD) are pure client obligations. I skip them per the brief.

### `spec-tracker/maps/v2.toml`

`initialization.mdx` is a whole-doc `[[core_doc]]` with no `sections` (`maps/v2.toml:73-81`). The sentence-casing breaks no address, and the new subsections ("Before initialization completes", `:86`; "Repeating initialization", `:135`) are automatically core. That is correct: they govern every connection. Sentence-cased headings at target, for reference: Before initialization completes (86), Protocol version (96), Version negotiation (104), Repeating initialization (135), Capabilities (143), Client capabilities (166), Terminal authentication (172), Elicitation (184), Agent capabilities (198), Session capabilities (229), Session prompt capabilities (306), Session MCP capabilities (333), Implementation information (358). Optional: add `src/tck/v2/__init__.py`, which builds the `initialize` params, to that entry's `code` list.

### Reference SDK behaviour (only where it bears on testability and tiering)

Rust SDK @ e75d6f19fabb, in `src/agent-client-protocol/src/`:
- `role/acp.rs:404-423` (doc of the `.v2()` builder): a newer-version request is accepted with what parses (unparsable capabilities/`_meta` dropped; missing/malformed `info` replaced). A repeat before any other request is negotiated like the first, and the latest wins. A repeat after another request, or while one is in flight, gets `-32600`. A failed repeat keeps the previous initialization.
- `role/acp.rs:461-464`: a rejected first message, `-32022` included, leaves the connection uninitialized and open, and the client may retry. Notifications before init are ignored.
- Enforcement: `jsonrpc/protocol_compat.rs:956-990` (`begin_initialize`; `Ready if repeatable`, otherwise `-32600`), `:994-999` (window closed on any other request), `:1061-1079` (`fail_initialize` restores the previous init or `Uninitialized`), `:1178-1182` (`initialization_required` -> `-32600`), `:654-656` (incoming non-init request before init -> `-32600`).
- Tests: `protocol_compat.rs:1911` (`v2_agent_accepts_repeated_initialize_before_other_requests`, asserting `-32600` after another request at `:1950-1951`) and `:1989` (`failed_repeated_initialize_keeps_previous_initialization`).
- Conclusion: the Rust SDK implements every proposed row INIT-209..214.

Python SDK @ 8a9940744d0a (checkout possibly stale, see above):
- `src/acp/experimental/v2/_initialization.py:24-31`: any `initialize` after the first is `-32600` "may only be initialized once", and a version `!= 2` gets `-32602`.
- `:45-50`: a handler failure sets the phase to `failed`, which makes `require()` reject later requests with `-32600` (`:61-67`) and `begin()` reject any retry.
- `agent.py:35-48`: the full `InitializeRequest` is validated with pydantic *before* the version is read.
- `src/acp/experimental/negotiation.py:86-98`: the router rejects pre-init requests with `-32600` and rejects a second `initialize`. `:118-121`: an unsupported version gets **`-32600`**, not `-32022`.
- Conclusion: Python SDK-based v2 agents would FAIL INIT-212 and INIT-213's counterpart cases (the repeat is rejected), possibly INIT-211 (after a handler failure) and INIT-214, and existing INIT-202/205 in some configurations. That is evidence the SDK lags the spec, not a reason to change the spec reading.

## Testability notes

- Every new row needs fresh processes with `handshake=False`. None can reuse the cached `agent_initialize_result` connection.
- INIT-209/210/211 must tolerate an agent that exits after a failed `initialize`.
  - INIT-209: if the agent exits before answering the follow-up request, that is FAIL. The MUST requires a `-32600` response, and an exiting agent never sends one. Treat it like INIT-206's "no reply" FAIL.
  - INIT-211: exit is FAIL.
  - INIT-210: exit is PASS.
- Quiet periods: reuse `quiet_period(default_timeout)` / `drain_quiet`, as INIT-207 does. The startup quiet window in INIT-210(a) adds wall time to every run, so keep it short (e.g. the same `quiet_period`).
- Under the rules at target, a conforming agent:
  - answers a pre-init `session/new` with `-32600`, and the connection stays open;
  - accepts a corrected `initialize` afterwards;
  - accepts `initialize, initialize` back to back;
  - rejects `initialize, _tck/x, initialize` with `-32600` on the third message;
  - is silent until its first successful `initialize` response.
- Fixture work the programmer should expect: update `_base.py` (fresh-connection gate, clear `_init_rejected` on success, repeat window), `pushes_status_notifications.py` (flag only on success), `starts_session_after_mismatch.py` (FAIL set becomes {207, 209}), and `tests/v2/test_cli.py` expectations. Then add one non-conforming fixture per new row.

## Discrepancies

1. **The pre-init `-32600` rule is a MUST in error.mdx but indicative in initialization.mdx.** Compare `init:90` ("Agents reject them with `-32600` and ignore notifications") with `error.mdx:60` ("Agents **MUST** reject ..."). They agree in substance. Cite both and take the tier from error.mdx.
2. **The `initialize`-after-another-request rejection has no explicit agent keyword anywhere.** `error.mdx:60` "They also reject..." and the `error.mdx:29` table, against `init:139` (client MUST NOT only). The Rust SDK enforces it. This is the source of the INIT-213 DECISION NEEDED.
3. **The Python SDK (experimental v2) contradicts the target spec** on: a repeat before another request (it rejects with `-32600`), retry after a handler failure (rejected), the `-32022` code (its router uses `-32600`), validating params before reading `protocolVersion` (`agent.py:38`), and requests above v2 on a plain `AgentSideConnection` (`-32602`, `_initialization.py:27-31`). The Rust SDK matches the spec on every point checked.
4. **The inventory says "new `session.fork` capability entry".** Only the *doc* entry is new; `SessionCapabilities.fork` and `McpCapabilities.acp` already existed in the base schema. This does not affect any id.

## Open questions

- **Id coordination**: the error.mdx owner may also propose a row for error.mdx:60 (pre-init `-32600`, repeat `-32600`). Settle on one owner so INIT-209/213 are not duplicated. I recommend the INIT area, since `init:86-94/135-141` is the primary statement.
- **Owners of the new unstable methods**: `auth.status` (`auth/status`, `auth/status_update`) and `session.archive/status/title` (`session/archive|unarchive|status|set_title`). From this doc alone, the only observable rule per capability is "supplying `{}` means the Agent supports them" (`init:215-220,261-287`), which would give a CAPABILITY-gated row per method ("advertised -> not `-32601`, schema-valid result"). The behavioural detail lives in `session-list.mdx#archived-sessions-unstable`, `error.mdx:65-67` and the RFDs (`/rfds/get-auth-state`, `/rfds/session-status`, `/rfds/session-set-title`). Route to whoever owns those docs; I propose no ids for them.
- **Config, authentication and transports owners**: three cross-doc follow-ups listed in the summary table: CONFIG-202 citation add, AUTH-202 repoint plus AUTH-203/204 citation add, and the SCHEMA-001 test's batch rationale under B1.
- **Python SDK checkout freshness**: the `pull --ff-only` failed. If its behaviour matters for the cross-check baseline, re-check it after fixing the checkout's branch config.
