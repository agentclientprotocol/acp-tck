# Impact (v1): `prompt-turn.mdx` and `cancellation.mdx`, spec update 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (checkout
`../agent-client-protocol-2`, read-only), diffed against `3961af94`. Read in full at target:
`docs/protocol/v1/draft/prompt-turn.mdx` (873 lines), `docs/protocol/v1/draft/cancellation.mdx` (70
lines). Rules they depend on, read where linked: `initialization.mdx:244-303`, `session-setup.mdx:146-156`,
`subagents.mdx:280-290`, `error.mdx:47,67`, `schema/v1/schema.unstable.json` (`PromptSuggestionsUpdate`,
`PromptSuggestion`, `CursorUpdate`, `CursorAnchor`, `CursorCapabilities`, `ForkSessionRequest`,
`ClientSessionCapabilities`, `SessionCapabilities`), Draft RFDs `rfds/session-cursors.mdx`,
`rfds/prompt-suggestions.mdx` (for discrepancies only), `rfds/request-cancellation.mdx` (Completed) diff.
RFD stages from `docs/docs.json` at target: `prompt-suggestions` Draft, `session-cursors` Draft,
`session-fork` Draft, `subagents` Preview, `request-cancellation` Completed.
TCK @ `ceef9a8`: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/`
(`_helpers.py`, `test_client_capabilities.py`, `test_plan.py`, `test_cancel.py`).
Reference SDKs not consulted: every new rule is stated in the docs; the only silent point (timing of the
suggestion-replacement MUST, see D3) is agent policy, which a protocol SDK does not implement.
**Confidence:** high for classification and line maps (verified line by line against both revisions);
medium for the tier/gate proposals of the new rows (they hinge on decisions D1-D4).

## `cancellation.mdx`

The file is byte-identical between the two revisions (`git diff --stat` empty). The Completed
request-cancellation RFD changed one sentence (v1 Client must answer pending permission requests on
`session/cancel`; v2 differs): client-side, cited by no v1 row.

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-JSONRPC-006 | unchanged | `cancellation.mdx:12-14 @ 3ea94133` | |
| ACP-JSONRPC-007 | unchanged | `cancellation.mdx:16-22 @ 3ea94133` | |
| ledger | none cite this doc | | v2 ledger has 4 entries; not copied (see Open questions) |

## `prompt-turn.mdx`

Line map base -> target: 1-34 same; +2 after 34; 35-102 -> +2; 103-111 reworded -> 105-113 plus new
115-118; base N>=112 -> N+7 up to 352; +67 (Prompt suggestions, 360-426) -> N+74 up to 502; +134
(Session cursors, 577-710) -> N+208 up to 527; +2 (usage cost) -> N+210 after.

| Id / ledger | Classification | Target citation (`@ 3ea94133`) | Note |
|---|---|---|---|
| ACP-PROMPT-001 | citation-only | `prompt-turn.mdx:740` | was :530 |
| ACP-CANCEL-001 | citation-only | `prompt-turn.mdx:855,862` | was :645,652 |
| ACP-CANCEL-002 | citation-only | `prompt-turn.mdx:40,866` | was :38,656. `HISTORY_KINDS` needs no change: `prompt_suggestions_update` MAY be sent any time (:415) and `cursor_update` is neither content nor a tool call update |
| ACP-LOAD-002 | citation-only (this doc's part) | `prompt-turn.mdx:40` | was :38. See Open questions for replayed `cursor_update` |
| ACP-CLOSE-002 | citation-only (this doc's part) | `prompt-turn.mdx:855,862,866` | was :645,652,656 |
| ACP-CLIENTCAP-004 | citation-only | `prompt-turn.mdx:300-303` | was :293-296 |
| ACP-CLIENTCAP-005 | citation-only | `prompt-turn.mdx:429-434` | was :355-360 |
| ACP-CLIENTCAP-006 | unchanged | `prompt-turn.mdx:25-26` | |
| ACP-CLIENTCAP-007 | citation-only (this doc's part) | `prompt-turn.mdx:19-21,44` | was :19-21,42. Line 19 reworded ("Announces a subagent session or updates its labels, directories, and state"), the gate is unchanged. Its `rfds/subagents.mdx ... (Active RFD)` part is now Preview, and `subagents.mdx` documents the capability check: that belongs to the subagents researcher |
| ACP-SUBAGENT-009 | citation-only (this doc's part) | `prompt-turn.mdx:98-102` | was :96-100 |
| ACP-SUBAGENT-011 | changed text (scope widened) | `prompt-turn.mdx:108-113` | was :106-111. "The task a parent gives a subagent" became "A message from a parent to a subagent, including the first one that starts its work". The row judges only the first task (before the child's first output). That is still a valid subset, but the row text says "the task". The link now goes to `subagents.mdx#messages-from-a-parent-to-a-child` (`subagents.mdx:280-287`), not the RFD. See D5 |
| ACP-SUBAGENT-012 | changed text (scope widened) | `prompt-turn.mdx:108-113` | same as -011 |
| ACP-SUBAGENT-013 | citation-only | `prompt-turn.mdx:48-52` | was :46-50 |
| core_doc `prompt-turn.mdx` | unchanged | sections at :10, :815, :835 | The three section titles still exist. The new sections sit under "The prompt turn lifecycle", outside the core sections |

