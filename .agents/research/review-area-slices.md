# Review: milestone 2 (area slices), 7254513..c80a543

Scope: every non-`chore: state:` commit in the range (31 commits, ~15k lines). Spec lines were checked with
`git -C ../agent-client-protocol-2 show 3ea94133:<path>`. Abbreviations follow `plan-consolidated.md`: SA = the
version's `subagents.mdx`, PL / PT = prompt-lifecycle / prompt-turn, SS = session-setup, SCO = session-config-options,
TC = tool-calls.

**Runs**
- Full suite at c80a543: `uv run pytest -q`, **1189 passed** in 608 s. Other review processes were running at the same time and nothing flaked.
- Narrow runs: v1 CLI and subagent helpers, 164 passed.
- `acp-tck` against `conforming_full` and every new or edited fixture in both versions. FAIL sets match the fixture docstrings and the `test_cli.py` sets, except where noted below.

**Counts:** 0 blocker, 10 should-fix, 18 nit.

---

## Should-fix (most severe first)

### S1. v2 ACP-SUBAGENT-205: a missing mirror (ADVISORY 201) also FAILs CAPABILITY 205
- **Where:** `src/tck/v2/conformance/_helpers.py:1186-1194` (`child_state_order`).
- **Spec:** SA:350-351.
- **Defect:** when one mirror is missing, the alignment scans forward past mirrors that don't match. The own state then pairs with a much later mirror of the same state, and the next pair is reported out of order.
- **Scenario:**
  - own states: `running, requires_action, idle, requires_action, idle`
  - mirrors: `running, idle, requires_action, idle` (the first `requires_action` mirror is missing)
  - 205 FAILs with "a copy of its 'requires_action' state arrived after ... 'idle'".
  - That contradicts the row text ("a state with no counterpart is ACP-SUBAGENT-201's and is not judged here"). A SHOULD defect now moves the verdict.
- **Fix:** on a mismatch, don't advance the mirror cursor. Treat the own state as unaligned, or stop pairing after the first unaligned state. Add a unit test for this sequence.
- **Confidence:** confirmed by running (a fork reproduced it) and by reading.

### S2. ACP-CURSOR-001 (both versions): the replay reset also judges live updates after the replay
- **Where:** `src/tck/v2/conformance/test_cursors.py:159-178,202-218` and `src/tck/v1/conformance/test_cursors.py:214-226`.
- **Spec:**
  - v2: PL:949 (the anchor MUST applies to the first update of a `cursorId`); PL:1024-1027 (SHOULD clear `capabilities` when the agent stops accepting); SS:339 (replay sends only cursors still accepted).
  - v1: PT:619, PT:704-709, SS:154.
- **Defect:** `_walk` resets the anchor map at the resume or load request. Every later `cursor_update` is then judged as a "first update", not only the replayed ones.
- **Scenario:**
  1. Cursor X is anchored live.
  2. A full replay leaves X out: it is no longer accepted (allowed), or it was simply not replayed (a SHOULD the ledger calls not observable).
  3. After the response the agent sends `cursor_update {cursorId: X, capabilities: null}` without an anchor, as PL:1027 / PT:707-708 suggest.
  4. CURSOR-001 FAILs. That is CAPABILITY in v2 and **MANDATORY** in v1.
  - The v1 flow (load 2 and the fork come straight after load 1) makes this nearly unreachable today. The v2 resume flow is similar.
- **Fix:** keep the reset, but after a reset demand an anchor only for a `cursorId` whose first post-reset update falls inside the replay window (request to `replay_complete` / response). Or never flag an anchor-less update for a cursor anchored before the reset.
- **Confidence:** plausible (from reading).

