"""Hand-maintained id sets the CLI tests assert against: the requirement tiers (kept in sync
with the registry by `tests/v2/test_registry.py`) and the ids each conforming fixture is
expected to SKIP."""

from __future__ import annotations


_MANDATORY_IDS = {
    "ACP-INIT-001",
    "ACP-INIT-003",
    "ACP-INIT-201",
    "ACP-INIT-202",
    "ACP-INIT-004",
    "ACP-INIT-204",
    "ACP-INIT-205",
    "ACP-INIT-206",
    "ACP-INIT-207",
    "ACP-INIT-208",
    "ACP-ERROR-005",
    "ACP-INIT-210",
    "ACP-INIT-211",
    "ACP-INIT-212",
    "ACP-INIT-213",
    "ACP-INIT-214",
    "ACP-SCHEMA-001",
    "ACP-TRANSPORT-001",
    "ACP-TRANSPORT-002",
    "ACP-TRANSPORT-203",
    "ACP-JSONRPC-001",
    "ACP-JSONRPC-002",
    "ACP-JSONRPC-003",
    "ACP-JSONRPC-004",
    "ACP-JSONRPC-202",
    "ACP-ERROR-006",
    "ACP-JSONRPC-006",
    "ACP-CANCEL-211",
    "ACP-AUTH-001",
    "ACP-AUTH-002",
    "ACP-AUTH-206",
    "ACP-AUTH-006",
    "ACP-EXT-001",
    "ACP-EXT-204",
}
_CAPABILITY_IDS = {
    "ACP-SUBAGENT-019",
    "ACP-SUBAGENT-203",
    "ACP-SUBAGENT-204",
    "ACP-SUBAGENT-205",
    "ACP-SUBAGENT-206",
    "ACP-LIST-004",
    "ACP-ENUM-201",
    "ACP-ENUM-203",
    "ACP-META-203",
    "ACP-SESSION-001",
    "ACP-SESSION-002",
    "ACP-PROMPT-002",
    "ACP-PROMPT-201",
    "ACP-PROMPT-203",
    "ACP-STATE-201",
    "ACP-STATE-202",
    "ACP-STATE-203",
    "ACP-STATE-205",
    "ACP-STATE-206",
    "ACP-STATE-207",
    "ACP-STATE-208",
    "ACP-PROMPT-003",
    "ACP-PROMPT-207",
    "ACP-PROMPT-209",
    "ACP-PROMPT-211",
    "ACP-PROMPT-212",
    "ACP-PROMPT-213",
    "ACP-PROMPT-214",
    "ACP-PROMPT-215",
    "ACP-PROMPT-217",
    "ACP-PROMPT-218",
    "ACP-PROMPT-219",
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PROMPTCAP-201",
    "ACP-PROMPTCAP-202",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-PERM-204",
    "ACP-CLIENTCAP-003",
    "ACP-CLIENTCAP-008",
    "ACP-CLIENTCAP-202",
    "ACP-CLIENTCAP-203",
    "ACP-SUGGEST-001",
    "ACP-SUGGEST-002",
    "ACP-SUGGEST-003",
    "ACP-CURSOR-001",
    "ACP-CURSOR-002",
    "ACP-CURSOR-003",
    "ACP-OPTIONS-001",
    "ACP-OPTIONS-002",
    "ACP-OPTIONS-003",
    "ACP-OPTIONS-004",
    "ACP-OPTIONS-005",
    "ACP-OPTIONS-006",
    "ACP-OPTIONS-011",
    "ACP-CANCEL-001",
    "ACP-CANCEL-002",
    "ACP-CANCEL-203",
    "ACP-CANCEL-205",
    "ACP-CANCEL-206",
    "ACP-CANCEL-207",
    "ACP-CANCEL-208",
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-JSONRPC-007",
    "ACP-CANCEL-214",
    "ACP-SESSION-203",
    "ACP-SESSION-204",
    "ACP-SESSION-208",
    "ACP-RESUME-001",
    "ACP-RESUME-202",
    "ACP-RESUME-002",
    "ACP-RESUME-204",
    "ACP-RESUME-205",
    "ACP-RESUME-206",
    "ACP-RESUME-207",
    "ACP-RESUME-208",
    "ACP-RESUME-209",
    "ACP-RESUME-210",
    "ACP-RESUME-212",
    "ACP-RESUME-213",
    "ACP-RESUME-217",
    "ACP-RESUME-218",
    "ACP-RESUME-219",
    "ACP-RESUME-220",
    "ACP-RESUME-221",
    "ACP-RESUME-223",
    "ACP-RESUME-224",
    "ACP-RESUME-225",
    "ACP-RESUME-226",
    "ACP-ERROR-003",
    "ACP-ERROR-004",
    "ACP-LIST-001",
    "ACP-LIST-002",
    "ACP-LIST-203",
    "ACP-LIST-204",
    "ACP-LIST-205",
    "ACP-LIST-003",
    "ACP-CLOSE-001",
    "ACP-CLOSE-002",
    "ACP-CLOSE-203",
    "ACP-CLOSE-205",
    "ACP-CLOSE-206",
    "ACP-DELETE-001",
    "ACP-DELETE-003",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-ADDDIRS-001",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-203",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-FORK-206",
    "ACP-SYSPROMPT-001",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-CONFIG-201",
    "ACP-CONFIG-002",
    "ACP-CONFIG-203",
    "ACP-CONFIG-001",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-COMMANDS-201",
    "ACP-COMMANDS-202",
    "ACP-AUTH-004",
    "ACP-AUTH-003",
    "ACP-AUTH-208",
    "ACP-AUTH-007",
    "ACP-AUTH-008",
    "ACP-PATCH-201",
    "ACP-PATCH-203",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PLAN-003",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-210",
    "ACP-PATCH-213",
    "ACP-PATCH-214",
    "ACP-PATCH-215",
    "ACP-TOOLCANCEL-201",
    "ACP-TOOLCANCEL-202",
    "ACP-TERMCANCEL-201",
    "ACP-TERMCANCEL-202",
    "ACP-TOOLCANCEL-203",
    "ACP-TERMCANCEL-203",
    "ACP-TOOLCANCEL-204",
    "ACP-TERMCANCEL-204",
    "ACP-TOOLCANCEL-206",
    "ACP-TERMCANCEL-206",
    "ACP-TOOLCANCEL-208",
    "ACP-TERMCANCEL-208",
    "ACP-TOOLCANCEL-210",
    "ACP-TERMCANCEL-210",
    "ACP-SUBAGENT-016",
    "ACP-SUBAGENT-017",
    "ACP-SUBAGENT-202",
    "ACP-SUBAGENT-001",
    "ACP-SUBAGENT-002",
    "ACP-SUBAGENT-003",
    "ACP-SUBAGENT-004",
    "ACP-SUBAGENT-005",
    "ACP-SUBAGENT-006",
    "ACP-SUBAGENT-007",
    "ACP-SUBAGENT-008",
    "ACP-SUBAGENT-009",
}
_ADVISORY_IDS = {
    "ACP-PROMPT-216",
    "ACP-PROMPT-220",
    "ACP-INIT-215",
    "ACP-SUBAGENT-011",
    "ACP-SUBAGENT-012",
    "ACP-SUBAGENT-013",
    "ACP-SUBAGENT-014",
    "ACP-SUBAGENT-201",
    "ACP-SUBAGENT-207",
    "ACP-SUBAGENT-018",
    "ACP-STATE-204",
    "ACP-STATE-209",
    "ACP-STATE-210",
    "ACP-SUGGEST-004",
    "ACP-RESUME-222",
    "ACP-CURSOR-004",
    "ACP-OPTIONS-007",
    "ACP-OPTIONS-008",
    "ACP-OPTIONS-009",
    "ACP-CANCEL-204",
    "ACP-JSONRPC-005",
    "ACP-BATCH-209",
    "ACP-DELETE-002",
    "ACP-CLOSE-204",
    "ACP-CLOSE-003",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-SESSION-206",
    "ACP-SESSION-207",
    "ACP-SESSION-209",
    "ACP-LIST-207",
    "ACP-LIST-208",
    "ACP-LIST-209",
    "ACP-RESUME-214",
    "ACP-RESUME-216",
    "ACP-MCP-204",
    "ACP-SESSION-006",
    "ACP-AUTH-005",
    "ACP-AUTH-210",
    "ACP-AUTH-211",
    "ACP-ADDDIRS-204",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-PATCH-216",
    "ACP-TOOLCANCEL-205",
    "ACP-TERMCANCEL-205",
    "ACP-TOOLCANCEL-207",
    "ACP-TERMCANCEL-207",
    "ACP-TOOLCANCEL-209",
    "ACP-TERMCANCEL-209",
    "ACP-TOOLCANCEL-211",
    "ACP-TERMCANCEL-211",
    "ACP-META-001",
    "ACP-META-201",
    "ACP-META-202",
    "ACP-META-204",
    "ACP-ENUM-204",
    "ACP-EXT-002",
    "ACP-EXT-202",
    "ACP-EXT-203",
    "ACP-ERROR-001",
    "ACP-ERROR-008",
    "ACP-ERROR-204",
    "ACP-SHUTDOWN-001",
    "ACP-SCHEMA-002",
}
_INFORMATIONAL_IDS = {
    "ACP-INFO-CONCURRENT-201",
    "ACP-INFO-CANCEL-201",
    "ACP-INFO-BACKGROUND-201",
    "ACP-INFO-BACKGROUND-202",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-STDERR-001",
    "ACP-INFO-PARSE-001",
    "ACP-INFO-INVALIDREQ-001",
    "ACP-OPTIONS-010",
    "ACP-OPTIONS-201",
}
_ALL_IDS = _MANDATORY_IDS | _CAPABILITY_IDS | _ADVISORY_IDS | _INFORMATIONAL_IDS