Line citations in code and fixtures that also need remapping (same map):
- `src/tck/v1/conformance/_helpers.py`: line 225 (`:38` -> `:40`); lines 419, 539, 551 (`:641` -> `:851`).
- `tests/v1/test_run_prompt.py:331`, `tests/fixtures/agents/v1/perm_only_reject_always.py:5` (`:641` -> `:851`).
- `tests/fixtures/agents/v1/asks_permission.py:3` (`:133-144` -> `:140-151`).
- `_helpers.py:1118` says "Active Subagents RFD, Delegated tasks": stale label and anchor (now Preview).
  The docs now point to `subagents.mdx#messages-from-a-parent-to-a-child`.

Removed: none.

## New requirements

All of these are unstable ("Draft only") features. The TCK's default connection advertises
`clientCapabilities: {}` (`src/tck/v1/__init__.py:18`), so each positive check needs its own connection,
like `test_plan.py` (`connected_agent(..., client_capabilities=...)` already supports this). The mock
client needs no new behaviour: everything is transcript analysis plus generic `send_request`. Ids are
provisional. v2 gains the same features (`spec-diff-v2.md:153-154`), so align shared ids with the v2
researcher (rule B).

**N1. ACP-CLIENTCAP-008**: MANDATORY, no gate.
The agent MUST NOT send `prompt_suggestions_update` unless the client advertised
`clientCapabilities.session.promptSuggestions`.
Citation: `prompt-turn.mdx:35,364`; `initialization.mdx:244-255`;
`schema/v1/schema.unstable.json#/$defs/PromptSuggestionsUpdate`.
Test: add one assertion over `_received_with_no_client_capabilities` (`test_client_capabilities.py:148`),
exactly like ACP-CLIENTCAP-004. It already covers `session/load` and a quiet period. The PASS is vacuous.

**N2. ACP-CLIENTCAP-009**: MANDATORY, no gate.
The agent MUST NOT send `cursor_update` unless the client advertised
`clientCapabilities.session.cursors`, either live or in `session/load` replay.
Citation: `prompt-turn.mdx:36,584-589`; `initialization.mdx:289-297`; `session-setup.mdx:152`;
`schema/v1/schema.unstable.json#/$defs/CursorUpdate`.
Test: same as N1.

**N3. ACP-SUGGEST-001**: MANDATORY with a vacuous PASS (D1).
On a connection that advertised `session.promptSuggestions: {}`, every `prompt_suggestions_update`
must meet all of these:
- It validates against the schema: `suggestions` is required, and each `prompt` is a `ContentBlock[]`
  with at least one item.
- Each suggestion's `prompt` is valid as a `session/prompt` `prompt`.
- Each suggestion uses only `text` and `resource_link` blocks, because the client advertised no
  `image`, `audio` or `embeddedContext`.

Citation: `prompt-turn.mdx:398-405`; `initialization.mdx:257-279`;
`#/$defs/PromptSuggestion`; `#/$defs/PromptSuggestionsCapabilities`.
The TCK validator deliberately ignores `x-deserialize-skip-invalid-items` on `suggestions`
(`src/tck/v1/validation.py:30`), so an invalid entry fails, which matches the agent-side MUST.