### S3. v1 ACP-OPTIONS-008 also flags `config_option_update`, which overlaps -007
- **Where:** `src/tck/v1/conformance/test_initial_config.py:292-297`, row text `src/tck/v1/requirements.py:1006`, and `tests/v1/test_cli.py` (expects `options_notifies_initial.py` to FAIL both 007 and 008).
- **Spec:** v1 SCO:567 (no `config_option_update`) versus SCO:568 ("**other** `session/update` notifications", with a fallback notice or `current_mode_update` as examples).
- **Scenario:** one early `config_option_update` before the `session/new` response FAILs two ADVISORY rows. Confirmed by running `options_notifies_initial.py`.
- **Fix:**
  - Have 008 judge every kind except `config_option_update`, not only `current_mode_update`.
  - `options_notifies_initial.py` then FAILs only 007; update its docstring and the CLI set.
  - `options_announces_mode.py` already isolates 008.
- **Confidence:** confirmed by running and reading.

### S4. v2 ACP-RESUME-225 (and -223): child traffic already in flight when the resume is sent counts against the resume
- **Where:** `src/tck/v2/conformance/test_session_capabilities.py:1055-1086` (judging starts at `start = len(agent.transcript)`); same pattern in RESUME-223 (`:978` ff.); `_helpers.py:1284` `unannounced_resumed_child_traffic`.
- **Spec:** SA:469; SS:55 ("Ongoing work continues" when resuming a session already active on the connection).
- **Scenario:**
  1. `obtain_resumable_session` route 1 resumes the session just created, on the same connection, so a background child of the subagent turn may still be running.
  2. `drain_quiet` reads for a fixed period; it does not wait for silence.
  3. A child `session/update` written before the agent read `session/resume` is read after `start` and FAILs as "not re-announced".
  - For RESUME-223, a child `state_update` in flight before that child's `replay_complete` is flagged the same way.
- **Fix:** start judging at the agent's first message of the resume exchange (its first update for the resumed session, or the response), or exclude children that were live during the pre-resume quiet period.
- **Confidence:** plausible (from reading).

### S5. v2 ACP-OPTIONS-002: late setup traffic, or lazy persistence of the closed session, is blamed on `session/options`
- **Where:** `src/tck/v2/conformance/test_session_options.py:116-140`.
- **Spec:** SCO:551; SS:48.
- **Scenario A:**
  - The test runs `session/new`, `session/close` and `session/list` back to back, without draining before `start`. `_updates_since` counts any `session/update`, whatever the session.
  - Agents that push `available_commands_update` asynchronously after `session/new` (a common adapter pattern) can land it after the `session/options` request. That FAILs a CAPABILITY row.
- **Scenario B:** an agent that persists the never-prompted, closed session lazily shows it only in the second listing, so the TCK's own `session_id` lands in `created`.
- **Fix:** `drain_quiet` after `close_session` and before `before`; drop `session_id` from `created`. Optionally judge only updates that name no session, or the closed one.
- **Confidence:** plausible.

### S6. v2 ACP-RESUME-221: the row text claims "replays nothing", but the test never checks it
- **Where:** `src/tck/v2/requirements.py:2553`; `src/tck/v2/conformance/test_session_capabilities.py:903-931`.
- **Spec:** SS:406 ("replays nothing and does not send `replay_complete`"), SS:382.
- **Defect:** the test runs on a session with no history (no `_add_history`) and looks only for `replay_complete`. RESUME-207/208 judge only the error code.
- **Scenario:** an agent that replays the full history and then answers `-32602` without `replay_complete` PASSes a row whose text says it is judged.
- **Fix:** `_add_history` first and FAIL on any update for the session before a `-32602`. Otherwise drop "replays nothing" from the text and ledger that half.
- **Confidence:** confirmed by reading.

