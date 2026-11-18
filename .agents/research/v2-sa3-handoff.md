# V2-SA3 handoff (child-session probes, list, ordering) -- NOT committed, full suite NOT run

Branch eugenethedev/spec-update, tip a1dd1c8. Working tree holds all edits uncommitted.

## Done (all implemented, targeted tests green)
- `src/tck/v2/requirements.py`: added ACP-SUBAGENT-018 (ADVISORY), -019 (CAPABILITY `capabilities.session`),
  -205 (CAPABILITY `inferred:subagents`), ACP-LIST-004 (CAPABILITY `capabilities.session`); extended
  ACP-SUBAGENT-004 text (later `session/new` never returns an announced child id). Citations verified at
  3ea94133: error.mdx:58 (research said :57), SA:369,376,379-380,425,381,350-351,80-84; session-list.mdx:6.
- `src/tck/v2/conformance/_helpers.py`: new `announced_children`, `child_state_order` (+ `ChildStateOrder`),
  internal `_child_state_paths` (child_state_mirrors refactored onto it, same behaviour).
- `src/tck/v2/conformance/test_subagents.py`: probe phase inside `_connection_transcript` after the transcript
  snapshot (`_probe_children`, `ChildProbe(s)`, `_connection_probes`). Order: session/list (<=10 pages), one
  session/new, then per method over the first two children: session/resume, session/delete (only with
  `capabilities.session.delete`), session/close LAST. New tests for 018/019/205/LIST-004; 004 also asserts the
  probe `session/new` id is not an announced child. 019 and LIST-004 carry `@pytest.mark.capability("capabilities.session")`.
- Fixtures (tests/fixtures/agents/v2, mode 644): `exposes_subagent.py` now answers any request naming an announced
  child (except tool_call/cancel, terminal/cancel) with -32602 via `_answer_child_request`, tracking
  `_announced_children` (NOT `_children`: `replays_subagent_history.py` uses that name as a dict).
  New: `exposes_subagent_full.py` (advertises `session.delete`), negatives `child_close_wrong_code.py` (018),
  `child_close_succeeds.py` (019), `child_delete_succeeds.py` (019), `lists_child_session.py` (LIST-004),
  `child_id_reused_for_new_session.py` (004), `late_child_state_mirror.py` (205). Each verified via CLI to FAIL
  only its row.
- Tests: `tests/v2/test_helpers.py` (announced_children, child_state_order cases), `tests/v2/test_registry.py`
  (ids + advisory set), `tests/v2/test_cli.py` (tier/skip sets updated; new `_CHILD_PROBE_IDS`,
  `test_child_probe_and_ordering_rows_pass_non_vacuously`, `test_child_probe_rows_skip_without_a_child`,
  `test_child_probe_and_ordering_violators_fail_exactly_their_row`; `_SUBAGENT_ROW_IDS` extended).

## Verification state
- Green: `tests/v2/test_helpers.py`, `tests/v2/test_registry.py`, spec-tracker tests (120 passed with
  `--spec-repo .../agent-client-protocol`), and the `-k "child_probe or subagent or child"` slice of tests/v2/test_cli.py
  (60 passed, 1 failed). The 1 failure (returncode assertion on the ADVISORY 018 violator: scoped runs always exit 1)
  was fixed by deleting that assertion; the fix was NOT re-run.
- NOT run: the full `uv run pytest -q` (needs ~10 min, foreground, 600000 ms). Run it, then commit.
  Possible fallout to check: other v2 test_cli expected-skip/PASS sets for fixtures extending
  ExposesSubagentAgent (probes now run for all of them), tests/v2 fixtures docs listing, `-k` scoped tests.

## Left
- Run the full suite, fix any set-membership failures, commit (one commit, e.g.
  `feat(v2): child-session probes, list and state-ordering rows`), stage by explicit path including the 7 new fixture files.
- Do NOT add SUBAGENT-203/-204 or RESUME-223..225 (next slice). No `.agents/` references exist in product files.

## Decisions to keep
- Probes run on the shared subagents connection (a child can only be named while its root is active), not a new one;
  018 judged only on errors, 019 only on successes (one defect, one row); 018 SKIPs when nothing came back as an error.
- 205 aligns copies exactly like 201 (greedy in-order) and judges only aligned transitions, so a missing/swapped
  mirror is 201's alone and a delayed one (all mirrored in order) is 205's alone.
- No spec-tracker map changes were needed (v1 slice made none either).
