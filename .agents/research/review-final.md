# Final review: spec update, c80a543..df1b924 (target 3ea94133)

Scope: product commits 7ee8a00 (FIX-SA), 8765ae0 (FIX-ROWS), 18de542 (FIX-LEDGER), 426f87b (FOLLOWUP-ROWS),
79edd34 (GAPS), c19acff (CROSS-CHECK). I skipped the `chore: state:` commits. Hygiene (goal 6) covers `ee2af8a..HEAD`.
I checked spec lines with `git show 3ea94133:<path>` and exact line numbers (`grep -n ""`).

**Runs**
- Full suite at df1b924: `uv run pytest -q -rfE`, **1235 passed** in 620 s. No flake.
- spec-tracker: `uv run --package spec-tracker pytest spec-tracker/tests --spec-repo ...`, **121 passed**.
- cross-check tests: `uv run --directory cross-check pytest -q`, **20 passed**.
- `acp-tck --protocol-version 2 -k "test_replay_resume_sends_exactly_one or test_only_replayed_history_precedes"`
  against `cross-check/python_v2_agent.py`: RESUME-218 **PASS** and RESUME-220 **PASS**. This confirms the c19acff
  fixture change. The `scratch/cross-check/python-v2.json` report predates it and still shows 218 FAIL; it is not committed.
- Probe fixture `/tmp/review-final-fx/options_idle_before_response.py` (outside the repo; finding F1).

**Counts:** 0 blocker, 1 should-fix, 5 nits.

---

## Should-fix

### F1. ACP-OPTIONS-008 (v2 and v1) FAILs an early `state_update`, which the spec explicitly allows before the response
- **Where:**
  - `src/tck/v2/conformance/test_initial_config.py:384` (`kinds = set(_update_kinds(exchange.before, session_id)) - {"config_option_update"}`)
  - baseline `_early_kinds_without_entries`, `:316`
  - same design in v1, `src/tck/v1/conformance/test_initial_config.py:394` and `:331`
- **Spec:**
  - v2 SCO:584 only covers updates "caused by applying the entries".
  - v2 SS:100-103: "Updates may arrive before or after the `session/new` response ... An optional initial idle
    notification is a snapshot".
- **Defect:** only two kinds are excluded from judging:
  - `config_option_update`;
  - kinds that one baseline `session/new` without entries happens to send before *its* response.

  The initial idle `state_update` is legal before the response and is never caused by entries, yet it is judged. The
  baseline is a single timing sample and has a bias. Applying entries delays the response, so an asynchronously sent
  snapshot (or an async `available_commands_update` in v1) is *more* likely to overtake the response in the judged
  exchange than in the baseline.
- **Scenario (confirmed by running):**
  - The probe fixture is `_base.ConformingAgent` with `_options_config`. It sends `{"sessionUpdate":"state_update","state":"idle"}`
    before the response only when the request carried entries, which models an async snapshot that overtakes a
    response slowed by applying them.
  - `acp-tck --protocol-version 2 -k test_initial_config` gives ACP-OPTIONS-008 FAIL: "session/update ['state_update'] sent
    before the session/new response for an initial entry".
  - ADVISORY, so the verdict is unaffected. Still, the row reports a SHOULD miss for behaviour the spec permits.
- **Fix:**
  - v2: always exclude `state_update` (SS:100-103).
  - Both versions: compute the baseline over the plain request's traffic through a quiet period *after* its response,
    not only before it. A kind the plain setup sends at all is not caused by entries, so this removes the timing bias.
  - Add a fixture like the probe above with an expected PASS.
- **Confidence:** confirmed by running and by reading.

---

## Nits

- **N-a. A parent mirror can clear `target_unknown`** (`src/tck/v2/conformance/_child_cancel.py:276`).
  - The S7 reset runs for both own and mirrored states.
  - In the sequence own `unknown`, then a stale mirror `running`, then own `idle`/`end_turn`, the outcome is
    `not_cancelled` (016 FAIL) instead of `unobservable`.
  - It only happens together with another defect (a late mirror, which SUBAGENT-205 judges), and before S7 `target_unknown`
    was set from mirrors too.
  - Fix: update `target_unknown` only when `own` is true. v1 has no own path, so it is unaffected.
