# Consolidated plan: spec update 3961af94 -> 3ea94133 (v1 and v2, full audit)

**Sources checked:** all 27 `impact-*.md` reports (13 v1 incl. `impact-rfd-plan-operations.md`, 14 v2), the four
`scope-rfds-*.md` side reports, `spec-diff-v{1,2}.md`; `.claude/skills/update-to-spec/SKILL.md`, `docs/spec-updates.md`,
`docs/requirements.md`, `.agents/state.md`. Spot checks against agent-client-protocol @ `3ea94133` (read with
`git show`): `AbsolutePath`/`PlanMarkdown.path`/`Skill.path` shapes, v2 `session-setup.mdx:232-392`,
`prompt-lifecycle.mdx:766-768`, v1/v2 `subagents.mdx` child-cancel text. TCK @ `4e31d3a`: row and ledger counts,
id numbering, `open_enums.py`, `protocol.py`, `cross-check/run.sh`. Citation movement counted mechanically (difflib over
base/target of every cited `.mdx`).
**Confidence:** high for the dedupe and the counts; medium for slice sizes (estimates).

Abbreviations: `v1d/` = `docs/protocol/v1/draft/`, `v2d/` = `docs/protocol/v2/draft/`, `RFD-SA` = `docs/rfds/subagents.mdx`
(Preview at target), `SA` = the version's `subagents.mdx`, `PL` = v2 `prompt-lifecycle.mdx`, `PT` = v1 `prompt-turn.mdx`,
`SS` = `session-setup.mdx`, `SCO` = `session-config-options.mdx`, `TC` = `tool-calls.mdx`. All lines are `@ 3ea94133`.
"cap.session" = `capabilities.session`. "vacuous" = MANDATORY that PASSes when the agent never emits the thing.
Decision numbers `D#` refer to section 3.

---

## 1. Requirement changes

### 1.1 v1

**Removed rows**

| id | reason | cleanup |
|---|---|---|
| ACP-PLAN-001 (MANDATORY) | `PlanFile`/`type:"file"` and "Plan file URIs MUST be absolute" deleted from docs, RFD and schema (D1) | row, `test_plan_file_uri_is_absolute`, `is_absolute_uri` (`_helpers.py:196`, only user), `tests/v1/test_plan_uri.py` URI unit tests (rename the module), fixture `emits_relative_plan_file_uri.py`, `test_cli.py` id sets (`:59,525,1909,1922`) and the dedicated CLI test. Number 001 not reused in this change. |

**Retiered:** none.

**Changed text / gate / test** (tiers unchanged unless stated)

| id | change | citation (primary first) | slice |
|---|---|---|---|
| ACP-CONFIG-003 | also judge the `session/options` result's `configOptions` when `sessionCapabilities.options` is advertised (`:535` "same type and rules as `NewSessionResponse`") | `v1d/SCO:207-209,535`; `initialization.mdx:189-198` | V1-OPT1 |
| ACP-CLIENTCAP-007 | docs become primary: `SA:61,530`, `initialization.mdx:308-314`, `PT:19-21,44`, `TC:358`; RFD-SA `76-78,663-664` (Preview) secondary. MANDATORY kept, incl. the keyword-less `session` content clause | as left | V1-SA1 |
| ACP-SUBAGENT-001 | provenance rewrite ("draft docs and schema"); test: after a `session/load`, judge post-response child traffic against announcements made during that load (`SA:517`), not the earlier turn's set (D9) | `SA:90-97,212,517,531,533-534`; `schema.mdx:9709-9715`; RFD-SA `95-99,189-193,970-972,979-985,1018-1024` | V1-SA1 (text), V1-SA2 (test) |
| ACP-SUBAGENT-002 | doc MUST is primary; keep the replay exemption citing RFD-SA `649-650` (Preview) and record discrepancy U13a in the text (D9) | `SA:90,94`; `TC:349-352,364-365`; RFD-SA `647-650` | V1-SA1 |
| ACP-SUBAGENT-003/-004/-005/-014/-017 | drop "stated only by the Subagents RFD ... capped"; doc lines primary. Tiers unchanged (CAPABILITY `inferred:subagents`/`inferred:subagentCancel`; -014 ADVISORY) | -003 `SA:144`; -004 `SA:99-102,144`; -005 `SA:88,144,531`, `schema.mdx:9705-9707`; -014 `SA:272-273,427`; -017 `SA:447`; RFD-SA lines per `impact-v1-rfd-subagents.md` | V1-SA1 |
| ACP-SUBAGENT-011/-012 | text: "a message from a parent to a child (judged: the first one, which starts its work)"; add `SA:286` / `SA:284,287`. -012 test: an incoming `session_message` with no `senderSessionId` before the child's first output counts as reported (`SA:287`, PT:115-118) (D9) | `PT:108-113`; RFD-SA `667-690` / `667-676` | V1-SA1 (text), V1-SA2 (test) |
| ACP-SUBAGENT-016 | provenance (`SA:449` states the confirmation); test: an `unknown` snapshot after the cancel SKIPs ("not observable"), a later `idle`/`cancelled` still confirms (`SA:450`) (D9) | `SA:423,435,449-451`; `schema.mdx:9694`; RFD-SA `1113-1117,1133-1139` | V1-SA1, V1-SA2 |
| ACP-JSONRPC-003 | drop `rfds/mcp-over-acp.mdx:225,257 (Active RFD)` (now Draft, docs state it); add `v1d/schema.mdx:285-302` | `overview.mdx:242`; `schema.mdx:285-302` | R-V1 |

Citation-only within the subagent family (label + remap, plus optional additions): -006, -007, -008, -009 (+`SA:285`),
-013, -015 (+`SA:356-372,382`); ACP-CLIENTCAP-001/002/003 optional `+SA:95,157`.

**New rows** (provisional ids; id alignment settles them)

| prov. id | rule (short) | tier / gate | primary citation | test approach | harness / fixtures |
|---|---|---|---|---|---|
| ACP-PLAN-003 (shared) | markdown `plan.path`, when a string, is an absolute native path, not a URI | MANDATORY vacuous (D2) | `v1d/agent-plan.mdx:112-117`; `overview.mdx:233`; `#/$defs/PlanMarkdown/properties/path`; `rfds/plan-operations.mdx:64,196` (Preview) secondary | `_updates_with_plan_capability`, `is_absolute_path` on each markdown `path` | none; `conforming_full.py` PLANS file->markdown+abs path, `plan_turn_never_ends.py` off `file`, new `emits_relative_plan_markdown_path.py` |
| ACP-PLAN-004 (v1) | every `plan_update`/`plan_removed` on the `plan` connection validates against `SessionUpdate` (a legacy `file` plan FAILs) | MANDATORY vacuous (D1) | schema `#/$defs/SessionUpdate`; `agent-plan.mdx:55,108-117` | `validate_against_def` over the same transcript (SUBAGENT-015 pattern) | new `emits_file_plan.py` |
| ACP-CLIENTCAP-008 (shared) | no `prompt_suggestions_update` unless `clientCapabilities.session.promptSuggestions` | MANDATORY vacuous | `PT:35,364`; `initialization.mdx:244-256`; `#/$defs/PromptSuggestionsUpdate` | one more assertion on `_received_with_no_client_capabilities` (CLIENTCAP-004 pattern; covers load replay) | new fixture `emits_prompt_suggestions_unadvertised.py` |
| ACP-CLIENTCAP-009 (v1) | no `cursor_update` unless `clientCapabilities.session.cursors`, live or in load replay | MANDATORY vacuous | `PT:36,584-589`; `initialization.mdx:289-297`; `SS:152`; `#/$defs/CursorUpdate` | same transcript | new `emits_cursor_unadvertised.py` |
| ACP-SUGGEST-001 (shared) | with `session.promptSuggestions: {}`, each suggestion's `prompt` holds only `text`/`resource_link` and is a valid prompt | MANDATORY vacuous (D2) | `PT:398-405`; `initialization.mdx:257-279`; `#/$defs/PromptSuggestion` | own connection `{session:{promptSuggestions:{}}}`: new, 2 turns + quiet, load if advertised; scan | new `suggests_image_block.py` |
| ACP-SUGGEST-002 (shared) | no suggestion whose only content is empty/whitespace text | MANDATORY vacuous | `PT:402` | same scan | new `suggests_blank_prompt.py` |
| ACP-SUGGEST-003 (shared) | an accepted `session/prompt` while the list is non-empty is followed by a replacing/withdrawing update | CAPABILITY `inferred:promptSuggestions` (D3) | `PT:409,412` | same connection; window = turn 2 response + `quiet_period`; SKIP if no non-empty list before prompt 2 | new `stale_suggestions.py` |
| ACP-SUGGEST-004 (shared) | suggestions not replayed inside the `session/load` exchange | ADVISORY; test gated `loadSession`, SKIPs if no suggestion was seen live | `PT:425`; `SS:150` | same connection, load, check pre-response window | new `replays_suggestions.py` |
| ACP-CURSOR-001 (shared) | first `cursor_update` per `cursorId` carries non-null `anchor`; anchor never changes (reset per session on load) | MANDATORY vacuous (D2) | `PT:617,619,621-623`; `SS:156`; `#/$defs/CursorUpdate` | own connection `{session:{cursors:{}}}`: new, 2 turns, load; per-(session,cursorId) state | new `cursor_anchor_moves.py` |
| ACP-CURSOR-002 (shared) | an anchor of a known `type` names an entity already reported on that session (live and in replay) | MANDATORY vacuous | `PT:652-657`; `SS:154`; `#/$defs/CursorAnchor` | same transcript, reported-entity set per session, reset on load, only sessions created here | new `cursor_anchor_unknown_entity.py` |
| ACP-CURSOR-003 (shared) | `session/fork` with an unissued `cursorId` gets `-32602` (no whole-session fallback) | CAPABILITY `agentCapabilities.sessionCapabilities.fork` (D5) | `PT:676-680,698-701`; `#/$defs/ForkSessionRequest/properties/cursorId` | probe (a) fabricated id; (b)/(c) cross-session / non-`fork` cursor SKIP when unavailable; probe breaks a client MUST on purpose | new `fork_ignores_cursor_id.py` |
| ACP-CURSOR-004 (shared) | two loads replay the same `cursorId` for the same position | ADVISORY; SKIP when the first load replays no cursor | `SS:155` | key by (anchor type, position, ordinal of entity); not by message id (`SS:157`) | new `unstable_cursor_ids.py` |
| ACP-OPTIONS-001 (shared) | `session/options {cwd}` succeeds, result validates as `SessionOptionsResponse` | CAPABILITY `agentCapabilities.sessionCapabilities.options` | `SCO:475,479-500,511-535`; `initialization.mdx:424-429`; `#/$defs/SessionOptions{Request,Response}` | fresh connection; `-32000` SKIPs | conforming fixture advertises `options: {}`; new `options_method_errors.py` |
| ACP-OPTIONS-002 (shared) | `session/options` sends no `session/update` and adds no `session/list` entry | CAPABILITY options | `SCO:537`; `#/$defs/SessionOptionsRequest` | list before/after when `list` advertised; quiet window | new `options_creates_session.py` |
| ACP-OPTIONS-003 (shared) | unknown `sessionId` -> error, not a result (code not asserted in v1) | CAPABILITY options; SKIP without `loadSession`/`resume` | `SCO:507` | `sessionId: acp-tck-unknown-<uuid>` | new `options_accepts_unknown_session.py` |
| ACP-OPTIONS-004 (shared) | schema-invalid initial entry -> `-32602` | CAPABILITY options | `SCO:563`; `#/$defs/InitialSessionConfigOption` | `[{"value":"x"}]`, `[{"configId":"x","value":42}]` on `session/new` | new `options_accepts_malformed.py` |
| ACP-OPTIONS-005 (shared) | duplicate `configId` -> `-32602` | CAPABILITY options | `SCO:564` | real select option at its current value, synthetic id fallback | new `options_accepts_duplicate.py` |
| ACP-OPTIONS-006 (shared) | valid or inapplicable entries (unknown id, disallowed value, mismatched `type`) never fail setup; option keeps a valid value | CAPABILITY options | `SCO:475,565-566`; `SS:456` | `session/new` probes (+ load/resume probe of the unknown id when advertised); boolean probe only on a connection advertising `clientCapabilities.session.configOptions.boolean` | new `options_rejects_unknown_entry.py` |
| ACP-OPTIONS-007 (shared) | no `config_option_update` for applying initial entries | ADVISORY | `SCO:567` | pre-response + quiet window, select O with alternative V | (shared negative with 008) |
| ACP-OPTIONS-008 (v1) | no other `session/update` caused by the entries before the `session/new` response | ADVISORY | `SCO:568` | same exchange; judge `current_mode_update`/`config_option_update` only | new `options_notifies_initial.py` |
| ACP-OPTIONS-009 (shared) | `session/options` with a `sessionId` does not connect MCP servers | ADVISORY; SKIP without load/resume or when the agent does not persist | `SCO:509` | create with `_mcp_stub` on conn 1, delete marker, `session/options` on conn 2, marker must not reappear | reuse `_mcp_stub.py` |
| ACP-OPTIONS-010 (shared) | records whether a valid initial value shows in the setup response | INFORMATIONAL | `SCO:559,566` | the 007 exchange | none |
| ACP-OPTIONS-011 (shared) | the setup response's values are the actual ones: a no-op `set_config_option` returns the same pairs | CAPABILITY options (bucket) | `SCO:566` | CONFIG-209 technique; SKIP if a `config_option_update` intervenes | none |
| ACP-SUBAGENT-018 (shared) | a Client request naming an announced child (other than `session/cancel`) gets `-32602` | ADVISORY; SKIP no child / no probe method (D4) | `error.mdx:57`; `SA:419-428`; RFD-SA `1093-1096` | post-judging probe: `session/close` (if `close`), `session/load` (if `loadSession`), `session/delete` (if `delete`); judged only when an error came back | probe phase after the judged transcript; new `child_close_wrong_code.py` |
| ACP-SUBAGENT-019 (shared) | `session/close`/`session/delete` naming a child does not report success | CAPABILITY `sessionCapabilities.close` (and `.delete` probe when advertised) (D4) | `SA:428` | same probe; success FAILs | new `child_close_succeeds.py` |
| ACP-LIST-004 (shared) | `session/list` never returns an announced child | CAPABILITY `agentCapabilities.sessionCapabilities.list`; SKIP no child | `SA:430`; RFD-SA `1098-1100` secondary | subagents connection: list after the turn, follow `nextCursor` (bounded) | new `lists_child_session.py` |
| ACP-SUBAGENT-020 (v1) | child `state.state` is a protocol value or `_`-prefixed; idle `stopReason` a v1 `StopReason`, `error` or `_`-prefixed | ADVISORY | `SA:365,380`; `#/$defs/StateUpdate`, `IdleStateUpdate` | transcript check on subagents connection | new `child_custom_state.py` |

