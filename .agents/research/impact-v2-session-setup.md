# v2 impact audit: `docs/protocol/v2/draft/session-setup.mdx` (beac4ba -> 3961af9)

**Sources checked:** agent-client-protocol spec checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (target), diffed against base `beac4ba96190018e9f6d82e148ff275084c5aa3e` (not pulled, per brief). Read whole: `session-setup.mdx` @ target; `error.mdx` @ target (Unknown sessions); `transports.mdx:41-67` @ target; target and base `schema/v2/schema.unstable.json` (`NewSession*`, `ResumeSession*`, `CloseSession*`, `ReplayFrom`, `SessionInfo`, `SystemPrompt*`, `McpServer*`, `EnvVariable`, `HttpHeader`, `BackgroundWork*`, `AvailableCommand`, `CancelRequestNotification`). Rust SDK `/Users/eugene/Documents/JetBrains/projects/acp-rust-sdk` @ `e75d6f19fabb` (2026-11-09), for one question only (request processing order, CLOSE-204). Python SDK and A2A TCK: not consulted (nothing here needed them).
TCK side: `src/tck/v2/requirements.py`, `src/tck/v2/conformance/{test_session,test_session_capabilities,test_session_config,test_cancel,_helpers}.py`, `src/tck/v2/validation.py`, `tests/fixtures/agents/v2/_base.py` and the `resume_*`/`close_*`/`system_prompt_*`/`fork_*` fixtures, `spec-tracker/maps/v2.toml`.
**Confidence:** high for classifications and line remaps (read from the target text, not inferred from hunks); medium for the tier calls on the new ids flagged DECISION NEEDED (they hinge on declarative, non-keyword sentences).

## Answer

No registered requirement citing this doc is invalidated. 18 of the 23 citing ids only need line remaps. Five need a closer look:

- `ACP-CONFIG-203`: its cited MAY lines are now MUSTs.
- `ACP-RESUME-202` and `ACP-RESUME-209`: part of the text they cite was deleted or moved into the new "Replay contents" section.
- `ACP-CLOSE-204`: the new "active session" rule makes `-32002` a third legal outcome.
- `ACP-MCP-201`: its rationale text is out of date.

The doc adds many new agent-side rules that the TCK can observe. The strongest are:

- `-32002` for prompts on a closed session and for resuming an unknown session.
- `$/cancel_request` for pending permission requests before `session/close` responds.
- No session messages after the close response.
- `-32602` for a relative `cwd`, a relative `additionalDirectories` entry, and an unsupported MCP transport (including v1 `sse`).
- The setup response must carry `configOptions`/`availableCommands` when the session has them.
- No replayed historical `state_update`.
- Background-item updates must precede the resume snapshot.

`validation.py` has no carve-out specific to session setup or resume. Its existing carve-outs are unaffected. Four `_base.py` fixture behaviours become non-conforming if the new ids are adopted: unknown-session prompt returns `-32602`, resume accepts any id, close sends no `$/cancel_request`, and `resume_lists_foreign_session.py` returns `-32602`.

## Summary table

