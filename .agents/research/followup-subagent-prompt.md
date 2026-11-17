# What would it take to add `--subagent-prompt` (PR #10 follow-up), and how complex is it?

**Sources checked:** acp-tck @ `f5d3aa3` (branch `pr10-follow-ups`, clean); agent-client-protocol @ `94d7666d`
(pulled, up to date), read at the TCK's pin `3961af94` via `git show`; PR #10 body (`gh pr view 10`).
Rust/Python SDKs and A2A TCK not needed: this is a TCK-harness question, not a protocol-behaviour one.
**Confidence:** high for the file map and the sketch, which come from reading the code paths end to end. Medium for
the LOC estimate, which depends on the design choices below.

## Answer

The change is **Small**: about 200 to 300 LOC including tests and docs, in one PR. Two places drive a turn whose
traffic the subagent rows judge, and each sends a hard-coded prompt today:

- the subagents connection, which serves `ACP-SUBAGENT-001..015` in v1 (plus `ACP-CLIENTCAP-001..003`) and
  `ACP-SUBAGENT-001..014` and `-201` in v2. v1 sends `"Summarize what you can help me with in this project."` and v2
  sends `"hi"`.
- the child-cancel driven turn, which serves `016`/`017`, v2 `202` and the child `TOOLCANCEL-203`/`TERMCANCEL-203`
  rows. It already sends `--cancel-prompt`, and the README already tells users to pick a delegating prompt for it.

The minimal change copies the `--cancel-prompt` plumbing exactly: an `acp-tck --subagent-prompt TEXT` flag passed
through as `--tck-subagent-prompt`, a `subagent_prompt_text` fixture, and the two connection builders sending it in
place of their constant. The real work is in three user decisions:

1. whether the option also drives the child-cancel turn;
2. what timeout budget a real delegating turn gets, because a turn over `--timeout` FAILs every row instead of
   SKIPping them;
3. whether the default stays as it is.

A provided prompt that produces no child should keep the rows SKIPPED. The Active Subagents RFD only *allows* an
agent to expose subagents; nothing obliges it to spawn one.

## Requirements

None of these are new protocol requirements. The table lists the existing rules and policies the option touches.

| # | Requirement / policy | Tier | Citation |
|---|---|---|---|
| 1 | An Agent *may* expose subagents it creates when delegating. Exposing them is permitted, not obliged | capability:`inferred:subagents` (Active RFD, so never MANDATORY) | agent-client-protocol `docs/rfds/subagents.mdx:12-16 @ 3961af94`; stage Active per `docs/docs.json:211-214 @ 3961af94` |
| 2 | An RFD-only MUST is CAPABILITY when a gate fits | policy | acp-tck `docs/requirements.md:79-80` |
| 3 | A SKIP must be honest. A FAIL when an agent defect breaks the setup: an agent that cannot finish a turn fails the dependent rows, and an uncaught `AgentTimeout` is a FAIL | policy | acp-tck `docs/writing-tests.md:82-88` |
| 4 | v1 subagent traffic goes only to a client that advertised `clientCapabilities.subagents`, which is why there is a separate connection | MUST (v1 docs) | acp-tck `src/tck/v1/conformance/test_subagents.py:4-15` (module docstring, citing `ACP-CLIENTCAP-007`) |

## Details

### How the rows get child traffic today

| Version | Driven turn | Prompt sent | Rows served | Code |
|---|---|---|---|---|
| v1 | subagents connection (`subagents: {}`, `session/new`, one turn, drain, optional `session/load`, drain), made once per run | `_PROMPT_TEXT = "Summarize what you can help me with in this project."` | `ACP-SUBAGENT-001..009`, `-011..015`; also `ACP-CLIENTCAP-001..003` (MANDATORY) via `subagents_connection_received` | `src/tck/v1/conformance/_subagents_connection.py:23,85`; `test_client_capabilities.py:43,68-144` |
| v2 | `_connection_transcript` (`v2_only_agent`, `session/new`, one turn, drain), made once per run | `_PROMPT_TEXT = "hi"` | `ACP-SUBAGENT-001..009`, `-011..014`, `-201` | `src/tck/v2/conformance/test_subagents.py:55,62-91` |
| v1 | child-cancel run (`drive_child_cancel`) | `cancel_prompt_text` (from `--cancel-prompt`) | `ACP-SUBAGENT-016/017` | `src/tck/v1/conformance/test_subagent_controls.py:46-70` |
| v2 | child-cancel run (`drive_child_cancel`) | `cancel_prompt_text` | `ACP-SUBAGENT-016/017/202`, `ACP-TOOLCANCEL-203`, `ACP-TERMCANCEL-203` | `src/tck/v2/conformance/test_subagent_controls.py:46-65` |

