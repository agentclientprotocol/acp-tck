# Review: M5 (v2 background-work backfill)

**Range:** `5e5941b^..d090970`, product commits 5e5941b (S5.1), 2978360 (S5.2), d090970 (S5.3). The
`chore: record` commits and the v1 commit a6379b1 (S3.2) were skipped.
**Goal:** gaps G1-G8 in `.agents/research/backfill-v2-background-work.md`. Decisions from `.agents/state.md`.
**Spec:** agent-client-protocol @ 3961af94 (`git show`): `prompt-lifecycle.mdx`, `tool-calls.mdx`, `session-setup.mdx`,
`schema/v2/schema.json`.
**Worktree:** detached at d090970 (`../acp-tck-review-m5`). Throwaway probe fixtures were written to `/tmp/m5review/`,
outside the repo.

**Counts:** 1 blocker, 4 should-fix, 6 nits.

## Blocker

### B1. A conforming agent with a long streaming turn FAILs all four item-cancel rows
- **Where:** `src/tck/v2/conformance/_helpers.py:2537-2545` (`drive_item_cancel`), with
  `src/tck/v2/conformance/test_item_controls.py:45-61` (`_item_cancel_run` caches the error).
- **Defect:** the driver sends its own `session/cancel` only once every probe is settled *and* the transcript has
  been silent for `max(quiet_period, timeout/4)`. But `run_prompt` gets the same `timeout` as an **overall**
  deadline from the moment the prompt is sent (`overall_deadline = loop.time() + timeout`, `_helpers.py:~1711`).
  An `AgentTimeout` raised while `cancel_sent` is False is re-raised. `_item_cancel_run` caches it, and all four
  CAPABILITY rows re-raise it as FAIL.
- **Failure scenario:** take a real agent and the default `--cancel-prompt` ("at least 2000 words"). The agent streams
  `agent_message_chunk`s continuously for more than 30 s (the default `--timeout`) and advertises nothing
  cancellable. The silence condition never holds, so the TCK never cancels. `run_prompt` times out, and
  ACP-TOOLCANCEL-201/202 and ACP-TERMCANCEL-201/202 all FAIL, so the run is NOT CONFORMANT. The same happens when a
  cancellable tool call shows up late in the turn (say at 25 s): the probe's `timeout/2` window plus the silence
  wait run past the overall deadline. These rows should have SKIPped, or been judged on what was observed.
  The fixtures never stream for long, so the suite cannot catch this.
- **Confidence:** confirmed by running. `/tmp/m5review/streams_long_turn.py` is `ConformingAgent`, sending 25
  chunks 0.2 s apart. With `--timeout 3 -k test_item_controls` it gives 4 FAIL, each with
  `AgentTimeout: session/prompt 3 on session 'sess-0001' did not reach a turn end within 3.0s` at
  `_helpers.py:2013`.

## Should-fix

### S1. Legitimate `-32602` races false-FAIL ACP-TOOLCANCEL-201 / ACP-TERMCANCEL-201
- **Where:** `src/tck/v2/conformance/_helpers.py:2458-2466` (`_ItemProbe.step`).
- **Defect:** an error counts as `raced` only when the item's *final update* came before the response. Any other
  error is `rejected`, which is a FAIL. tool-calls.mdx:459/605 also allow `-32602` for an item that is "not
  cancellable", and they put no order on the response and the final update. Two conforming cases are misjudged:
  - (a) The agent clears `capabilities.cancel` with a `null` patch or `{cancel: null}` while the item is still live
    (tc:440 allows this). A `tool_call/cancel` that was already in flight then gets `-32602`.
  - (b) A concurrent agent has already finalized the item internally. It answers `-32602 already final` before its
    `tool_call_update` or `terminal_update` notification is flushed.
- **Amplifier:** for a Codex-style command item (a tool call plus the terminal it references, both advertising
  `cancel`), the driver sends both cancels in the same loop iteration. Cancelling one usually ends the other, which
  invites exactly these races.
- **Failure scenario:** a conforming agent gets FAIL on a CAPABILITY row, so the run is NOT CONFORMANT.
- **Confidence:** (a) confirmed by running. In `/tmp/m5review/withdraws_cancel.py` the tool call advertises
  `cancel`, then sends `capabilities: null` 0.3 s later while still `in_progress`, and answers `-32602`. Result:
  `ACP-TOOLCANCEL-201 FAIL ... answered with an error: {'code': -32602, ...}`. (b) is plausible, from reading the
  code.