# `ACP-CANCEL-204` (an unconditional record-only probe for cancellation) never PASSes for *any*
# fixture; it always SKIPs -- except that `ACP-CANCEL-204` FAILs instead of
# SKIPping against a fixture that hangs forever on `session/cancel` (`cancel_no_idle.py` and its
# siblings): an uncaught `AgentTimeout` in shared setup is a FAIL, not a SKIP, so "always" here
# means "for any fixture that lets the turn reach a terminating idle", not literally always.
#
# `ACP-INIT-208` only judges a result that selects v1, which a v2-only fixture never returns (it
# rejects v1 with -32022), so it SKIPs for every `_base.py` fixture except the dual-stack ones.
_V2_ONLY_SKIP_IDS = {"ACP-INIT-208"}
_ALWAYS_SKIPPED_IDS = {"ACP-CANCEL-204"} | _V2_ONLY_SKIP_IDS

# CAPABILITY-tier cancel rows that need a turn to still be in flight when `session/cancel` is
# sent to be exercised at all -- against a fast fixture with no `--cancel-prompt` override the
# turn routinely resolves before the TCK can act, so these legitimately SKIP ("cancellation not
# exercised") rather than PASS. `ACP-CANCEL-205` (no direct response to the cancel notification
# itself) holds regardless of the race outcome, so it is not in this set. `ACP-CLOSE-002` shares
# `ACP-CANCEL-208`'s exact test (`test_close_cancels_foreground_work`), so it races the same way;
# `ACP-CLOSE-203` drives the same close-mid-turn scenario and SKIPs unless the turn ended
# `cancelled`. `ACP-PROMPT-209`/`ACP-CANCEL-214`/`ACP-INFO-CONCURRENT-201` need the first turn
# still active when the second prompt is read, so they SKIP for the same reason.
_CANCEL_RACE_SKIP_IDS = {
    "ACP-CANCEL-001",
    "ACP-CANCEL-002",
    "ACP-CANCEL-203",
    "ACP-CANCEL-206",
    "ACP-CANCEL-207",
    "ACP-CANCEL-208",
    "ACP-CANCEL-214",
    "ACP-ARCHIVE-201",
    "ACP-CLOSE-002",
    "ACP-CLOSE-203",
    "ACP-DELETE-204",
    "ACP-INFO-CONCURRENT-201",
    "ACP-PROMPT-209",
    "ACP-PROMPT-215",
}