**New ledger entries (v1)** (`spec-tracker/maps/v1.toml`; reasons per the cited report unless noted)

| citation | statement (short) | reason (short) | from |
|---|---|---|---|
| `PT:411` | predict from the conversation as sent; discard stale predictions | not observable | prompt-turn |
| `PT:413` | replace/withdraw the list when it stops applying for other reasons | not observable | prompt-turn |
| `PT:705-709` | accept a cursor while history is retained; clear `capabilities` when it stops | not observable (agent may stop any time) | prompt-turn (+ D5c) |
| `SS:154` | replay a `cursor_update` for each cursor still accepted | not observable (D5b) | session-setup |
| `SA:287`; `PT:115-118` | no evidence of sender -> omit `senderSessionId`, never assume the parent; link views only on evidence | not observable | prompt-turn L3 = subagents N4 (merged) |
| `SCO:236,238` | `speed` ordering / boolean `true` is faster | not observable | config-options |
| `SCO:240` | no `speed` for model/reasoning/mode options | not observable | config-options |
| `SCO:507` | with `sessionId`, result equals what load/resume would return | not deterministically observable | config-options |
| `SCO:537` (rest) | no resume, no change, no history write | not deterministically observable | config-options |
| `SCO:559` | entries applied in order over restored/fork config | not observable | config-options |
| `TC:362-363`; RFD-SA `655-657` | new `content` re-sends session references | not decidable | tools |
| `TC:363-365`; RFD-SA `659-661` | reference only resolvable handles; never guess | not observable beyond SUBAGENT-002 | tools |
| `#/$defs/AuthAccount/properties/description`; `rfds/get-auth-state.mdx:173-177 (Draft RFD)` | `description` MUST NOT contain credentials | not observable (separate entry, bucket) | auth/schema |
| `SA:157` | child requests pass parent checks; no circumvention | not observable beyond CLIENTCAP-001..003 | subagents N1 |
| `SA:269,522` | report child config (SHOULD) | not observable | N2 |
| `SA:285` | report outgoing view + link (SHOULD) | not observable | N3 |
| `SA:428` (first sentence) | ignore `session/cancel` for a child without `cancel` | not observable as violation | N6 |
| `SA:454` | cancel cascades to waited-on descendants | not observable | N7 |
| `SA:449-450` | stop, flush, confirm only on observed stop | not observable | N8 |
| `SA:518` | report child state after load/resume (SHOULD) | not observable | N9 |
| `SA:528,536` | replay associations/history; report gaps (SHOULD) | not observable | N10 |
| `SA:531,535` | replayed child updates keep ids/order; all before response; no historical state after | not observable | N11 |
| `SA:544`; `PT:736` | cost includes descendants | not observable as violation (no deadline) | N12 (replaces removed cost entry) |
| `SA:484-490`; RFD-SA `1102-1107` | fork remaps copied session ids | Deferred: needs fork-of-parent + load driver (D8) | R4 |
| RFD-SA `586-588` (Preview) | no outgoing view for a known-failed send | not observable | rfd L1 |
| RFD-SA `471-472` (Preview) | supply message references once known | not observable | rfd L2 |
| RFD-SA `995-996` (Preview) | retain/reconstruct child data where practical | not observable | rfd L3 |

**Removed / rewritten ledger entries (v1)**

| entry | action |
|---|---|
| RFD-SA `1168-1170` (no fabricated exclusive cost) | delete (text deleted; replaced by `SA:544` entry above) |
| `UnknownStateUpdate`; RFD-SA `855-860` | rewrite statement: "...when observability is actually lost, including when the Agent stops tracking a child that may still be working..."; fold in `SA:414-415` (no invented final status; new capabilities) instead of a separate entry; primary `SA:410,414-415`, RFD-SA `881-889` |
| RFD-SA `1151-1153` | primary `SA:470`; reason's pointer `:1126-1128` -> `SA:466` (rule still holds in v1) |
| RFD-SA `942-949` | primary `SA:534`; reason's `(:945)` -> RFD-SA `:982` |
| RFD-SA `576-577` | primary `PT:102-104`; RFD-SA `584-585` secondary |
| other subagent entries | docs primary per `impact-v1-subagents-doc.md` section 2; block header -> `subagents (v1d/subagents.mdx; RFD-SA, Preview RFD)` |
| `agent-plan.mdx:179,181` | citation `:171,173`; reason prose "line 185" -> "line 177" (hand fix) |
| `error.mdx:37` unknown code | reason rests on a TCK choice: reword (D10) |
| `transports.mdx:10,45` | reason "the TCK only launches agents over stdio" is a TCK choice: reword to "an agent reached over stdio supports stdio by construction, and ACP does not specify custom transports, so no generic client can drive one" (D10) |
| `TC:250` | reword: "not decidable: the approved request describes the operation only in agent-authored free-form fields" (D10) |
| `get-auth-state.mdx:297` SHOULD advertise `auth.status` | reword onto the client MUST on the same line (D10) |
| `get-auth-state.mdx:313` SHOULD send `auth/status_update` | reword: Draft-RFD SHOULD with no deadline, absence never conclusive (D10) |
| `session-list.mdx:258` archive persists | "Deferred": real blocker = no mid-test agent restart, ephemeral store inconclusive; the load/resume half -> follow-up row (D10) |
| `session/status`, `session/set_title` entries | reason names TCK progress; see D10 (follow-up rows for the `-32002` halves) |

**Citation-only (v1):** 53 of 108 rows and 35 of 57 ledger entries have a moved line or a stage label to refresh
(49 rows / 28 entries moved, 19 / 16 relabels). `spec-impact --fix` handles the line remaps; its "Needs review" list
should be: ACP-CLIENTCAP-007 (`PT:19`, `TC:358`), ACP-SUBAGENT-011/-012 (`PT:106-111` -> `108-113`), ACP-PLAN-001
(left for V1-PLAN), ledger RFD-SA `576-577` and `1168-1170` (left for V1-SA1).

### 1.2 v2

**Removed rows:** none.

**Retiered**

| id | change | citation |
|---|---|---|
| ACP-CANCEL-213 | ADVISORY -> CAPABILITY `cap.session` (SHOULD -> MUST at `PL:1452`, `cancellation.mdx:42`); keep the `confirm_window`; row text notes "the Agent decides which requests belong to the work" and the narrow unlisted-background risk (D3) | `PL:1452`; `cancellation.mdx:42,65`; `#/$defs/CancelRequestNotification`, `CancelSessionNotification` |