### S2. The `raced` SKIP hides an agent that advertises `cancel` but does not implement the method
- **Where:** `src/tck/v2/conformance/_helpers.py:2460-2464` and `test_item_controls.py:66-68`.
- **Defect:** the "already final" excuse accepts *any* error code. Only `-32602` is the documented already-final
  answer (tc:459, 605). A `-32601` says the method does not exist, however the timing fell.
- **Failure scenario:** an agent advertises `capabilities.cancel` on short tool calls (reads, greps) but answers
  `tool_call/cancel` with `-32601`. Each call finishes before the agent reads the request, so every attempt is
  `raced`. All four rows SKIP "every tool call ... was already final", and the missing method is never reported.
  This is the common case for quick tools, and it breaks the rule that a SKIP must never hide a violation.
- **Confidence:** confirmed by running `/tmp/m5review/advertises_cancel_unimplemented.py` (in_progress with
  `cancel`, `completed` 0.3 s later, method `-32601`). All four rows SKIPPED with that reason.

### S3. The ACP-PATCH-211 terminal exemption false-PASSes a Codex-style tool call whose terminal already exited
- **Where:** `src/tck/v2/conformance/test_patches.py:343,353`.
- **Defect:** `listed` is the union of every `background` list seen during the turn. A tool call is exempt if *any*
  terminal it ever referenced was ever listed, even if that terminal has since reported `exitStatus` and left the
  list. pl:216 makes a tool call live only if it "references a listed terminal", which means the latest list. The
  pre-existing union for `tool_call` items is harmless, because STATE-208 catches a non-final listed tool call that
  is dropped at idle. Nothing catches the terminal variant.
- **Failure scenario:** a command's terminal is listed on a mid-turn `running` snapshot. The process exits
  (`exitStatus` is sent) and the terminal leaves the list before the idle. The tool call stays `in_progress` at
  idle, which is abandoned work the SHOULD at tc:423 / pl:998 is about. PATCH-211 still PASSes. The row is
  ADVISORY, so the verdict is unaffected, but the report is wrong.
- **Confidence:** confirmed by running `/tmp/m5review/abandons_tool_call_after_terminal_exit.py`
  (`-k "patches or background"`): `ACP-PATCH-211 PASS`, `ACP-STATE-206..208 PASS`.

### S4. The new cancel ledger reasons rest on a TCK choice and misstate observability
- **Where:** `spec-tracker/maps/v2.toml:600-608`.
- **Defect:** both reasons say the "already final" / "has exited" `-32602` case is reachable "only [by] a race",
  and that `ACP-TOOLCANCEL-201` (`TERMCANCEL-201`) "leaves that answer unjudged". Both claims are wrong:
  - It is reachable without breaking a client rule. An agent that keeps advertising `cancel` after the item's final
    status or `exitStatus` (PATCH-212 is only a SHOULD) lets the client send the request, and the agent then must
    answer `-32602`. This is the R15/R18 "already final" add-on that G1 and G3 asked for. It was dropped without a
    note.
  - When the race does happen, the driver already observes the answer. "Leaves it unjudged" is a TCK choice, which
    `docs/requirements.md` ("a rule that becomes observable … belongs in a row that can SKIP") and the state
    decision forbid as a ledger reason.
- **Failure scenario:** a spec update reads this entry as "covered on purpose, unobservable". The row that could
  SKIP is never written.
- **Confidence:** confirmed by reading (tc:440, 456, 459; `_ItemProbe._live` excludes final items even while they
  advertise `cancel`).

## Nits

- **N1.** The `--cancel-prompt` docs (`README.md:102-107`, `docs/mock-client.md:112`) still describe it as the
  cancellation tests' knob. They don't say that ACP-TOOLCANCEL/TERMCANCEL now depend on it: those rows SKIP unless
  the prompt makes the agent advertise `cancel` on a live item, and the default essay prompt essentially never does.
  `docs/mock-client.md` also does not document `drive_item_cancel` as client behaviour: it sends
  `tool_call/cancel`, `terminal/cancel` and a trailing `session/cancel`, and after the idle it reads without
  answering agent requests. A user seeing four SKIPs has no guidance on which prompt to choose. Confirmed by reading.
- **N2.** `_helpers.py:~2550` (`drive_item_cancel`, after `turn_done`): the loop reads lines with
  `agent.read_line` but answers no agent → client request. Suppose a listed background item asks
  `session/request_permission` after the idle, which tc:268 allows. If the agent's confirmation of the cancel waits
  on that answer, TOOLCANCEL-202 reports it `unconfirmed`. Plausible.