- **N-b. The S1 fix also drops coverage** (`src/tck/v2/conformance/_helpers.py:1192`).
  - The n-th/n-th `zip` starts at the first copy. An extra *leading* mirror, such as an announcement that carries an
    `idle` snapshot before the child's own first `running`, therefore stops all pairing.
  - SUBAGENT-205 then SKIPs for that child. This is a false negative only.
  - Fix: drop mirrors that come before the first own state's first matching mirror, then pair n-th with n-th.
- **N-c. The new fork probes cascade from a broken fork** (`src/tck/v{1,2}/conformance/test_initial_config.py:90/86`, `_setup_targets`).
  - When `fork` is advertised but forking a fresh session always errors (for example `-32603`), OPTIONS-004/-005 FAIL
    "must fail with -32602" and OPTIONS-006 FAILs on the fork probes. FORK-201 FAILs as well, so one defect FAILs four
    CAPABILITY rows.
  - FORK-201 already forks a never-prompted session, so a conforming agent is not affected.
  - Fix (optional): first do a plain fork of the source and skip the fork target when it fails ("FORK-201's").
- **N-d. A malformed update crashes the replay walker** (`src/tck/v2/conformance/test_cursors.py:175`, `_replay_end`).
  - `params.get("sessionId")` runs when `method == "session/update"` even if `params` is not a dict.
  - A malformed `session/update` without params raises `AttributeError`, so CURSOR-001/-002 error (FAIL) instead of
    ignoring the message, as `_walk` does.
  - Fix: guard with `isinstance(params, dict)`.
- **N-e. README omits the v2 resume rows from `--subagent-prompt`** (`README.md:132-145`).
  - The section says the one subagent turn is what `ACP-SUBAGENT-*` judge (plus v1 CLIENTCAP).
  - In v2, `ACP-RESUME-223/225/226` also run that text on their resume connection.
  - 223 and 225 already did this before the range; 226 adds to it. A user tuning the prompt or `--timeout` should know.

---

## Milestone-2 findings: per-finding verdicts

| # | Verdict | Evidence |
|---|---|---|
| S1 | **Fixed** (the fix narrows coverage, see N-b) | n-th/n-th pairing stops at the first difference. `test_a_missing_mirror_is_not_reported_as_a_late_one` covers the review's sequence. |
| S2 | **Fixed** (both versions) | `anchor_problems` demands an anchor after a reset only inside the replay window (v1: up to the load response; v2: up to `replay_complete`, else the response). A cursor anchored before the reset is exempt afterwards. Unit tests in `tests/v{1,2}/test_cursor_rows.py`. Row texts and the PT:707-708 / PL:1026-1027 / SS:379 citations check out. |
| S3 | **Fixed** | v1 008 judges every kind except `config_option_update`, minus the baseline. `options_notifies_initial.py` now FAILs only 007 (CLI set updated). The baseline has a flaw of its own (F1). |
| S4 | **Partial; the stated reason holds** | `resume_reaction_start` starts at the first message naming the resumed session, or at the response. In-flight traffic *on the resumed session* (a late parent `state_update`, say) still opens the window early, and a client cannot tell it apart: any parent update may be the agent's reaction. Anchoring on announcements instead would hide real violations. Acceptable. |
| S5 | **Fixed** | `drain_quiet` after close; `created` excludes `session_id`. Covered by `options_late_setup_traffic.py`. |
| S6 | **Fixed** | `_add_history` + drain before the probes; replayed history kinds before a `-32602` FAIL. New fixture `rejected_cursor_replays_history.py`. Adding 221 to five run_prompt-cascade CLI sets is justified (the row now prompts). SS:406 checked. |
| S7 | **Fixed** (both versions) | A later `running`/`requires_action` resets `target_unknown`. Helper tests in v1/v2 `test_run_prompt.py`. Mirror nuance in N-a. |
| S8 | **Fixed; the claim holds** | `test_session_references_after_a_load_response_follow_the_load_scope` already existed. A failed-load assert was added, the 002 text states the post-load scope, and the citation adds SA:517. |
| S9 | **Fixed (superseded)** | The entry was reworded in 18de542, then deleted in 426f87b when RESUME-226 judged SA:482. The user decision supersedes D8's Deferred entry. |
| S10 | **Fixed (superseded)** | Reworded, then narrowed in 426f87b to the unobservable remainder (other metadata changes; other connections need a second connection, SS:56). LIST-208/209 judge the observable half. |
| N1 | Fixed | v1 SCO:507 lists fork; `_skip_unless_session_id_allowed`, texts and the CLI test on a fork-only agent. |
| N2 | Fixed | `compared_loads` requires both loads to succeed. |
| N3 | Fixed | `_result_of` treats `AgentTimeout` as no payload; `options_never_answers.py` CLI test. |
| N4 | Fixed | A non-cancelled `idle` straight after `unknown` is `unobservable`; texts and docs updated. |
| N5 | Fixed | `ChildProbes.methods`; separate SKIP message; unit test. |
| N6 | Fixed | `_duplicate_entry` prefers a select, then a boolean; `options_only_boolean.py`. |
| N7 | Fixed | `reused_key_rejected_then_forgotten.py` FAILs only PROMPT-214. |
| N8 | Fixed | `removesuffix("\r")`. |
| N9 | Fixed | `_RepeatProbe` skips `claimed` items. |
| N10 | Fixed | Fixture docstring says MUST. |
| N11 | Fixed | `settled_after_release` only within `quiet_period` of the last released answer; unit test. |
| N12 | Fixed | `stopped_requests_kept` exempts requests whose `subject` names work in the child's latest `background` list (PL:1452); unit test. |
| N13 | Fixed | The 016 text mentions the release extension; the 225 text says `params.sessionId`. |
| N14 | Fixed | Gate is `inferred:subagents`, and the text explains the parent-cascade case. |
| N15 | Fixed | Walker tests with tool-call, compaction and session-message anchors and a custom position, both versions. |
| N16 | Fixed | OPTIONS-004..006 (both) and v1/v2 -008 repeat on fork; 7 v1 + 4 v2 fork fixtures each FAIL only their row. Cascade nit N-c. |
| N17 | Fixed | Header reworded in both maps. |
| N18 | Fixed | `CLI_STARTUP_TIMEOUT = "5"` and `CLI_SUBPROCESS_TIMEOUT = 300` in both suites, with `"1"` kept where the fixture never answers. My full run under default parallelism had no flakes. The constants only report hangs and cannot change a verdict. |