# The background-work rows judge only an agent that reports a `background` list, which no
# `_base.py` fixture does unless it opts into `report_background_work`
# (`reports_background_work.py` and the `background_*.py` defect fixtures).
_BACKGROUND_SKIP_IDS = {"ACP-STATE-206", "ACP-STATE-207", "ACP-STATE-208"}

# The `tool_call/cancel`/`terminal/cancel` rows judge only an item that advertises
# `capabilities.cancel` while still live, which no `_base.py` fixture offers unless it opts into
# `cancellable_work` (`conforming_full.py` and the `*_cancel_*` defect fixtures) and the cancel
# prompt is `__hang__`. The `-204`/`-205` rows judge only an item that is final yet still
# advertises `cancel` (`keeps_cancel_after_final.py` and its defect siblings), so they also SKIP for
# `conforming_full.py`, whose items stop advertising it. The `-206`/`-207` unknown-id rows judge
# a request sent once an item of the kind advertised `cancel` during the turn, so they SKIP
# wherever nothing advertises it. The `-208`/`-209` not-cancellable rows also need a live item
# without `cancel`, which only `uncancellable_work` (`conforming_full.py`, the `*uncancellable*`
# fixtures) or an agent that withdraws `cancel` from a live item offers. The `-210`/`-211` repeat
# rows judge a request sent again for the item the main request was accepted for, once it is final
# and no longer advertises `cancel`: they SKIP wherever the main request was not accepted and
# confirmed, and wherever the item keeps advertising `cancel` (the already-final rows judge that).
_ITEM_ACCEPT_IDS = {"ACP-TOOLCANCEL-201", "ACP-TOOLCANCEL-202", "ACP-TERMCANCEL-201", "ACP-TERMCANCEL-202"}
_STALE_CANCEL_IDS = {"ACP-TOOLCANCEL-204", "ACP-TOOLCANCEL-205", "ACP-TERMCANCEL-204", "ACP-TERMCANCEL-205"}
_UNKNOWN_CANCEL_IDS = {"ACP-TOOLCANCEL-206", "ACP-TOOLCANCEL-207", "ACP-TERMCANCEL-206", "ACP-TERMCANCEL-207"}
_UNCANCELLABLE_CANCEL_IDS = {
    "ACP-TOOLCANCEL-208",
    "ACP-TOOLCANCEL-209",
    "ACP-TERMCANCEL-208",
    "ACP-TERMCANCEL-209",
}
_REPEAT_CANCEL_IDS = {"ACP-TOOLCANCEL-210", "ACP-TOOLCANCEL-211", "ACP-TERMCANCEL-210", "ACP-TERMCANCEL-211"}
_ITEM_CANCEL_IDS = (
    _ITEM_ACCEPT_IDS | _STALE_CANCEL_IDS | _UNKNOWN_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS | _REPEAT_CANCEL_IDS
)