| Id | Classification | One-line note |
|----|----------------|---------------|
| ACP-SESSION-001 | citation-only | `:72` -> `:84`. Its schema validation now also catches `null` `configOptions`/`availableCommands` and B5 (`AvailableCommand.type`). |
| ACP-SESSION-002 | citation-only | `:72,478` -> `:84,511` |
| ACP-SESSION-203 | unchanged | Cites only the schema. `default-on-null` is a receiver hint, not a wire change. |
| ACP-RESUME-201 | citation-only (+ cosmetic text) | `:129-130` -> `:144-145`. The gate wording is now "advertise `capabilities.session`" (same gate). The stale "B3" label in the text should go. |
| ACP-RESUME-202 | citation-only, **Needs review** | `:212-215` (notices) moved to `:228` in "Replay contents". `:123` -> `:138`. The kind filter is still right (see Details). |
| ACP-RESUME-203 | citation-only | `:164-169` -> `:179-184`. The new sentence at `:184` (in-progress updates are live, not replay) is consistent with the test. |
| ACP-RESUME-204 | citation-only | `:261-266` -> `:282-287` |
| ACP-RESUME-205 | citation-only | `:279-292` -> `:299-312` |
| ACP-RESUME-206 | citation-only | `:36-37,301-303,319-324` -> `:36-37,321-323,339-344`. The new background rule `:346` is a separate new id. |
| ACP-RESUME-207 | citation-only | `:197-201` -> `:211-215`. `ReplayFrom/anyOf/1` still resolves (it only lost `_meta`). |
| ACP-RESUME-208 | citation-only | `:200-201` -> `:214-215` |
| ACP-RESUME-209 | citation-only, **Needs review** | `:192-195` -> `:207-209`. The cited sentence ("can each be replayed ... as chunks") was deleted; its successor is `:221`. `:261-263` -> `:282-284`. |
| ACP-CLOSE-201 | citation-only | `:338-340,360-376` -> `:367-369,389-405` |
| ACP-CLOSE-202 | citation-only | `:360-364` -> `:389-393` |
| ACP-CLOSE-203 | citation-only | `:364` -> `:393` (not flagged by the tool, but the text is unchanged) |
| ACP-CLOSE-204 | **changed text** (DECISION NEEDED) | `:366` -> `:395`. Accept `-32002` as a third legal outcome (`:51`). |
| ACP-CANCEL-208 | citation-only (session-setup part) | `:360-366` -> `:389-395`. The added `$/cancel_request`/background text at `:391` is a separate new id. |
| ACP-ADDDIRS-201 | citation-only | `:383-411` -> `:414-441`. The new `:443` MAY-reject-nonexistent does not affect it, because the test uses an existing directory. |
| ACP-ADDDIRS-202 | citation-only | `:385-386,409` -> `:415-416,439` |
| ACP-SYSPROMPT-201 | citation-only (+ cosmetic) | `:441-445,450` -> `:473-477,483`. Stabilized: the heading lost "(unstable)", and the test-module docstring still says "unstable". |
| ACP-SYSPROMPT-202 | citation-only (+ cosmetic) | `:444-445,450` -> `:476-477,483` (the `initialization.mdx` part belongs to another researcher) |
| ACP-MCP-201 | **changed text** (rationale only, tier unchanged) | `:508-558,612,637` -> `:555-607,656,681-683`. `:685` now explicitly allows both outcomes. |
| ACP-MCP-202 | citation-only | `:560-608` -> `:609-652` |
| ACP-CONFIG-203 | **changed citation meaning**, text kept (DECISION NEEDED) | `:94,313-315` -> `:108,333-335`. The cited MAYs are now MUSTs. Presence goes to new `ACP-RESUME-210`. |
| ACP-FORK-202 (not on my list) | citation improvement | It can now cite the normative `session-setup.mdx:49` ("active from a successful ... `session/fork`"). |
| ACP-INFO-UNKNOWNSESSION-001 (error.mdx researcher) | affected | `session-setup.mdx:51` + `error.mdx:54` now specify `-32002`. See new `ACP-SESSION-205`. |
| **new** ACP-SESSION-204 | new, CAPABILITY (DECISION NEEDED) | `session/new` with a relative `cwd` -> `-32602` (`:524`) |
| **new** ACP-SESSION-205 | new, CAPABILITY | `session/prompt` on a session closed on this connection -> `-32002` (`:51`, `error.mdx:54`) |
| **new** ACP-SESSION-206 | new, ADVISORY | No session-scoped agent->client request before the `session/new` response (`:103`) |
| **new** ACP-SESSION-207 | new, ADVISORY | No `config_option_update`/`available_commands_update` before the `session/new` response (`:103`) |
| **new** ACP-SESSION-208 | new, CAPABILITY (DECISION NEEDED) | A non-empty list notified before the response must also appear in the response (`:108,136,138`) |
| **new** ACP-RESUME-210 | new, CAPABILITY (DECISION NEEDED) | The resume response carries `configOptions`/`availableCommands` when the session has them (`:108,333-335`) |
| **new** ACP-RESUME-211 | new, CAPABILITY | `session/resume` of a never-created id -> `-32002` (`:47`, `error.mdx:54-56`) |
| **new** ACP-RESUME-212 | new, CAPABILITY | No replayed historical `running`/`requires_action` `state_update` before the resume response (`:227,348`) |
| **new** ACP-RESUME-213 | new, CAPABILITY | Each snapshot `background` item is preceded by its current update (`:346`) |
| **new** ACP-RESUME-214 | new, ADVISORY | `session_info_update` before the resume response (`:358`) |
| **new** ACP-RESUME-215 | new, ADVISORY (low priority) | Replayed tool calls with no live work end with a final status (`:223`) |
| **new** ACP-RESUME-216 | new, ADVISORY (DECISION NEEDED: add or ledger) | Resuming a session active on the same connection succeeds (`:49,53`) |
| **new** ACP-CLOSE-205 | new, CAPABILITY | A pending `session/request_permission` gets `$/cancel_request` before the close response (`:391`) |
| **new** ACP-CLOSE-206 | new, CAPABILITY (DECISION NEEDED) | No session messages after the close response (`:395`) |
| **new** ACP-CLOSE-207 | new, ADVISORY | Closing an already-closed session -> `{}` (`:407-410`) |
| **new** ACP-ADDDIRS-203 | new, CAPABILITY:additionalDirectories | A relative entry -> `-32602` (`:443`) |
| **new** ACP-MCP-203 | new, CAPABILITY (DECISION NEEDED: probe value) | An unsupported transport (v1 `sse`) -> `-32602` (`:545`) |
| **new** ACP-MCP-204 | new, ADVISORY (DECISION NEEDED: or ledger) | Duplicate server `name` -> `-32602` (`:547`) |
| **new** ACP-MCP-205 | new, ADVISORY (overlaps security researcher) | `env`/`headers` secret values never appear in agent output (`:695`) |
| ledger x16 | deliberate non-requirements | See "Ledger" below |

## Requirements

Tiers of the new rules (citations are `docs/protocol/v2/draft/session-setup.mdx` @ 3961af94fa62 unless noted):

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | Session-scoped requests require an active session, otherwise `-32002` (with `data.sessionId`) | MUST (error.mdx keyword; session-setup declarative) -> capability:session | `:51`; `error.mdx:54-56` |
| 2 | Resuming a session the Agent no longer has fails with `-32002` | MUST (error.mdx) -> capability:session | `:47`; `error.mdx:54,56` |
| 3 | Setup responses MUST include the session's config options / commands; MUST NOT send `null` | MUST -> capability:session | `:108,136`; `slash-commands.mdx:12` |
| 4 | SHOULD put initial state in the response, not in notifications before it; SHOULD NOT send session-scoped requests before the response | SHOULD | `:103` |
| 5 | MUST NOT replay historical `state_update`; replay does not include them | MUST | `:227,348` |
| 6 | Before the snapshot, MUST send a current update for each `background` item not already delivered | MUST | `:346` |
| 7 | SHOULD send `session_info_update` before the resume response | SHOULD | `:358` |
| 8 | Replayed tool calls with no live work SHOULD have a final status | SHOULD | `:223` |
| 9 | Before responding to close, MUST cancel every pending permission request/elicitation with `$/cancel_request` | MUST | `:391`; `elicitation.mdx:233` |
| 10 | After the close response, the Agent sends no other messages for the session | declarative (normative) | `:395`; `#/$defs/CloseSessionRequest` description |
| 11 | Closing a session that does not exist or is not active SHOULD succeed with `{}` | SHOULD | `:407-410`; `error.mdx:56` |
| 12 | Relative `cwd` -> `-32602` | MUST bullet + declarative "Agents reject" | `:524` |
| 13 | A non-absolute `additionalDirectories` entry -> `-32602` | MUST -> capability:session.additionalDirectories | `:443` |
| 14 | An unsupported or unadvertised MCP transport (incl. v1 `sse`) -> `-32602` | MUST | `:545` |
| 15 | Duplicate MCP server `name` -> `-32602` | MUST on data + declarative "Agents reject" | `:547` |
| 16 | `env`/`headers` values SHOULD NOT appear in updates, errors, `_meta`, list results, replay | SHOULD | `:695` |