- **N3.** `test_session_capabilities.py:2121-2124` (ACP-FORK-206): a fork turn that times out SKIPs before the test
  checks the fork snapshots already received, for example a fork-response snapshot that copies the source list.
  FORK-202 FAILs, so the verdict is still right, but FORK-206's own violation shows as SKIPPED. Confirmed by reading.
- **N4.** The `raced` branch (`_helpers.py:2460-2464`) has no deterministic fixture. `completes_before_cancel.py`
  writes the final updates in the same synchronous burst, so the driver almost always sees them first, takes the
  `none` path, and never sends a request. A fixture that sleeps between the advertisement and the final status
  (like `/tmp/m5review/advertises_cancel_unimplemented.py`, but answering `-32602`) would pin the path down.
  Confirmed by reading.
- **N5.** The ledger reason at `spec-tracker/maps/v2.toml:189-191` says started work "cannot be told from
  foreground work". While the session is `idle` there is no foreground work. A new non-final tool call or running
  terminal announced while idle (pl:184 "even while the session is `idle`"), followed by neither `running` nor a
  list that names it, is the start-side mirror of STATE-209 and is observable with a SKIP. Plausible; it may be a
  deliberate scope cut, but then the reason should say so.
- **N6.** The ACP-TOOLCANCEL-201 citation (`tool-calls.mdx:440,456-459`) and the ACP-TERMCANCEL-201 citation
  (`:600-605`) include the `-32602` lines (459, 605) that the new ledger entries (`v2.toml:601,606`) declare
  untested. The row text notes the overlap, but spec-update tooling will see 459/605 as both covered and ledgered.
  A second small point: the ACP-RESUME-217 text says "on the connection that created it", but route 3 of
  `obtain_resumable_session` resumes on another connection. Confirmed by reading.

## Checked and found sound
- **Tiers, gates and citations.** ACP-TOOLCANCEL/TERMCANCEL-201/202 are CAPABILITY behind
  `inferred:toolCallCancel` / `inferred:terminalCancel`, self-SKIP, and carry no capability marker. They match
  tc:456-459 and 600-605 and the decision.
  - **202 accepts any final status.** This matches tc:458 ("normally `cancelled`, and may send `completed` or
    `failed` if the work finished first"). The client cannot tell an ignored cancel from a race.
  - **FORK-206 as CAPABILITY.** This is defensible. ss:49 states it declaratively, the docs decide the tier, the
    FORK-202 "Definitional" precedent applies, and no requirement was invented.
  - **The other new rows.** STATE-209 ADVISORY (pl:205 SHOULD), RESUME-217 CAPABILITY (pl:204 MUST + ss:346), the
    ENUM-201 `background[].type` site (schema `BackgroundWork` `other` branch) and the INFO-BACKGROUND rows match
    the docs. RFD citations are labelled `(Active RFD)`.
- **Ids (rule B).** TOOLCANCEL, TERMCANCEL and INFO-BACKGROUND are new v2-only areas at 201. RESUME-217 and
  FORK-206 are the next free numbers, and none of these numbers is used in v1.
- **`_base.py` opt-ins.** All defaults are no-ops:
  - `_finish_cancellable_work`, `_fork_background` and `_start_hung_background_work` do nothing without their
    option.
  - The `_run_background_work` refactor keeps the old order of announce, list, `running`, finalize, remove.
  - Without the option, `tool_call/cancel` and `terminal/cancel` stay `-32601`.
- **Violators trip only their row.** The narrow `test_cli` selection passed (32 passed). I also ran the full suite
  under `--cancel-prompt __hang__`, beyond the `-k` scope the tests use: `tool_call_cancel_never_final.py` FAILs
  only ACP-TOOLCANCEL-202, and `terminal_cancel_errors.py` FAILs only ACP-TERMCANCEL-201.
- **Driver hygiene.** It never sends a cancel for an item the TCK has not seen advertise `cancel` while non-final;
  the tracker applies the nullable patch rules. It sends no `session/cancel` while a probe is in flight. It runs on
  its own process, and its module name keeps it out of `-k cancel`, so it does not interfere with ACP-CANCEL-*.
- **Repo rules.** No `.agents/` references and no v1/v2 cross-imports in the range. The spec-tracker suite gives
  115 passed, 5 skipped. `tests/v2/test_registry.py`, `test_open_enums.py`, `test_validation.py` and `tests/common`
  give 197 passed.
