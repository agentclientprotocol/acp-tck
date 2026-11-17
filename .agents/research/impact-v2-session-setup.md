# Impact research, v2: `docs/protocol/v2/draft/session-setup.mdx` (3961af94 -> 3ea94133)

**Sources checked:** agent-client-protocol, read by ref (`git show 3ea94133:` / `git diff 3961af94..3ea94133`) from
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`. That checkout's HEAD is now `6ace4f6a`, one commit
past the target. `session-setup.mdx` is byte-identical at both, so the target line numbers below hold. Files read:
`docs/protocol/v2/draft/session-setup.mdx` (whole doc, 786 lines), `session-config-options.mdx:380-394,480-585`,
`prompt-lifecycle.mdx:909-1028` (session cursors), `subagents.mdx` (sections "Closing the parent", "Resuming",
"Replayed child history"), `docs/docs.json` (RFD stages), and the `NewSessionRequest`/`ResumeSessionRequest`/`ForkSessionRequest`,
`InitialSessionConfigOption`, `SessionOptions*`, `ReplayComplete`, `SessionUpdate` and chunk `$defs` in
`schema/v2/schema.unstable.json` and `schema/v2/schema.json`. On the TCK side: `src/tck/v2/requirements.py` (55 rows cite
the doc), `spec-tracker/maps/v2.toml` (16 ledger entries cite it), `src/tck/v2/conformance/test_session_capabilities.py`
(RESUME-202/002/204/205), `tests/fixtures/agents/v2/_base.py` (replay behaviour), and the coordinator-referenced
`.agents/research/scope-rfds-v2-prompt-session.md`. I did not need the SDKs: no rule below depends on runtime behaviour the
docs leave implicit.
**Confidence:** high for the classifications and line maps. I mapped lines with a `difflib` pass over base/target and
spot-checked them by hand. Medium for decisions D1, D2 and D6, where the spec text is ambiguous or uses no RFC keyword.

RFD stages at target (`docs/docs.json`): `subagents` is Preview (lines 242-243). `session-fork`, `session-options` and
`rfds/v2/*` (incl. `background-work`, `session-resume-replay`) are Draft (lines 200-234). `ReplayComplete` and the
`replay_complete` `SessionUpdate` variant are in v2's **stable** `schema.json`, so `replay_complete` is part of the
`capabilities.session` baseline, not an unstable feature. Initial config values, `session/options` and `cursor_update` are unstable.

## Summary of target changes in this doc

- Line 35, 216, 344-346, 360-420: new **`replay_complete`** (MUST family, incl. child sessions).
- Lines 188-191, 431: a resume without replay resynchronizes state, not foreground work. After a replay, current
  `subagent_update`s for listed children follow the parent's `replay_complete`.
- Line 236: prompt suggestions SHOULD NOT be replayed.
- Lines 303, 307-321, 328: the chunk-primer MUST now covers `session_message`, tool-call content, terminal output and
  compaction summary chunks.
- Lines 337-342: replay of unstable session cursors (SHOULDs).
- Line 53: child sessions are not "active". Line 57: held prompts on connection end (MAY), `idempotencyKey` retry (client).
- Line 476: client SHOULD dismiss prompts, and closing stops child sessions at any depth.
- Lines 594-596: **initial config option values** (`session.options`), pointing to `session-config-options.mdx:553-585`.
- Everything from old line 392 on shifts +85, and from old line 509 on +89.

## Registry rows citing session-setup.mdx

| id | classification | target citation (`docs/protocol/v2/draft/session-setup.mdx:… @ 3ea94133`) | note |
|---|---|---|---|
| ACP-SESSION-001 | citation-only | 86 | |
| ACP-SESSION-002 | citation-only | 86,600 | |
| ACP-CANCEL-208 | citation-only | 474-480 | 476 gained client/child-session sentences; the row's rule is unchanged |
| ACP-INFO-CANCEL-201 | citation-only | 52 | |
| ACP-SESSION-204 | citation-only | 613 | |
| ACP-SESSION-209 | citation-only | 613 (error.mdx part not mine) | |
| ACP-SESSION-206 | citation-only | 105 | |
| ACP-SESSION-207 | citation-only | 100-101,105 | also covers SC:583-584 for `session/new` (see OPTIONS) |
| ACP-SESSION-208 | citation-only | 110,138,140 | |
| ACP-RESUME-001 | citation-only | 146-147 | |
| ACP-RESUME-202 | citation-only | 140,214-216,232-237,344-346,424-427 | Optional: add `session_message`/`session_message_chunk` to `_REPLAYED_HISTORY_KINDS` (303 makes them upserts like the others). Mostly superseded by N1/N3 but still valid |
| ACP-RESUME-002 | citation-only, plus the RFD-to-docs swap in the text | 181-186,188; replace `docs/rfds/subagents.mdx:1008-1013 (Active RFD)` with `docs/protocol/v2/draft/subagents.mdx:462` | Docs now govern the subagents rule. The text's "(Active Subagents RFD)" must go |
| ACP-RESUME-204 | citation-only | 290-295 | |
| ACP-RESUME-205 | **changed text** | 303-321 (table 310-316); subagents RFD cite -> `subagents.mdx:463-464,482` | The MUST now covers every chunked entity. Widen: `session_message_chunk` needs a prior `session_message` with a `content` array (same `messageId`); `tool_call_content_chunk` a prior `tool_call_update` with a `content` array (same `toolCallId`); `terminal_output_chunk` a prior `terminal_update` with `output` (same `terminalId`); `compaction_summary_chunk` a prior `compaction_update` with a `summary` array (same `compactionId`). Keep accepting full content (321: "an update that carries the whole content can instead replace it"). When `replay_complete` is present, limit the window to updates before it: per 386, live chunks after the cut append to the replayed entity. This folds in the coordinator's R7 item |
| ACP-RESUME-206 | citation-only | 37-38,344-346,424-429 | N3 gives the new `replay_complete` -> snapshot order; this row's meaning stays as it is |
| ACP-RESUME-207 | citation-only | 218-222 | see N4 (no `replay_complete` on rejection) |
| ACP-RESUME-208 | citation-only | 221-222 | see N4 |
| ACP-RESUME-209 | citation-only, plus the RFD-to-docs swap | 214-216,228,290-292; replace the subagents RFD cite with `subagents.mdx:143,145,469,482,484` | `replay_complete` (no required fields) validates. A `replay_complete` for an unannounced session already FAILs here |
| ACP-RESUME-210 | citation-only | 110,138,356-358 | |
| ACP-RESUME-212 | citation-only | 234,433 | N3 is stricter for the replay window; keep both |
| ACP-RESUME-213 | citation-only | 188,431 | 431's additions (foreground work, children after a replay) do not affect a no-replay check |
| ACP-RESUME-214 | citation-only | 443-446 | |
| ACP-RESUME-216 | citation-only | 50,55 | |
| ACP-RESUME-217 | citation-only | 431 (prompt-lifecycle part not mine) | |
| ACP-CLOSE-001 | citation-only | 452-454,474-490 | |
| ACP-CLOSE-002 | citation-only | 474-478 | |
| ACP-CLOSE-203 | citation-only | 478 | |
| ACP-CLOSE-204 | citation-only | 52,480 | |
| ACP-CLOSE-205 | citation-only | 476 | |
| ACP-CLOSE-206 | citation-only | 480 | |
| ACP-CLOSE-003 | citation-only | 492-495 | |
| ACP-DELETE-001 | citation-only | 50 | |
| ACP-DELETE-204 | citation-only | 478,480 | |
| ACP-ARCHIVE-201 | citation-only | 478,480 | |
| ACP-ADDDIRS-001 | citation-only | 497-526 | |
| ACP-ADDDIRS-202 | citation-only | 501,524 | |
| ACP-ADDDIRS-203 | citation-only | 522,528 | |
| ACP-FORK-201 | citation-only | 50 | |
| ACP-FORK-202 | citation-only | 50 (`session-fork` is still a Draft RFD) | |
| ACP-FORK-204 | citation-only | 54 | |
| ACP-FORK-205 | citation-only | 110,142 | |
| ACP-FORK-206 | citation-only, plus a label fix | 50; `docs/rfds/v2/background-work.mdx:226` is now **Draft**, not Active | The docs (50) state the rule, so drop the Draft RFD cite (cite a Draft RFD only where nothing else does) |
| ACP-SYSPROMPT-001 | citation-only | 558-562,568 | |
| ACP-SYSPROMPT-202 | citation-only | 561-562,568 | |
| ACP-SYSPROMPT-002 | citation-only | 559,566 | |
| ACP-SYSPROMPT-003 | citation-only | 562,566 | |
| ACP-MCP-201 | citation-only | 644-696,745,770-774 | |
| ACP-MCP-202 | citation-only | 698-741 | |
| ACP-MCP-203 | citation-only | 634,642 | |
| ACP-MCP-204 | citation-only | 636,774 | |
| ACP-SESSION-006 | citation-only | 780,784 | |
| ACP-CONFIG-203 | citation-only | 138,356-358 | |
| ACP-PATCH-211 | citation-only (my part) | 476 | Its `background-work.mdx:56 (Active RFD)` label is now Draft. That belongs to the prompt-lifecycle/tool-calls researcher |
| ACP-ERROR-003 | citation-only | 48-52 | |
| ACP-ERROR-004 | citation-only | 48-52 | |

No row is removed. `ACP-RESUME-205` is the only changed-text row. The rest are citation-only, with label or RFD-to-docs swaps
on RESUME-002, RESUME-209 and FORK-206.

## Ledger entries citing session-setup.mdx (`spec-tracker/maps/v2.toml`)

| ledger citation @ base | classification | target citation | note |
|---|---|---|---|
| transports:43; SS:55 (connection end -> not active) | citation-only | SS:57 | Reason OK: one stdio connection is one process, inherent to the transport |
| elicitation:225-227,233; SS:391 | citation-only (my part) | SS:476 | Elicitation part belongs to that doc's researcher |
| SS:49 (fork history not live) | citation-only | SS:50 | |
| SS:223 (replayed tool call final status) | citation-only | SS:230 | Reason still holds |
| SS:228 (notices SHOULD NOT be replayed) | **remove; superseded by N3** | SS:235 | The reason ("indistinguishable from a new live notice") no longer holds: 384 makes the agent hold every non-history update, `notice` named, until after `replay_complete`. A notice before `replay_complete` is now observable as a fault. See D5 |
| SS:289 (preserve other entity IDs) | citation-only | SS:297 | |
| SS:355,356 (re-establish pending requests after connection loss) | citation-only | SS:440,441 | Reason OK (needs a reconnect, and stdio is one process) |
| SS:391; delete:95; list:247 (free resources, stop background) | **changed statement** | SS:476 | Add "and its child sessions, at any depth" (new at 476). Same reason: internal, and needs an agent that exposes children |
| SS:443 (unadvertised `additionalDirectories` ignored) | citation-only; **reason rests on a TCK choice** | SS:528 | "the unadvertised-capability probe is not built" is a TCK choice. Propose a row instead (N17, D6) and delete the entry |
| SS:475,476,480 (systemPrompt placement) | citation-only | SS:560,561,565 | |
| SS:538,539 (root-set security) | citation-only | SS:627,628 | |
| SS:549 (mcpServers not restored) | citation-only | SS:638 | "Deferred" with a TCK-stub blocker; allowed by the rule |
| SS:607,626 (stdio launch cwd/env; transport headers) | citation-only | SS:696,715 | Deferred, allowed |
| SS:693 (no shell) | citation-only | SS:782 | |
| SS:695 (no creds in model context/logs) | citation-only | SS:784 | |
| SS:696 (headers only to origin) | citation-only | SS:785 | Deferred, allowed |
| slash-commands:12; SS:108 | citation-only (my part) | SS:110 | |

## New requirements

Gate convention: the `capabilities.session` baseline rule from the `requirements.py` docstring. All `replay_complete` rows
are CAPABILITY `capabilities.session`, because `replay_complete` is in the stable schema and binds `session/resume`. Every
test obtains the session like `ACP-RESUME-001` (`obtain_resumable_session` plus `_add_history`) and SKIPs when the resume errors.

**N1 `ACP-RESUME-2xx` (replay_complete exactly once).** A successful `session/resume` with `replayFrom: {"type":"start"}`
carries exactly one `replay_complete` for the resumed `sessionId` before its response. On an idle session, no
replayed-history message update (`user_message`, `agent_message`, `agent_thought`, `session_message` or their `_chunk`
forms) for that session arrives between it and the response. Probed on a prompted session and on a never-prompted session,
the empty-history case (380). Tier CAPABILITY `capabilities.session`.
Cite SS:216,344-346,362,379-380,402; `schema/v2/schema.unstable.json#/$defs/ReplayComplete`.
Test: `resume_session` already returns the pre-response updates in wire order. Count `replay_complete`s for the session
(0 or more than 1 FAILs) and check that no message-kind update follows it. Harness: none. Fixtures: `_base.py` must emit
`replay_complete` after replay and before the snapshot. Add negatives `resume_omits_replay_complete`,
`resume_replay_complete_twice`, `resume_history_after_replay_complete`.

**N2 `ACP-RESUME-2xx` (no replay_complete without replay).** No `replay_complete` for the session in the `session/new`
exchange, or in a `session/resume` exchange with `replayFrom` omitted or explicit `null`. The check covers the time up to
the response plus a `drain_quiet` period. CAPABILITY `capabilities.session`. Cite SS:381; `$defs/ReplayComplete`.
Test: a new helper path that sends `replayFrom: null` explicitly (today `resume_session` omits the field for `None`).
Fixture negative: `replay_complete_without_replay`.

**N3 `ACP-RESUME-2xx` (only history before replay_complete).** Between a `session/resume` request with
`replayFrom: {"type":"start"}` and the resumed session's `replay_complete`, no `state_update`, `notice` or
`prompt_suggestions_update` for that session arrives. These are not history (234-236), and the agent holds every
non-history update until after `replay_complete` (384). With RESUME-206 this also fixes the order `replay_complete` ->
snapshot -> response (345). SKIPs when no `replay_complete` arrives (N1 judges that). CAPABILITY `capabilities.session`.
Cite SS:232-236,345,384,433. Test: slice the update list at `replay_complete`. Fixture negatives:
`resume_snapshot_before_replay_complete`, `resume_notice_before_replay_complete`. For other kinds see D1.

**N4 `ACP-RESUME-2xx` (rejected cursor sends no replay_complete).** When RESUME-207/208's probes are rejected with
`-32602`, no `replay_complete` for that session arrives before the error. CAPABILITY `capabilities.session`.
Cite SS:382,406. Test: reuse the RESUME-207/208 exchanges. SKIP when the probe was not rejected with `-32602`. See D2.

**N6 `ACP-RESUME-2xx` (child replay_complete).** During a replay resume, every child announced by `subagent_update` between
the request and the response (on the resumed session or a descendant) gets exactly one `replay_complete` on its own
`sessionId`. It comes after that announcement, before the response, and no `state_update` for the child precedes it
(`subagents.mdx:464`). SKIPs when no child is announced in the exchange. CAPABILITY `capabilities.session`, with a
self-SKIP (D3). Cite SS:412-418; `docs/protocol/v2/draft/subagents.mdx:463-465,486`.
Fixtures: `replays_subagent_history.py` and `exposes_subagent.py` must emit child `replay_complete`s. Add negative
`child_missing_replay_complete`. Overlaps the subagents.mdx researcher, so dedupe.

**N7 `ACP-RESUME-2xx` (current child update after the parent's replay_complete).** With replay, each `subagent` item in
the resume snapshot's `background` list is preceded by a `subagent_update` with that `sessionId` on the parent. That update
arrives after the parent's `replay_complete` and before the snapshot. SKIPs when the snapshot lists no subagent item.
CAPABILITY `capabilities.session`. Cite SS:431; `subagents.mdx:470`. Fixture: a variant of `resume_lists_background_work`
with a child, plus a negative that sends the child update only before `replay_complete`. Dedupe with the subagents researcher.

**N8 `ACP-RESUME-2xx` (agent requests wait for replay_complete).** No `session/request_permission` or `elicitation/create`
naming the resumed session (or an announced child) arrives before that session's `replay_complete`. ADVISORY (SHOULD).
SKIPs when no agent request arrives in the exchange. Cite SS:388; `subagents.mdx:488`. Passive check in N3's exchange.
It will usually SKIP. See D4.

**N9 `ACP-CURSOR-2xx` (replayed cursor follows its anchor entity).** In a replay window, each `cursor_update` for the
resumed session that carries an `anchor` is preceded, inside the window, by an update for the anchored entity
(`messageId`/`toolCallId`/`compactionId` of the anchor's `type`). Gate `inferred:cursors` (no Agent capability,
PL:919). The test self-SKIPs when no `cursor_update` is replayed. CAPABILITY. Cite
`prompt-lifecycle.mdx:982-983,993`; SS:339. The primary rule is in prompt-lifecycle, so dedupe with that researcher's live
version. Fixture: a cursor-announcing variant of `_base.py`.

**N10 `ACP-CURSOR-2xx` (replayed cursor carries its anchor).** In a replay window, the first `cursor_update` for each
`cursorId` carries a non-null `anchor` (and `capabilities`). ADVISORY (SS:339 SHOULD bullet). Gate `inferred:cursors`,
self-SKIP. Cite SS:339,341; PL:949.

**N11 `ACP-CURSOR-2xx` (stable cursorId across replays).** Run two consecutive full replays of one session. A cursor whose
anchor (`type`, entity ID, `position`) is identical in both carries the same `cursorId`. ADVISORY. SKIPs when no cursor
anchor matches across the two (341 allows changed anchors). Cite SS:340.

**N12-N15 `ACP-OPTIONS-2xx` (initial config option values).** Gate CAPABILITY `capabilities.session.options` (a real,
unstable marker, `$defs/SessionCapabilities/properties/options`). Primary citation is `session-config-options.mdx`, with SS:596 and the
schema as secondary. **Dedupe with the v2 session-config-options researcher.** Each runs on `session/new` and, if a
resumable session is obtained, on `session/resume`.
- N12: an entry with an unknown `configId` (`_tck_unknown_option`, `type:"boolean"`) is ignored. The request succeeds and
  the response has no such option. MUST, SC:581; `$defs/NewSessionRequest/properties/configOptions`.
- N13: two entries with the same `configId` -> `-32602`. MUST, SC:580. Use a real option from a probe `session/new`'s
  `configOptions` at its current value, falling back to an unknown id.
- N14: a schema-invalid entry (`configId` missing, or `type:"boolean"` with a string `value`) -> `-32602`. MUST, SC:578.
- N15: an entry with an unsupported value `type` (`_tck_unsupported`) -> `-32602`. MUST, SC:579. It conflicts with
  SC:581, so the recommendation is INFORMATIONAL (D7).
- Not proposed as a FAIL row: whether a valid entry is applied. SC:581 lets the runtime refuse it, so an INFORMATIONAL
  record is the most a test can do. SC:583-584 (no `config_option_update` before the `session/new` response) is already
  `ACP-SESSION-207`.
- Harness: none. Fixtures: an `advertises_options` base plus negatives (`options_rejects_unknown_id`,
  `options_accepts_duplicate`, ...).

**N17 `ACP-ADDDIRS-2xx` (unadvertised field ignored).** Replaces ledger SS:443/528. An agent that does not advertise
`session.additionalDirectories` accepts `session/new` carrying `additionalDirectories: [<absolute tmp dir>]`. The probe
breaks client MUST 526 on purpose, as SESSION-204 does. The test SKIPs when the capability is advertised. Tier ADVISORY
(D6). Cite SS:526,528.

## New ledger entries

| citation (@ 3ea94133) | statement | reason |
|---|---|---|
| SS:392 | Agents SHOULD report known replay gaps after `replay_complete`, for example with a notice. | Not observable: the client cannot know what history the agent no longer has. |
| SS:390; SS:52 | A session that was not active becomes active only with the successful `session/resume` response, so `session/prompt` before it gets `-32002`. | Not observable as pass/fail. A prompt sent after `replay_complete` and before the response is seen may reach the agent after it has sent the response, so an accepted prompt is no evidence of a violation. |
| SS:330-335 | Replay applies `_meta` as a patch. When the client may hold metadata for an entity, the Agent removes stale keys with `null` or sends `_meta: null` first. | Not observable: under patch semantics an omitted key means "unchanged", so a client cannot tell a stale key left behind from a current one without knowing the entity's current metadata. The coordinator's R10; agrees with `scope-rfds-v2-prompt-session.md`. |
| SS:339 (first clause) | When replaying, the Agent SHOULD send a `cursor_update` for each cursor in the history that it still accepts. | Not observable: whether the agent still accepts a cursor is agent state that may change at any time (`prompt-lifecycle.mdx:1026`), so a cursor's absence from a replay is no evidence. |
| SS:342 | A resume without replay announces no cursors for earlier history. | Not observable: a newly offered cursor (PL:952) may legitimately anchor to an earlier entity, and the wire cannot tell it from an announcement "for earlier history". |
| SS:388 (only if N8 is not adopted) | Agent requests SHOULD wait until after `replay_complete`. | Not provokable: a client cannot make the agent issue a new request during a resume exchange. |

Nothing is needed for SS:57: its held-prompt and connection-end text is MAY, and the `idempotencyKey` retry sentence binds the client.
SS:236 (prompt suggestions not replayed) and SS:235 (notices) are covered by N3, so they get no ledger entries.

## Decisions for the user

- **D1 (N3 scope).** SS:239 says agents "need not replay" historical `usage_update`, `session_info_update`,
  `config_option_update` and `available_commands_update`, which suggests replaying them is allowed. SS:384 names
  `available_commands_update` and `config_option_update` (and the current-state updates) as non-history to hold until
  after `replay_complete`. *Recommend:* judge only `state_update`, `notice` and `prompt_suggestions_update`, which the
  replay exclusions name explicitly (234-236). Record the other four in a `record_property`, not as FAILs.
- **D2 (N4 tier).** SS:406 is declarative ("replays nothing and does not send `replay_complete`"). The keyword is only
  SS:382's MUST NOT ("when it cannot finish the replay"). *Recommend:* CAPABILITY, as a definitional rule like
  ACP-FORK-202/206. The alternative is folding it into RESUME-207/208 as an extra assertion, but that changes their meaning.
- **D3 (child-row gate, N6/N7).** `capabilities.session` with a self-SKIP (precedent: RESUME-209), or `inferred:subagents`
  (precedent: the subagent rows near `requirements.py:352`). *Recommend:* `capabilities.session`. The docs state the rule
  as a MUST, the method is baseline, and children are opted into by behaviour, which the SKIP handles.
- **D4 (N8).** A passive ADVISORY row that nearly always SKIPs, or a ledger entry. *Recommend:* the row. It costs nothing in
  N3's exchange and catches a real ordering bug.
- **D5.** Delete ledger SS:228 (notices) because N3 covers it.
- **D6 (N17).** "Agents that don't advertise the capability ignore the field" has no RFC keyword, and the probe violates a
  client MUST. *Recommend:* ADVISORY, by precedent ACP-SESSION-209's no-keyword reasoning. Either way, the existing ledger
  reason rests on a TCK choice and must go.
- **D7 (N15).** SC:579 says an entry with an unsupported value `type` MUST fail with `-32602`. SC:581 says an entry whose
  `type` does not match the option's type, or whose `configId` is unknown, MUST be ignored. Any `_tck_unsupported` probe
  matches both: on a known option it is also a type mismatch, and on an unknown id it is also an unknown id. The schema
  supports neither reading decisively. `InitialSessionConfigOption`'s description lists only unknown id, type mismatch and
  disallowed value as ignored. `NewSessionRequest.configOptions` lists only malformed entries and duplicates as
  `-32602`. *Recommend:* make N15 INFORMATIONAL (record rejection or ignore), or drop it, until upstream clarifies which
  rule takes precedence. N12-N14 are unaffected.
- **D8 (dedupe).** N9-N11 (cursors), N12-N15 (options) and N6/N7 (children) overlap the prompt-lifecycle,
  session-config-options and subagents researchers. Assign each family one owner.

## Discrepancies

- SS:239 vs SS:384, on whether historical config/commands updates may be replayed (see D1).
- `session-config-options.mdx:579` vs `:581`, on an unsupported value type versus a type mismatch or unknown id. The
  schema descriptions do not settle it (see D7).
- RFD vs docs: `session-resume-replay.mdx` (Draft) ends replay with the snapshot. The docs insert `replay_complete` first
  (SS:344-346). The docs win; this is an addition, not a conflict.

## Open questions (route elsewhere)

- Fork cursors (`prompt-lifecycle.mdx:997-1020`): the MUST at PL:999 (an unissued, unaccepted or non-`fork` `cursorId`
  -> `-32602`, no fallback to a whole-session fork) is observable on `session/fork` with a nonce `cursorId`, gate
  `capabilities.session.fork`. It belongs to the prompt-lifecycle researcher. `ForkSessionRequest.cursorId` states it too.
- `session/options` rules (SC:514,549,551: no session created, no updates, no `session/list` entry, `-32002` for an unknown
  `sessionId`) are observable. They belong to the session-config-options researcher.
- SS:404 (a `session/resume` cancelled with `$/cancel_request` still gets a response): check that a cancellation row covers
  request cancellation generally.
- Cross-check: upstream agents built on SDKs that predate `replay_complete` will FAIL N1, a CAPABILITY row. Expect
  `--expect` churn in the cross-check refresh.