## Details

### What changed in the doc (normative content only)

- **Session lifecycle (new, `:45-55`).** A session exists until the Agent discards it, and resuming a discarded session gives `-32002` (`:47`). A session is "active" on a connection from a successful new/resume/fork until close or the end of the connection. The Agent SHOULD NOT discard an active session (`:49`). Requests to a session that is not active get `-32002`, and `session/cancel` to one is ignored (`:51`). Closing does not discard (`:52`). Re-resuming an already-active session re-synchronizes it and replaces its MCP servers and roots (`:53`). Activity across several connections is up to the Agent (MAY, `:54`). When the connection ends, sessions stop being active (`:55`).
- **Initial session state (`:96-140`).**
  - New SHOULD/SHOULD NOT at `:103`.
  - MAY -> **MUST include** config options and commands when the session has them (`:108`). Reason given: a setup response replaces the lists the Client holds (`:138`).
  - The "MUST NOT send `null`" rule is extended from `availableCommands` to `configOptions` (`:136`). The schema already forbids it: both are `type: array` in `NewSessionResponse`/`ResumeSessionResponse` at base and at target (structural diff: unchanged).
  - The old receiver-tolerance sentence was removed.
- **Resuming (`:142-335`).**
  - Gate wording changed to "advertise `capabilities.session`" (`:144`). Same gate.
  - New sentence: in-progress updates are live, not replay (`:184`).
  - New "Replay contents" subsection (`:217-236`): replay covers messages, tool calls, display terminals, plans and compactions (`:219`). It may send current state only (`:221`). Replayed tool calls SHOULD carry a final status (`:223`). Exclusions: historical `state_update`, notices (SHOULD NOT), pending permission requests and elicitations (`:225-229`). There is no need to replay usage/info/config/commands updates (`:231`).
  - The ID-preservation SHOULD now covers all entities (`:289`).
  - The resume response "also includes" (was MAY) `configOptions`/`availableCommands` (`:333`).
- **Current-state synchronization (`:337-363`).** New background-item MUST (`:346`). New SHOULD `session_info_update` (`:358`). New MAY `usage_update` (`:363`).
- **Close (`:365-410`).**
  - New MUST `$/cancel_request` for pending permission requests and elicitations before responding (`:391`).
  - Background work is stopped. The Client SHOULD treat unfinished listed work as cancelled, and the Agent MAY send final updates (`:391`).
  - "may also cancel ... queued prompts" -> "also cancels pending prompts whose messages have not been inserted, including held prompts" (`:395`).
  - New: "After the close response, the Agent sends no other messages for the session on that connection" (`:395`).
  - "Agents MAY return an error if the session does not exist" -> idempotent: SHOULD respond `{}`, and Clients SHOULD treat `-32002` as success (`:407-410`).
- **Additional workspace roots (`:412-443`).** Fork now accepts the field, with a non-inherited list (`:416`). The client-side resume rule now uses the MUST keyword (`:439`). New agent MUST: reject a non-absolute entry with `-32602`. New MAYs: reject nonexistent or non-directory entries, and ignore duplicates or entries equal to `cwd`. Non-advertising agents ignore the field (`:443`).
- **System prompt (`:445-507`).** Stabilized: the heading lost "(unstable)". RFD `client-system-prompt` moved to Completed (inventory section 3). The only new rule is client MUST NOT send empty `content`, with agent MAY `-32602` (`:478`). No structural schema change (`SystemPrompt` identical at base and target).
- **Working directory (`:520-539`).**
  - New declarative rule: a relative `cwd` gets `-32602` (`:524`).
  - New client MUST: send the session's `cwd` on resume. Agent MAY reject a different one with `-32602`. Agent MAY normalize (`:529`).
  - New "Workspace root security" subsection, all SHOULDs (`:533-539`).
- **MCP servers (`:541-697`).**
  - New MUST: reject an unsupported transport, including an unadvertised one and v1 `sse`, with `-32602` (`:545`).
  - New: names MUST be unique, and duplicates are rejected with `-32602` (`:547`).
  - The resume and fork set is complete; SHOULD NOT restore servers (`:549`).
  - Stdio `cwd`/env semantics (`:607`). Transport-owned HTTP headers (`:626`).
  - New sentence after "SHOULD connect": either fail the request or continue, and SHOULD tell the user (`:685`).
  - New "Security" subsection, all SHOULDs (`:689-697`).
  - `EnvVariable`/`HttpHeader` `name`/`value` are now marked `required` in the doc. They were already required in the schema.