### S7. `_child_cancel.py` (both versions): `target_unknown` is never cleared, so ACP-SUBAGENT-016 SKIPs where it should FAIL
- **Where:** `src/tck/v1/conformance/_child_cancel.py:142,195`; `src/tck/v2/conformance/_child_cancel.py:258,393`.
- **Spec:** v1 SA:413 / v2 SA:363 ("A later `running`, `requires_action`, or `idle` replaces `unknown`"); v1 SA:449-450, v2 SA:400-401.
- **Scenario:** after the cancel the child reports `unknown`, then `running` again, and never confirms. The outcome is `unobservable` (SKIP) instead of `unconfirmed` (FAIL), a false negative on a CAPABILITY row.
- **Fix:** reset `target_unknown` on a later `running`/`requires_action`, and add a helper or CLI case.
- **Confidence:** confirmed by reading.

### S8. v1 ACP-SUBAGENT-002 changed scope silently with the D9 post-load rescope
- **Where:** `src/tck/v1/conformance/_helpers.py:748-775` (`_wire_messages_indexed`), used by `session_content_references` (`:869-918`); row text `src/tck/v1/requirements.py:1456`.
- **Spec:** SA:90,94,517. These support the stricter behaviour, so the behaviour itself is not wrong.
- **Defect:** after a successful `session/load`, only announcements made during that load count, for 002 as well. No row text, commit message or D9 item records the change; D9 lists only 001/012/016.
- **Scenario:** a child is announced in the turn, the load replays no announcement, and a live `tool_call_update` then references the child. That FAILed nothing before 2800a5a and FAILs 002 now. No fixture or test pins the behaviour.
- **Fix:** state the post-load scope in 002's text and add a helper unit test.
- **Confidence:** confirmed by reading.

### S9. v2 ledger `subagents.mdx:482`: the Deferred reason names a blocker this range removed
- **Where:** `spec-tracker/maps/v2.toml:922-924`.
- **Spec:** SA:482.
- **Defect:**
  - The reason says the resume tests keep no live child tree and that "it would be unblocked by a resume step that reuses the subagents connection's announced children".
  - 4dfbf16 added exactly that. RESUME-223/225 run the subagent prompt and then resume, and on route 1 the announced tree is in `agent.transcript`.
  - The entry now rests on a TCK choice.
- **Fix:** reword to the remaining real limit (routes 2/3 carry no tree), or add a follow-up row that compares replayed announcements with the pre-resume parents on route 1.
- **Confidence:** plausible.

### S10. v2 ledger `session-list.mdx:162`: the reason argues from the losing source
- **Where:** `spec-tracker/maps/v2.toml:565-567` (reworded in 6fe8518).
- **Spec:** `session-list.mdx:162` (docs SHOULD, which covers changes requested through `session/set_title`) against Draft `rfds/session-set-title.mdx:156` (MAY). This is U14, and the plan's rule is "docs win".
- **Defect:**
  - The reason says a missing notification "proves nothing" because of the RFD MAY.
  - Under the docs, a `set_title` on an advertising agent followed by no `session_info_update` is an observable SHOULD miss.
  - Plan D10(b) lists exactly this as a follow-up row.
- **Fix:** reword to "Deferred: observable via `session/set_title` when advertised; SKIPpable follow-up row (D10b). The Draft RFD says MAY (U14)."
- **Confidence:** confirmed by reading.

---

## Nits

**v1**
- **N1.** `src/tck/v1/conformance/test_session_options.py:141-145` (OPTIONS-003) and `:179-183` (OPTIONS-009) leave `sessionCapabilities.fork` out of the gate and text.
  - v1 SCO:507 allows `sessionId` with load, resume **or fork**.
  - An options+fork-only agent gets a false SKIP, no false verdict.
  - Fix: add fork, or cite U3 if the schema-only gate is deliberate.
- **N2.** `src/tck/v1/conformance/test_cursors.py:97-105,320-330` (CURSOR-004): when the second `session/load` fails, the row PASSes (nothing is compared) instead of SKIPping as its docstring says.
  - Fix: count only successful loads (`_successful_load_starts`).