Test, on one connection with `{"session": {"promptSuggestions": {}}}`:
1. `session/new`.
2. Prompt turn 1, then a quiet period.
3. Prompt turn 2, then a quiet period.
4. `session/load` if `loadSession` is advertised.
5. Scan every `prompt_suggestions_update`.

Advertising `{}` makes any `image`/`audio`/`resource` block a FAIL whatever the agent's
`promptCapabilities` are. The "both sides" branch (:405) would need a second connection with all three
client fields set, judged against `agentCapabilities.promptCapabilities`. That is optional; I recommend
skipping it.

**N4. ACP-SUGGEST-002**: MANDATORY with a vacuous PASS.
Agents MUST NOT send a suggestion whose only content is empty or whitespace-only text.
Citation: `prompt-turn.mdx:402`; `#/$defs/PromptSuggestion/properties/prompt`.
Test: same scan as N3. FAIL when every block of a suggestion is `text` and every `text.strip()` is
empty. The TCK chose this reading of "only content", which is the strict one; say so in the row text.

**N5. ACP-SUGGEST-003**: CAPABILITY, `inferred:promptSuggestions` (D2).
When the agent accepts a `session/prompt` while its current list is non-empty, it MUST replace the list
or withdraw it (`suggestions: []`).
Citation: `prompt-turn.mdx:409,412`.
Test, on the N3 connection:
- If the last update before prompt 2 was sent carried a non-empty list, expect some
  `prompt_suggestions_update` for the session after prompt 2 is sent and before turn 2's response plus
  a quiet period.
- SKIP ("agent sent no non-empty suggestion list") otherwise.

The FAIL is heuristic because the docs give no deadline (D3).

**N6. ACP-SUGGEST-004**: ADVISORY, no gate.
Agents SHOULD NOT include prompt suggestions in session replay.
Citation: `prompt-turn.mdx:425`; `session-setup.mdx:150`.
Test, on the N3 connection when `loadSession` is advertised: no `prompt_suggestions_update` for the
session arrives between the `session/load` request and its response. One sent after the response is
allowed (:425). SKIP when `loadSession` is not advertised.

**N7. ACP-CURSOR-001**: MANDATORY with a vacuous PASS (D1).
On a connection that advertised `session.cursors: {}`, the first `cursor_update` for a `cursorId`
carries a non-null `anchor`, and no later update for it carries a different non-null `anchor`. This
covers both "MUST include" and "MUST NOT change", and the cursorId being "never reused for another
position".
Citation: `prompt-turn.mdx:617,619,621-623`; `#/$defs/CursorUpdate`.
Test, on one connection with `{"session": {"cursors": {}}}`:
1. `session/new`.
2. Two prompt turns, then a quiet period. Two turns, because a session's first prompt has no cursor
   before it (:660-664).
3. `session/load` if `loadSession` is advertised.
4. Keep per-(session, cursorId) state. Reset a session's state when the TCK sends `session/load` for it,
   because "a load rebuilds the session's cursors" (`session-setup.mdx:156`) and message IDs may change
   across a load (:157).

**N8. ACP-CURSOR-002**: MANDATORY with a vacuous PASS.
A `cursor_update` anchor names an entity the agent has already reported on that same session. An agent
that announces cursors sends a `messageId` on every message it anchors to.
Citation: `prompt-turn.mdx:652-653,656-657`; `#/$defs/CursorAnchor`.
Test, on the N7 connection. Per session, keep the set of reported `(type, id)` pairs:
- `user_message_chunk`, `agent_message_chunk` and `agent_thought_chunk` record their `messageId`
  (as `user_message`, `agent_message` and `agent_thought`).
- `session_message` and `session_message_chunk` record their `messageId` (as `session_message`).
- `tool_call` and `tool_call_update` record their `toolCallId`.
- `compaction_update` records its `compactionId`.

Then judge each anchor:
- Each anchor of a known `type` must be in the set at the moment its `cursor_update` arrives.
- Unknown `type` or `position` values are preserved for extensions (:654), so they are not judged.
- Reset the set when the TCK sends `session/load`, since the replay re-delivers the entities first
  (:674).