- **Schema hints.** `x-deserialize-default-on-null` was added on `NewSessionRequest`/`ResumeSessionRequest`/`ForkSessionRequest.{mcpServers,additionalDirectories}`, `McpServerStdio.{args,env}` and `McpServerHttp.headers`. This only documents existing Rust `DefaultOnNull` deserialization (changelog `schema/v2/CHANGELOG.md:123` "mark DefaultOnNull lists with an x-deserialize hint", #2569; `agent-client-protocol-schema/src/v2/agent.rs:1184` pattern). It is not a wire change. `SessionInfo.additionalDirectories` went from `default-on-error` + `skip-invalid-items` to `default-on-null`. Its JSON type is `array` at both revisions, so a `null` was already schema-invalid for the agent-authored `SessionInfo`. B10's "no longer nullable" therefore changes only receiver tolerance, not what `ACP-LIST-*` validation accepts.

### Per-id notes where more than a remap is needed

- **ACP-CONFIG-203.** The base citations `:94` ("Agents **MAY** include initial configuration options") and `:313-315` ("The response **MAY** also include") now read `:108` "**MUST** include them" and `:333` "also includes". The text "`configOptions`, when present, validates the same way as ACP-CONFIG-201" is still true, and the test still matches it (validate when present, SKIP when absent). **DECISION NEEDED:** either (a) keep CONFIG-203 as a shape-only check with remapped citations and add presence as new `ACP-RESUME-210` (recommended: separate findings, separate ids), or (b) tighten CONFIG-203 to FAIL on omission. If (b), drop the `config_options is None -> skip` branch in `test_session_config.py:209-210`.
- **ACP-RESUME-202.** Base `:212-215` (notices SHOULD NOT be replayed) was deleted and restated as a bullet at `:228`. `spec-impact --fix` cannot remap deleted lines, so expect it under "Needs review". Point that piece at `:225-229`.
  The test's trailing-kind filter (`_REPLAYED_HISTORY_KINDS` = message kinds only) should stay as it is. "Replay contents" `:219` now names tool calls, terminals, plans and compactions as replayable history too. But live work may legitimately continue after resume with live updates (`:223`, `:346`), so tool-call and terminal updates trailing the response cannot be told apart from live ones. Plan and compaction kinds could be added, but it is not worth the false-positive risk. The requirement text's list of kinds that "may legitimately follow" is still accurate (`:231`, `:358`, `:363`).
- **ACP-RESUME-209.** Base `:194-195` ("User, agent, and thought messages can each be replayed as message updates with full `content` arrays or as chunks") was deleted. Its successor is `:221` ("The Agent can replay each entity's updates or only its current state"). Repoint to `:207-209,221,282-284`. Text and test are unchanged.
- **ACP-RESUME-201.** The text "(B3 makes `session/resume` a baseline-mandatory method)" refers to a label from an older research report. In the current inventory, B3 is the `AuthCapabilities` rename. Replace it with a plain citation of `:144-145` (cosmetic). "No route is spec-guaranteed" is still defensible: route 1 (resume a session still active on the same connection) depends on the SHOULD NOT at `:49`, and route 2 (after close) on retention at `:52`. Keep the SKIP semantics.
- **ACP-CLOSE-204 (DECISION NEEDED: recommend accept `-32002`).**
  - The test sends `session/prompt` then `session/close` without awaiting, and accepts only `-32800` or success with `messageId`.
  - At target, a session is not active after close (`:49`), and a session-scoped request to a non-active session gets `-32002` (`:51`, `error.mdx:54` MUST).
  - The spec mandates in-order *delivery* (`transports.mdx:61`) but not in-order *processing*. An agent that handles the close before the prompt request would correctly answer `-32002`.
  - The Rust SDK runs one dispatch loop per connection (`md/design.md:87-99`), and handlers can `cx.spawn(...)` for concurrency (`md/migration_v0.11.x.md:288`). So the processing order is an agent implementation choice. This is a hypothesis about agents; I did not trace a concrete agent.
  - Proposed text: "...is answered with `-32800`, with a success carrying a string `messageId`, or with `-32002` (the close took effect first, `:51`) -- never another error, never left unanswered." Record the outcome `"not_active"`. Keep the tier ADVISORY.
  - Also fix the docstring wording "queued prompts" -> "held prompts" (`:395`).
- **ACP-MCP-201.** Its text says "'Agents SHOULD connect' has no client-observable surface in stable v2". `:685` now states the two allowed outcomes outright ("the Agent either fails the request or continues without that server"). The only follow-up SHOULD is "tell the user, for example with a notice", which is not tied to any wire event. Keep INFORMATIONAL. Rewrite the rationale to cite `:685`. Optionally `record_property` whether a `notice` for the session followed an accepted `session/new`. The test is unchanged otherwise. It already sends `type: "stdio"`, an absolute `command`, and `args: []`.
- **ACP-SESSION-001.** No change, but two wire changes now flow through its schema validation and can turn previously passing agents into FAILs:
  - B5: every `availableCommands` item needs `type: "command"` (or a `_`-prefixed custom type).
  - `null` lists are forbidden.
  No v2 fixture emits `availableCommands` (grep of `tests/fixtures/agents/v2/` finds none), so no fixture breaks.
- **ACP-CANCEL-208 / ACP-CLOSE-202/203.** The text at `:389-393` is unchanged apart from added sentences. The test is still correct. The new `$/cancel_request` and background-work obligations at `:391` are not folded in. They get their own ids (`ACP-CLOSE-205`, and background is left to the prompt-lifecycle/background researcher).
- **ACP-SYSPROMPT-201/202.** No requirement change. The `test_session_capabilities.py` module docstring ("the unstable ... `systemPrompt` ... surfaces") and the section comment `# --- systemPrompt (... unstable) ---` are now stale (cosmetic).
- **ACP-FORK-202 (outside my list, flagged).** Its text says "Definitional prose without an RFC keyword" and cites `schema.mdx`/RFD. `session-setup.mdx:49` now defines a forked session as active on success, and `:51` + `error.mdx:54` make a prompt to it a MUST-level success path. Add `session-setup.mdx:49` to its citation. The tier stays CAPABILITY.

### New requirements (detail)

Each row lists: id; tier; gate; text; citation; how to observe it; suggested non-conforming fixture.

1. **ACP-SESSION-204**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`. DECISION NEEDED: the keyword is on the client value ("**MUST** be an absolute path") and the agent half is declarative ("Agents reject a request with a relative `cwd` with `-32602`"). This is the same shape as `ACP-RESUME-208`'s "also result in `-32602`", which is registered CAPABILITY. Recommend CAPABILITY.
   - **Text:** `session/new` with a relative `cwd` (e.g. `"tck-relative-dir"`) is rejected with `-32602`.
   - **Citation:** `docs/protocol/v2/draft/session-setup.mdx:522-524 @ 3961af94fa62`.
   - **Observe:** error code. A success FAILs, as does any other code. `-32000` (auth) goes through `skip_if_auth_gated`.
   - **Fixture:** `accepts_relative_cwd.py`, which creates the session anyway.
2. **ACP-SESSION-205**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`.
   - **Text:** `session/prompt` for a session closed earlier on this connection is rejected with `-32002`.
   - **Citation:** `docs/protocol/v2/draft/session-setup.mdx:49-51 @ 3961af94fa62`; `docs/protocol/v2/draft/error.mdx:54-56 @ 3961af94fa62`.
   - **Observe:** new -> close -> prompt, then check the error code. Whether `data.sessionId` must equal the id belongs to the error.mdx researcher. Coordinate so that one id, not two, asserts `data.sessionId`.
   - **Fixture impact:** `_base.py:_handle_prompt` currently answers unknown or closed sessions with `-32602` (`tests/fixtures/agents/v2/_base.py:485`). It must switch to `-32002` (+ `data.sessionId`).
   - **Defect fixture:** `prompt_after_close_wrong_code.py` (keeps `-32602`).
3. **ACP-SESSION-206**
   - **Tier:** ADVISORY (SHOULD NOT). Gate: `capabilities.session`.
   - **Text:** before the `session/new` response, the agent sends no agent->client request whose `params.sessionId` equals the returned id.
   - **Citation:** `session-setup.mdx:103 @ 3961af94fa62`.
   - **Observe:** scan the transcript lines read before the response. Match by id after the response arrives.
   - **Fixture:** `permission_before_new_response.py`.
4. **ACP-SESSION-207**
   - **Tier:** ADVISORY (SHOULD). Gate: `capabilities.session`.
   - **Text:** before the `session/new` response, the agent sends no `config_option_update` or `available_commands_update` for the new session.
   - **Citation:** `:103 @ 3961af94fa62`.
   - **Observe:** the same pre-response scan. `state_update` is explicitly allowed (`:98-99`) and is not judged.
   - **Fixture:** `commands_notified_before_new_response.py`. It can share the defect with SESSION-208 by omitting the list from the response; give each id its own fixture to keep "exactly one FAIL".
5. **ACP-SESSION-208**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`. DECISION NEEDED: MUST at `:108`, but the inference "the session has commands/options" rests on the pre-response notification. A residual edge exists (the list legitimately emptied in between). Recommend CAPABILITY; ADVISORY if the orchestrator wants zero false-FAIL risk.
   - **Text:** if a non-empty `config_option_update`/`available_commands_update` for the new session arrives before the `session/new` response, the response carries the corresponding list, non-empty.
   - **Citation:** `:108,136,138 @ 3961af94fa62`.
   - **Observe:** the pre-response scan plus the response field. Vacuous (recorded) when no such notification precedes the response.
   - **Fixture:** `commands_only_in_early_notification.py`.
6. **ACP-RESUME-210**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`. DECISION NEEDED: see ACP-CONFIG-203. This overlaps the session-config-options and slash-commands researchers (`slash-commands.mdx:12` states the same MUST for commands). Recommend one id here covering both lists.
   - **Text:** when a session's own `session/new` response carried a non-empty `configOptions` (resp. `availableCommands`), a successful `session/resume` of that session carries that list, non-empty.
   - **Citation:** `session-setup.mdx:108,333-335 @ 3961af94fa62`; `slash-commands.mdx:12 @ 3961af94fa62`.
   - **Observe:** create (keeping the full result), then resume on the same connection (route 1). SKIP if the resume errors, or if `session/new` carried neither list.
   - **Fixture:** `resume_omits_config_options.py`. `_base.py:_resume_result` already includes `configOptions`, so it is conforming.
7. **ACP-RESUME-211**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`.
   - **Text:** `session/resume` of a `sessionId` the agent never created (e.g. `tck-nonexistent-<uuid>`, with the TCK's own `cwd`) is rejected with `-32002`.
   - **Citation:** `session-setup.mdx:47 @ 3961af94fa62`; `error.mdx:54-56 @ 3961af94fa62`.
   - **Observe:** error code. A success FAILs. Safe, because a random id cannot name an operator's session.
   - **Fixture impact:** `_base.py:_handle_resume_session` accepts any id (`_base.py:360-376`, module docstring `:25-33`). It must reject ids it has neither live nor closed. Routes 1 and 2 of `obtain_resumable_session` use known ids, and route 3 needs a persisting agent, so they keep working. `resume_lists_foreign_session.py:30-32` rejects TCK ids with `-32602`: switch it to `-32002` or expect a RESUME-211 FAIL in `tests/v2/test_cli.py`. `resume_always_errors.py` (`-32603`) would FAIL RESUME-211; update its expected set.
   - **Defect fixture:** `_base`'s current lenient behaviour, i.e. `resume_accepts_unknown_session.py`.
8. **ACP-RESUME-212**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`.
   - **Text:** with `replayFrom: {"type":"start"}` on a session whose last turn reached idle (no prompt in flight), no `state_update` with `state` `running` or `requires_action` for that session arrives before the resume response.
   - **Citation:** `:225-227,348 @ 3961af94fa62`.
   - **Observe:** after `_add_history`, any such update can only be a replayed historical state. A replayed historical idle cannot be told apart from the allowed idle snapshot carrying the last stop reason (`:350-352`), so idle is not judged.
   - **Fixture:** `resume_replays_state_updates.py` (records and replays `state_update`). `_base._record_history` records message kinds only (`_base.py:659-677`), so the base agent conforms.
9. **ACP-RESUME-213**
   - **Tier:** CAPABILITY. Gate: `capabilities.session`.
   - **Text:** for every item in the `background` list of the resume's current-state snapshot, a `terminal_update` (same `terminalId`), `tool_call_update` (same `toolCallId`) or `subagent_update` (same `sessionId`) for the resumed session arrives during the resume exchange before that snapshot.
   - **Citation:** `:346 @ 3961af94fa62`; `schema/v2/schema.unstable.json#/$defs/BackgroundWork`.
   - **Observe:** the resume update stream. Replayed updates satisfy it, because the rule only requires what replay "did not already deliver at its current state". Vacuous (recorded) when `background` is absent or empty, which is the norm. Unknown `_`-typed items are ignored.
   - **Fixture:** `resume_background_without_updates.py` (snapshot lists a terminal that was never sent). Confirm the `background` model with the prompt-lifecycle/background researcher before implementing.
10. **ACP-RESUME-214**
    - **Tier:** ADVISORY (SHOULD). Gate: `capabilities.session`.
    - **Text:** a successful `session/resume` is preceded by a `session_info_update` for the resumed session.
    - **Citation:** `:358-361 @ 3961af94fa62`.
    - **Observe:** the resume update stream.
    - **Fixture:** `_base.py` sends none, so the base agent would FAIL this ADVISORY id. Either add one to `_send_resume_snapshot` (needs a schema-valid `SessionInfoUpdate`) or accept an ADVISORY FAIL on every fixture. Adding it is recommended.
11. **ACP-RESUME-215**
    - **Tier:** ADVISORY (SHOULD). Gate: `capabilities.session`. Low priority.
    - **Text:** after replay of an idle session with an empty `background` snapshot, every replayed `toolCallId` has ended in `completed`, `failed` or `cancelled`, accumulated across its replayed patches.
    - **Citation:** `:223 @ 3961af94fa62`.
    - **Observe:** only with an agent that replays tool calls. `conforming_full.py`'s rich updates are not recorded into `_base` history, so this is vacuous on fixtures unless the history recorder is widened.
    - **Fixture:** optional.
12. **ACP-RESUME-216**
    - **Tier:** ADVISORY. DECISION NEEDED: add, or put in the ledger. `:49` is SHOULD NOT and `:53` is declarative. Recommend adding.
    - **Text:** `session/resume` of a session created (and not closed) on the same connection succeeds.
    - **Citation:** `:49,53 @ 3961af94fa62`.
    - **Observe:** route 1 directly. It makes the frequent SKIP cause visible instead of silent.
    - **Fixture impact:** `resume_always_errors.py` and `resume_lists_foreign_session.py` would show an ADVISORY FAIL. Update the `test_cli.py` expectations.
13. **ACP-CLOSE-205**
    - **Tier:** CAPABILITY. Gate: `capabilities.session`.
    - **Text:** when `session/close` arrives while the agent's own `session/request_permission` for that session is pending (unanswered by the client), the agent sends `$/cancel_request` with `params.requestId` equal to that request's id before its successful close response.
    - **Citation:** `:391 @ 3961af94fa62`; `elicitation.mdx:233 @ 3961af94fa62`; `schema/v2/schema.unstable.json#/$defs/CancelRequestNotification`.
    - **Observe:** `run_prompt(..., hold_permission=True, on_action=close)`. The machinery exists for `ACP-CANCEL-209` (`_helpers.py:821-1021`). SKIP when no permission request was held when close was sent.
    - **Fixture impact:** `AsksPermissionAgent._handle_close_session` (`_base.py:758-765`) sends the cancelled idle but no `$/cancel_request`. It must emit one, which affects `asks_permission.py`, `conforming_full.py`, `requires_action_then_idle.py` and `starts_blocked.py`.
    - **Defect fixture:** `close_leaves_permission_pending.py`.
    - Coordinate with the cancellation researcher, who owns the general `$/cancel_request` rules.
14. **ACP-CLOSE-206**
    - **Tier:** CAPABILITY. Gate: `capabilities.session`. DECISION NEEDED: a declarative sentence, repeated in the `CloseSessionRequest` schema description. Same precedent as `ACP-DELETE-202` (declarative, kept CAPABILITY). Recommend CAPABILITY.
    - **Text:** after its successful `session/close` response, the agent sends no `session/update` notification and no agent->client request carrying that `sessionId` on the connection. Responses to earlier `session/prompt` requests are exempt (`:395` "Prompt responses need not precede the close response").
    - **Citation:** `:395 @ 3961af94fa62`; `schema/v2/schema.unstable.json#/$defs/CloseSessionRequest`.
    - **Observe:** `drain_quiet` after the close response, in both the idle-close and the mid-turn-close scenarios.
    - **Fixture:** `updates_after_close.py` (emits a late idle or notice after replying). The `_base.py` close path finishes the turn before replying (`_base.py:429-438`), so it conforms.
15. **ACP-CLOSE-207**
    - **Tier:** ADVISORY (SHOULD). Gate: `capabilities.session`.
    - **Text:** `session/close` of a session already closed on this connection succeeds with an empty-object result. `-32002` FAILs this ADVISORY id; clients tolerate it, but it is not the recommended answer.
    - **Citation:** `:407-410 @ 3961af94fa62`; `error.mdx:56 @ 3961af94fa62`.
    - **Observe:** close twice.
    - **Fixture:** `close_twice_errors.py`. `_base.py` already replies `{}`.
16. **ACP-ADDDIRS-203**
    - **Tier:** CAPABILITY. Gate: `capabilities.session.additionalDirectories`.
    - **Text:** `session/new` with a relative `additionalDirectories` entry is rejected with `-32602`.
    - **Citation:** `:437,443 @ 3961af94fa62`.
    - **Observe:** error code. Sending the field is allowed because the capability is advertised (`:441`). The relative value breaks the per-entry MUST at `:437`, but `:443` explicitly assigns the agent's response, as `RESUME-208` does for malformed `replayFrom`.
    - **Fixture:** `adddirs_accepts_relative.py`. `_base.py` ignores the field (`_base.py` docstring `:42-44`), so the base agent must start validating entries when it advertises the capability. Check which fixtures advertise it.
17. **ACP-MCP-203**
    - **Tier:** CAPABILITY. Gate: `capabilities.session`.
    - **Text:** `session/new` with an MCP server of a transport the agent does not support is rejected with `-32602`. Probe: v1's `{"type":"sse","name":"tck-sse","url":"http://127.0.0.1:1/tck","headers":[]}`.
    - **Citation:** `:545 @ 3961af94fa62`.
    - **Observe:** error code.
    - DECISION NEEDED: probe value. `sse` is named explicitly and is the realistic defect: v1-ported agents with an `sse` branch. It is a non-`_` reserved type (`:553`), but the client MUST at `:656` only covers stdio/http, so sending it breaks no client MUST. A `_tck_unsupported_transport` probe is the more conservative alternative. Recommend `sse`.
    - **Fixture:** `accepts_sse_mcp.py`. `_base.py` ignores `mcpServers` entirely, so it would FAIL until it validates transport types against what it advertises.
18. **ACP-MCP-204**
    - **Tier:** ADVISORY. Gate: `capabilities.session.mcp.stdio`. DECISION NEEDED: ADVISORY, or ledger.
    - **Text:** `session/new` with two stdio servers sharing a `name` is rejected with `-32602`.
    - **Citation:** `:547 @ 3961af94fa62`.
    - **Observe:** error code. Risk: an agent that launches before validating may fail with a launch error instead, which `:685` permits with no code specified. That is why ADVISORY, not CAPABILITY.
    - **Fixture:** `accepts_duplicate_mcp_names.py`.
19. **ACP-MCP-205**
    - **Tier:** ADVISORY (SHOULD NOT). Gate: `capabilities.session.mcp.stdio` (or http, as a second probe).
    - **Text:** an MCP server `env` value (resp. header value) carrying a per-run nonce never appears in any message the agent writes to stdout: session updates, errors, `_meta`, `session/list` results.
    - **Citation:** `:691,695 @ 3961af94fa62`.
    - **Observe:** substring scan of the transcript after `session/new` plus `session/list`. Optionally `record_property` for a stderr appearance; stderr is a log, but "SHOULD NOT log" is not reliably observable.
    - Overlaps the security.mdx researcher, so route there for a single owner.
    - **Fixture:** `echoes_mcp_env.py`.

### Ledger (deliberate non-requirements), all `docs/protocol/v2/draft/session-setup.mdx @ 3961af94fa62`

| Citation | Statement | Reason |
|----------|-----------|--------|
| `:49` | Agents SHOULD NOT discard a session while it is active, except through `session/delete` | Only if `ACP-RESUME-216` is not adopted. Otherwise observable only indirectly. |
| `:51` (last sentence) | Agents ignore `session/cancel` for a session that is not active | Observable only as the absence of a reaction to a notification. Already implied by connection liveness. |
| `:54` | An agent MAY reject `session/resume` for a session active on another connection, or end its activity there | Out of scope: a stdio TCK connection is one process, so it cannot open a second connection to the same agent. MAY. |
| `:55` | At connection end the agent MAY continue or cancel foreground work; a later resume reports the outcome | Cross-process persistence; out of scope. MAY. |
| `:228` | Notices SHOULD NOT be replayed | Unobservable: a notice before the resume response cannot be told apart from a new live notice, which `:228` permits. |
| `:289` | Agents SHOULD preserve the IDs of other replayed entities when possible | Hedged ("when possible", "not guaranteed"). Matching replayed entities to live ones needs content heuristics. |
| `:356` | If connection loss made a pending permission request or elicitation unusable, the agent SHOULD reestablish it or safely resolve the wait | Needs connection loss and reconnection; out of scope. |
| `:443` (last sentence) | Agents that do not advertise `session.additionalDirectories` ignore the field | Probing breaks the client MUST at `:441`. |
| `:474,477,481` | An unsupported `systemPrompt` mode or content block MUST get an error and MUST NOT create, resume or fork the session | Probing breaks client MUSTs (`:474`, `:477`). Same reasoning as the existing test-module docstring. |
| `:478` | Agents MAY reject an empty `systemPrompt.content` with `-32602` | Client-side MUST NOT plus agent MAY. |
| `:475-476,480` | `append` SHOULD get system-level precedence; `override` semantics; SHOULD apply a changed prompt on resume or fork | Model-internal; unobservable. |
| `:529` | Agents MAY reject a different `cwd` on resume with `-32602` | MAY. |
| `:537-539` | Workspace-root security: don't treat model output as granting access; check resolved paths; fail closed | Unobservable without driving tool use; unsafe to probe. |
| `:549` | Agents SHOULD NOT restore MCP servers from earlier requests | Observable only with a TCK-supplied MCP server; out of scope. |
| `:607,626` | Launch stdio servers in the session `cwd`; `env` merge semantics; transport-owned HTTP headers; MAY reject duplicate env names | Needs a real TCK-supplied MCP server; out of scope. |
| `:685` | If the agent continues without a failed server it SHOULD tell the user | "Tell the user" is not tied to a wire event (a notice is only an example). `ACP-MCP-201` records instead. |
| `:693-697` | No shell; don't log or persist credentials; headers only to the configured origin | Unobservable from the client (`:695`'s in-band part is `ACP-MCP-205`). |