# The child-stop rows judge only a running child that advertises `capabilities.cancel` (or a child's
# own cancellable tool call or terminal) in the `__hang__` turn: only `cancellable_subagent.py` and
# its siblings offer one, so every other fixture SKIPs them, `exposes_subagent.py` and
# `conforming_full.py` included.
_CHILD_CONTROL_IDS = {
    "ACP-SUBAGENT-016",
    "ACP-SUBAGENT-017",
    "ACP-SUBAGENT-202",
    "ACP-TOOLCANCEL-203",
    "ACP-TERMCANCEL-203",
}

# The child replay and withdrawal rows judge only children on the wire: `ACP-RESUME-223` a child
# announced in a replay resume (`replays_subagent_history.py`), `-224` a `subagent` item in the
# resume snapshot (`resume_lists_background_subagent.py`), `-225` child traffic after a resume
# without replay and `-226` replayed history of a child seen before the resume (both
# `replays_subagent_history.py`), `ACP-SUBAGENT-203` a child permission request
# pending at `session/close` (`exposes_subagent.py` and its siblings) and `-204` one pending when
# a cancellation stops its child (`cancellable_subagent_asks.py`). Every other fixture SKIPs them.
_CHILD_REPLAY_WITHDRAWAL_IDS = {
    "ACP-RESUME-223",
    "ACP-RESUME-224",
    "ACP-RESUME-225",
    "ACP-RESUME-226",
    "ACP-SUBAGENT-203",
    "ACP-SUBAGENT-204",
}

