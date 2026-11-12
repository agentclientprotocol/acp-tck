# What does the latest upstream Subagents RFD require, and how well does acp-tck cover it?

**Sources checked:**
- `agentclientprotocol/agent-client-protocol` @ `upstream/main` = `95452a77a7c2f8324ba2970a17867585539d68f8` (2026-11-12). The local checkout's
  `origin` is a fork (`EugeneTheDev/...`) on a feature branch, so `git pull --ff-only` did not reach upstream HEAD. Everything
  below was read with `git show upstream/main:<path>` after `git fetch upstream`; the working tree was not touched.
- The same repo @ `3961af94` (the TCK pin), for the diff.
- Unmerged upstream branch `upstream/docs/subagents-preview` @ `67806695` (2026-11-12).
- `agentclientprotocol/rust-sdk` @ `91d368ad` and `agentclientprotocol/python-sdk` @ `da202e0c`. Both have only schema support
  or nothing; see Discrepancies.
- acp-tck working tree @ `13c4f7a` (main, clean).

**Confidence:** high on the RFD contents, the revision diff, and the mapping to TCK code. Medium on the tier of the RFD's
declarative, lowercase "must" sentences, which are flagged where they occur.

## Answer

The RFD is `docs/rfds/subagents.mdx` ("Subagent Sessions"). On upstream main it is listed in the **Active** RFD group, and an
unmerged branch moves it to **Preview**. Its wire shapes exist **only in the unstable schemas** (`schema/v{1,2}/schema.unstable.json`,
behind `unstable_subagents`). They are not in the stable `schema.json`. Nothing subagent-related changed between the TCK pin
`3961af94` and upstream HEAD: the RFD file is identical, and no subagent `$def` changed.

The RFD puts few obligations on agents that a black-box client can check, and almost all of them apply only if the agent actually
exposes a subagent. No prompt can force that. The TCK covers the two easiest ones:
- the v1 capability gate (`ACP-CLIENTCAP-007`);
- in v2, the "announce before child traffic" rule, but only for `session/update` notifications inside a prompt turn
  (`ACP-PROMPT-002`).

Coverage is therefore **not adequate**:
- **v1 has no positive coverage at all.** The TCK never advertises `clientCapabilities.subagents`.
- **v2 misses several passively checkable MUSTs:** requests that carry a child's session ID, participant IDs on
  `session_message`, `session` tool-call content, absolute `cwd`, and association integrity.
- **One v2 row is wrong against the RFD.** `ACP-RESUME-209` would FAIL an agent that replays child history, which the RFD
  recommends.

## Requirements

Legend for *Obs.*: **BB** means a black-box client can observe it. **BB-coop** means observable only if the agent exposes a
subagent (otherwise SKIP or vacuous). **U** means unobservable from the client. **C** means the rule binds the client, not the
agent. All RFD line numbers are from `docs/rfds/subagents.mdx` @ `95452a77`, which is byte-identical at `3961af94`. Draft-doc
line numbers are @ `95452a77`, and the cited files are unchanged since `3961af94`.

