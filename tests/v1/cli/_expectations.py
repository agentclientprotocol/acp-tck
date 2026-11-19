"""Hand-maintained id sets the CLI tests assert against: the requirement tiers (kept in sync
with the registry by `tests/v1/test_registry.py`) and the ids each conforming fixture is
expected to SKIP."""

from __future__ import annotations


_MANDATORY_IDS = {
    "ACP-TRANSPORT-001",
    "ACP-TRANSPORT-002",
    "ACP-JSONRPC-001",
    "ACP-JSONRPC-002",
    "ACP-JSONRPC-003",
    "ACP-JSONRPC-006",
    "ACP-JSONRPC-007",
    "ACP-INIT-001",
    "ACP-INIT-002",
    "ACP-INIT-003",
    "ACP-SCHEMA-001",
    "ACP-SESSION-001",
    "ACP-SESSION-002",
    "ACP-SESSION-003",
    "ACP-PROMPT-001",
    "ACP-PROMPT-002",
    "ACP-PROMPT-003",
    "ACP-PROMPT-004",
    "ACP-CANCEL-001",
    "ACP-CANCEL-002",
    "ACP-CONFIG-003",
    "ACP-AUTH-002",
    "ACP-AUTH-006",
    "ACP-CLIENTCAP-001",
    "ACP-CLIENTCAP-002",
    "ACP-CLIENTCAP-003",
    "ACP-CLIENTCAP-004",
    "ACP-CLIENTCAP-005",
    "ACP-CLIENTCAP-006",
    "ACP-CLIENTCAP-007",
    "ACP-CLIENTCAP-008",
    "ACP-CLIENTCAP-009",
    "ACP-PLAN-003",
    "ACP-PLAN-004",
    "ACP-SUGGEST-001",
    "ACP-SUGGEST-002",
    "ACP-CURSOR-001",
    "ACP-CURSOR-002",
    "ACP-EXT-001",
}
# The subagent rows judge a connection that advertises `clientCapabilities.subagents`. They are
# gated by what the agent exposes (`inferred:subagents`, or a self-SKIP for the ADVISORY ones),
# so every one SKIPs against a fixture that exposes no child, including `conforming.py`.
_SUBAGENT_CAPABILITY_IDS = {f"ACP-SUBAGENT-{n:03}" for n in (*range(1, 10), 15)}
_SUBAGENT_ADVISORY_IDS = {f"ACP-SUBAGENT-{n:03}" for n in range(11, 15)}
_SUBAGENT_IDS = _SUBAGENT_CAPABILITY_IDS | _SUBAGENT_ADVISORY_IDS
# The child-cancel rows need a running child that advertises `capabilities.cancel` in the driven
# `--cancel-prompt` turn, which only `cancellable_subagent.py` and its siblings offer. Every other
# fixture SKIPs them, `exposes_subagent.py` included.
_SUBAGENT_CANCEL_IDS = {"ACP-SUBAGENT-016", "ACP-SUBAGENT-017"}
# The child-session probes (`ACP-SUBAGENT-018`, `-019`, `ACP-LIST-004`) ask an agent that advertised
# `loadSession`/`list`/`close`/`delete` about an announced child, so they SKIP against every fixture
# that exposes no child or advertises none of those; only `exposes_subagent_full.py` and its
# siblings PASS them. `ACP-SUBAGENT-020` judges the reported states and PASSes wherever a child
# reports one.
_SUBAGENT_PROBE_IDS = {"ACP-SUBAGENT-018", "ACP-SUBAGENT-019", "ACP-LIST-004"}
_SUBAGENT_STATE_IDS = {"ACP-SUBAGENT-020"}