Client-side MUSTs (`:98-101`, `:138`, `:150`, `:291-293`, `:439`, `:441`, `:483`, `:529`, `:656`) are skipped. They are rules about the client and are not tested by a TCK that drives the agent.

### `spec-tracker/maps/v2.toml` sections for this doc

All current addresses fail to resolve at target. These are the new exact addresses (headings at target: `:45,57,96,142,217,337,365,412,445,509,520,533,541,551,555,609,654,689`):

```
"Session lifecycle",          # NEW, recommend core
"Creating a session",
"Initial session state",
"Resuming sessions",          # covers "Replay contents" and "Current-state synchronization"
"Closing active sessions",
"Session ID",
"Working directory",          # now also covers new "Workspace root security"
```

- **Recommend `Session lifecycle` as core.** It defines "active", which `error.mdx:54`, `session-delete.mdx:95`, `session-list.mdx:162,207`, `session-config-options.mdx:375` and `transports.mdx:43` all link to, and which the `-32002` rules depend on.
- "Replay contents" is automatically core under "Resuming sessions". Keep it: prompt-lifecycle links to it (`prompt-lifecycle.mdx:46,752`).
- "Workspace root security" is automatically included under "Working directory". It is SHOULD-only guidance that `security.mdx:38,66,79` and `tool-calls.mdx:774` link to. Including it is harmless and keeps the root-set rules together. If the orchestrator wants it excluded, list `"Working directory > (intro)"` instead.
- "Additional workspace roots", "System prompt" and "MCP servers" (now including the new "Security" subsection) stay non-core, per the map's own reason string ("individual features").