- **N3.** `src/tck/v1/conformance/test_session_config.py:248-255` (CONFIG-003, MANDATORY): an `AgentTimeout` on the new `session/options` call FAILs the row.
  - The existing load and resume calls already behave this way, so accepting it is fine. Otherwise catch the timeout.
- **N4.** `_child_cancel.py` v1 `_settle`: `unknown`, then a later non-cancelled `idle`, FAILs 016.
  - Arguably conforming: the work ended while it was out of sight (SA:415).
  - Fix: settle it as `unobservable`, or say so in the row text.
- **N5.** `src/tck/v1/conformance/test_subagents.py:302` (SUBAGENT-018): the SKIP message says no probe method was advertised. It also fires when the agent stopped answering during the `session/list` phase.

**v2**
- **N6.** `src/tck/v2/conformance/test_initial_config.py:166-170` (OPTIONS-005) falls back to a synthetic id when the agent lists only boolean options.
  - With an unknown id, SCO:580 (duplicate, `-32602`) and SCO:581 (unknown, MUST ignore) both apply.
  - Fix: try a real boolean option at its current value first.
- **N7.** No fixture isolates PROMPT-214 (`tests/v2/test_cli.py`, `test_idempotency_defect_fixtures_fail_only_their_rows`): `retry_inserts_second_message.py` FAILs 212 and 214.
  - The `-32602`-then-forget branch of 214 is not exercised.
- **N8.** `src/tck/v2/conformance/_helpers.py:863` `git_patch_paths` splits on `\n`, so a CRLF patch leaves `\r` on the path. A Windows agent would false-FAIL PATCH-214.
  - Fix: `removesuffix("\r")`.
- **N9.** `_helpers.py:3251-3257` `_RepeatProbe._target` can send a second request to an item the `_StaleProbe` already probed. That contradicts the "no item is asked twice" docstring; no verdict changes.
- **N10.** `tests/fixtures/agents/v2/cancel_waits_for_permission_answer.py:4` still says "SHOULD send `$/cancel_request`". It is a MUST since a8c38d8 (PL:1452).
- **N11.** SUBAGENT-204, slow stop (`test_subagent_controls.py:196`, `_child_cancel.py:380-392`): a child that takes more than `timeout / 2` to stop legitimately still holds its request. The release is then followed by the confirmation, which gives 016 PASS + 204 FAIL "waited".
  - The FAIL count is unchanged against pre-SA4, but the FAIL is attributed to the wrong row.
  - Fix: count `waited` only when the confirmation comes within `quiet_period` of the release.
- **N12.** SUBAGENT-204 requires every held request of a stopped child to be withdrawn. PL:1452 exempts requests for work in the latest `background` list.
  - Plausible false FAIL for a child whose request concerns its own background item.
  - Fix: exclude requests whose `subject` names such an item.
- **N13.** Two row texts are stale:
  - ACP-SUBAGENT-016 (`requirements.py:673`) does not mention the post-release `timeout / 2` extension.
  - ACP-RESUME-225 (`:2633`) says "every `session/update` and agent request carrying a child's `sessionId`", but only `params.sessionId` is judged.
- **N14.** ACP-SUBAGENT-204's gate label `inferred:subagentCancel` (`requirements.py:843`) is narrower than what it judges.
  - It also covers parent-cascade stops of children without `cancel`, which is `inferred:subagents`, like 202.
  - Documentation only; no verdict effect.

**Both versions / tooling**
- **N15.** Cursor fixtures anchor only to messages. The v1 fixtures use only `agent_message`/`after`; the v2 ones use only `user_message`/`before`.
  - The `tool_call`, `compaction` and `session_message` mappings in `_ENTITY_OF_UPDATE`, and the other `position`, are never exercised.
  - Reading against the schema, the maps are correct today.
  - Fix: add a walker unit test with a tool-call anchor and a compaction anchor per version.