_ADVISORY_IDS = _SUBAGENT_ADVISORY_IDS | _SUBAGENT_STATE_IDS | {
    "ACP-SUBAGENT-018",
    "ACP-JSONRPC-004",
    "ACP-JSONRPC-005",
    "ACP-INIT-004",
    "ACP-SESSION-004",
    "ACP-SESSION-006",
    "ACP-LOAD-003",
    "ACP-LIST-003",
    "ACP-DELETE-002",
    "ACP-CLOSE-003",
    "ACP-META-001",
    "ACP-ERROR-001",
    "ACP-ERROR-002",
    "ACP-ERROR-003",
    "ACP-ERROR-004",
    "ACP-ERROR-005",
    "ACP-ERROR-006",
    "ACP-ERROR-007",
    "ACP-ERROR-008",
    "ACP-EXT-002",
    "ACP-SCHEMA-002",
    "ACP-AUTH-005",
    "ACP-AUTH-008",
    "ACP-PLAN-002",
    "ACP-PERM-001",
    "ACP-PERM-002",
    "ACP-SUGGEST-004",
    "ACP-CURSOR-004",
    "ACP-OPTIONS-007",
    "ACP-OPTIONS-008",
    "ACP-OPTIONS-009",
    # ACP-AUTH-001: its only assertion, AUTH-A5 (auth method ids are unique), is advisory in
    # the auth research -- not in _MANDATORY_IDS.
    "ACP-AUTH-001",
}
_INFORMATIONAL_IDS = {
    "ACP-SHUTDOWN-001",
    "ACP-STDERR-001",
    "ACP-INFO-PARSE-001",
    "ACP-INFO-INVALIDREQ-001",
    "ACP-OPTIONS-010",
}
_CAPABILITY_IDS = _SUBAGENT_CAPABILITY_IDS | _SUBAGENT_CANCEL_IDS | {
    "ACP-SUBAGENT-019",
    "ACP-LIST-004",
    "ACP-LOAD-001",
    "ACP-LOAD-002",
    "ACP-RESUME-001",
    "ACP-RESUME-002",
    "ACP-LIST-001",
    "ACP-LIST-002",
    "ACP-DELETE-001",
    "ACP-DELETE-003",
    "ACP-ARCHIVE-001",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-CLOSE-001",
    "ACP-CLOSE-002",
    "ACP-ADDDIRS-001",
    "ACP-SYSPROMPT-001",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-MODES-001",
    "ACP-MODES-002",
    "ACP-CONFIG-001",
    "ACP-CONFIG-002",
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-AUTH-004",
    "ACP-AUTH-007",
    # ACP-SUGGEST-003: CAPABILITY with capability="inferred:promptSuggestions" -- SKIPs itself
    # unless the agent sent a non-empty suggestion list before the second prompt.
    "ACP-SUGGEST-003",
    "ACP-CURSOR-003",
    "ACP-OPTIONS-001",
    "ACP-OPTIONS-002",
    "ACP-OPTIONS-003",
    "ACP-OPTIONS-004",
    "ACP-OPTIONS-005",
    "ACP-OPTIONS-006",
    "ACP-OPTIONS-011",
    # ACP-AUTH-003: CAPABILITY with capability="inferred:authMethods" -- runs only when
    # `authMethods` is non-empty and `--tck-auth-method` was given, otherwise SKIPPED.
    "ACP-AUTH-003",
}
_ALL_IDS = _MANDATORY_IDS | _ADVISORY_IDS | _CAPABILITY_IDS

_CANCEL_IDS = {"ACP-CANCEL-001", "ACP-CANCEL-002", "ACP-JSONRPC-007"}
"""None of the fixtures below `hangs_until_cancel.py`, `cancel_returns_error.py`,
`cancel_wrong_stop_reason.py`, and `update_after_response.py` deliberately withhold their
response until `session/cancel` arrives for arbitrary prompt text -- they resolve the turn
immediately, same as `conforming.py`. So for all of them, `session/cancel` (and
`ACP-JSONRPC-007`'s `$/cancel_request`) always loses the race and the cancel tests SKIP with
"cancellation not exercised" rather than PASS or FAIL."""

_CAPABILITY_GATED_IDS = _CAPABILITY_IDS | _SUBAGENT_ADVISORY_IDS | _SUBAGENT_STATE_IDS | {
    "ACP-SUBAGENT-018",
    "ACP-LOAD-003",
    "ACP-LIST-003",
    "ACP-DELETE-002",
    "ACP-CLOSE-003",
    "ACP-AUTH-008",
    "ACP-ERROR-004",
    "ACP-ERROR-007",
    "ACP-PERM-001",
    "ACP-PERM-002",
    "ACP-SUGGEST-004",
    "ACP-CURSOR-004",
    "ACP-OPTIONS-007",
    "ACP-OPTIONS-008",
    "ACP-OPTIONS-009",
    "ACP-OPTIONS-010",
}
"""Every id that SKIPs (rather than PASSes) against `conforming.py`, which advertises
`agentCapabilities: {}` and no modes/configOptions/authMethods -- every CAPABILITY-tier id
(including `ACP-AUTH-003`, `capability="inferred:authMethods"` and the `inferred:subagents` rows),
plus the ADVISORY `ACP-SUBAGENT-011..014`, the INFORMATIONAL `ACP-OPTIONS-010` and the fourteen ADVISORY ids
(`ACP-LOAD-003`, `ACP-LIST-003`, `ACP-DELETE-002`, `ACP-CLOSE-003`, `ACP-AUTH-008`, `ACP-ERROR-004`, `ACP-ERROR-007`,
`ACP-PERM-001`, `ACP-PERM-002`, `ACP-SUGGEST-004`, `ACP-CURSOR-004`, `ACP-OPTIONS-007`, `ACP-OPTIONS-008`, `ACP-OPTIONS-009`) whose tests are still gated (by a `@pytest.mark.capability(...)`
marker, for `ACP-ERROR-004`/`007` by what `session/new` returned, for `ACP-PERM-*` by the agent
never sending `session/request_permission`) even though their `Requirement.tier` itself is
ADVISORY, not CAPABILITY (see `test_session_capabilities.py` module docstring)."""