Every row SKIPs itself when nothing was exercised: `"inferred:*"` gates are documentation-only, with no
`@pytest.mark.capability` (`src/tck/v1/conformance/test_subagents.py:22-27`). The README already says the
child-cancel rows use `--cancel-prompt` and that users should pick a delegating prompt for them (`README.md:117-122`,
`docs/mock-client.md:146-153`). The real gap is therefore the first two rows of the table: their prompt is hard-coded
and cannot be overridden.

### How `--cancel-prompt` is threaded (the pattern to copy)

1. `src/tck/__init__.py:56-65` defines the argparse `--cancel-prompt` flag (default `None`), and `:162-163` passes it
   through as `--tck-cancel-prompt`.
2. `src/tck/common/plugin.py:98-109` registers the pytest option `--tck-cancel-prompt` (default
   `_DEFAULT_CANCEL_PROMPT`, `:54-60`).
3. The fixture `cancel_prompt_text` is at `src/tck/common/plugin.py:310-315`.
4. Tests take `cancel_prompt_text` as a fixture argument and hand it to helpers.
5. `tests/v1/test_cli.py:175-215` (`_run_cli(..., cancel_prompt=...)`) and `tests/v2/test_cli.py:~495-525` (same
   shape) are the self-test runners.
6. The fixture agents special-case only the `__hang__` sentinel: `tests/fixtures/agents/v1/_base.py:525`,
   `tests/fixtures/agents/v2/_base.py:954-957`, `tests/fixtures/agents/v{1,2}/cancellable_subagent.py`. The default
   prompt itself is "deliberately not special-cased by any fixture agent" (`plugin.py:58-60`).

### Sketch of the minimal change

The design defaults below are the recommended ones; see the open questions.

- **`src/tck/__init__.py`** (about 12 LOC): add `--subagent-prompt TEXT`, default `None`, with help text. Pass it
  through as `--tck-subagent-prompt` only when it is given.
- **`src/tck/common/plugin.py`** (about 20 LOC): add `group.addoption("--tck-subagent-prompt", default=None,
  metavar="TEXT", help=...)` and a fixture
  `subagent_prompt_text(request) -> str | None`. Default `None` means "use the version's own built-in text", so
  existing runs and cross-check baselines don't change.
- **`src/tck/v1/conformance/_subagents_connection.py`** (about 10 LOC): `subagents_connection` already receives
  `request`. Read `request.config.getoption("tck_subagent_prompt") or _PROMPT_TEXT` and pass it into `_run`. Update
  the module docstring. `subagents_connection_received` inherits the change automatically.
- **`src/tck/v2/conformance/test_subagents.py`** (about 10 LOC): same in `_connection_transcript`, plus a docstring
  update.
- **Optional skip-reason tweak** (about 10 to 20 LOC across both versions): when a prompt was supplied, add something
  like "(with --subagent-prompt)" to the "exposed no subagent" SKIP reasons. A small helper in each `test_subagents.py`
  avoids touching all 14 or 15 `pytest.skip` strings by hand. Alternatively, record a `record_property(
  "acp_tck_subagent_prompt", "custom")` on each row.
- **Timeout** (about 5 LOC if chosen): give the subagents-connection turn `timeout * 3`, as `drive_child_cancel`
  already does (`src/tck/v1/conformance/_child_cancel.py:229-233`, `src/tck/v2/conformance/_child_cancel.py:385-389`).
  See open question 2.
- **Docs** (about 25 to 40 lines):
  - `README.md` "Options": a new `### --subagent-prompt TEXT` section after `--cancel-prompt` (`README.md:102-122`),
    plus the "What is covered" subagent bullet (`README.md:262-264`).
  - `docs/mock-client.md`: the subagents-connection description (`:14-15`) and the `drive_child_cancel` section if
    option A in question 1 is chosen.
  - `docs/writing-tests.md:88-89`: optionally mention it beside `--cancel-prompt`.
  - Module docstrings in `src/tck/v1/conformance/test_subagents.py`, `_subagents_connection.py` and
    `src/tck/v2/conformance/test_subagents.py`.
  - `requirements.py` descriptions say "one prompt turn" and don't name the text, so no change is needed there.