- **N16.** Initial `configOptions` are never probed on `session/fork` (OPTIONS-004..006, v1 -008). v1 SCO:541,559,568, SS:456; v2 SCO:555,572.
  - False negative only; the row texts say `session/new` (U2).
  - Fix: a follow-up repeating the probes on fork when fork is advertised.
- **N17.** `spec-tracker/maps/v1.toml:24` and `v2.toml:25` header comment says `rfd_audit` is "absent until the first full RFD audit". Both maps now set it.
  - Fix: "set by the update process after each full RFD audit".
- **N18.** The two CLI tests that failed under load (`test_mcp_unsupported_transport_fixtures_fail_mcp_203_only`, `test_permission_before_requires_action_judges_cancel_while_blocked`): no real race found. Details are under the known items.
  - If one fails again, keep its stdout and the failing ids.

---

## Verdicts on the known items

| Item | Verdict |
|---|---|
| v1 OPTIONS-008 also flags `config_option_update` | **Real defect, S3.** "Other" in SCO:568 excludes the kind -007 judges; the CLI test bakes in the double FAIL. |
| `session/fork` initial entries not probed (both) | **Acceptable coverage gap, N16.** Follows D13 and U2; the texts are honest. Track as a follow-up; no ledger entry is needed because the rows cite the lines. |
| CURSOR-001 requires an anchor on the first replayed update | **Sound for replayed updates.** SS:154/SS:339 say a replayed update carries the anchor "like a first update". SS:156/SS:341 say a full replay rebuilds the cursors, so the client can't place one without it. Applying PL:949 / PT:619 to the rebuilt cursor is a fair inference (MANDATORY in v1 is OK). **Flaw:** the reset also judges post-replay live updates (S2). |
| Cursor fixtures exercise only message anchors | **True, low risk, N15.** The maps are correct against the schema, but untested. |
| SUBAGENT-204 gate narrower than what it judges | **Labelling nit, N14.** It also judges parent-cascade stops (`inferred:subagents`). No verdict effect, since inferred gates are documentation-only. D8 fixed the gate, so the orchestrator decides between a relabel and a sentence in the text. |
| 016 PASS + 204 FAIL possible with held child requests | **Intended attribution** (one defect, one row), shown by `child_cancel_waits_for_permission.py`. The exception is a legitimately slow stop (N11). |
| 202 may SKIP when the parent waits on a held child request | **Acceptable.** SKIP, never FAIL. The driver's added quiet period covers `run_prompt`'s grace. |
| RESUME-225 judges only `params.sessionId` traffic | **Acceptable narrowing** (false negatives only). Fix the text (N13). The real risk is the in-flight race (S4). |
| RESUME-224 doesn't judge update fields | **Correct.** SA:471 lets `capabilities` be omitted, and SA:470's current-state report is a SHOULD "when it can determine it". |
| `CLI_SUBPROCESS_TIMEOUT` 60 -> 120 s | **Fine.** `conforming_full` really takes about 61 s; the cap only affects how quickly a hung CLI run is reported. |
| Two CLI tests flaked under full-suite load | **No race found.** `permission_before_requires_action.py` sends `$/cancel_request` synchronously before its idle. The hold path of `run_prompt` reduces to the old condition without child holds. The MCP fixtures only answer setup. **Reproduction:** none. Each test alone passes (about 50 s). An 81-test CLI subset with `-n 12` passed 3 times. `-n 4` with 14 CPU hogs passed. My full run (1189) passed while other review processes were running. **Likely cause:** these CLI runs use `--timeout 1 --startup-timeout 1`, and this range made their `-k` selections much larger. `-k test_session` and the tool-call `-k` now pull in the OPTIONS, RESUME-218..225 and SUGGEST tests, so more 1 s waits are exposed to load. **Fix if it recurs:** a per-invocation `--timeout 2` for those heavy selections. |
| c80a543: new modules not in core_doc `code` lists | **Consistent** with the user's decision: their sections are not core. |
| c80a543: stale `rfd_audit` header comment | **Nit, N17.** |
| V2-SA3: error.mdx cite `:58` vs plan `:57` | **`:58` is right** ("Agents SHOULD reject any other request that names a child with `-32602`"); the plan was off by one. |
| V2-SA3: probes share the subagents connection | **Fine.** They run after the judged transcript is copied, `close` goes last, and they stop at the first unanswered probe. 018 judges only the code and 019 only success. |