# `ACP-RESUME-213` judges only a resume snapshot that lists background work, and SKIPs otherwise.
# Only a fixture with `background_on_resume` (`resume_lists_background_work.py` and its defect
# sibling) leaves live work at resume; no other fixture does, not even
# `reports_background_work.py`, whose turns finish their work before they end.
_RESUME_BACKGROUND_SKIP_IDS = {"ACP-RESUME-213"}

# The other background rows judge only an agent that reports a `background` list, and
# `ACP-STATE-209` needs one of its items to end while idle (`background_outlives_turn="finish"`),
# `ACP-STATE-210` one to start while idle (`background_after_idle`), `ACP-INFO-BACKGROUND-202` a list that is non-empty when `session/cancel` lands. A fixture that
# merely reports lists (`reports_background_work.py`) PASSes `ACP-RESUME-217` and
# `ACP-INFO-BACKGROUND-201` and SKIPs the other three.
_BACKGROUND_OTHER_SKIP_IDS = {
    "ACP-STATE-209",
    "ACP-STATE-210",
    "ACP-INFO-BACKGROUND-201",
    "ACP-INFO-BACKGROUND-202",
    "ACP-RESUME-217",
}

# A fixture that advertises only the bare `capabilities: {"session": {}}}` baseline (or nothing
# session-related at all) legitimately SKIPs the session-management extras below -- `delete`,
# `additionalDirectories`, `mcp`, `fork`, `systemPrompt`, and `configOptions` (inferred from
# `session/new`'s own result, not a capability marker) -- exactly as it does for `conforming.py`
# itself (see
# `test_v2_conforming_agent_passes_everything` above). `ACP-SESSION-203`/`ACP-RESUME-*`/
# `ACP-LIST-*`/`ACP-CLOSE-001` are NOT in this set: they are gated on the baseline
# `capabilities.session` marker alone, present even as `{}`.
_SESSION_MGMT_EXTRAS_SKIP_IDS = {
    "ACP-DELETE-001",
    "ACP-DELETE-003",
    "ACP-DELETE-002",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-LIST-208",
    "ACP-LIST-209",
    "ACP-ADDDIRS-001",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-MCP-204",
    "ACP-SESSION-006",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-FORK-206",
    "ACP-SYSPROMPT-001",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-CONFIG-201",
    "ACP-CONFIG-002",
    "ACP-CONFIG-203",
    "ACP-CONFIG-001",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-COMMANDS-201",
    "ACP-COMMANDS-202",
    "ACP-RESUME-210",  # neither `configOptions` nor `availableCommands` to carry over
}

# A fixture that advertises no `authMethods` and no `capabilities.auth.status`, run with no
# `--auth-method`/`--allow-logout`, legitimately SKIPs these ids: `ACP-AUTH-003`/`004`/`208`/`210`
# all need `authMethods` non-empty (`203` additionally needs `--allow-logout`); `ACP-AUTH-006`
# needs a `type: "terminal"` entry to appear on a dedicated connection advertising
# `capabilities.auth.terminal`; `ACP-AUTH-007`/`008` need `capabilities.auth.status`.
# `ACP-AUTH-001`/`206` also SKIP here: with no `authMethods` advertised at all there is nothing
# to check uniqueness/type-shape of, and a MANDATORY/ADVISORY row SKIPping on "nothing to check"
# is more honest than a vacuous PASS. `ACP-AUTH-002`/`005` are NOT in this set: each is judged
# against the empty-`authMethods` case itself and PASSes.
_NO_AUTH_SKIP_IDS = {
    "ACP-AUTH-001",
    "ACP-AUTH-004",
    "ACP-AUTH-003",
    "ACP-AUTH-206",
    "ACP-AUTH-006",
    "ACP-AUTH-208",
    "ACP-AUTH-007",
    "ACP-AUTH-008",
    "ACP-AUTH-210",
    "ACP-AUTH-211",
}