**Changed text / gate / test**

| id | change | slice |
|---|---|---|
| ACP-COMMANDS-201 | `type` may be `command`, `skill` (unstable) or `_`-custom; names unique across commands and skills; also scan a connection advertising `session.commands.skill: {}`; add `#/$defs/Skill`; `slash-commands.mdx:12,37-43,91-113,186-192` | V2-SKILL |
| ACP-PROMPTCAP-201 | add `skill` to the unadvertised types probed (same rule, Rule B); cite `content.mdx:24,244-246`, `slash-commands.mdx:255`, `#/$defs/PromptSkillCapabilities` | V2-SKILL |
| ACP-ENUM-201 | add sites: `cursor_update` `anchor.type`/`anchor.position` (`PL:984`; `#/$defs/CursorAnchor`, `CursorAnchorPosition`) [V2-CUR]; permission `subject.type` (`TC:259-265`; `#/$defs/RequestPermissionSubject`), delete "subject.type is not checked", flip `tests/v2/test_open_enums.py:142` [V2-TOOL]. Set updates happen in R-V2 | V2-CUR, V2-TOOL |
| ACP-RESUME-205 | chunk primer widened to `session_message_chunk`, `tool_call_content_chunk`, `terminal_output_chunk`, `compaction_summary_chunk` (each needs the emptied whole-entity update first, or full content); window ends at `replay_complete`; `SS:303-321`; subagent cite -> `SA:463-465,482` | V2-REPLAY |
| ACP-AUTH-004 | standalone path (no TCK login before logout): FAIL only on `-32601`, other errors SKIP citing `authentication.mdx:273`; unchanged after a TCK login | V2-AUTH |
| ACP-SUBAGENT-001/-003/-004/-005/-006/-011/-014/-016/-017/-201/-202 | provenance rewrites, doc primary (`SA:68-78,126,80-83,106-113,218,264,251-252,330,350-352,373-403,405`; `PL:1448` for -202). Tiers unchanged | V2-SA1 |
| ACP-SUBAGENT-002 | drop "a reference does not count as traffic carrying the child's ID" (contradicts `SA:74`); add `TC:754-756` | V2-SA1 |
| ACP-SUBAGENT-004 | extension: a later `session/new` never returns an announced child id (`SA:82-83`) | V2-SA3 |
| ACP-SUBAGENT-011/-012 | as v1 (text + -012 absent-sender test change), `SA:262-265`, `PL:142-152` | V2-SA1/-SA2 |
| ACP-SUBAGENT-016 | require the child's own idle `state_update` (`SA:400`; mirror is SHOULD, judged by -201); `unknown` after cancel SKIPs (`SA:401`) (D9) | V2-SA2 |
| ACP-RESUME-002/-209 | subagents RFD -> docs (`SA:462`; `SA:143,145,469,482,484`) | V2-SA1 |
| ACP-TOOLCANCEL-203 / ACP-TERMCANCEL-203 | cite `SA:369,374` first | V2-SA1 |
| ACP-META-203 | text literal "`:108-115`" -> "`:111-118`" | R-V2 |
| ACP-CANCEL-209 | optional text note on "the Agent decides" (`PL:1452`, `cancellation.mdx:42`) | V2-CAN |
| ACP-JSONRPC-003 | drop `mcp-over-acp.mdx (Active RFD)` | R-V2 |
| ACP-PROMPT-209, ACP-INFO-CONCURRENT-201 (`rfds/v2/prompt.mdx:88`), ACP-STATE-209/-210, ACP-PATCH-211 (+ drop "an Active RFD allows this explicitly"), ACP-FORK-206, ACP-TOOLCANCEL-206, ACP-TERMCANCEL-206 (`rfds/v2/background-work.mdx`) | drop the now-Draft RFD citations; docs state each rule | R-V2 |
| ACP-ERROR-006 | add `session/options {cwd}` to the probes when `cap.session.options` is not advertised | V2-OPT1 |
| ACP-CONFIG-001/-210, ACP-COMMANDS-201, ACP-CLIENTCAP-203 | include the `session/options` result in their payload scans when options is advertised (instead of restating those rules in OPTIONS-001) | V2-OPT1 |

**New rows (v2)**