### `validation.py` carve-outs touching session setup or resume

None is specific to session setup or resume (`src/tck/v2/validation.py:1-27`).

- **Point 2 (no null-response special case)** still holds. `NewSessionResponse`, `ResumeSessionResponse` and `CloseSessionResponse` are `type: object` and non-nullable at target. `ResumeSessionResponse` and `CloseSessionResponse` are structurally unchanged.
- **Point 3 (open-enum fallback)** applies only to root `params`/`result` objects in `find_unknown_root_keys`. `AvailableCommand`'s new `other` branch is nested inside the response, so it does not interact with the carve-out. Full schema validation handles it.
- **Point 1 (batching)** is the transports/batch researcher's.

## Testability notes

- Every new MUST above is judged on the error code or the ordering of a single exchange. Each needs no client-MUST violation, apart from the explicit "agent rejects malformed value" pattern already used by `ACP-RESUME-208`.
- The `-32002` ids (SESSION-205, RESUME-211) need `_base.py` changes before they can pass on the conforming fixture. Without those changes, every v2 fixture run gains two FAILs.
- CLOSE-205 is exercised only when the agent asks permission. Against real agents it will often SKIP, like `ACP-CANCEL-209`.
- RESUME-213 and RESUME-215 will be vacuous on all current fixtures. Register them only if the orchestrator accepts vacuous-pass ids. A background-work fixture would need to be designed together with the prompt-lifecycle researcher.
- SESSION-206/207/208 can share one `session/new` probe. They need a transcript scan of the lines read before the response (`wait_for_response` already retains them in `agent.transcript`).