_CONFORMING_EXPECTED_SKIPS = {
    "ACP-PROMPT-218",  # the fixture keeps no session across processes
    "ACP-SUGGEST-001",  # the fixture sends no suggestion
    "ACP-SUGGEST-002",
    "ACP-SUGGEST-003",
    "ACP-SUGGEST-004",
    "ACP-RESUME-222",  # the fixture sends no request during a resume
    "ACP-CURSOR-001",  # the fixture announces no cursor
    "ACP-CURSOR-002",
    "ACP-CURSOR-003",  # ... and advertises no `fork`
    "ACP-CURSOR-004",
    "ACP-OPTIONS-001",  # the fixture advertises no `session.options`
    "ACP-OPTIONS-002",
    "ACP-OPTIONS-003",
    "ACP-OPTIONS-009",
    "ACP-OPTIONS-004",
    "ACP-OPTIONS-005",
    "ACP-OPTIONS-006",
    "ACP-OPTIONS-007",
    "ACP-OPTIONS-008",
    "ACP-OPTIONS-010",
    "ACP-OPTIONS-011",
    "ACP-OPTIONS-201",
    "ACP-JSONRPC-202",
    "ACP-ERROR-204",
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PROMPTCAP-202",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-PERM-204",
    "ACP-DELETE-001",
    "ACP-DELETE-003",
    "ACP-DELETE-002",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-LIST-208",  # the fixture advertises no `session.title`
    "ACP-LIST-209",  # the fixture advertises no `session.title`
    "ACP-ADDDIRS-001",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-MCP-204",
    "ACP-SESSION-006",
    "ACP-CONFIG-201",
    "ACP-CONFIG-002",
    "ACP-CONFIG-203",
    "ACP-CONFIG-001",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-COMMANDS-201",
    "ACP-COMMANDS-202",
    "ACP-RESUME-210",
    "ACP-SUBAGENT-001",
    "ACP-SUBAGENT-002",
    "ACP-SUBAGENT-003",
    "ACP-SUBAGENT-004",
    "ACP-SUBAGENT-005",
    "ACP-SUBAGENT-006",
    "ACP-SUBAGENT-007",
    "ACP-SUBAGENT-008",
    "ACP-SUBAGENT-009",
    "ACP-SUBAGENT-011",
    "ACP-SUBAGENT-012",
    "ACP-SUBAGENT-013",
    "ACP-SUBAGENT-014",
    "ACP-SUBAGENT-201",
    "ACP-SUBAGENT-205",
    "ACP-SUBAGENT-206",
    "ACP-SUBAGENT-207",
    "ACP-SUBAGENT-018",
    "ACP-SUBAGENT-019",
    "ACP-LIST-004",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-FORK-206",
    "ACP-SYSPROMPT-001",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-AUTH-001",
    "ACP-AUTH-004",
    "ACP-AUTH-003",
    "ACP-AUTH-206",
    "ACP-AUTH-006",
    "ACP-AUTH-208",
    "ACP-AUTH-007",
    "ACP-AUTH-008",
    "ACP-AUTH-210",
    "ACP-AUTH-211",
    "ACP-ENUM-203",
    "ACP-ENUM-204",
    "ACP-META-203",
    "ACP-META-204",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PLAN-003",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-210",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-PATCH-213",
    "ACP-PATCH-214",
    "ACP-PATCH-215",
    "ACP-PATCH-216",
    "ACP-STATE-205",
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-PROMPT-207",
} | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS | _BACKGROUND_OTHER_SKIP_IDS | _ITEM_CANCEL_IDS | _CHILD_CONTROL_IDS | _CHILD_REPLAY_WITHDRAWAL_IDS | _CANCEL_RACE_SKIP_IDS | _ALWAYS_SKIPPED_IDS