| prov. id | rule (short) | tier / gate | primary citation | test approach | harness / fixtures |
|---|---|---|---|---|---|
| ACP-PLAN-003 (shared) | markdown `path` absolute | CAPABILITY `cap.session`, SKIP unobserved (D2) | `v2d/agent-plan.mdx:104-109`; `#/$defs/PlanMarkdown/properties/path`, `AbsolutePath`; plan-operations `:64,196` (Preview) secondary | PATCH-205's turn + `is_absolute_path` (schema does not catch relative: `AbsolutePath` is a bare string) | new `relative_markdown_plan_path.py`; conforming base sends abs path |
| ACP-CLIENTCAP-008 (shared) | no suggestions without `session.promptSuggestions` | CAPABILITY `cap.session` | `PL:42,707`; `initialization.mdx:206-215`; `#/$defs/PromptSuggestionsUpdate`; `extensibility.mdx:39` | default handshake transcript (CLIENTCAP-003 pattern) + extra launches with `promptSuggestions: null` and `session: {}` | new `suggests_unadvertised.py` |
| ACP-CLIENTCAP-203 (v2) | no `type:"skill"` command entries without `session.commands.skill` | CAPABILITY `cap.session` | `slash-commands.mdx:171`; `initialization.mdx:254-261`; `#/$defs/Skill` | setup results + `available_commands_update` (+ `session/options` result); extra launches `skill: null`, `commands: {}` | new `skills_unadvertised.py` |
| ACP-COMMANDS-202 (v2) | an agent listing `skill` entries advertises `session.prompt.skill` | CAPABILITY `inferred:skills` (new inferred gate) | `slash-commands.mdx:173`; `initialization.mdx:417-418` | connection with `{session:{commands:{skill:{}}}}`; SKIP no skill entry | new `skills_without_prompt_skill.py` |
| ACP-PROMPTCAP-202 (v2) | a `skill` block naming no invocable skill -> `-32602`, not inserted | CAPABILITY `cap.session.prompt.skill` | `slash-commands.mdx:253,255`; `content.mdx:244-250`; `#/$defs/SkillReference/properties/name` | first block `{type:skill,name:_tck_no_such_skill_<uuid>}` + text; `assert_prompt_rejected_not_inserted` | new `accepts_unknown_skill.py` |
| ACP-PROMPT-220 (v2) | no `skill` block outside user messages | ADVISORY | `content.mdx:252` | passive walk of agent-authored content | shared content-block walker |
| ACP-SUGGEST-001/-002 (shared) | as v1 | CAPABILITY `cap.session`, SKIP no suggestion (D2) | `PL:743,745-748` | connection advertising `promptSuggestions: {}` | 2 new fixtures |
| ACP-SUGGEST-003 (shared) | as v1 | CAPABILITY `cap.session`, SKIP no non-empty list (D3) | `PL:755`; `PL:339` | same, window turn 2 idle + `quiet_period` | 1 new |
| ACP-SUGGEST-004 (shared) | no suggestion between `replay_complete` and the resume response (before `replay_complete` is RESUME-220's) | ADVISORY; SKIP no suggestion | `PL:768`; `SS:236` | resume with `replayFrom: start` | 1 new |
| ACP-CURSOR-001 (shared) | as v1; also covers the first replayed update after a reset (absorbs session-setup N10) | CAPABILITY `cap.session`, SKIP no cursor (D2) | `PL:947,949,952`; `SS:339,341` | passive; reset at full replay | 1 new |
| ACP-CURSOR-002 (shared) | as v1, incl. replay window (absorbs session-setup N9) | CAPABILITY `cap.session` | `PL:966-975,982-983,993`; `SS:339` | sessions created here; not resumed-without-replay | 1 new |
| ACP-CURSOR-003 (shared) | as v1 | CAPABILITY `cap.session.fork` (D5) | `PL:999,1017-1020`; `#/$defs/ForkSessionRequest/properties/cursorId` | nonce `cursorId` | 1 new |
| ACP-CURSOR-004 (shared) | same `cursorId` for identical anchor across two full replays | ADVISORY; SKIP no matching anchor | `SS:340` | two resumes with `replayFrom: start` | 1 new |
| ACP-PROMPT-212 (v2) | retry with same `idempotencyKey` returns the original `messageId`, no second insertion | CAPABILITY `cap.session` (D7) | `PL:439,451-452,455,457,465-466`; `#/$defs/PromptRequest/properties/idempotencyKey` | prompt with key, re-send raw with new JSON-RPC id, collect + quiet | "send and collect" helper (`run_prompt` would time out) |
| ACP-PROMPT-213 (v2) | malformed key (`""`, 256 chars, `42`) -> `-32602`, nothing inserted | CAPABILITY `cap.session` | `PL:333,441`; `#/$defs/IdempotencyKey` | rejection helper (`_helpers.py:2922`) | — |
| ACP-PROMPT-214 (v2) | reused key with different prompt -> original id or `-32602`, never a 2nd insertion | CAPABILITY `cap.session` | `PL:444,457` | breaks client MUST NOT on purpose | — |
| ACP-PROMPT-215 (v2) | two held retries of one key get the same outcome | CAPABILITY `cap.session`; SKIPs as PROMPT-209 | `PL:400-404,453,1446` | extend `prompt_during_active_work` | — |
| ACP-PROMPT-216 (v2) | the key never appears in agent messages | ADVISORY | `PL:459` | piggyback on 212 + list + resume replay | — |
| ACP-PROMPT-217 (v2) | key scoped to session: same key in another session is a new submission | CAPABILITY `cap.session` | `PL:461` | second session | — |
| ACP-PROMPT-218 (v2) | key recognized across connections while the message is retained | CAPABILITY `cap.session`; SKIP if not replayed/resumable (D7) | `PL:465,467,471` | two-process flow via `obtain_resumable_session` route 3 | — |
| ACP-PROMPT-219 (v2) | a rejected prompt leaves its key unrecorded | CAPABILITY `cap.session` (D7) | `PL:451,456` | `_tck_unknown` block with key, then valid prompt with key | idempotency fixtures: ~5 negatives |
| ACP-RESUME-218 (v2) | exactly one `replay_complete` per replay resume, before the response; also for empty history | CAPABILITY `cap.session` | `SS:216,344-346,379-380`; `#/$defs/ReplayComplete` | `resume_session` pre-response updates; prompted and never-prompted session | `_base.py` emits it; negatives `resume_omits_replay_complete`, `..._twice` |
| ACP-RESUME-219 (v2) | none without replay (`session/new`, `replayFrom` omitted / explicit `null`) | CAPABILITY `cap.session` | `SS:381` | helper path sending `replayFrom: null` | `replay_complete_without_replay` |
| ACP-RESUME-220 (v2) | only history before `replay_complete`: judge `state_update`, `notice`, `prompt_suggestions_update` (record others) | CAPABILITY `cap.session` (bucket) | `SS:232-236,345,384` | slice at `replay_complete`; SKIP when absent | `resume_snapshot_before_replay_complete`, `resume_notice_before_replay_complete`, `resume_history_after_replay_complete` |
| ACP-RESUME-221 (v2) | a cursor rejected with `-32602` sends no `replay_complete` | CAPABILITY `cap.session` | `SS:382,406` | reuse RESUME-207/208 exchanges | 1 new |
| ACP-RESUME-222 (v2) | agent requests wait for `replay_complete` | ADVISORY; SKIP no request | `SS:388`; `SA:488` | passive in RESUME-220's exchange | — |
| ACP-RESUME-223 (v2) | each child announced in a replay gets exactly one own `replay_complete`, after its announcement, before the response, no prior `state_update` | CAPABILITY `cap.session`, SKIP no child | `SS:412-418`; `SA:463-465,486` | replay of a subagent session | `replays_subagent_history.py`/`exposes_subagent.py` emit it; `child_missing_replay_complete` |
| ACP-RESUME-224 (v2) | each `subagent` item in the resume snapshot is preceded by a current `subagent_update` after the parent's `replay_complete` | CAPABILITY `cap.session`, SKIP none | `SS:431`; `SA:470` | resume snapshot | variant of `resume_lists_background_work` + negative |
| ACP-RESUME-225 (v2) | after a resume without replay, child traffic follows a re-announcement (ancestors first) made since that resume | CAPABILITY `cap.session` (D8) | `SA:70,462,469` | RESUME-209 shape without replay | 1 new |
| ACP-OPTIONS-001..007, -009, -010, -011 (shared) | as v1; -002 adds a "not resumed" probe (closed id still gets `-32002` on prompt); -003 asserts `-32002` (bucket); -006 boolean probes need no client cap; -009 same connection (create with stub, close, delete marker) | CAPABILITY `cap.session.options` (007/009 ADVISORY, 010 INFORMATIONAL) | `SCO:482,486-512,514,516,549,551,578,580-583`; `initialization.mdx:348-353` | as v1 | ~6 new fixtures; conforming base advertises `session.options: {}` |
| ACP-OPTIONS-201 (v2) | entry with an unsupported value `type` -> records rejection vs ignore | INFORMATIONAL (D6) | `SCO:579,581` | `_tck_unsupported` type | none |
| ACP-SUBAGENT-018/-019 (shared) | as v1 | ADVISORY / CAPABILITY `cap.session` (close is baseline in v2; delete probe only with `cap.session.delete`) (D4) | `error.mdx:58`; `SA:369,376,379-380,425` | own connection; probes `session/resume`, `session/close` (last), `session/delete` if advertised | 2 new |
| ACP-LIST-004 (shared) | `session/list` never returns an announced child | CAPABILITY `cap.session` + SKIP no child | `session-list.mdx:6`; `SA:381` | list from the shared subagent connection before it closes | 1 new |
| ACP-SUBAGENT-203 (v2) | before the `session/close` response, pending child requests get `$/cancel_request` | CAPABILITY `cap.session` (D8) | `SA:427`; `SS:476` | CLOSE-205 machinery on child requests | 1 new |
| ACP-SUBAGENT-204 (v2) | stopped descendants' pending permission requests get `$/cancel_request`; the cancel confirmation does not wait for them | CAPABILITY `inferred:subagentCancel` (D8) | `SA:417,421`; `PL:1452` | child-cancel driver holds child requests | harness change in `_child_cancel.py`; 1 new |
| ACP-SUBAGENT-205 (v2) | both copies of a state transition precede a later transition on either path | CAPABILITY `inferred:subagents` (D8) | `SA:351` | per-child ordered states, child vs mirror | 1 new |
| ACP-PATCH-213 (v2) | `diff` `changes[].path`/`oldPath` absolute; each `path` at most once | CAPABILITY `cap.session` (D10) | `TC:615,622,690-696`; `#/$defs/DiffChange` | passive walk over `_drive_one_turn` | `relative_diff_path.py` |
| ACP-PATCH-214 (v2) | `git_patch` header paths absolute or `/dev/null`, and each matches a `changes` entry | CAPABILITY `cap.session` (D10) | `TC:615-617,653-660`; `#/$defs/DiffPatch` | Git-unquote, strip trailing TAB; skip `diff --git` line | `git_patch_ab_prefix.py` |
| ACP-PATCH-215 (v2) | `git_patch` text has no commit metadata/email envelope (first line `diff --git `) | CAPABILITY `cap.session` (D10) | `TC:653-654,661` | first-line check | `git_patch_email_envelope.py` |
| ACP-PATCH-216 (v2) | no `terminal_output_chunk` after a concrete `exitStatus` | ADVISORY (D10) | `TC:578-579` | passive | `output_after_exit.py` |
| ACP-TOOLCANCEL-210 / ACP-TERMCANCEL-210 (v2) | a repeat cancel after an accepted one and a final status/`exitStatus` gets an error | CAPABILITY `inferred:toolCallCancel` / `inferred:terminalCancel` | `TC:456,458-459` / `TC:602,604-605` | `_RepeatProbe` in `drive_item_cancel`; `_StaleProbe` skips the main item | `repeat_tool_cancel_accepted.py`, `repeat_terminal_cancel_accepted.py` |
| ACP-TOOLCANCEL-211 / ACP-TERMCANCEL-211 (v2) | that error is `-32602` | ADVISORY | `TC:459` / `TC:605` | same | — |
| ACP-AUTH-211 (v2) | a second `auth/logout` right after a successful one returns the empty result | ADVISORY; SKIP no `--allow-logout`/methods | `authentication.mdx:273`; `#/$defs/LogoutAuthResponse` | as `test_logout_succeeds`, twice | `logout_not_idempotent.py` |
| ACP-ADDDIRS-204 (v2) | an agent not advertising `additionalDirectories` accepts `session/new` carrying it | ADVISORY (D10) | `SS:526,528` | probe breaks client MUST on purpose; SKIP when advertised | `rejects_unadvertised_dirs.py` |

**New ledger entries (v2)** (`spec-tracker/maps/v2.toml`)

| citation | statement (short) | reason (short) | from |
|---|---|---|---|
| `SA:265`; `PL:149-152` | no sender evidence -> omit `senderSessionId`; link only on evidence | not observable | PL 1 = subagents E3 (merged) |
| `PL:469` | store the key with the message | not observable | PL 2 |
| `PL:466` | non-retained message: recognize key while active | unsafe (local command) | PL 3 |
| `PL:455` | a retry starts no second round of work | not decidable | PL 4 |
| `PL:754` | predict from conversation as sent; discard stale | not observable | PL 5 |
| `PL:756` | replace/withdraw when the list stops applying otherwise | not observable | PL 6 |
| `PL:1024,1026-1027` | accept cursor while retained; clear when stopping | not observable | PL 7 (+D5c) |
| `PL:999` (positive half) | valid cursor: fork at that position only | Deferred: fork replay + entity-id mapping undefined | PL 8 |
| `SS:339` (first clause) | replay a `cursor_update` per accepted cursor | not observable (D5b) | session-setup |
| `SS:342` | resume without replay announces no cursors for earlier history | not observable | session-setup |
| `SS:392` | report known replay gaps | not observable | session-setup |
| `SS:390`; `SS:52` | not active until the resume response | not observable as pass/fail | session-setup |
| `SS:330-335` | replay applies `_meta` as patch; clear stale keys | not observable | session-setup |
| `SCO:209` | `thought_level` ordering | not observable | config |
| `SCO:215,217` | `speed` ordering | not observable | config |
| `SCO:219` | no `speed` for model/level/mode | not observable | config |
| `SCO:514` | with `sessionId`, equals what resume would return | not deterministically observable | config |
| `SCO:551` (rest) | no change, no history write | not deterministically observable | config |
| `SCO:572,574` | order of application; before replay on resume | not observable | config |
| `SCO:584` | no other updates caused by entries before new/fork response | not attributable (SESSION-207/OPTIONS-007 cover config) | config |
| `SCO:585` | resume with entries notifies other connections | Deferred: stdio gives one connection per agent instance | config |
| `slash-commands.mdx:194-197` | send short skill description | not observable | config |
| `slash-commands.mdx:210` | advertise only invocable skills | unsafe | config |
| `slash-commands.mdx:238-239,255` (position/count) | non-first or repeated `skill` block without `inline` -> `-32602` | unsafe (needs a real skill name) | config |
| `content.mdx:252`; `slash-commands.mdx:254,256` | a `skill` block is an invocation and is echoed in `user_message`/replay | unsafe | transports-content (one entry) |
| `TC:528-529` | provide `command` on first terminal update when applicable | not decidable | tools |
| `TC:617-618,648` | provide `patch` whenever feasible | not decidable | tools |
| `TC:753-754` | new `content` re-sends session references | not decidable | tools |
| `#/$defs/AuthAccount/properties/description`; `rfds/get-auth-state.mdx:174-176 (Draft RFD)` | `description` MUST NOT contain credentials | not observable (separate entry) | auth/schema |
| `SA:139` | no circumvention of parent restrictions | not observable | E1 |
| `SA:248,474` | report child config (SHOULD) | not observable | E2 |
| `SA:380` (first sentence) | ignore `session/cancel` for a child without `cancel` | not observable as violation | E4 |
| `SA:401,403` | `cancelled` only once stopped; cancel does not close | not observable | E5 |
| `SA:418` | parent cancel does not resolve a running child's requests | not observable as violation | E6 |
| `SA:470,480,487` | report child state; replay what is kept; report gaps (SHOULD) | not observable | E7 |
| `SA:494-496`; `PL:1055` | cost includes descendants | not observable as violation | E8 (replaces cost entry) |
| `SA:482` | replay keeps child identity and parent | Deferred: needs live tree carried across reconnection (D8) | subagents N7 |
| `SA:436-438` | fork remaps copied session ids | Deferred: needs fork-of-parent + replay driver (D8) | subagents N10 |
| RFD-SA `586-588`, `471-472`, `995-1000` (Preview) | as v1 L1-L3 | not observable | rfd |

**Removed / rewritten ledger entries (v2)**

| entry | action |
|---|---|
| `agent-plan.mdx:119` Plan file URIs absolute | delete (rule removed; successor ACP-PLAN-003) |
| RFD-SA `1168-1170` cost | delete (replaced by E8) |
| `SS:228` notices not replayed | delete: superseded by ACP-RESUME-220 (`SS:384` makes it observable) |
| `TC:622,653-661` git_patch paths | delete: promoted to PATCH-213/214 (D10) |
| `TC:578,579` output before exit | delete: promoted to PATCH-216 (D10) |
| `SS:443` unadvertised `additionalDirectories` | delete: promoted to ADDDIRS-204 (D10) |
| `UnknownStateUpdate`; RFD-SA `855-860` | rewrite as v1; fold `SA:365` (no invented final status) |
| `SS:391; delete:95; list:247` free resources | statement adds "and its child sessions, at any depth" (`SS:476`) |
| `elicitation.mdx:225-227,233; SS:391` | restate as MUST (`elicitation.mdx:225-228,236`; `SS:476`); reason "Deferred" naming the harness blocker (mock client advertising modes + holding `elicitation/create` + an MCP-stub-forwarded trigger) |
| `v2.toml:358` elicitation section header and reasons for `:56-57,67-77,197,211-216` | reword away from "the TCK never advertises an elicitation mode" to the same Deferred blocker (D10) |
| RFD-SA `1117-1121` close cascades | narrow: `SA:427`'s wire signal is now ACP-SUBAGENT-203; primary `SA:425,428`, `SS:476` |
| RFD-SA `1151-1153` | primary `SA:420`; delete the reason's second sentence (relies on the v1-only client rule) |
| RFD-SA `942-949` | primary `SA:485`; reason pointer `(:945)` -> `SA:485` |
| RFD-SA `203-206` | add `SA:413` |
| `PL:67`; RFD-SA `439-441` | `PL:70`; keep RFD-SA relabelled as secondary |
| `error.mdx:38` unknown code | drop "the TCK's mock client sends only well-known codes" (D10) |
| `SCO:375` fan-out | reword: "Deferred: needs a second connection to the same agent instance, which stdio cannot provide; multi-connection activity is optional (`SS:54`)" |
| `security.mdx:81` provider `headers` | reword "Deferred": off-schema nested key, and a useful check needs a `providers/set` canary (persistent config change, unsafe) (D10) |
| `session-list.mdx:162`, `:248`, `:249` | reasons rest on TCK choices; D10 (`:249` persistence half "Deferred" with the restart blocker; the rest follow-up rows) |
| `transports.mdx:10,71,73` | same reword as v1 (D10; the v2 transports report called it acceptable, the scope report and v1 core did not; reworded for both) |
| auth `get-auth-state.mdx:297`, `:313` | as v1 |
| `session/status`, `session/set_title` | D10 |
| prose in reasons | `v2.toml:326` "`schema.mdx:954`" -> `:990`; tool-calls `terminalId` entry "`prompt-lifecycle.mdx:67`" -> `:70`; slash-commands entry "`slash-commands.mdx:47`" -> `:49` |

**Citation-only (v2):** 166 of 233 rows and 73 of 110 ledger entries move or relabel (148 rows / 63 entries moved,
33 / 14 relabels). Expected "Needs review" (citation inside a changed region): 33 rows (SUBAGENT-011/-012/-201,
PROMPT-209, INFO-CONCURRENT-201, CANCEL-209/-213/-214, INFO-CANCEL-201, JSONRPC-007, RESUME-202/-205/-206/-209/-213/-217,
CLOSE-205, PATCH-211, COMMANDS-201, ENUM-201, META-203, TOOLCANCEL-204..209, TERMCANCEL-204..209) and 10 entries
(`PL:372`, `transports.mdx:45`, `SS:55`, elicitation `225-227`, `SS:391`, `agent-plan.mdx:119`, `cancellation.mdx:40`,
RFD-SA `577`, `1168-1170`, `overview.mdx:266`). Target lines for every one are in `impact-v2-prompt-lifecycle.md`,
`impact-v2-session-setup.md`, `impact-v2-tool-calls.md`, `impact-v2-cancellation-elicitation.md`,
`impact-v2-extensibility.md`, `impact-v2-overview-error.md`.

### 1.3 Hand fixes `spec-impact --fix` will not make (both versions; do them in the re-vendor slices)

- **Ledger `reason` prose:** v1 `agent-plan.mdx:179,181` ("line 185" -> 177); v1 RFD-SA `1151-1153` (`:1126-1128`),
  `942-949` (`:945`) — pointer only, rewording waits for V1-SA1; v2 `v2.toml:326` (`schema.mdx:954` -> 990), tool-calls
  `terminalId` entry (`PL:67` -> 70), slash-commands entry (`:47` -> 49).
- **Row text literals:** v2 ACP-META-203 (`:108-115` -> `:111-118`). Grep `text=` strings for `\.mdx:[0-9]` in both
  registries; none else was reported.
- **Code docstrings/comments (no `@` rev, no test catches them):**
  - v1: `_helpers.py:225` (`PT:38` -> 40), `:419,539,551` (`:641` -> 851), `:808-810` and `:1118` ("Active Subagents
    RFD", anchor -> `SA#messages-from-a-parent-to-a-child`); `tests/v1/test_run_prompt.py:331`,
    `tests/fixtures/agents/v1/perm_only_reject_always.py:5` (`:641` -> 851), `asks_permission.py:3` (`:133-144` ->
    140-151).
  - v2: `open_enums.py:7` (237-240 -> 240-243); `protocol.py:176` (108-115 -> 111-118), `:193` (102,259 -> 105,262);
    `test_enums.py:5,21,27,224`; `test_jsonrpc.py:14,165`, `:141` (MCP-over-ACP "(Active)" -> Draft or drop);
    `test_extensibility.py:44,133,189,239,272,297,327,356,361,392,419` (+3 for lines >= 39); fixtures
    `accepts_contentless_embedded_resource.py:4`, `rejects_malformed_meta.py:3`, `malformed_traceparent.py:4`,
    `unprefixed_meta_key.py:3`, `rejects_unknown_capability_fields.py:4` (stale `:148` -> `:160`);
    `test_patches.py:169` (agent-plan 147 -> 139); `test_session_config.py:14,442`, `_base.py:881,914` and config
    fixtures (`:234` -> 249, `:375-379` -> 390-394); slash-commands fixtures (`:98-100` -> 101-103, `:110` -> 113);
    `test_authentication.py:216` (`schema.mdx:954` -> 990); `test_prompt.py:322`, `test_prompt_capabilities.py:160`
    (`content.mdx:22` -> 24); `test_cancel.py:409` (`cancellation.mdx:31` -> 33); `test_session_capabilities.py:1499`
    (`error.mdx:54,66` -> 54,68); PL offsets (`:1177` -> 1452, `:384` -> 402-404, `:382-384` -> 400-404, rest per the
    offset table in `impact-v2-prompt-lifecycle.md`) in `test_background.py`, `test_cancel.py`, `test_patches.py`,
    `_helpers.py`, `_child_cancel.py`, `test_prompt*.py`, `test_informational.py`, `test_session_capabilities.py`,
    `tests/v2/test_run_prompt.py`, `tests/fixtures/agents/v2/*.py`; `spec-tracker/maps/v2.toml:42` comment (heading lost
    "(unstable)"); pre-existing `src/tck/common/plugin.py:446` (`initialization.mdx:100` -> 112).
- **RFD stage relabels:** subagents `(Active RFD)` -> `(Preview RFD)` (v1 17 rows + 16 entries + `v1.toml:319` header;
  v2 rows + 14 entries) and every "Active Subagents RFD" string in code: v2 `_helpers.py:645,674,722,796,821,826,839,
  889,935,942,964,1051,1164,1181,1216,1986`, `test_session_capabilities.py:197,287,434,468`; v2
  `_helpers.py:1972-1974` and `tests/v2/test_run_prompt.py:847` re-cite from the now v1-only RFD section to
  `PL:1452` (Client MAY) and RFD-SA `1268`. plan-operations Draft -> Preview (only ACP-PLAN-001, deleted in V1-PLAN).
- **Dropped Draft-RFD citations** (docs state the rule): ACP-JSONRPC-003 v1+v2 (`mcp-over-acp`); v2 PROMPT-209,
  INFO-CONCURRENT-201 (`rfds/v2/prompt.mdx:88`); STATE-209, STATE-210, PATCH-211 (+phrase), FORK-206, TOOLCANCEL-206,
  TERMCANCEL-206 (`rfds/v2/background-work.mdx`).

---

## 2. Cross-report conflicts

**Resolved**

| conflict | resolution |
|---|---|
| ACP-PLAN-001: delete + new id (content-plan, v1 schema, plan-operations) vs re-target in place (v1 core D3) | delete + ACP-PLAN-003 (rule object changed URI -> native path; guard 1 forbids reusing 001 now). Shared with v2. D1 confirms. |
| PLAN-003 tier: v1 MANDATORY vacuous vs v2 CAPABILITY `cap.session` | per version (Rule B allows), as the general pattern in D2 |
| v1 plan-connection shape: new PLAN-004 (content-plan) vs bind to PROMPT-002/SCHEMA-001 (v1 schema) | PLAN-004, so one defect FAILs one row (SUBAGENT-015 pattern); optional in D1 |
| v1 schema report claims a relative `PlanMarkdown.path`/`Skill.path` FAILs schema validation | wrong: `AbsolutePath` is a bare `string` at target (checked); relative paths need PLAN-003 |
| Child `-32602` row: id family (v1 SUBAGENT-018 vs ERROR-009), owner (core, subagents-doc v1/v2, overview-error) | one shared ACP-SUBAGENT-018, subagents slices own it, cites `error.mdx` + `SA` |
| Child probe methods: v1 close+load (core) / close-or-delete, fallback prompt (subagents-doc) / v2 prompt+resume+set_config_option+close (overview-error) / close only (subagents-doc) | v1 `close`, `load`, `delete` (each gated); v2 `resume`, `close` (last), `delete` if advertised; no `prompt`/`set_mode`/`set_config_option` (start work or ambiguous `-32602`). D4 confirms |
| "close/delete of a child is not success": separate CAPABILITY row (v2 subagents-doc N3a, v1 R1 optional) vs folded | separate ACP-SUBAGENT-019; ACP-SUBAGENT-018 judges only the code of an error, so a success FAILs one row. D4 |
| `session/list` excludes children: SUBAGENT-019 (v1) vs LIST-2xx (v2) | shared ACP-LIST-004; gate = the version's real marker (v1 `sessionCapabilities.list`, v2 `cap.session`) + SKIP no child. v2 subagents-doc's `capabilities.session.list` gate does not exist |
| v2 `close` gates: subagents-doc N1/N3 use `capabilities.session.close` | no such marker in v2 (close is baseline): `cap.session` |
| CLIENTCAP prompt-suggestions row: owners (v1 init, PT, schema; v2 extensibility, PL, init) | one shared ACP-CLIENTCAP-008 (v1 MANDATORY, v2 CAPABILITY `cap.session`) |
| Cursor gate rows: v1 has a client cap, v2 none | ACP-CLIENTCAP-009 v1 only |
| Skill gate id: CLIENTCAP-2xx vs COMMANDS-2xx; "skill implies prompt.skill": COMMANDS-202 vs SKILL-2xx | ACP-CLIENTCAP-203 and ACP-COMMANDS-202 (existing families) |
| Unadvertised `skill` block: extend PROMPTCAP-201 (content, plan-commands) vs new SKILL row (v2 init D3) | extend PROMPTCAP-201 (same rule, Rule B); bucket |
| `skill` placement (a)-(d) (v2 init) | (d) = PROMPTCAP-202; (a)/(c) need a listed skill (runs user code): dropped; (b) ledgered Unsafe |
| Suggestions content: v1 two rows (types, whitespace) vs v2 one | split in both: SUGGEST-001 types, SUGGEST-002 whitespace |
| Suggestions not replayed: v1 PT (`loadSession` gate, vacuous) vs v1 SS (`LOAD-0xx`, SKIP if none seen) | one ACP-SUGGEST-004 citing both, SKIP if none seen live |
| v2 suggestions before resume response: PL N13 (ADVISORY) vs SS N3 (CAPABILITY, before `replay_complete`) | split by window: RESUME-220 before `replay_complete` (MUST `SS:384`), SUGGEST-004 between `replay_complete` and the response (SHOULD NOT) |
| Cursor replay: v1 SS rows 2-3, v2 SS N9-N11, PL N14/N15 | N9 -> CURSOR-002 (replay window), N10 -> CURSOR-001 (reset), stable ids -> CURSOR-004 (both); "replay accepted cursors" row (v1) vs ledger (v2) -> ledger in both (D5b) |
| v2 cursor gate: `cap.session` (PL) vs `inferred:cursors` (SS) | `cap.session` + self-SKIP (registry convention; verdict identical) |
| CURSOR-003 scope: v1 self-skip unless the agent shows cursors vs v2 literal | unresolved between researchers -> D5a |
| Positive fork at a fresh cursor: v1 ADVISORY row vs v2 ledger | ledger in both (agent "can stop accepting at any time"); D5c |
| OPTIONS family: v1 config, v1 init N4/N5, v1 SS row 4, v2 plan-commands-config, v2 init 6, v2 SS N12-N15 | one shared family; init/SS proposals merged into 001/006; SS N15 = OPTIONS-201 |
| OPTIONS-001 restating CONFIG/COMMANDS rules (v2) | extend CONFIG-001/-210, COMMANDS-201, CLIENTCAP-203 (v1: CONFIG-003) payload scans to the `session/options` result instead |
| OPTIONS-003 code: v1 error only vs v2 `-32002` | per version (v2 `error.mdx:52` MUST; v1 SHOULD) |
| OPTIONS-201 (v2): CAPABILITY (plan-commands) vs INFORMATIONAL/drop (SS D7) | unresolved upstream ambiguity -> D6 |
| OPTIONS-011: v2 "add if v1 adopts" | add in both (bucket) |
| AuthAccount.description: separate entry (v1 auth, v2 auth) vs merged (v1 schema, v2 schema) | separate entry in both (schema-stated rule; existing entry is Draft-RFD-only and broader) |
| UnknownStateUpdate extras: separate v1 entry N5 vs folded (v2) | fold in both |
| senderSessionId ledger: PT/PL, SA, RFD reports | one entry per version citing `SA` + PT/PL |
| `transports.mdx:10,...` reason: acceptable (v2 transports) vs TCK choice (scope, v1 core) | reword in both |
| v2 ledger `PL:67; RFD-SA 439-441`: drop RFD (PL) vs relabel (subagents-doc) | keep as Preview secondary (uniqueness phrasing is the RFD's) |
| CANCEL-213: owned by PL and cancellation reports | one change, same recommendation (D3) |
| ERROR-006 `session/options`: v1 "stable only" vs v2 probes unstable already | v2 only |

**Not resolved (routed to decisions):** CURSOR-003 strictness (D5a); OPTIONS-201 meaning (D6); v1 MANDATORY-vacuous vs
`inferred:` for passive rules (D2).

---

## 3. Decisions for the user

**D1. ACP-PLAN-001 (v1).** (a) delete it and add ACP-PLAN-003 (markdown `path` absolute, shared with v2); (b) rewrite
001 in place. Sub-choice: add ACP-PLAN-004 (MANDATORY vacuous shape sweep of the v1 `plan` connection, so a legacy
`file` plan FAILs; a pre-existing gap this update makes visible). **Recommend (a) + PLAN-004.**

**D2. Tier pattern for passive "everything the agent sends satisfies X" rules on Draft-only features** (PLAN-003,
CLIENTCAP-008/-009/-203, SUGGEST-001/-002, CURSOR-001/-002). (a) v1 MANDATORY vacuous (precedent PLAN-001,
CLIENTCAP-004..007), v2 CAPABILITY `cap.session` with SKIP when unobserved (precedent PATCH-205/206, CLIENTCAP-003);
(b) CAPABILITY `inferred:promptSuggestions`/`inferred:cursors` in v1 too. **Recommend (a).**

**D3. Heuristic windows that become verdict-affecting.** ACP-CANCEL-213 retier ADVISORY -> CAPABILITY (upstream SHOULD
-> MUST; `confirm_window` after the cancelled idle); ACP-SUGGEST-003 CAPABILITY with "turn-2 idle + `quiet_period`"
(the MUST has no deadline). (a) CAPABILITY both; (b) keep both ADVISORY. **Recommend (a)**, with the window stated in
the row text. Expect cross-check movement (CAPABILITY FAILs move the verdict, not `--expect`).

**D4. Child-session probes (ACP-SUBAGENT-018/-019, both versions).** They deliberately break the client MUST NOT
(`SA:419,425` v1; `SA:425` v2), justified because the docs define the agent's answer. (a) ADVISORY `-32602` row + CAPABILITY
"never a success" row, probes v1 close/load/delete (gated), v2 resume/close/delete-if-advertised, run after the judged
transcript; (b) only the ADVISORY row; (c) no probe, Deferred ledger. **Recommend (a).**

**D5. Cursor family scope.** (a) CURSOR-003: probe every fork-advertising agent with a fabricated `cursorId` (literal
docs; cursor-unaware fork agents FAIL a CAPABILITY row) vs only agents that announced a cursor. **Recommend literal**
in both versions (the docs bind any agent and forbid the whole-session fallback). (b) "replay accepted cursors" SHOULD:
ledger in both (recommended) vs v1 ADVISORY row with a "never cleared" proxy. (c) positive fork at a fresh cursor:
ledger in both (recommended) vs ADVISORY row.

**D6. ACP-OPTIONS-201 (v2), ambiguous upstream.** `SCO:579` (unsupported value `type` MUST fail `-32602`) vs `SCO:581`
(mismatched `type` or unknown `configId` MUST be ignored): every probe matches both. (a) INFORMATIONAL record; (b)
CAPABILITY on `-32602`; (c) drop. **Recommend (a)** and record the discrepancy (U7).

**D7. Idempotency rows (v2, ACP-PROMPT-212..219).** Tiers: declarative behaviours define "MUST support the key" ->
CAPABILITY `cap.session`; PROMPT-216 (key not echoed) ADVISORY. Scope: include PROMPT-218 (two-process
recognition) and PROMPT-219 (rejected prompt leaves key unrecorded); defer the `$/cancel_request` variant (N9). Expect
SDK agents to FAIL several (verdict movement). **Recommend as stated.**

**D8. New v2 subagent rows.** SUBAGENT-203 (close withdraws child requests; CLOSE-205 machinery), SUBAGENT-204
(cancelled descendants' requests withdrawn; needs the child-cancel driver to hold child permission requests),
SUBAGENT-205 (mirror ordering, CAPABILITY `inferred:subagents` vs ADVISORY), RESUME-225 (re-announce after
no-replay resume, new row vs widening RESUME-209). Deferred ledger for replay-keeps-parent (`SA:482`) and fork remap
(v1 `SA:484-490`, v2 `SA:436-438`). **Recommend all four rows (205 CAPABILITY, 225 a new row) and both Deferred
entries.**

**D9. Test-logic changes to existing subagent rows** (may flip verdicts): v1 SUBAGENT-001 judges post-load traffic
against announcements made during that load (`SA:517`); SUBAGENT-012 counts an incoming `session_message` with no
`senderSessionId` (both); SUBAGENT-016 `unknown` after cancel SKIPs (both) and v2 requires the child's own
`state_update` (mirror judged by -201); SUBAGENT-002 keeps the replay exemption on the Preview RFD's basis (vs the
stricter literal docs reading). **Recommend all as stated.**

**D10. Ledger reasons that rest on a TCK choice.** (a) Promote to rows now where the reports say so: v2 PATCH-213/-214/-215
(diff paths, envelope), PATCH-216 (output after exit), ADDDIRS-204 (unadvertised dirs; breaks a client MUST on purpose);
reword the rest with their real blockers now (v1/v2 unknown error code, custom transports, v1 `TC:250`, auth
`auth.status`/`status_update`, archive persistence half, v2 config fan-out, provider headers, elicitation header).
(b) Entries whose honest fix is a SKIPpable row with no blocker to name (`session/status` and `session/set_title`
`-32002` halves, v1/v2; v2 `session-list.mdx:162` via `set_title`; `:248` unarchive probe; archive load/resume half):
add those rows now (S each), or leave the wording and file a follow-up. **Recommend (a) now, and (b) as a follow-up
slice after this PR.**

**D11. Pre-existing gaps the full audit found** (no row, no entry; not caused by this range): v1 elicitation ledger
backfill (9 rules), v2 meta-patch entries (`extensibility.mdx:154,156`, 5), v1 `agent-plan.mdx:53` fallback MUST, v2
`security.mdx:59` second sentence; row candidates: v1 notices not replayed (`SS:144-148`, `PT:356-357`), compaction id
reuse / terminal status (`PT:465,482`), stop work ASAP (`PT:853`), internal cancel `-32800` (`cancellation.mdx:35-38`),
terminal release (`terminals.mdx:109-110,249`), tool `name` SHOULDs (`TC:14,48-49`), v2 `locations[].path` absolute
(`TC:769-770`), ENUM-201 `category`, v2 P2/P16/P24/P27. (a) ledger-only backfills as one optional slice per version in
this PR, row candidates as follow-ups; (b) everything as follow-ups. **Recommend (a).**

**D12. MCP-over-ACP and transport RFDs (Draft at target, untracked).** (a) MCP-over-ACP rows (~7-8 per version,
shared provider, 2-3 slices) as a follow-up PR; transport RFD out of scope with no ledger entries; (b) include
MCP-over-ACP in this PR. **Recommend (a).** (Pending since the scope research.)

**D13. Accept all recommended defaults** (one approval):
- Re-vendor mechanics (section 5, R-V1/R-V2): vendor with `git show 3ea94133:<path>`; temporary ACP-PLAN-001
  pointer; v2 enum sets updated to the schema; Draft-RFD citations dropped where the docs state the rule.
- ACP-CLIENTCAP-007: docs primary, RFD as Preview secondary, MANDATORY kept.
- Subagent provenance rewrites; tiers unchanged (`inferred:` gates stay; no MANDATORY rises).
- ACP-JSONRPC-003: drop the mcp-over-acp citation (both), add v1 `schema.mdx:285-302`.
- ACP-CONFIG-003 (v1) and CONFIG-001/-210, COMMANDS-201, CLIENTCAP-203 (v2) scan the `session/options` result.
- OPTIONS family: tiers as tabled; OPTIONS-003 code per version; -005 synthetic id fallback; -006 tested on
  `session/new` (+ load/resume unknown-id probe); -009 row; -010 INFORMATIONAL; -011 added in both; v1-only -008.
- ACP-ERROR-006 (v2) probes `session/options` when not advertised.
- Skills: PROMPTCAP-201 extended; COMMANDS-201 also on a `commands.skill` connection; COMMANDS-202 with new
  `inferred:skills`; PROMPTCAP-202; PROMPT-220 ADVISORY; `skill: null` / `commands: {}` / `promptSuggestions: null` /
  `session: {}` extra launches for the gate rows; no row for `Skill.path` absoluteness (no keyword).
- ACP-ENUM-201: add cursor anchor sites and `subject.type` (exclusion from `13c4f7a` has no recorded reason; say if
  you remember one).
- `replay_complete`: RESUME-218..224 tiers as tabled; RESUME-220 judges `state_update`/`notice`/`prompt_suggestions_update`
  only and records the other four kinds (U9); RESUME-221 CAPABILITY; RESUME-222 a row; child rows on `cap.session`;
  delete ledger `SS:228`.
- ACP-RESUME-205 widened to all chunk kinds.
- Repeat-cancel rows TOOLCANCEL/TERMCANCEL-210 (CAPABILITY) and -211 (ADVISORY code).
- ACP-AUTH-211 ADVISORY; ACP-AUTH-004 standalone path loosened.
- Elicitation `$/cancel_request` MUST stays in the ledger (restated, Deferred), no CANCEL-2xx row now.
- ACP-LIST-004 CAPABILITY; ACP-SUBAGENT-020 (v1) ADVISORY; SUBAGENT-004 extension (v2).
- All new ledger entries in section 1; AuthAccount.description as a separate entry; cost entries deleted;
  UnknownStateUpdate extras folded.
- Optional secondary citations skipped (plan-operations on CLIENTCAP-006/PLAN-002); CLIENTCAP-001..003 get `SA:95,157`.
- Stable `slash-commands.mdx` `required`: no change.
- Set `rfd_audit = "3ea94133bb4e7cfdb1105df75660ff83e66acf62"` in both maps when the subagent slices land.

---

## 4. Upstream discrepancies to record (docs win)

Record each in the affected row text or ledger statement; "none" means no TCK artefact depends on it.

| # | discrepancy | where to record |
|---|---|---|
| U1 | v1 `SCO:535,541`, `schema.mdx:1209,5790` and schema descriptions say `sessionCapabilities.configOptions.boolean`; real path `clientCapabilities.session.configOptions.boolean` | ACP-CONFIG-003 / OPTIONS-006 (v1) text |
| U2 | v1 `SCO:475` lists new/load/resume for initial values; `:541`, `SS:456`, schema add fork (v1 and v2) | OPTIONS row text ("checked on `session/new`") |
| U3 | `SessionOptionsRequest.sessionId`: schema load/resume only; v1 `SCO:507` adds fork | none (client-side) |
| U4 | Child requests: `error.mdx` "any other request" gets `-32602` vs RFD-SA `1088-1091` read-only ops keep normal semantics (v1, v2) | ACP-SUBAGENT-018 text (probes are mutating only) |
| U5 | v2 `error.mdx:66-70` Unstable list omits `session/options` `-32002` (schema and `SCO:514` state it) | ACP-OPTIONS-003 (v2) text |
| U6 | v2 schema `New/Fork/ResumeSessionRequest.configOptions` lack the unsupported-`type` `-32602` (`SCO:579`) | OPTIONS-201 text |
| U7 | v2 `SCO:579` vs `:581` (unsupported vs mismatched `type`) | OPTIONS-201 text |
| U8 | Draft RFD `session-options.mdx` says MUST where docs are declarative (`:64`, `:87`, `:151`) | none |
| U9 | v2 `SS:239` (historical config/commands updates need not be replayed) vs `SS:384` (hold them until after `replay_complete`) | ACP-RESUME-220 text |
| U10 | v2 `CreateElicitationRequest` description still SHOULD; `elicitation.mdx:225-228` MUST | elicitation ledger statement |
| U11 | v2 `extensibility.mdx:111` patch-site list omits `cursor_update` (`PL:950` and schema make it one) | none |
| U12 | v2 `AvailableCommand.name` description dropped "without the leading `/`" (`slash-commands.mdx:101` keeps it) | ACP-COMMANDS-201 text |
| U13 | Subagents RFD vs docs: (a) RFD-SA `649-650` replay exemption for `session` content absent from `SA:90,94,517` (v1); (b) RFD-SA `1169-1170` "this section describes v1" vs `1270-1272`; (c) client may answer a child request `cancelled` only after the child's cancelled idle (`SA:419` v2) vs RFD-SA `1260`/`PL:1452`; (d) `SA:427` close withdraws (RFD silent); (e) `SA:488` SHOULD wait vs RFD "may proceed"; (f) `SA:470` MUST vs RFD declarative; (g) `TC:754-756` no keyword vs RFD MUST NOT guess | (a) SUBAGENT-002; (b) RFD-SA `1151-1153` entry; (c) SUBAGENT-204 / mock-client docstring; (d) SUBAGENT-203; (e) RESUME-222; (f) RESUME-224; (g) tools ledger entry |
| U14 | v2 `session-list.mdx:162` SHOULD notify vs Draft `session-set-title.mdx:156` MAY | `:162` ledger reason |
| U15 | v1 plan-operations RFD fallback "for structured checklists" vs `agent-plan.mdx:53` unconditional MUST | none (D11 ledger if backfilled) |
| U16 | `get-auth-state.mdx` "Never contains credentials" (no keyword) vs schema MUST NOT | description ledger entry |
| U17 | v2 `cancellation.mdx:14` "remains optional" beside the MUST at `:42` (about reacting, not sending) | none |
| U18 | v2 RFD-SA links the stable `/protocol/v2/subagents` page; the TCK cites draft | none |

---

## 5. Slice plan

One programmer at a time, one commit per slice (re-vendor: one commit per version). Each slice keeps `uv run pytest`
green and lands its own `test_cli.py` id sets, fixture docstrings and ledger changes. Sizes: S (<300 lines), M, L (>800).

### 5.1 Re-vendor (first, alone; no requirement semantics change)

**R-V1 (v1, M).** Steps in order:
1. With the pin at `3961af94`: `uv run --package spec-tracker spec-impact 3961af94 3ea94133 --version v1 --spec-repo
   /Users/eugene/Documents/JetBrains/projects/agent-client-protocol --fix`. Fix "Needs review" by hand: CLIENTCAP-007
   -> `PT:19-21,44`, `TC:358`; SUBAGENT-011/-012 -> `PT:108-113`; ledger RFD-SA `576-577` -> `584-585`. Leave ACP-PLAN-001
   and the cost entry as written (deleted in later slices; their lines still exist in the target files).
2. Vendor `schema/v1/schema.unstable.json` and `meta.unstable.json` with `git -C ../agent-client-protocol-2 show
   3ea94133:<path>` (never `cp`: that tree is at `6ace4f6a`). Update `VENDORED.md` (commit, date) and `SCHEMA_REVISION`.
3. Minimal edits for green: ACP-PLAN-001's `#/$defs/PlanFile` no longer resolves -> temporarily cite
   `schema/v1/schema.unstable.json#/$defs/PlanUpdateContent`; leave row text, test and fixtures (per the v1 schema report nothing
   validates the `plan` connection, so `conforming_full.py`'s now schema-invalid `file` plan should not FAIL; confirm
   with the full suite and escalate if it does). Run `tests/v1/test_registry.py`,
   `test_validation.py` and spec-tracker tests with `--spec-repo`.
4. Stage labels: subagents -> `(Preview RFD)` in rows, ledger, code strings; JSONRPC-003 drops `mcp-over-acp`, adds
   `schema.mdx:285-302`. Hand fixes of section 1.3 (v1 items).

**R-V2 (v2, L, mechanical).** Same steps for v2 (`schema.unstable.json`, `meta.unstable.json`; v2 also vendors only
the unstable files). Needs review: the 33 rows / 10 entries in 1.2, using the reports' target lines; leave ledger
`agent-plan.mdx:119` and the cost entry for later slices. Minimal edits for green:
`tests/v2/test_validation.py::test_enum_sets_match_the_schema` fails on three sets; update `protocol.py`
`SESSION_UPDATE_KIND` (+`cursor_update`, `prompt_suggestions_update`, `replay_complete`), `PLAN_CONTENT_TYPE`
(-`file`), `AVAILABLE_COMMAND_TYPE` (+`skill`). This keeps ENUM-201's rule ("defined values or `_`") and only follows
the vendored definition; say in the commit that conforming agents emitting the new kinds stop FAILing and `file` plans
start FAILing ENUM-201 (no v2 fixture sends one). No other v2 pointer breaks (0 of 158). Drop the Draft-RFD citations
listed in 1.3, relabel subagents, ACP-META-203 literal, hand fixes (v2 items).

### 5.2 Area slices (suggested order)

| # | slice | files (main) | rows / ledger | fixtures | size |
|---|---|---|---|---|---|
| 1 | V1-PLAN | v1 `requirements.py`, `test_plan.py`, `_helpers.py` (drop `is_absolute_uri`), `tests/v1/test_plan_uri.py` (rename), `test_cli.py`, `test_registry.py` | -PLAN-001; +PLAN-003, +PLAN-004 (D1) | +2, edit `conforming_full.py`, `plan_turn_never_ends.py`; delete `emits_relative_plan_file_uri.py` | M |
| 2 | V2-PLAN | v2 `requirements.py`, `test_patches.py`, `v2.toml` | +PLAN-003; ledger -`agent-plan.mdx:119` | +1, base abs path | S |
| 3 | V1-GATES+SUGGEST | `test_client_capabilities.py`, new `test_prompt_suggestions.py` | +CLIENTCAP-008/-009, +SUGGEST-001..004; ledger +2 | +6 | M |
| 4 | V2-GATES | `test_client_capabilities.py` | +CLIENTCAP-008, +CLIENTCAP-203 | +2 | S |
| 5 | V2-SUGGEST | new `test_prompt_suggestions.py` | +SUGGEST-001..004; ledger +2 | +4 | M |
| 6 | V1-CURSOR | new `test_cursors.py` | +CURSOR-001..004; ledger +2 (`PT:705-709`, `SS:154`) | +4 | M |
| 7 | V2-CURSOR | new `test_cursors.py`, `open_enums.py`, `protocol.py`, `tests/v2/test_open_enums.py` | +CURSOR-001..004; ENUM-201 anchor sites; ledger +4 | +4 | M |
| 8 | V1-OPT1 (method) | `test_session_config.py` (or new `test_session_options.py`), conforming fixture | +OPTIONS-001/-002/-003/-009; CONFIG-003 ext | +3, conforming advertises `options` | M |
| 9 | V1-OPT2 (initial values) | same | +OPTIONS-004..008/-010/-011; ledger +5 | +4 | M |
| 10 | V2-OPT1 (method) | same (v2), `test_errors.py` | +OPTIONS-001/-002/-003/-009; ERROR-006 ext; CONFIG/COMMANDS payload ext | +3 | M |
| 11 | V2-OPT2 (initial values) | same | +OPTIONS-004..007/-010/-011/-201; ledger +8 | +3 | M |
| 12 | V2-SKILL | `test_slash_commands.py`, `test_prompt_capabilities.py`, `test_prompt.py`, `protocol.py` (walker) | COMMANDS-201 change, PROMPTCAP-201 ext; +COMMANDS-202, +PROMPTCAP-202, +PROMPT-220; ledger +4; `docs/requirements.md` adds `inferred:skills` | +3 | M |
| 13 | V2-IDEM | new `test_idempotency.py`, `_helpers.py` | +PROMPT-212..219; ledger +3 | +5 | L |
| 14 | V2-REPLAY | `test_session_capabilities.py`, `_helpers.py` (`replayFrom: null`), `_base.py` | +RESUME-218..222; RESUME-205 widened; ledger +3, -`SS:228` | +7, `_base.py` emits `replay_complete` | L |
| 15 | V2-CAN | `test_cancel.py`, `v2.toml` | CANCEL-213 retier (+`test_cli.py:2176` rename, exit code), CANCEL-209 note; elicitation entries restated/reworded | 0 | S |
| 16 | V2-TOOL | `test_patches.py`, `test_item_controls.py`, `open_enums.py`, `tests/v2/test_open_enums.py` | +PATCH-213..216, +TOOLCANCEL/TERMCANCEL-210/-211; ENUM-201 `subject.type`; ledger +3, -2 | +6 | L |
| 17 | V2-AUTH+DIRS | `test_authentication.py`, `test_session_capabilities.py` | +AUTH-211, AUTH-004 change, +ADDDIRS-204; ledger +1 (description), -`SS:443` | +2 | S |
| 18 | V1-SA1 (provenance) | v1 `requirements.py`, `v1.toml`, docstrings | text/citations of CLIENTCAP-007, SUBAGENT-*; ledger +15 subagent, +2 tools, -1 cost, rewrites | 0 | M |
| 19 | V1-SA2 (test logic) | `_subagents_connection.py`, `_child_cancel.py`, `_helpers.py`, `tests/v1/test_subagent_helpers.py` | SUBAGENT-001/-012/-016 changes (D9) | edit 2-3 | M |
| 20 | V1-SA3 (new rows) | `test_subagents.py`, `_subagents_connection.py` (post-judging probe phase) | +SUBAGENT-018/-019/-020, +LIST-004 | +4 | M |
| 21 | V2-SA1 (provenance) | v2 `requirements.py`, `v2.toml`, docstrings | as V1-SA1 + RESUME-002/-209, TOOL/TERMCANCEL-203; ledger +13, -1 cost, rewrites | 0 | M |
| 22 | V2-SA2 (test logic) | `test_subagents.py`, `_child_cancel.py`, `_helpers.py` | SUBAGENT-012/-016 changes | edit 2 | M |
| 23 | V2-SA3 (probes, list, ordering) | `test_subagents.py` | +SUBAGENT-018/-019/-205, +LIST-004, SUBAGENT-004 ext | +4 | M |
| 24 | V2-SA4 (child replay + withdrawal) | `test_session_capabilities.py`, `_child_cancel.py`, `run_prompt` hold mode | +RESUME-223/-224/-225, +SUBAGENT-203/-204 | +5, edit replay fixtures | L |
| 25 | LEDGER-HYGIENE v1 | `v1.toml` | D10 rewords (v1); +1 AuthAccount.description entry | 0 | S |
| 26 | LEDGER-HYGIENE v2 | `v2.toml` | D10 rewords (v2) | 0 | S |
| 27 | BACKFILL (optional, D11) | `v1.toml`, `v2.toml` | v1 elicitation 9 + `agent-plan.mdx:53`; v2 meta-patch 5 + `security.mdx:59` | 0 | S |
| 28 | DOCS + rfd_audit | `docs/requirements.md`, `docs/spec-updates.md`, both maps | "Active > v2" stage wording removed (no Active stage upstream); `inferred:` list (`skills`, `promptSuggestions`); `rfd_audit` set in both maps; core_doc `code` lists gain new modules | 0 | S |

Order rationale: plan first (clears R-V1's temporary pointer); gates before the features that reuse their connections;
options and skills before replay (V2-REPLAY touches `_base.py`, which most v2 fixtures inherit); subagent slices last
because V2-SA4 depends on `replay_complete` (slice 14) and CANCEL-213 (slice 15); ledger-only slices at the end.

### 5.3 Id alignment (after all area slices)

Researcher inventory, then user approval per rename, then one programmer slice. Expected shared ids to confirm:
PLAN-003, CLIENTCAP-008, SUGGEST-001..004, CURSOR-001..004, OPTIONS-001..007/-009/-010/-011, SUBAGENT-018/-019,
LIST-004. Check: v1-only numbers (CLIENTCAP-009, PLAN-004, OPTIONS-008, SUBAGENT-020) do not collide with a v2
meaning; whether SUBAGENT-020 restates a rule v2 judges under ENUM-201/STATE-203 (borderline); whether v2
CLIENTCAP-203/COMMANDS-202/PROMPTCAP-202 have v1 counterparts (no: v1 has no skills). Apply renames in registries,
markers, `test_cli.py`/`test_registry.py` sets, fixture docstrings, `cross-check/run.sh`, `.github/workflows/ci.yml`.

### 5.4 Cross-check refresh (last)

- Check whether newer SDK tags (Rust > v5.1.0, Python > 1.0.0) target schema 1.32 / v2 alpha.16; bump per
  `cross-check/README.md` if so.
- `--expect` is MANDATORY-only. New MANDATORY rows are vacuous for agents that never emit the feature, and
  ACP-PLAN-001 leaves no expect line, so the expect sets should not move; re-observe anyway.
- Expected CAPABILITY movement (comment block, verdict): SDK agents predating `replay_complete` FAIL RESUME-218 (and
  -223 with children); agents ignoring `idempotencyKey` FAIL PROMPT-212..219; agents not sending `$/cancel_request`
  FAIL CANCEL-213; fork agents ignoring `cursorId` FAIL CURSOR-003 (if D5a literal); `file` plans FAIL ENUM-201.
  `python_v2_agent.py` (repo fixture) may need updating if it is meant to stay near-conformant.
- Never bake a suspected TCK false positive into `--expect`.

### 5.5 Deliberately left out (follow-ups)

- MCP-over-ACP rows (D12), and the transport RFD (out of scope, no ledger).
- D10(b) rows: `session/status`/`session/set_title` `-32002`, `session/list` `session_info_update` via `set_title`,
  unarchive `-32002` probe, archive load/resume half.
- D11 row candidates (pre-existing gaps listed there), `ACP-EXT-204` probe under `capabilities.session`.
- Elicitation `$/cancel_request` CANCEL-2xx row and the MCP-stub elicitation trigger (unblocks several elicitation entries).
- v1 SUBAGENT-001 coverage of `session/resume` (`SA:517`); v1 SUBAGENT-004 "later `session/new`" extension.
- `auth/status_update` ADVISORY row (`--auth-method` flow).
- Prompt-suggestion opt-in branch (`image`/`audio`/`embeddedContext` vs agent `promptCapabilities`), both versions.
- Idempotency `$/cancel_request` variant (N9).
- `validation.py` docstring note that `x-deserialize-default-on-error` is deliberately not honoured.
- Next update: checkout HEAD `6ace4f6a` adds `Diff.changes` `minItems: 1` + MUST (extends PATCH-213).

---

## 6. Totals

| | v1 | v2 |
|---|---|---|
| rows now | 108 (32 MANDATORY, 42 CAPABILITY, 30 ADVISORY, 4 INFORMATIONAL) | 233 (34 / 139 / 50 / 10) |
| removed | 1 (PLAN-001) | 0 |
| new (recommended defaults) | 27 | 57 |
| rows after | **134** (D1 without PLAN-004: 133; D4(b): -1 per version) | **290** (D7 minimal -2; D8 minimal -4; D10(a) rows -5) |
| changed text/gate/test | ~15 | ~30 incl. 1 retier |
| citation-only (remap/relabel) | 53 rows, 35 entries | 166 rows, 73 entries |
| ledger now -> after | 57 -> 83 (+27, -1; +10 with D11 backfill) | 110 -> 145 (+41, -6; +6 with D11 backfill) |
| new fixtures (estimate) | ~23 (+4 edited) | ~49 (+`_base.py` and ~6 edited) |
| slices | R-V1, 9 v1 area slices, shared docs/backfill | R-V2, 17 v2 area slices |

Total: 2 re-vendor + 28 area slices (one optional) + id alignment + cross-check refresh.