---

## Judgement calls

- **SUBAGENT-207 as an ADVISORY row, not a ledger entry: right.**
  - The rule is PL:1059 / PL:1209 (a SHOULD stopReason on the idle ending foreground work, applied to children via
    SA:313 "same meaning as for any session").
  - The ledger is for rules the TCK does not test; an observable SHOULD is an ADVISORY row, as STATE-204 already is
    for the prompted session.
  - Scope is conservative: only the first own idle after own active work, and mirrors are not judged.
  - Companion SUBAGENT-206 (CAPABILITY `inferred:subagents`; extensibility.mdx:238-243 MUST NOT, like STATE-203) is
    correctly gated and cited. SA:313/354 and PL:1059/1209 checked.
- **LIST-209 does not judge duplicates: right.**
  - SCO:392-394 asks for the duplicate *before* the response and for *subsequent changes* after it.
  - A second copy after the response is not a subsequent change and breaks no rule.
  - PASSing when any matching update is early is the safe reading. Updates with another title are rightly ignored.
  - ADVISORY is correct (SHOULD); the citation SL:163-165 + SCO:392-394 checks out.
- **LIST-208: correct.**
  - ADVISORY for the docs SHOULD (SL:162). The Draft RFD MAY (`rfds/session-set-title.mdx:156`, labelled Draft in
    `docs.json`) is recorded as a discrepancy the docs win.
  - It compares against the response's stored title, so normalisation is safe (the schema says the stored title "may
    be normalized"), and it SKIPs when the call fails.
  - `conforming_full` advertising `title` changes no other row (green suite).
- **RESUME-226 SKIP on conforming_full: acceptable.**
  - Same model as 223/225: conforming_full announces no child, so its PASS comes from `replays_subagent_history.py`.
  - Both negative fixtures fail only 226, with 223 and 225 PASS.
  - The tier (CAPABILITY `capabilities.session` + SKIP without a child) matches D8 and 223/225 for a docs MUST (SA:482).
  - False-positive analysis:
    - Only a child's updates before its own `replay_complete` count as replayed.
    - Only entities replayed under their old IDs are compared.
    - Only pairs whose spans did not overlap before the resume are ordered.
    - The parent check uses the first-seen parent.
  - I found no conforming behaviour that FAILs it. The remaining exposure is an agent that regenerates IDs *and* by
    chance reuses an old ID of the same type in a different order, which I judge negligible.