### Files to touch (summary)

| File | Change |
|---|---|
| `src/tck/__init__.py` | new flag and passthrough |
| `src/tck/common/plugin.py` | new pytest option and fixture |
| `src/tck/v1/conformance/_subagents_connection.py` | use the option; docstring |
| `src/tck/v2/conformance/test_subagents.py` | use the option; docstring |
| `src/tck/v1/conformance/test_subagent_controls.py`, `src/tck/v2/conformance/test_subagent_controls.py` | only if option A in question 1 is chosen |
| `tests/fixtures/agents/v1/…`, `tests/fixtures/agents/v2/…` | one new sentinel-gated fixture per version (below) |
| `tests/v1/test_cli.py`, `tests/v2/test_cli.py` | `_run_cli(..., subagent_prompt=...)`; new tests |
| `tests/common/test_plugin.py` (optional) | option default and fixture value |
| `README.md`, `docs/mock-client.md`, `docs/writing-tests.md` (optional) | docs |

## Testability notes (test strategy for the repo's own tests)

- **New fixture per version.** `exposes_subagent_on_request.py` subclasses `ExposesSubagentAgent`
  (`tests/fixtures/agents/v{1,2}/exposes_subagent.py`) and exposes the child only when the prompt is a single text
  block equal to a new sentinel, for example `__subagent__`. That follows the `__hang__` convention, and the default
  prompt stays un-special-cased. v1 can override the `_exposes_subagents(session_id)` seam
  (`tests/fixtures/agents/v1/exposes_subagent.py:46-47`) after recording the prompt in `_handle_prompt`. v2 can gate
  `announce_child` / `_handle_prompt` the same way. About 25 to 35 LOC each.
- **CLI tests, per version** (about 30 to 50 LOC each):
  1. `--subagent-prompt __subagent__ -k test_subagents` against the new fixture: every `_SUBAGENT_IDS` row PASSes in
     v1, and `ACP-SUBAGENT-001..014`/`-201` in v2.
  2. The same fixture without the flag: every row SKIPs. This proves the default prompt does not trigger it and
     replaces nothing else.
  3. Optionally, `--help` mentions `--subagent-prompt`.

  Reuse `_table_statuses`/`_output_fail_ids` and the `_SUBAGENT_IDS` sets (`tests/v1/test_cli.py:62-67`;
  `tests/v2/test_cli.py:634-650`). Note that v2's `_SUBAGENT_EXERCISED_IDS` also lists `ACP-PATCH-*` rows that
  `exposes_subagent.py` exercises on *every* connection. A sentinel-gated variant exercises only the subagent
  connection, so assert on the `ACP-SUBAGENT-*` subset only.
- **If option A in question 1 is chosen**, add one test that `--subagent-prompt __hang__` alone, with no
  `--cancel-prompt`, makes `cancellable_subagent.py` PASS `016/017` (`-k` on `_CHILD_STOP_K`), and that
  `--cancel-prompt __hang__` alone still does.
- **What stays unobservable:** whether a real agent's model *chooses* to delegate. The TCK can only make delegation
  likely. A SKIP with a supplied prompt remains "not exercised", never a FAIL.

## Discrepancies

None between spec and code. One internal inconsistency to be aware of: the two versions' built-in subagent-turn
prompts differ for no stated reason. v1 sends `"Summarize what you can help me with in this project."`
(`_subagents_connection.py:23`) and v2 sends `"hi"` (`v2/conformance/test_subagents.py:55`). With the default `None`
design that difference survives. Unifying it is an optional cleanup that would change real-agent traffic on the
default run, so leave it out unless the user wants it.

## Open questions (design decisions for the user)

