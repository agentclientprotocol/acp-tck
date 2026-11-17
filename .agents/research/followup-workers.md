# What would an opt-in `acp-tck --workers N` take, and how complex is it?

**Sources checked:** acp-tck @ `f5d3aa3` (branch `pr10-follow-ups`); installed `pytest==9.1.1` and
`pytest-xdist==3.8.0` in `.venv` (the pinned versions); PR #10 description (`gh pr view 10`).
No ACP spec, SDK or A2A source applies: this is a question about the TCK's own harness. Nothing below
is a protocol requirement.
**Confidence:** high on the root cause and the mechanism (both verified by reading pytest/xdist
source and by running the suite under `-n`); medium on the LOC estimate.

## Answer

The report is empty under xdist because every piece of report state is built in hooks that run only
in the **worker** processes (`pytest_runtest_makereport`, the session fixture
`agent_initialize_result`), while the report is built in `pytest_sessionfinish` /
`pytest_terminal_summary` on the **controller**, whose `TEST_STATES_KEY` stash stays `{}`. The fix is
mechanical: have `pytest_runtest_makereport` attach the requirement ids, transcript and stderr to
the `TestReport` as extra attributes (pytest serializes them to the controller as-is), accumulate
state in `pytest_runtest_logreport` (which xdist replays on the controller), send the cached
`initialize` outcome via `config.workeroutput` / `pytest_testnodedown`, and keep workers from
writing the JSON report. Then add `--workers N` to the CLI, which swaps `-p no:xdist` for `-n N`,
and make pytest-xdist a runtime dependency. The tests need nothing changed: each test spawns its own
agent process, and the only cross-test ordering rule is `revokes` (logout). The simplest way to
handle that is to refuse `--workers` > 1 together with `--allow-logout`. It is worth doing: the
conforming fixtures go from 29 s to 6.6 s (v1, `-n 8`) and from 87 s to 24 s / 16 s (v2, `-n 4` /
`-n 8`) with identical pass/skip counts. **Complexity: Medium (about 250-350 LOC including tests and
docs, about 100 of it product code).** It fits in one PR as its own slice, or as two small slices
(see "Suggested split").

## Requirements

No ACP requirements apply. These are internal constraints the change must keep, from the current
code.

| # | Constraint | Tier | Citation |
|---|-----------|------|----------|
| 1 | Serial `acp-tck` (the default) still blocks xdist, so `PYTEST_ADDOPTS=-n 2` fails loudly | n/a (internal) | acp-tck `src/tck/__init__.py:148-150`, `tests/common/test_cli_isolation.py:122-134` |
| 2 | The `revokes` test runs after every other test, and at most one is collected | n/a (internal) | acp-tck `src/tck/common/plugin.py:223-242`, `:210-215` |
| 3 | The exit code comes from the verdict only for a normal run that executed at least one test | n/a (internal) | acp-tck `src/tck/common/plugin.py:861-868` |
| 4 | The JSON report has `agent_info`/`agent_capabilities` from the cached initialize | n/a (internal) | acp-tck `src/tck/common/plugin.py:831-836` |
| 5 | Exact `==` pins, managed with uv only | n/a (convention) | acp-tck `docs/development.md:99` |

## Details

### Why the report is empty today (verified)

- State is written only in `pytest_runtest_makereport` (`src/tck/common/plugin.py:685-725`). That
  hook runs where the item runs, so on a worker. It reads `item` (markers for requirement ids:
  `:666-670`, `:691`; the process transcript from `item.stash`: `:716-725`). The controller never
  sees `item`.
- `TEST_STATES_KEY` is created empty in `pytest_configure` (`:216`), which also runs on the
  controller. So on the controller `ran_any_test` is False (`:865-866`, `:899-908`) and it prints
  "ACP TCK: no test executed in this run".
- `AGENT_INIT_KEY` is set by the session-scoped autouse fixture `agent_initialize_result`
  (`:416-453`). Under xdist that runs once per worker, never on the controller, so even with test
  states fixed, `agent_info`/`agent_capabilities` would be `null` in the JSON.
- Reproduced: running plain pytest on `src/tck/v2/conformance` with `-p tck.v2.plugin -n 4`
  against `tests/fixtures/agents/v2/conforming.py` prints "110 passed, 132 skipped in 24.28s"
  followed by "ACP TCK: no test executed in this run".

### Why the fix is cheap: what crosses the worker-to-controller boundary

- xdist workers send each phase report via `pytest_report_to_serializable`
  (`.venv/.../xdist/remote.py:282`), and the controller replays it into
  `config.hook.pytest_runtest_logreport(report=rep)` (`xdist/dsession.py:326-329`).