- Judge only sessions created on this connection. On a `session/resume` without replay, an anchor may
  name an entity reported on an earlier connection.

**N9. ACP-CURSOR-003**: CAPABILITY, `agentCapabilities.sessionCapabilities.fork` (D4).
`session/fork` with a `cursorId` the agent did not issue for that session is rejected with `-32602`.
The agent neither forks the whole session nor acts at another position.
Citation: `prompt-turn.mdx:676-680,698-701`; `#/$defs/ForkSessionRequest/properties/cursorId`;
`docs/rfds/session-fork.mdx (Draft RFD)` for `session/fork` itself, if it is cited at all. The
schema already defines the method and the `fork` capability.
Test probes, on the N7 connection:
- (a) A fabricated id (`tck-unissued-<uuid>`) on a session that has history.
- (b) When a cursor was announced on session A: fork with that `cursorId` but with `sessionId` set to a
  second session B, or to the fork of A, since the new session "does not inherit them" (:700).
- (c) When a cursor's current `capabilities` lack `fork`: fork at it.

Each probe expects an error with code `-32602`. A success (close nothing; just record it) or any other
code FAILs. Probes (b) and (c) SKIP their part when no suitable cursor exists. Request params:
`sessionId` and `cwd` are required (`ForkSessionRequest.required`). Probe "no longer accepts" is not
elicitable.

**N10. ACP-CURSOR-004**: ADVISORY, no gate (D4 alternative scope).
A cursor the agent just announced with `capabilities.fork` is accepted by `session/fork`: the result
validates as `ForkSessionResponse`. Agents SHOULD accept a cursor while they still have the history at
its position. Right after announcing it, they do.
Citation: `prompt-turn.mdx:682-683,703-706`; `#/$defs/ForkSessionResponse`.
Test, on the N7 connection: fork at the first fork-capable cursor. SKIP when there is none, or when
`fork` is not advertised. This is optional (D6).

## New ledger entries

Every reason below rests on agent-internal state, not on a choice the TCK makes.

1. Citation: `docs/protocol/v1/draft/prompt-turn.mdx:411 @ 3ea94133...`
   - Statement: Agents MUST predict a suggestion list from the conversation as it stands when they send
     it, and MUST discard a prediction if the conversation changed before they sent it (for example,
     because a `session/prompt` arrived).
   - Reason: Not observable. A client cannot tell which conversation state a suggestion was predicted
     from, so a stale prediction sent after a `session/prompt` arrived looks the same as a fresh one.
2. Citation: `prompt-turn.mdx:413 @ 3ea94133...`
   - Statement: Agents SHOULD replace or withdraw the suggestion list when it stops applying for any
     reason other than an accepted prompt.
   - Reason: Not observable. No protocol event marks when a list stops applying, so a missing
     replacement cannot be told from a list that still applies.
3. Citation: `prompt-turn.mdx:115-118; docs/protocol/v1/draft/subagents.mdx:287 @ 3ea94133...`
   - Statement: When the agent has no evidence of who sent a message a child received, it omits
     `senderSessionId` and MUST NOT assume the parent. It links two views only when it can establish
     that they are the same message.
   - Reason: Not observable. Whether the agent had evidence is internal, so a `senderSessionId` naming
     the parent, or a link between views, looks the same whether it was established or assumed.
   - Coordinate with the subagents researcher so this is recorded once.
4. Citation: `prompt-turn.mdx:707-709 @ 3ea94133...`
   - Statement: When the agent stops accepting a cursor while the session is active on a connection,
     it SHOULD send a `cursor_update` that clears the cursor's `capabilities`.
   - Reason: Not observable. When the agent stops accepting a cursor is internal, and no deadline bounds
     the clearing update. A `-32602` for a cursor that still advertises `fork` cannot be told from a
     clearing update that is about to arrive.
   - If D6 rejects N10, extend this entry's citation to `:705-709` and the statement to the
     accept-while-retained SHOULD.

The doc has other agent-side text with no RFC keyword, which the ledger leaves out by its own rules:
- "announces a cursor only for a position where at least one method works" (:580-581).
- "does not invalidate a cursor" on connection end, close, load or resume (:703-705). The agent "can
  stop accepting a cursor at any time" (:707), so this is not testable.