1. **Scope: does `--subagent-prompt` also drive the child-cancel turn?**
   - **A.** The child-cancel turn uses the subagent prompt when it is given, otherwise `--cancel-prompt`. One flag
     covers every subagent row. Existing tests that pass `--cancel-prompt __hang__` keep working. This changes
     documented behaviour (`README.md:117-122`, `docs/mock-client.md:148-153`).
   - **B.** No: it applies only to the subagents connection (001..015/201). The cancel rows keep `--cancel-prompt` as
     documented today. This is the smallest change.
   - **C.** A separate `--subagent-cancel-prompt`. This is the most flexible, but it adds a third prompt flag.

   Trade-off: the cancel turn needs a child that is still *running* when the TCK reads it, while the 001.. turn must
   *finish* within the timeout. A single prompt such as "delegate a long essay to a subagent" can serve both only if
   the timeout is raised. B is the safe default; A is the most user-friendly.
2. **Timeout budget for the subagents-connection turn.** `run_prompt` enforces one overall deadline of `--timeout`
   (30 s by default; `src/tck/v1/conformance/_helpers.py:400-411,467-468,~590-593` raises `AgentTimeout`). The
   connection builder caches that error and re-raises it for every row (`_subagents_connection.py:63-77`;
   `v2/conformance/test_subagents.py:69-90`). So a real agent whose delegating turn takes more than 30 s turns
   CAPABILITY SKIPs into FAILs, and the verdict into NOT CONFORMANT. That follows the FAIL policy
   (`docs/writing-tests.md:84-86`) but would surprise users. The connection is built inside the first test that asks,
   so `--test-timeout` (120 s) also bounds it.
   - Options: (a) document "raise `--timeout`/`--test-timeout`"; (b) give that turn `timeout * 3` like
     `drive_child_cancel`, only when a subagent prompt is supplied or always; (c) both.

   (b) changes nothing for fixtures, which answer instantly.
3. **Default text.** Keep `None`, so the built-in prompts stay unchanged (recommended: no cross-check baseline or
   token-cost impact). Or ship a default delegating prompt, which changes every real-agent run and costs time and
   tokens. The cross-check runner passes only `--cancel-prompt wait_for_cancel` (`cross-check/run.sh:139-179`), so it
   is unaffected with `None`.
4. **Skip-vs-fail when a supplied prompt yields no child.** Recommendation: stay SKIPPED, because spawning is
   permitted, not required (agent-client-protocol `docs/rfds/subagents.mdx:12-16 @ 3961af94`, Active RFD; acp-tck
   `docs/writing-tests.md:82-83`). The open part is only cosmetic: whether to annotate the SKIP reason or record a
   report property noting a custom prompt was used.
5. **Side effect on MANDATORY rows (v1).** `ACP-CLIENTCAP-001..003` (MANDATORY; `src/tck/v1/requirements.py:1027,
   1046,1059`) also judge the v1 subagents connection, which advertises no `fs`/`terminal`/elicitation. A prompt that
   makes the agent do real work there is more likely to provoke `fs/*`/`terminal/*` requests and FAIL those rows.
   That is a correct finding, but users should know a subagent prompt can surface it. It is worth one README
   sentence.

## Risks

- **Timeout-induced FAILs on real agents** (question 2). This is the main usability risk.
- **The scope choice changes documented behaviour** if A is picked (question 1).
- **Fixture convention:** the new sentinel must not be the default text. Keep `None` as the default and use a
  `__subagent__`-style sentinel only in the self-tests.
- **v1 prompt also drives `session/load` replay judgement:** a richer turn means more replayed history. This is
  harmless and judged by the existing rules, but replay windows get longer. There is no code risk.

## Complexity estimate

**S (small).** Rough LOC:

| Part | LOC |
|---|---|
| product (`__init__.py`, `plugin.py`, two connection builders) | 50 to 70 |
| optional SKIP-annotation helper | 10 to 20 |
| two fixtures | 50 to 70 |
| CLI tests | 70 to 110 |
| docs | 30 to 40 lines |
| **Total** | **about 200 to 300** |

Reasoning:

- It is a mechanical copy of an existing, well-tested option pattern.
- The two touch points are already single cached builders, so one change covers every row.
- No requirement registry, ledger or spec-tracker change is needed: the row semantics and tiers are untouched.
- It fits in one PR beside other small follow-ups.

It grows toward M (about 400 LOC) only if the user picks option A or C in question 1, which means re-documenting the
cancel-prompt contract and adding control-turn tests, together with a dedicated timeout knob.