- `_pytest/reports.py:596-610` (`_report_to_json`) serializes `report.__dict__` wholesale, and
  `TestReport.__init__(**extra)` restores extra attributes (`_pytest/reports.py:335`, `:378`). So any
  JSON-able attribute set on the report in `makereport` reaches the controller, along with
  `user_properties`, `duration`, `sections` and `longrepr`. The requirement sections the plugin adds
  (`plugin.py:713-721`) already get there.
- Workers end with the `workerfinished` event carrying `config.workeroutput`
  (`xdist/remote.py:141-149`; the dict is set up at `:425`). A plugin's own `pytest_sessionfinish`
  runs inside that hookwrapper's `yield`, so it can add keys (pytest-cov uses the same pattern). On
  the controller, `pytest_testnodedown(node, error)` fires with `node.workeroutput` set
  (`xdist/dsession.py:193-201`, `workermanage.py:420`), before the controller's
  `pytest_sessionfinish`.
- xdist gives each worker `basetemp/<gwN>` under an explicit `--basetemp`
  (`xdist/workermanage.py:340-341`), so the CLI's private `mkdtemp` basetemp (`__init__.py:184-190`)
  keeps working, and `shutil.rmtree` still removes everything.

### Test independence (verified)

- Every test gets a fresh `AgentLaunch` (`plugin.py:297-307`, function scope) and spawns its own
  agent process(es) through `connected_agent`. There are no session- or module-scoped fixtures in
  `src/tck/v{1,2}/conformance` or `common/harness` (grep for `scope=`, sockets, module-level mutable
  state: no hits). The only session fixture is `agent_initialize_result`.
- Session cwds are per-test `tmp_path`s, e.g. v1 `test_session.py:189`, and
  `test_session_capabilities.py:213` uses an empty dir. So `session/list` filters do not see sessions
  from concurrent tests. `test_session_capabilities.py:190` lists without a filter but checks only
  the shape.
- The one ordering dependency is `revokes` (ACP-AUTH-004 logout), moved last in
  `pytest_collection_modifyitems` (`plugin.py:223-242`, `:262`). Under xdist that hook runs on every
  worker, so all workers get the same order. But `--dist load` sends the last item to one worker
  while the others are still running tests, so "after every other test" no longer holds. Without
  `--allow-logout` both versions skip without logging out (v1 `test_authentication.py:190-191`;
  v2 `test_authentication.py:359-360`; v2 spawns and initializes first, which is harmless).

### Sketch of the change

**1. `src/tck/common/plugin.py`: make the report process-agnostic (works serially and under xdist)**

- In `pytest_runtest_makereport` keep only the parts that need `item`: set
  `report.acp_tck_req_ids = _requirement_ids(item)`, append the requirement/transcript/stderr
  `sections` (as today), and on failure set `report.acp_tck_transcript` / `report.acp_tck_stderr`
  (the already truncated `_transcript_entries_dict` / `_truncate_stderr` values; all plain
  JSON-able types).
- Add a `pytest_runtest_logreport(report)` that does today's accumulation (`:690-706`) from
  `report.nodeid`, `getattr(report, "acp_tck_req_ids", [])`, `report.duration`,
  `report.user_properties`, `_phase_status(report)` and the two new attributes. Serially this fires
  once per phase in the same process, so behaviour is unchanged. Under xdist it fires on the
  controller (and also on the worker, which is harmless).
- In `pytest_sessionfinish`, on a worker (`hasattr(config, "workerinput")`): put the
  `InitializeOutcome` (as a `{"result", "error_message", "error"}` dict) into
  `config.workeroutput["acp_tck_init"]`, then return. Do not build the report, do not write
  `--tck-report-json` (otherwise every worker races to write a partial report to the same path), and
  do not touch `exitstatus`.
- Add `@pytest.hookimpl(optionalhook=True) def pytest_testnodedown(node, error)`. It stores the
  first worker's `acp_tck_init` in `config.stash[AGENT_INIT_KEY]`. `optionalhook=True` is required:
  without xdist loaded (serial runs use `-p no:xdist`), pytest rejects an unknown `pytest_*` hook. The
  v1/v2 shims copy hooks via `vars()` (`v1/plugin.py:25-27`), so the hookimpl marker carries over.
- Determinism: `_build_report` iterates `states` in insertion order (`:805`). Under xdist that is
  completion order, so `tests[]` within a requirement can differ between runs. Requirements are
  already sorted by id (`report.py:131`), and the status is worst-of so order does not matter
  (`report.py:115-122`). Sort the per-requirement test lists (by nodeid, or by a collection index
  attached in `makereport`) so the JSON is stable.