- "`cost` includes the costs of its descendants" (:736). That belongs to the subagents researcher, via
  `subagents.mdx` "Usage and cost".

Existing ledger entries citing these docs: none. Only the `core_doc` entry, which is unchanged.

## Decisions for the user

- **D1. Tier for the "every X the agent sends satisfies Y" rules (N3, N4, N7, N8).**
  - Recommend MANDATORY with a vacuous PASS, matching ACP-PLAN-001 and ACP-CLIENTCAP-005..007: the
    docs say MUST, and an agent that never sends the update passes.
  - Alternative: CAPABILITY `inferred:promptSuggestions` / `inferred:cursors`. The docs back this too:
    "There is no Agent capability. An Agent that supports cursors announces them." (:588-589).
- **D2. Gate for N5.** It applies only after the agent has shown the feature with a non-empty list.
  Recommend CAPABILITY `inferred:promptSuggestions`, a self-skipping test, and no marker (the
  `inferred:` gate rules in `docs/requirements.md`).
- **D3. N5 has no deadline.** The docs say MUST, with no time bound, and agents "typically" send the
  update after the response (:415). Recommend judging by turn 2's response plus `quiet_period`, the same
  heuristic as ACP-CANCEL-002, and saying so in the row text. Alternative: make N5 ADVISORY because the
  FAIL is heuristic. That is a weaker reading than the docs' MUST.
- **D4. N9 scope.** The docs bind any agent that gets a `cursorId` it did not issue, cursor-unaware fork
  agents included. Such agents, which ignore the field, would FAIL a CAPABILITY row on an unstable
  feature.
  - Recommend gating on the `sessionCapabilities.fork` marker, and having the test also self-skip when
    the agent announced no cursor on the `session.cursors: {}` connection (an inferred `cursors` opt-in).
  - Alternative: judge every fork-advertising agent with probe (a). That is stricter and literal.
- **D5. ACP-SUBAGENT-011/-012 widened scope.** The rule now covers every parent-to-child message, not just
  the task. Recommend rewording the rows' text to "A message from a parent to a child (judged: the first,
  which starts its work)", without widening the tests in this update. The subagents researcher owns
  `subagents.mdx:280-287` and should decide whether the tests widen and how the citations should read.
- **D6. N10 (positive fork at a cursor).** Recommend adding it as ADVISORY. Alternative: ledger it,
  folded into entry 4.

## Open questions

- **For the session-setup researcher.** `cursor_update` is "part of the replayed history"
  (`session-setup.mdx:152-156`) but is also a live upsert. ACP-LOAD-002's `HISTORY_KINDS` should
  probably stay as it is. The SHOULDs at `session-setup.mdx:154-155` (re-announce accepted cursors, keep
  the same `cursorId` per position) belong to that doc's impact report.
- **For the error-doc researcher.** `error.mdx:67` (`session/fork` of an unknown session gets `-32002`).
  `session/fork` has no v1 rows at all yet. Should fork's own baseline rows exist before N9 and N10?
- **Not introduced by this update.** These unchanged agent-side rules have neither a row nor a ledger
  entry (a citation grep, not a full audit):
  - `prompt-turn.mdx:356-357`: notices SHOULD NOT be replayed.
  - `prompt-turn.mdx:465`: a compaction ID MUST NOT be reused.
  - `prompt-turn.mdx:482`: the agent MUST report a terminal compaction status.
  - `prompt-turn.mdx:853`: the agent SHOULD stop model and tool work as soon as possible.
  - `cancellation.mdx:35-38`: internal cancellation SHOULD send `-32800`.

  v2's ledger covers the cancellation counterparts (`spec-tracker/maps/v2.toml:633-652`). Their reasons
  must be re-derived for v1, not copied.

## Discrepancies

None between the docs, the schema descriptions and the Draft RFDs, for the rules above.
`rfds/session-cursors.mdx:211` adds that a replayed cursor "can carry a different anchor than it had
before". The docs imply the same through "a load rebuilds the session's cursors"
(`session-setup.mdx:156`), which is why N7 resets its state on load.