---

## Checked and found fine

- **Tiers and gates** for every new or changed row follow D1-D13 and the plan tables:
  - PLAN-003/004 (v1 MANDATORY vacuous, v2 `cap.session`), CLIENTCAP-008/009/203, SUGGEST-001..004, CURSOR-001..004 (D5a literal).
  - OPTIONS-001..011/-201 (D6 INFORMATIONAL; U1, U5-U7 recorded), COMMANDS-201/202, PROMPTCAP-201/202, PROMPT-212..220 (D7), RESUME-205/218..225.
  - CANCEL-213 retier (D3), PATCH-213..216, TOOL/TERMCANCEL-210/211, AUTH-004/211, ADDDIRS-204.
  - SUBAGENT-001/002/011/012/016/018/019/020/203/204/205, LIST-004 (v1 `sessionCapabilities.list`, v2 `cap.session`).
- **Citations:** every new or changed row and ledger line the forks and I checked matches its text at 3ea94133 (lists in the per-area notes). That includes the v2 ledger rewords and the backfill I checked myself: `transports.mdx:10,71,73`, `error.mdx:38`, `session-list.mdx:162,248-249`, `SA:263`, `TC:753-756` with RFD 655-661, `SCO:390,585`, `security.mdx:59,81`, `extensibility.mdx:116,154,156`, `SS:56,300,330-335`.
- **RFD stages:** at 3ea94133 `docs.json` has only `Preview` (subagents, plan-operations), with `rfds/v2/*` under "Draft > v2". The c80a543 wording, `TRACKED_STAGES=("Preview",)`, the legacy-`Active` read and the new spec-tracker tests match.
- **D10 rewords** (v1 and v2) replace the TCK-choice reasons with real blockers, apart from S9/S10. The `session/status` and `set_title` entries state openly that their observable halves are left to follow-up rows (D10b).
- **D11 backfill:** v1 elicitation (9) plus `agent-plan:53`, and v2 meta-patch (5) plus `security:59`. Reasons are sound.
- **Negative fixtures:** each FAILs only its row on unscoped runs, except S3 (007+008) and the documented inherent overlaps (`resume_replays_state_updates` 212+220, `retry_inserts_second_message` 212+214). Positive fixtures (`conforming_full`, `exposes_subagent_full`, `cancellable_subagent_asks`, `resume_lists_background_subagent`) are CONFORMANT.
- **Harness:**
  - The probe phases run after the judged snapshot.
  - In hold mode, the `answered_on` check-then-set prevents a double answer between the driver release and `run_prompt`'s `$/cancel_request` handler.
  - SUBAGENT-203 accounts for requests answered at turn end.
  - The idempotency send-and-collect waits for the response plus a quiet period.
  - The `replay_complete` slicing is per session.
  - The `git_patch` parser handles quoting, TAB, rename, binary and `\ No newline`.
- **Common plugin `revokes` change:** several tests run last in collection order; v1 is unaffected (it has one). AUTH-211 SKIPs when the re-login fails, as `docs/writing-tests.md` now says.
- **DEL204-FIX:** the fixture withdraws the pending permission before answering delete, and a new CLI test covers the run without `__hang__`.
- **Isolation:** no `import tck.v1` in v2 code or the reverse (only docstring mentions). No `.agents/` references in `src/`, `tests/`, `spec-tracker/` or `cross-check/`. The `.agents/skills/*` edits in c80a543 are skill definitions, not code.