- **v2 OPTIONS-006 creates an extra source session when fork is advertised: fine.**
  - The source session is never used for the resume probe: `session_id` comes only from `session/new` targets.
  - Forking a fresh, never-prompted session is what FORK-201 already requires. The only cost is the cascade in N-c.
- **v1 OPTIONS-008 baseline attribution (second connection, same request without entries): the right idea, flawed sampling.**
  - It makes SCO:568's "caused by applying the entries" judgeable without guessing, and it is what let the v2 ledger
    entry SCO:584 become a row (shared id, rule B satisfied: same rule; v1 adds `current_mode_update` as SCO:568 does).
  - But the baseline must cover the plain request's traffic through a quiet period, and the v2 baseline must always
    exclude `state_update` (F1).

---

## Goals 4-6

- **Ledger (goal 4): sound.** Entries changed in the range:
  - v2 SL:162 reworded (real blockers: unobservable internal changes; stdio cannot reach a second connection to the
    same instance).
  - v2 SCO:584 and SA:482 deleted in the same change that added their rows (docs/requirements.md rule).
  - v1 SA:471 added as Deferred. The blocker is real: the v1 child-cancel driver has no request hold, and holding a
    descendant's request is legitimate only until its cancelled `idle` (v1 SA:467). The unblocking step is named.
  - None of them rests on "the TCK chose not to". The spec-tracker suite is green.
- **Cross-check (goal 5): justified.**
  - `gh api` shows Rust SDK v5.3.0's `Cargo.toml` pins `agent-client-protocol-schema = "=1.18.0"` and v5.4.0 pins `=1.19.0`.
  - `ls-remote` shows `v5.3.0^{}` = `05fd3893...`, matching `sdk-pins.sh`.
  - At 3ea94133 the spec workspace is `version = "1.18.0"`, 27 commits after the `v1.18.0` tag.
  - The new recorded FAILs are real SDK deviations: testy_v2 and python_v2_agent ignore `idempotencyKey`, which the
    stored reports confirm (PROMPT-215 shows two distinct `messageId`s for one key), and BATCH-209 was already
    documented. No TCK false positive is recorded as expected.
  - The `--expect` lines in `run.sh:242-245` and `ci.yml:158-161` are identical; the MANDATORY baseline is unchanged.
- **Hygiene (goal 6): clean.**
  - `git diff ee2af8a..HEAD` and `git grep` at df1b924 find no `.agents/(research|state.md|prompt.md)` reference in
    src, tests, spec-tracker, cross-check, docs or README.
  - Outside the product dirs the branch touches only `.agents/**`. No `tck-iso-*`, scratch or debug files; no
    `breakpoint`/`pdb`/debug prints.
  - `docs/mock-client.md` describes the final `unknown` handling, the slow-stop window and the background-subject
    exemption.
  - The `docs/requirements.md` inferred list already has every gate the new rows use (`inferred:subagents`); the other
    new rows use real paths or none (ADVISORY).
  - The README gap is N-e.

## Checked and fine
- **v1/v2 isolation:** no `tck.v1` import under v2 or the reverse, and none from common into either.
- **Harness:**
  - `run_prompt` hold mode only gains `HeldRequest.subject`.
  - The `_child_cancel` release bookkeeping (`release_index` = last released `answered_at`) is consistent with
    `stopped_requests_kept`'s index comparisons.
  - The cursor walkers' mark and event indices cannot collide: requests are SENT entries, and responses and updates
    are distinct RECEIVED entries.
- **test_cli.py expected-set diffs** match the fixture docstrings and stated reasons:
  - 221 joins five cascade sets, with the reason stated;
  - `options_notifies_initial` now FAILs only 007;
  - new SKIP-set entries for 206/207/226/LIST-208/209/OPTIONS-008;
  - `conforming_full` PASSes LIST-208/209.
- **Citations of the new rows** checked at 3ea94133: SCO:584 (v2), SCO:568 (v1), SS:55/105/297/596, SA:313/351/354/463-465/480/482,
  PL:1059/1209, extensibility.mdx:238-243, SL:162-165, SCO:392-394, initialization.mdx:361-366, v1 SCO:507, v1 SS:456.
  The schema pointers resolve (registry tests green).
- **Tiers and gates** follow docs/requirements.md:
  - ADVISORY rows have `capability=None` and SKIP through the marker;
  - CAPABILITY rows have a real path or an `inferred:` gate with a self-skip;
  - shared OPTIONS-008 follows rule B.