| # | Requirement (agent-side unless noted) | Tier | Obs. | Citation |
|---|---|---|---|---|
| S1 | v1: MUST NOT send `subagent_update`, `session_message`, `session_message_chunk`, or `session` tool-call content unless the Client advertised `subagents`. Also applies during replay. The agent may still use subagents internally. | MUST (v1 only) | BB | RFD:76-78, 644-645, 965-967; `docs/protocol/v1/draft/prompt-turn.mdx:19-21,42`; `docs/protocol/v1/draft/tool-calls.mdx:358`; `schema/v1/schema.unstable.json#/$defs/ClientCapabilities/properties/subagents` |
| S2 | v2: there is no capability. Subagent support is baseline, and an agent may send these updates to any v2 client. | (scoping fact) | n/a | RFD:80-85, 1195-1201; `docs/protocol/v2/migration.mdx:242-244` |
| S3 | The announcing `subagent_update` MUST precede any request or notification that carries the child's session ID. This includes a live `session_message` that names the child as sender or recipient, and permission, elicitation, fs, and terminal requests. | MUST (v1: when `subagents` advertised) | BB-coop | RFD:95-99, 189-193; `#/$defs/SubagentUpdate` description (both versions: "MUST be sent before any live request or notification bearing the child's session ID") |
| S4 | `update.sessionId` is unique within the connection and MUST NOT be reused for an unrelated session. | MUST | BB-coop (partial: only reuse of a known ordinary or root session ID is detectable) | RFD:122-124 |
| S5 | A child has one immediate parent. The association "cannot reparent an existing session, refer to itself, or create a cycle". Later updates patch metadata and do not transfer ownership. | declarative ("cannot"); schema says updates modify "not its ownership" | BB-coop | RFD:89-93, 165-169; `#/$defs/SubagentUpdate` description |
| S6 | Wire shapes: `SubagentUpdate` (only `sessionId` required), `SessionMessage` (`messageId` required), `SessionMessageChunk` (`messageId` + one `content` block required), `SessionReference` (`sessionId` required), `SubagentSessionCapabilities.cancel`, v1 `state` (StateUpdate incl. `unknown`, idle `stopReason` + `error`). | MUST (schema) | BB-coop | RFD:120-139, 439-459, 622-623, 815-829; `#/$defs/SubagentUpdate`, `SessionMessage`, `SessionMessageChunk`, `SessionReference`, `SubagentSessionCapabilities`, `UnknownStateUpdate` (both schemas) |
| S7 | `cwd` MUST be absolute, and each `additionalDirectories` entry MUST be absolute. | MUST | BB-coop | RFD:302-308; `#/$defs/SubagentUpdate/properties/cwd`, `.../additionalDirectories` ("Must be an absolute path") |
| S8 | MUST report a directory that differs from the parent's before child traffic that depends on it. SHOULD NOT expose a child as sharing the parent workspace if its directories are unknown. SHOULD report the narrowest directories. On reconnect, SHOULD send current values and MUST report a new value or `null` when a directory no longer exists. | MUST/SHOULD | U (the TCK cannot know the true directories) | RFD:322-326, 381-382, 387-390 |
| S9 | v1: SHOULD pass an explicit `cwd` on a child's `terminal/create`. | SHOULD | BB-coop, but needs `terminal` + `subagents` advertised; the mock client advertises neither | RFD:361-363 |
| S10 | MUST NOT guess parentage or temporarily announce a nested child under the root. MUST NOT later move an issued interaction to a different session. Once a child is exposed, its interactions MUST use its session ID. | MUST | U (truth not knowable) | RFD:195-208 |
| S11 | MUST NOT use a child to circumvent restrictions the Client imposed on the parent. A child's Agent-to-Client requests are subject to the same client capabilities. | MUST | BB (partly): a child-ID fs/terminal/elicitation request without the capability | RFD:210-217, 256-262 |
| S12 | Automatic delivery: the agent sends child events without any further client request. There is no attach or subscribe. | MUST-level contract (declarative) | U (cannot force a spawn) | RFD:221-232 |
| S13 | A `session` tool-call content item's session MUST already be known, through ordinary setup or a `subagent_update`, before a tool call references it. | MUST | BB-coop | RFD:636-638; `docs/protocol/v1/draft/tool-calls.mdx:349-351`; `docs/protocol/v2/draft/tool-calls.mdx:740-742` |
| S14 | `session_message`: when both participant IDs are known they name different sessions, and the outer `params.sessionId` equals one of them. Supplied live participant IDs refer to known sessions; the MUST in S3 covers "naming it as sender or recipient". | declarative ("must remain consistent", lowercase) + MUST via S3 | BB-coop | RFD:477-483; RFD:96-97 |
| S15 | When both views carry `senderMessageId` / `recipientMessageId`, they MUST name each other. SHOULD supply each reference once known. | MUST / SHOULD | BB-coop (MUST part) | RFD:466-475 |
| S16 | SHOULD put participant IDs on the first `session_message` when available, and send that upsert before the first chunk. | SHOULD | BB-coop (weak: "when available") | RFD:461-464; `docs/protocol/v1/draft/prompt-turn.mdx:46-50`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:77-81` |
| S17 | Delegated task: SHOULD report it as an incoming `session_message` in the child (outer = child, `senderSessionId` = parent) before the child's response. SHOULD NOT report it as `user_message_chunk` / v2 `user_message`. SHOULD report the outgoing view in the parent and link the views. | SHOULD / SHOULD NOT | BB-coop | RFD:648-664; `docs/protocol/v1/draft/prompt-turn.mdx:106-111`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:137-142` |
| S18 | `messageId` is unique within the enclosing session (no reuse for a different entity). | MUST (v2 general rule) | U (an upsert is indistinguishable from reuse) | RFD:439-441; `docs/protocol/v2/draft/prompt-lifecycle.mdx:67` |
| S19 | Report each side only when observed. Do not manufacture an incoming entry from an outgoing one. | declarative | U | RFD:576-583 |
| S20 | v1 work state: MUST report `running`/`idle` (on the parent's `subagent_update.state`) when the agent observes child foreground work start, resume, or stop. SHOULD report `requires_action` and `stopReason`. Cancellation is `idle`+`cancelled`; failure is `idle`+`error`(+`error`). | MUST / SHOULD | BB-coop (weak: "observes" is not knowable; heuristic only) | RFD:815-853 |
| S21 | MUST report `unknown` when observability of child work is actually lost (v1: parent snapshot; v2: child `state_update`, mirrored). | MUST | U | RFD:855-867 |
| S22 | v2: SHOULD mirror each child state on the immediate parent's `subagent_update.state`. Copies of a transition precede later transitions on either path. | SHOULD (+ declarative ordering) | BB-coop | RFD:765-774; `docs/protocol/v2/draft/prompt-lifecycle.mdx:1015-1018`; `schema/v2/...#/$defs/SubagentUpdate` description ("Agents SHOULD mirror") |
| S23 | A child's idle does not end the parent's turn, and the parent's idle or prompt response does not mean children finished. | client interpretation | C (TCK harness must honour it) | RFD:886-891, 903-907, 1216-1220 |
| S24 | Child context: SHOULD report child config via child-addressed `config_option_update` (snapshot after announcement). For a child that does not permit config changes (every child today), SHOULD restrict each select to its current value. | SHOULD | BB-coop | RFD:392-419 |
| S25 | Need not send `available_commands_update` for a child. | MAY | n/a | RFD:289-292 |
| S26 | Restricted methods: Clients MUST NOT prompt, load, resume, close, set config, or cancel a child without an advertised capability. The agent's response to a violating client is **not specified**. | C | not testable as an agent rule (probe rules forbid it; see Testability) | RFD:1030-1056 |
| S27 | Child cancel: if `capabilities.cancel` is non-null, `session/cancel` with the child's ID cancels that child's current work, "not its parent or siblings". The child confirms with `idle`+`cancelled` (v1: parent snapshot; v2: child `state_update` + mirror), after sending pending updates. A cancel racing with ended work does not rewrite the outcome. | per-child capability (not an initialize capability); declarative | BB-coop (active test) | RFD:1067-1095; `#/$defs/SubagentSessionCapabilities/properties/cancel` |
| S28 | Cancelling a session's current work also cancels descendant work it waits on. Other descendants (background children) are the Agent's choice. | declarative ("also cancels"; FAQ: "must still stop") | BB-coop, v2 only by inference (a running child not in the parent's `background` list is foreground) | RFD:1075-1087, 1413-1425; `docs/protocol/v2/draft/prompt-lifecycle.mdx:208,210` |
| S29 | Closing the parent cancels all active descendant work and releases resources. It does **not** require a terminal-state notification. | declarative | U (no wire obligation) | RFD:1117-1121 |
| S30 | Late responses MUST NOT restart cancelled work. A request MUST NOT get more than one response (client side). Requests stay attributed to their original child (client side). | MUST / C | U / C | RFD:1145-1156 |
| S31 | Replay: SHOULD replay recorded associations and child history best-effort. Replayed child updates MUST keep original identities, parentage, and per-session order, with announcements before child traffic. MUST NOT issue traffic for an unannounced child. MUST NOT invent participant IDs. All selected history MUST be sent before the response. MUST NOT reissue recorded Agent-to-Client requests. Ancestor chain established parent-before-child before live child traffic. MUST NOT manufacture failure, cancel, or orphan outcomes. | SHOULD / MUST | BB-coop (ordering and announcement parts); U (truthfulness parts) | RFD:917-1028 |
| S32 | Without replay, announcements, snapshots, and ordinary live child traffic may arrive before or after the resume response. | MAY (permission) | BB-coop (constrains what the TCK may FAIL) | RFD:1008-1013 |
| S33 | Fork: if forking copies child history, the agent MUST consistently remap copied session IDs in participant fields and `session` content, including the forked root. | MUST | BB-coop (very conditional) | RFD:1058-1065 |
| S34 | Cost: MUST NOT fabricate exclusive parent or child amounts. | MUST | U | RFD:1158-1182 |
| S35 | v2: `tool_call/cancel` / `terminal/cancel` for a child's item is sent with the child's `sessionId`. The item's own `cancel` enables it even when the child has no `cancel`. | capability (per item) | BB-coop | RFD:1042-1045; `docs/protocol/v2/draft/tool-calls.mdx:457,603` |
| S36 | v2 background: a `subagent` background item MUST be announced (by `subagent_update`) before the first list that names it. | MUST | BB-coop | `docs/protocol/v2/draft/prompt-lifecycle.mdx:182,206` |
| S37 | v2 background: a detached child is listed while its state is not `idle` or while its own `background` list is non-empty or unreported. An `idle` child with nothing running is not listed. | declarative | BB-coop (child `state_update`s are on the same connection) | `docs/protocol/v2/draft/prompt-lifecycle.mdx:210` |

## Details

### 1. RFD identity and revision status

- Path: `docs/rfds/subagents.mdx`, title "Subagent Sessions", authors Vadim Briliantov and Ben Brandt (RFD:1-6). It has no
  status field in its frontmatter. Status comes from `docs/docs.json` on upstream main: the RFD sits in the **"Active"** group
  (`docs/docs.json:211-215`), separate from "Draft" (:197) and an empty "Preview" (:240-241).
- Unmerged branch `upstream/docs/subagents-preview` @ `67806695` ("docs(rfd): move subagents to preview", 2026-11-12) moves it
  to "Preview". It adds the revision-history line "2026-11-12: Moved to Preview" and an updates entry saying "The schema covers
  ACP v1 and v2". It changes no wire shapes.
- Read at upstream `95452a77`. RFD history on main: `d2631c6f` (initial, #1992), `59172baf`, `06128106`, `bfeaad0c`, `788a9166`,
  `097a8a8e`, `b51ded35`, `64819c70`, `bf529a96`, `a965f1f1`, `7ec5185c`, `14560463` (#2775, 2026-11-09), `b3f6123f` (#2787,
  2026-11-09, the latest: `session` tool content plus one-shot clarification). All of these are ancestors of `3961af94`.
- **Since the TCK pin `3961af94`:** 7 upstream commits. None touch `docs/rfds/subagents.mdx`. The changed `$defs` are the same
  in both versions (`AgentResponse`, `AuthAccount`, `AuthStatus*`, `ClientRequest`, `ForkSessionRequest`,
  `InitialSessionConfigOption`, `NewSessionRequest`, `ResumeSessionRequest`, `LoadSessionRequest` (v1), `SessionCapabilities`,
  `SessionOptions*`), and none of them is a subagent def. The only subagent-adjacent textual diff is a reformatted table row
  in `docs/protocol/v2/draft/overview.mdx:263`. The vendored `src/tck/v{1,2}/schema/schema.unstable.json` is byte-identical
  to upstream `3961af94`.
- **Schema location:** in `schema/v1/schema.unstable.json` and `schema/v2/schema.unstable.json` only. There are 0 matches for
  `subagent` or `SessionMessage` in either stable `schema.json`. The Rust feature flag is `unstable_subagents` (RFD:1253-1254, 883-884).

### 2. Wire shapes (both versions unless noted)

- `session/update` → `update.sessionUpdate: "subagent_update"`, sent on the **parent** (`params.sessionId` = parent):
  - `sessionId` (child, required);
  - `title`, `description`, `capabilities` (`{cancel?: {}|null, _meta?}`), `state` (StateUpdate snapshot), `cwd`,
    `additionalDirectories`, `_meta`: all optional, nullable patches. Omitted means unchanged, `null` clears, and a value
    replaces. In v2, a concrete `_meta` patches by top-level key. `capabilities` and `state` are replaced whole.
- `session_message` (upsert): `messageId` (required); `senderSessionId`, `recipientSessionId`, `senderMessageId`,
  `recipientMessageId`, `content: ContentBlock[]`, `_meta`, all optional patch fields.
- `session_message_chunk`: `messageId` and `content` (a single ContentBlock) are both required; `_meta` is chunk-scoped. The
  chunk carries no participant IDs.
- `ToolCallContent` variant `{"type": "session", "sessionId", "_meta"?}` (`#/$defs/SessionReference`).
- v1 `ClientCapabilities.subagents`: optional, nullable object. `{}` means supported. v2 has no such field
  (`ClientCapabilities.subagents` is absent from the v2 unstable schema).
- v1 `subagent_update.state`: `running` | `requires_action` | `unknown` | `idle` (`stopReason`?, `error`? when
  `stopReason: "error"`, `usage`?). v2 uses its ordinary `StateUpdate`, with `unknown` added (RFD:878-884).
- The v2 TCK already lists `session_message`, `session_message_chunk`, and `subagent_update` in its known `SessionUpdate`
  kinds (`src/tck/v2/protocol.py:103-105`), and `session` in `TOOL_CALL_CONTENT_TYPE` (`:108`).

### 3. Mapping to existing TCK coverage

| Req | Status | Where |
|---|---|---|
| S1 | **Covered** (v1) | `ACP-CLIENTCAP-007` (`src/tck/v1/requirements.py:1108-1126`), `test_no_subagent_update_without_client_capability` (`src/tck/v1/conformance/test_client_capabilities.py:189-205`). It scans the whole connection (`session/new`, one turn, `session/load` replay if advertised, then a quiet period) for the three kinds, plus `session` items in `tool_call`/`tool_call_update`/`session/request_permission.toolCall` content. Fixtures: `emits_subagent_update_unadvertised.py`, `session_content_without_subagents.py`; `tests/v1/test_cli.py:1513-1518`. Small residual: a v1 agent sending a request with an unannounced child `sessionId` and no capability is not judged by this row. |
| S2 | Honoured | v2 never gates subagent traffic; `ACP-PROMPT-002` accepts announced children. |
| S3 | **Partial** (v2), **not covered** (v1) | v2 `ACP-PROMPT-002` (`src/tck/v2/requirements.py:332-348`; `test_updates_validate_and_carry_a_known_session_id`, `src/tck/v2/conformance/test_prompt.py:193-232`). It builds a `known` set per connection in wire order, handles nesting, and FAILs a child `session/update` before its announcement. Fixtures: `exposes_subagent.py` (PASS), `unannounced_child_update.py` (FAILs only PROMPT-002; `tests/v2/test_cli.py:1589-1600`). **Missing:** (a) only judges updates inside the prompt turn (`turn_lines`), not child traffic after the turn ends (RFD:1350-1351 expects that) or outside turns; (b) Agent-to-Client **requests** carrying a child `sessionId` (`session/request_permission`, `elicitation/create`) are not checked; (c) `session_message` `senderSessionId`/`recipientSessionId` naming an unannounced session are not checked; (d) not applied during `session/resume`. v1: nothing, since the TCK never advertises `subagents`. |
| S4, S5 | **Not covered** | `PROMPT-002` adds every `subagent_update.sessionId` to `known` without checking self-reference (`update.sessionId == params.sessionId`), reuse of a `session/new` ID, or re-announcement under a different parent. |
| S6 | **Partial** (v2), **not covered** (v1) | v2 `ACP-PROMPT-002` schema-validates every turn update (`validate_agent_message`), and `ACP-RESUME-209` does the same during resume, so a malformed `subagent_update`/`session_message`/`session` item emitted in a turn FAILs. v1: any emission already FAILs CLIENTCAP-007, so shapes are never judged under `subagents`. |
| S7 | **Not covered** | v1: ledgered (`spec-tracker/maps/v1.toml:202-205`, reason "TCK never advertises"). v2: **neither tested nor ledgered** (untracked). |
| S8, S10, S12, S18, S19, S21, S29, S30, S34 | Not testable (U) | Not ledgered in v2. `requirements.md` asks for agent-side, deliberately untested rules to be recorded in the ledger. |
| S9 | Not testable under the current mock client | v1 mock advertises neither `terminal` nor `subagents`. |
| S11 | **Partial** (v1) | `ACP-CLIENTCAP-001..003` FAIL *any* `fs/*`, `terminal/*`, `elicitation/create` request, including one carrying a child ID, but only on a `clientCapabilities: {}` connection, where a child cannot legitimately exist. v2 removed client fs/terminal (RFD:1209-1214). |
| S13 | **Not covered** | v1 ledger `spec-tracker/maps/v1.toml:298-301` (reason valid while `subagents` is never advertised). v2 ledger `spec-tracker/maps/v2.toml:596-599`: **reason is stale** (see below). |
| S14, S15 | **Not covered** | Not ledgered. |
| S16 | **Not covered** | Not ledgered. |
| S17 | **Not covered** | v1 ledger `spec-tracker/maps/v1.toml:197-200` (reason valid while not advertised). v2: **not ledgered** (untracked). |
| S20 | **Not covered** | |
| S22 | **Not covered** | Also `tests/fixtures/agents/v2/exposes_subagent.py` (the "conforming" child fixture) does **not** mirror child state on the parent association. |
| S23 | **Covered** (harness) | v2 `run_prompt` ignores child `state_update`s for turn end (`src/tck/v2/conformance/_helpers.py:844-855,1083`; `docs/mock-client.md:23`). Child traffic is excluded from per-session entity checks (`_helpers.py:1529-1545`, `test_patches.py:56-71`). `exposes_subagent.py` proves the parent turn is unaffected (`tests/v2/test_cli.py:1589-1593`). v1 `run_prompt` ends on the response, so it is unaffected. |
| S24 | **Not covered** | |
| S26 | Not testable as an agent rule | |
| S27, S28 | **Not covered** | |
| S31 | **Not covered**, and see stale check #1 | |
| S32 | Constrains TCK | See stale check #2. |
| S33, S35 | **Not covered** | Hypothesis, not verified: the existing v2 `tool_call/cancel` / `terminal/cancel` tests target the prompted session's items only. |
| S36 | **Covered** (v2) | `ACP-STATE-207` (`src/tck/v2/requirements.py:476-489`, `test_background_items_are_announced_before_they_are_listed`, `test_background.py:114-136`) and `ACP-RESUME-213` (`requirements.py:1424-1440`, `test_resume_announces_background_items_before_the_snapshot`, `test_session_capabilities.py:542-579`) both accept a `subagent_update` as the announcement of a `subagent` item. |
| S37 | Not covered | v2 ledger `spec-tracker/maps/v2.toml:194-197`, **reason factually wrong** (see below). |

### 4. Existing TCK checks that are wrong or stale against the RFD

1. **`ACP-RESUME-209` (v2) is wrong for agents that replay child history.** The row text is at `src/tck/v2/requirements.py:1372-1384`.
   The test is `test_resume_replay_updates_are_schema_valid`, `src/tck/v2/conformance/test_session_capabilities.py:411-440`;
   the check is at lines 435-437. It requires every `session/update` during `session/resume` with `replayFrom: start` to carry
   the *resumed* `sessionId`. The RFD says the agent **SHOULD** replay recorded associations and child history (RFD:925-929),
   and replayed child updates **MUST** keep their original session identities with announcements first (RFD:933-935).
   A v2 agent that follows the SHOULD sends child-addressed updates during the replay window and FAILs this MANDATORY-gated
   row (CAPABILITY on `capabilities.session`). The fix: accept a child ID announced earlier in the same exchange, the same rule
   as `ACP-PROMPT-002`.
2. **`ACP-RESUME-002` (v2) risks a false FAIL.** The test (`test_session_capabilities.py:190-212`) does not filter by session,
   but the row text says "for the resumed session". Live child traffic (`agent_message_chunk` etc.) is explicitly allowed before
   the resume response when no replay is requested (RFD:1008-1010), and it would be counted as replayed history. The fix: filter
   `history_updates` to `params.sessionId == session_id`.
3. **Stale ledger reasons in v2.** `spec-tracker/maps/v2.toml:197` and `:599` say the rule needs "the unstable `subagents` the
   TCK never advertises". v2 has no `subagents` marker: subagent updates need no client marker (`docs/protocol/v2/migration.mdx:242`,
   RFD:80-85, 1195-1201). Any v2 agent may emit them, and `ACP-PROMPT-002` already handles them. `:197` also claims "the child's
   own state and `background` list are not on the parent connection's wire". That is false: child events are delivered
   automatically on the same connection (RFD:223-225) and v2 child `state_update`s are child-addressed on that connection
   (RFD:765-768). Both rules are passively checkable when an agent emits subagents. `:599` is a MUST.
4. **`exposes_subagent.py` (v2) is "conforming" only for current rows.** It omits the S22 mirror and the S17 incoming task
   message. If ADVISORY rows for these are added, the fixture must be updated, because `_assert_conforming_baseline`
   (`tests/v2/test_cli.py:535-550`) requires PASS for every non-skip id.
5. Not stale but brittle: v1 ledger entries `spec-tracker/maps/v1.toml:197-205` and `:298-301` are justified only by "the TCK
   never advertises `subagents`". They must be converted to rows in the same change that adds a `subagents`-advertising v1
   connection (`docs/requirements.md`, ledger section).
6. `ACP-CLIENTCAP-007`'s citation `docs/rfds/subagents.mdx:76-78,644-645` is still accurate at HEAD. The RFD is now "Active"
   (soon "Preview") rather than in the "Draft" group. `docs/requirements.md` calls for a "(Draft RFD)" label only where nothing
   else states the rule, and here the draft docs do state it. No change needed.

## Testability notes

- **No prompt can force a spawn.** Every positive subagent row is cooperative. Per `docs/requirements.md` and `docs/writing-tests.md`,
  the honest outcome when no subagent traffic is seen is **SKIPPED** ("agent exposed no subagent"), or a vacuous PASS (the
  pattern of `ACP-PROMPT-002` and `ACP-CLIENTCAP-007`). SKIP is safe even for MANDATORY rows, since only FAIL and NOT_TESTED
  break the verdict. Precedent: `ACP-STATE-207` SKIPs when nothing is listed.
- **The per-child `cancel` capability is not an `initialize` capability** (`docs/protocol/v2/migration.mdx:244`), so
  `@pytest.mark.capability` cannot gate S27 or S35. Use an in-test SKIP: "no exposed child advertised `capabilities.cancel` while
  running".
- **Passive checks fit the existing transcript scans.** All of these are checkable over `agent.transcript` with a per-connection
  `known` set built in wire order:
  - S3 extended to requests and participant IDs;
  - S4/S5 integrity;
  - S7 absolute paths;
  - S13 known `session` references;
  - S14/S15 participant consistency;
  - S17 "child emits `user_message(_chunk)`";
  - S22 mirroring;
  - S36/S37.

  The `known` set seeds from `session/new`/`session/fork` results and from the resumed or loaded session.
- **v1 needs a new connection advertising `clientCapabilities: {"subagents": {}}`.** Today v1 helpers always send `{}` or the
  caller's dict (`src/tck/v1/conformance/_helpers.py:31,62`). Keep `ACP-CLIENTCAP-007` and v1 `ACP-PROMPT-002` on their own
  non-subagent connections: v1 PROMPT-002's "carries the prompted sessionId" is only right without `subagents`. Advertising
  the capability is not a probe. It makes the TCK claim client obligations it already meets: it never prompts, loads, resumes,
  or closes a child.
- **S20 "MUST report running/idle when it observes"** cannot be judged strictly. A reasonable heuristic, at INFORMATIONAL or
  ADVISORY tier: if a child emits agent output under its ID, a parent `subagent_update` with `state.state == "running"`
  should arrive at some point, and an `idle` should follow. Flag this as interpretation, not spec.
- **S26 (restricted methods).** The spec does not define the agent's answer to `session/prompt` (or `session/close`,
  `session/resume`, ...) on a child. Under `docs/writing-tests.md` probe rules ("only where the spec defines the agent's answer
  to exactly that input"), it must not be a normative row. At most it can be INFORMATIONAL.
- **S27 child cancel (active).** Needs the cancel-race machinery from `docs/mock-client.md`: fire `session/cancel` with the
  child ID while the child is `running`.
  - Conforming: the child reports `idle`+`cancelled` (v2 on the child stream; v1 on the parent's `subagent_update.state`), and
    the parent turn is not ended as `cancelled` because of it.
  - Non-conforming: the parent turn ends `cancelled`, or the child keeps reporting `running` past the timeout.
  - A child that reaches `end_turn` within the race window SKIPs.
- **S28 (v2 only).** A running child **not** in the parent's latest `background` list is, by `prompt-lifecycle.mdx:208,210`,
  foreground work. After a parent cancel, it must reach `idle`. The rule is declarative, so tier ADVISORY unless the
  orchestrator decides that "also cancels" is a MUST.
- **S31 replay ordering** is testable for v2 resume-with-replay and v1 `session/load` with `subagents`: child traffic in the
  replay window must be preceded by its announcement within that exchange (on a fresh connection). Truthfulness clauses
  (no guessed parent, no invented IDs, no manufactured outcomes) are unobservable.

## Verdict and prioritized gaps

**Verdict: inadequate.** The capability gate (v1) and the in-turn announcement rule for notifications (v2) are solid. Everything
else an agent that exposes subagents must do is unchecked. v1 has no positive coverage at all, and v2 has one wrong row
(RESUME-209) and one false-FAIL risk (RESUME-002).

All gaps below are cooperative unless noted: they SKIP (or pass vacuously) when the agent exposes no subagent. Proposed ids are
placeholders for the orchestrator. Per rule B in `docs/requirements.md`, a rule that is the same in v1 and v2 should share an id.

**P1. v2: fix `ACP-RESUME-209` (wrong) and `ACP-RESUME-002` (false-FAIL risk).** Not cooperative for the fix itself.
- RESUME-209 should accept updates for children announced earlier in the same resume exchange, and FAIL unannounced child IDs.
  This also delivers the S31 ordering check.
- RESUME-002 should filter to the resumed session.
- Fixtures: a conforming `replays_subagent_history.py` (announces the child, then replays its history during
  `replayFrom: start`, and emits live child traffic before a no-replay resume response), which must PASS everything. A
  violating `replays_unannounced_child.py` (child history with no announcement), which FAILs only RESUME-209.

**P2. v2: extend the announcement rule beyond in-turn notifications (S3).** MUST.
- Scan the whole connection, not just turn lines.
- FAIL any Agent-to-Client request whose `params.sessionId` is unannounced (`session/request_permission`, `elicitation/create`).
- FAIL a `session_message` whose `senderSessionId`/`recipientSessionId` names an unannounced session.

Options are to widen `ACP-PROMPT-002`'s text or to add a new row. A new row is cleaner, keeps the one-defect fixture rule, and
can carry the shared id later used by v1. Fixtures: `exposes_subagent.py` (extend it to send a child permission request and a
parent→child `session_message`), plus violators `child_permission_before_announce.py` and `session_message_unknown_participant.py`.

**P3. v2: `session` tool-call content names a known session (S13).** MUST. Rewrite the stale ledger entry
`spec-tracker/maps/v2.toml:596-599` into a row. Fixtures: the conforming `exposes_subagent.py` (add `{"type":"session",
"sessionId": child}` to a `tool_call_update` after the announcement) and the violating `session_content_unknown_session.py`.

**P4. v2: association integrity (S4, S5).**
- FAIL `update.sessionId == params.sessionId`.
- FAIL `update.sessionId` equal to a session created by `session/new` on the connection.
- FAIL a re-announcement of a known child under a different parent, or a cycle.

S4 is a MUST. Ask the orchestrator to decide the tier for the declarative S5. Fixtures: `self_parented_subagent.py` and
`reparents_subagent.py`.

**P5. v2: `cwd`/`additionalDirectories` absolute (S7).** MUST, cited by schema pointer. Fixture: `relative_subagent_cwd.py`.
This closes an untracked gap.

**P6. v2: session-message consistency (S14, S15).**
- When both participant IDs are present, they differ and the outer `sessionId` is one of them (declarative; tier decision needed).
- If an outgoing view's `recipientMessageId` and the matching incoming view's `senderMessageId` are both set, they name each
  other (MUST).

Fixture: `inconsistent_session_message.py`.

**P7. v2 ADVISORY rows (SHOULDs):**
- S22: a mirror for each child `state_update` arrives on the parent's `subagent_update.state`.
- S17: a child never emits `user_message`/`user_message_chunk` for the delegated task, and an incoming `session_message` with
  `senderSessionId` = parent precedes the child's first agent output.
- S16: participants are on the first `session_message` before the first chunk.
- S24: a child select config option has only its current value.

Update `exposes_subagent.py` to satisfy these, and add one violator each (e.g. `unmirrored_child_state.py`,
`child_task_as_user_message.py`). Also correct the factually wrong ledger reason at `v2.toml:194-197`, and either test S37
(detached child listed while non-idle) or re-ledger it with a true reason.

**P8. v1: add a `subagents`-advertising connection** (`clientCapabilities: {"subagents": {}}`): `session/new`, one turn,
`session/load` replay if `loadSession`, then a quiet period. Apply the v1 equivalents of P2–P7 with shared ids:
- announcement before child traffic, including child-ID `fs/*`/`terminal/*`/`session/request_permission`;
- known `session` content (S13);
- absolute `cwd` (S7);
- integrity (S4/S5);
- message consistency (S14/S15);
- v1 `state` snapshot schema validity (S6);
- ADVISORY S17;
- INFORMATIONAL or ADVISORY S20.

In the same change, convert ledger entries `spec-tracker/maps/v1.toml:197-205,298-301` to rows. Fixtures:
- a new v1 conforming `exposes_subagent.py` that emits subagent traffic **only** when `subagents` was advertised, so it still
  PASSes CLIENTCAP-007;
- violators mirroring the v2 ones (`unannounced_child_update.py`, `session_content_unknown_session.py`,
  `relative_subagent_cwd.py`, ...).

**P9. Active cooperative tests (both versions).** S27 child cancel (SKIP unless a running child advertises `capabilities.cancel`).
In v2, S28 parent-cancel cascade to a waited-on child, and S35 `tool_call/cancel` with a child's `sessionId` for a cancellable
child tool call. Fixtures: `cancellable_subagent.py` (conforming), plus `child_cancel_cancels_parent.py` and
`child_cancel_ignored.py`. These rows rely mainly on RFD text, so label them "(Draft RFD)".

**P10. Ledger hygiene (both).** Record the unobservable agent-side rules as `[[not_requirement]]` entries: S8, S10, S12, S18,
S19, S21, S29, S30 (agent half), S31 truthfulness clauses, S34. That way a spec update can tell "deliberately untested" from
"missed".

**P11. Design idea (TCK only, not from A2A):** a `--subagent-prompt TEXT` option, analogous to `--cancel-prompt`, so operators
can give a real agent a prompt likely to make it delegate. Without one, P2–P9 will SKIP on most real agents.

## Discrepancies

- **Spec vs. draft docs vs. schema.** No substantive conflict found.
  - The announcement MUST appears in the RFD (:95-99) and in both schemas' `SubagentUpdate` description, but not in the v2 or
    v1 draft prose. This is why `ACP-PROMPT-002` correctly cites the schema pointer.
  - The draft docs say the referenced session "must already be known" in lowercase (`tool-calls.mdx` v1:350, v2:741). The RFD
    says **MUST** (:636-638).
  - The v1 and v2 schemas differ only where the RFD says they should: v2 has no client marker, v2 `_meta` key-patches, and v2
    `state` uses the ordinary `StateUpdate` with `background`.
- **Reference SDKs.**
  - The Rust SDK @ `91d368ad` exposes only types behind `unstable_subagents`, and explicitly says it is "schema support, not a
    subagent scheduler or an implementation of application-level ownership and lifecycle policy" (`md/features.md:125-130`;
    tests in `src/agent-client-protocol/tests/schema_subagents.rs`).
  - The Python SDK @ `da202e0c` has no subagent support.
  - So neither SDK has runtime behaviour to compare against. Questions the spec leaves open, such as the agent's reply to
    `session/prompt` on a child, have no reference answer.
- **Status.** On main the RFD is in the "Active" group. Branch `upstream/docs/subagents-preview` moves it to "Preview" (not merged
  as of `95452a77`).

## Open questions

1. **Tier for declarative or lowercase rules.** S5 "cannot reparent/refer to itself/cycle", S14 "must remain consistent", S27
   "cancels current work in that child, not its parent or siblings", and S28 "also cancels the descendant work". Should they be
   MANDATORY or ADVISORY? This needs an orchestrator or user decision.
2. **Shape of the v2 S3 extension.** Widen `ACP-PROMPT-002` (text change, same id) or add new rows? Rule B allows either. The
   v1 counterpart (P8) would want a shared id, which argues for a new id in both registries.
3. **Citing the RFD after the Preview move.** If the Preview move merges, should `docs/requirements.md`'s "(Draft RFD)"
   labelling convention be renamed for Active or Preview RFDs? This is a TCK docs question, not a protocol one.
4. **v2 `tool_call/cancel` / `terminal/cancel` scope.** Do the existing tests deliberately exclude child items (S35)? Not
   verified here; a quick check by whoever implements P9 would settle it.
