# Review: M1 (v2 stale subagent fixes), range 26e3859..d899514

Product commit reviewed: d899514. RFD checked at 95452a77 and at the TCK pin 3961af94: `docs/rfds/subagents.mdx`
is identical at both, so the cited lines 925-935 and 1008-1013 say what the rows claim.

Verification run:
- `uv run pytest tests/v2 -k "resume or replays or conforming"`: 34 passed.
- `spec-tracker` `uv run pytest`: 110 passed, 5 skipped.
- Probe fixtures outside the repo (`/tmp/m1review/`, not product files), run with
  `uv run acp-tck --protocol-version 2 -k resume -- python <fixture>`. Results are under findings 1 and 2.

Counts: blocker 0, should-fix 2, nit 1.

## Findings

### 1. RESUME-209's known set covers the whole connection, so replayed child traffic sent before its announcement PASSes (should-fix)

- **Where:** `src/tck/v2/conformance/test_session_capabilities.py:437` (`known = {session_id}`, then
  grown from every line of `agent.transcript`, including the `_add_history` turn before the resume). The row text
  at `src/tck/v2/requirements.py:1382` says "already announced on this connection".
- **Defect:** a child announced during the earlier prompt turn counts as known throughout the resume. The RFD
  requires the announcement to come first inside the replay, and that requirement is never checked.
- **RFD basis:**
  - RFD:933-935: "Replayed child updates MUST preserve ... per-session ordering. Child announcements precede child
    traffic."
  - RFD:995-1000: "The Client need not retain an earlier session tree. ... the Agent establishes the child's
    complete ancestor chain ... during this load/resume."
  - The research recommended this same scoping: "announced earlier in the same resume exchange", and S31 "within
    that exchange".
- **Failure scenario (confirmed by running):** `child_before_announce.py` subclasses `ExposesSubagentAgent`. On
  `replayFrom: start` it replays each child's history first, then the parent history that holds the
  `subagent_update`. A client resuming on a fresh connection would see child traffic for an unknown session. The
  TCK still reports `ACP-RESUME-209 PASS`, because the TCK always resumes on the connection where the turn ran.
- **Suggested direction (not a fix):**
  - Count only announcements on lines in `resume_lines`, still seeded with `session_id`.
  - Update the row text to match.
  - Add a violating fixture like the one above.
  - No conforming agent loses: the RFD requires announcement within this load/resume for both replayed and live
    child traffic (RFD:933-935 and 995-1003). `replays_subagent_history.py` re-announces inside the replay and
    keeps passing.
- **Confidence:** confirmed by running (the false PASS); the spec reading is plausible but strong.

### 2. RESUME-205 does not filter by session: a live child chunk during a replay-requested resume is a false FAIL (should-fix; the known item)

- **Where:** `src/tck/v2/conformance/test_session_capabilities.py:296`. `replayed` comes from `update_of(entry)`
  over every update in the resume window, whatever its `sessionId`.
- **Defect:** a live `agent_message_chunk` addressed to an announced child, arriving before the
  `replayFrom: start` response, is judged as a replayed chunk. No whole-message update precedes it, so the row
  FAILs.
- **Is this a false FAIL? Yes.** The brief says the RFD allows live child traffic only on no-replay resumes. That
  is incomplete:
  - RFD:999-1006 is in the general replay part, before the "When no replay is requested" paragraph. It says:
    "Other live transcript traffic can also proceed if the Agent preserves per-session ordering and ensures
    subsequent replay cannot overwrite or duplicate newer live content. Buffering ... is not a requirement to stop
    every child stream."
  - "subsequent replay" only makes sense when replay was requested.
  - The rule behind RESUME-205 (`session-setup.mdx:299-312`) is about replayed messages, and a live chunk is not
    one.
  - A conforming agent hits this whenever a detached background subagent is still streaming when the client
    resumes with replay.
- **Failure scenario (confirmed by running):** `live_child_during_replay.py` is `replays_subagent_history.py` with
  the live child chunk also sent on `replayFrom: start`. The run gives `ACP-RESUME-205 FAIL`; RESUME-002, 202,
  204, 206, 209 and 212 all PASS.
- **Suggested direction:**
  - Restrict 205 to the resumed session, or to the resumed session plus children announced inside the replay
    window, judging each child's replayed chunks per `messageId`.
  - Add a conforming fixture that sends live child chunks on a replay resume.
- **Confidence:** confirmed by running and by reading the RFD.

### 3. RESUME-204 does not filter by session: a replayed child `user_message` can trip it (nit)

- **Where:** `src/tck/v2/conformance/test_session_capabilities.py:244-249`, which reads `update_of(entry)` over
  all sessions.
- **Defect:**
  - The row FAILs any replayed `user_message` whose text equals the TCK's nonce prompt but whose `messageId`
    differs from the parent turn's.
  - The check covers child-addressed updates too.
  - The RFD asks agents to send a delegated task as a `session_message`. But an agent that gives the child the
    user's prompt verbatim as the child's own `user_message` is only missing a SHOULD (S17 in the research).
- **Failure scenario:**
  - An agent forwards the prompt "remember this <nonce>" to a subagent as the child's `user_message`, with the
    child's own `messageId`.
  - On `replayFrom: start` it replays the child's history.
  - RESUME-204 (CAPABILITY) FAILs, although the parent's message kept its id.
- **Confidence:** plausible, from reading only. This code predates M1 but is in the milestone's "stale subagent
  checks" area.

## Checked, no defect

- **Known-set logic matches ACP-PROMPT-002** (`test_prompt.py:209-230`):
  - same wire-order walk over `agent.transcript`;
  - array-carried messages handled by `iter_messages`;
  - nesting: a child's `subagent_update` announces grandchildren;
  - an announcement only counts when its carrier is known.
  - The one difference is scoping, which is finding 1.
- **RESUME-002 filter.** `_update_for(msg, session_id)` matches the row text ("for the resumed session"). The
  conforming fixture sends a live child chunk before every no-replay response, so the fix has a regression test:
  the old code would FAIL it.
- **Fixtures:**
  - `replays_unannounced_child.py`: its orphan `agent_message` is schema-valid (checked with
    `validate_agent_message`), so it FAILs RESUME-209 only through the sessionId check. It contains no chunk, so
    205 is unaffected, and it leaves the no-replay path alone, so 002 PASSes.
  - The `test_cli.py` FAIL/PASS sets match both fixtures' docstrings.
  - `replays_subagent_history.py` replays the child's recorded history: `_send_update` records child updates
    under the child id, so the 209 accept path really is exercised.
- **Tiers and citations:**
  - The rows remain CAPABILITY on `capabilities.session`.
  - The RFD citations only relax rows that the docs already back, so the "RFD-only, never MANDATORY" decision is
    not touched.
  - Citations follow the `docs/rfds/<name>.mdx:<line>` form and are pinned by `_cite`.
  - The "(Draft RFD)" label is the known S0.1 item; not counted.
- **Ledger** (`spec-tracker/maps/v2.toml:197`, `:599`):
  - The reasons no longer rest on a TCK self-choice.
  - The claims they make are correct per the research: there is no v2 client marker, and child `state_update`s
    arrive on the parent connection.
  - "Deferred" is an existing category (used 16 times).
  - spec-tracker tests are green.
- **Conventions:** no `.agents/` references in product code, no v1/v2 cross-imports, nothing outside the slice's
  scope.