## Discrepancies

- **`session-config-options.mdx:10` vs `session-setup.mdx:108`.** The config doc still says the Agent "**MAY** return a list of configuration options" during session setup. Session setup now says an Agent whose session has options "**MUST** include them". Read together they are compatible: MAY offer options at all, but MUST include them when it has them. Still, the config doc's sentence is outdated. Flag it to the session-config-options researcher and do not cite `:10` for presence.
- **B10 wording vs the schema.** The inventory says "`SessionInfo.additionalDirectories` no longer allows null". The JSON type is `array` (non-null) at both base and target. Only the receiver hint changed (`default-on-error` -> `default-on-null`). There is no wire impact on agent-authored `SessionInfo` validation.
- No disagreement found between the doc and the schema descriptions. The `CloseSessionRequest`, `NewSessionResponse` and `ResumeSessionRequest.mcpServers` descriptions restate the doc's new rules verbatim in substance.

## Open questions

- **error.mdx researcher:**
  - Who owns `data.sessionId` on `-32002`?
  - Should `ACP-INFO-UNKNOWNSESSION-001` be promoted, given `error.mdx:54` now MUSTs `-32002`?
  - Avoid two ids asserting the same unknown-session code; SESSION-205 deliberately uses a *closed* session, not a never-created one.
- **Cancellation researcher:** general `$/cancel_request` rules vs the close-specific CLOSE-205.
- **Prompt-lifecycle/background researcher:** the `background` list model, needed for RESUME-213. Also fork's `background: []` rule at `:49`, which the FORK area could test.
- **Session-config-options and slash-commands researchers:** confirm the single combined RESUME-210 (both lists), or split it per area. Fork-response presence (`:108` also names `session/fork`) is uncovered. It could be a FORK-area id gated on `capabilities.session.fork`.
- **Security researcher:** ownership of ACP-MCP-205 (credential echo).