- Nothing else in the hooks reads worker-only state. `pytest_sessionstart` (`:786`) and
  `pytest_terminal_summary` run on the controller and read only the stash.

**2. `src/tck/__init__.py`: CLI**

- `--workers N` (int, default 1; decide whether to accept `auto`). When N > 1: drop `-p no:xdist`
  and pass `-n N` (and probably `--max-worker-restart 0`, see the open questions). When N == 1: keep
  today's args exactly.
- Fail with `parser.error` when `--workers` > 1 is combined with `--allow-logout` (constraint 2). If
  xdist stays optional, also fail when `importlib.util.find_spec("xdist")` is None.
- Update the comment at `:148-149` ("The TCK's report only works in a single process").

**3. `pyproject.toml` / `uv.lock`**: pytest-xdist is dev-only today (`pyproject.toml` lines 42-45,
`[dependency-groups] dev`). Move `pytest-xdist==3.8.0` into `[project].dependencies` (this pulls in
`execnet`), or add an extra `acp-tck[parallel]` plus the `find_spec` guard. Re-lock with uv.

**4. Docs**: `README.md` (options table), `docs/testing.md:39-41` ("acp-tck blocks xdist because its
report needs a single process"), the `_assert_isolated` docstring in
`tests/common/test_cli_isolation.py:1-8`, the plugin module docstring (exit-code paragraph,
`plugin.py:11-14`), and `docs/harness.md` or the docs page that covers the reporting plugin (check
`docs/README.md` for which).

### Files to touch

| File | Change | Rough LOC |
|------|--------|-----------|
| `src/tck/common/plugin.py` | split makereport/logreport, worker guard, workeroutput, `pytest_testnodedown`, sort | +70 / -25 |
| `src/tck/__init__.py` | `--workers`, arg swap, logout guard, optional xdist guard | +25 |
| `pyproject.toml`, `uv.lock` | runtime dep or extra | small |
| `tests/common/test_cli_isolation.py` (or a new `tests/common/test_cli_workers.py`) | end-to-end worker tests | +100-150 |
| `tests/common/test_plugin.py` | unit test: logreport accumulation from a serialized+deserialized report | +30-50 |
| `README.md`, `docs/testing.md`, docs page for the plugin | option and behaviour | +30-50 |

## Testability notes (test strategy for the repo's own tests)

All runs are subprocesses, like `test_cli_isolation.py` (pytest is not re-entrant). Use `_env()` to
drop `PYTEST_ADDOPTS`.

1. **Parity, v1 and v2:** run the conforming fixture serially and with `--workers 2`, both with
   `--report-json`. Compare the JSON after dropping `started_at`, `finished_at` and `duration_s`.
   The requirements, statuses, tests and `agent_info`/`agent_capabilities` should be equal. This one
   test covers test-state forwarding, the `workeroutput` initialize outcome, and sort determinism. It
   costs about 2x a full conforming run per version (v2 is about 87 s serial), so use `-k` on a few
   files, or accept the cost given that the repo suite runs `-n auto` anyway.
2. **Failure details forwarded:** run a failing fixture (e.g. `answers_notifications.py`, which fails
   only ACP-JSONRPC-003 per `tests/v1/test_cli.py:611`) with `--workers 2 --report-json`. Assert the
   failing requirement's test has a non-empty `transcript` and `stderr`, and that the console has
   "VERDICT: NOT CONFORMANT" and the exit code is 1.
3. **Guards:** `--workers 2 --allow-logout` exits with a usage error. The existing
   `PYTEST_ADDOPTS="-n 2"` test still holds for the default (serial) mode.
4. **Selection edge:** `--workers 2 -k nomatch` still prints "no test executed" and keeps pytest's
   exit code (5).
5. **Unit test:** build a `TestReport` with the `acp_tck_*` attributes, round-trip it through
   `config.hook.pytest_report_to_serializable` / `pytest_report_from_serializable` (or `_to_json` /
   `_from_json`), feed it to `pytest_runtest_logreport`, and assert the state. This catches a
   non-serializable attribute early.
6. `_assert_isolated` asserts that `"workers"` and `"[gw"` do not appear in the output
   (`test_cli_isolation.py:32-33`). Worker-mode tests need their own assertions (e.g. the
   "created: 2/2 workers" line).

## Risks

- **Timing-sensitive checks under load.** Absence checks wait `quiet_period` = clamp(timeout/10,
  0.5 s, 2 s) (`v1/conformance/_helpers.py:210-215`), and `run_prompt` peeks for a cancel race for
  `cancel_race_peek` = clamp(timeout/50, 0.05 s, 0.5 s) (`:283-288`). Under CPU contention a late
  forbidden reply can arrive after the quiet window, so the failure mode is mostly a **false PASS**
  (non-conformance missed), not a false FAIL. Cancel tests SKIP "not exercised" when the turn ends
  before cancel lands, and load can shift that either way. CI already runs each cross-check agent on
  its own runner because "several checks are timing-sensitive" (`.github/workflows/ci.yml:54-57`).
  This is the main argument for keeping `--workers` opt-in and documenting "for a verdict you rely
  on, run serially". With the local fixtures, `-n 4` and `-n 8` gave the same 110/132 (v2) and
  54/70 (v1) pass/skip counts as serial, which is one observation, not proof.
- **Real agents are not built for N concurrent processes.** All workers launch the agent in the same
  `--agent-cwd` with the same HOME and credentials. Agents that keep process-level state there (lock
  files, a session DB, token refresh on login with `--auth-method`), or that call a rate-limited LLM
  API, can produce false FAILs or timeouts. The TCK cannot detect this. Document it.
- **Startup storms:** N agents start at once, plus one `initialize` handshake per worker
  (`agent_initialize_result` is per worker). Heavy agents (node/npx) can get close to
  `--startup-timeout`.
- **Worker crash:** if a worker process dies, xdist sends a synthetic failure report for the item,
  which lacks `acp_tck_req_ids`. That requirement then reads NOT_TESTED instead of FAIL, which is
  still non-conformant for MANDATORY but silently wrong for CAPABILITY/ADVISORY. Options: pass
  `--max-worker-restart 0` and treat any report without the attribute as an aborted run (no verdict,
  pytest's exit code), which matches serial behaviour where a crash kills the run. Workers are very
  unlikely to crash, since agent hangs are bounded by the per-test watchdog (`plugin.py:272-291`).
- **Usage errors from collection** (`pytest_collection_modifyitems` raising `UsageError`,
  `plugin.py:263-266`) surface from workers as collection errors, not the clean serial message. This
  only affects TCK developers with an invalid test, not operators.
- **Plugin shim footgun** (`v1/plugin.py:13-16`): new helpers must live in `tck.common.plugin`, and
  new hooks are copied automatically. No problem as long as nothing is overridden per version.

## Open design questions

1. **Default and accepted values:** default 1 (opt-in, as PR #10 says) or `auto`? Recommend default 1,
   with `auto` accepted for convenience, given the timing risk above.
2. **Dependency:** a hard runtime dep (simplest, about 2 small wheels) or an extra `acp-tck[parallel]`
   with a guard?
3. **Logout:** refuse `--workers` > 1 with `--allow-logout` (recommended, about 3 LOC), or support it
   with a custom `pytest_xdist_make_scheduler` that holds back the `revokes` item until all others
   finish (about 60+ LOC against a semi-internal xdist API), or run a serial second phase and merge
   (largest)?
4. **Order of `tests[]` in the JSON:** sort by nodeid (simple; changes serial output order slightly)
   or by collection index (keeps today's serial order exactly; needs an index attribute from
   `makereport`)? Cross-check compares only MANDATORY FAIL sets, so either is safe for it.
5. **Initialize outcome disagreement:** each worker does its own `initialize`. Should the controller
   warn if workers saw different `agentInfo`/capabilities (a nondeterministic agent), or just take
   the first?
6. **Record the worker count in the JSON report?** The report has no run-options field today
   (`plugin.py:838-849`). This would help anyone reading the report judge timing-sensitive results.
7. **`--agent-cwd` interaction:** document only (shared cwd for all workers), or offer per-worker
   cwds? Recommend document only. The TCK does not own the agent's state layout.
8. **`--max-worker-restart 0` and crash semantics** (see Risks).

## Suggested split (if it should not be one slice)

- **Slice A (S, about 120 LOC with tests):** make the plugin report process-agnostic (makereport ->
  logreport, workeroutput initialize, worker guard on the JSON write, stable sort). The CLI still
  passes `-p no:xdist`. Verify with plain pytest `-n 2` in a test. No user-visible change.
- **Slice B (S, about 150 LOC with tests and docs):** `--workers`, dependency move, logout guard,
  docs, CLI end-to-end tests. Depends on A.

Both fit in one PR next to other small follow-ups. Overall Medium: few files and no protocol
questions, but it touches the reporting core that every verdict depends on, and needs careful parity
tests.

## Discrepancies

None between sources. The PR #10 description says the report "came out empty" under workers, which
matches the code and the reproduction above.

## Open questions

- Which docs page owns the reporting plugin's contract (`docs/README.md` index), to update alongside
  `docs/testing.md`. Not checked.
- Whether cross-check CI should ever use `--workers`. Probably not, given its per-runner isolation for
  timing.
