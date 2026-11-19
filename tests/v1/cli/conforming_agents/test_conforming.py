"""Full `acp-tck` runs against the conforming fixture agents: every row PASSes or SKIPs as
expected, and the verdict is CONFORMANT."""

from __future__ import annotations

from .._expectations import (
    _ALL_IDS,
    _CANCEL_IDS,
    _CAPABILITY_GATED_IDS,
    _INFORMATIONAL_IDS,
    _SUBAGENT_CANCEL_IDS,
    _SUBAGENT_IDS,
    _SUBAGENT_PROBE_IDS,
    _SUBAGENT_STATE_IDS,
)
from .._runner import _run_cli, _table_statuses


def test_conforming_agent_passes_everything():
    """`conforming.py` only withholds a response for the literal `__hang__` prompt text (see
    its docstring), which the cancel tests deliberately do not send -- the TCK must not rely on
    a fixture's own sentinel, and a real agent doesn't know it either. So `session/cancel`
    always loses the race against this fixture's immediate reply, and ACP-CANCEL-001/002 SKIP
    ("cancellation not exercised") rather than PASS. `conforming.py` also advertises
    `agentCapabilities: {}` (no `loadSession`, no `sessionCapabilities`), so every
    CAPABILITY-tier id -- plus the ADVISORY ids gated behind a capability or an advertised
    mode/config option (`_CAPABILITY_GATED_IDS` above) -- SKIPs too, rather than PASSing or being
    NOT_TESTED. Everything else still PASSes, including `ACP-ERROR-005`/`006` (this fixture rejects pre-initialize requests and
    every unadvertised gated method)."""
    result = _run_cli("conforming.py")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    # `_table_statuses` must parse INFORMATIONAL-tier rows too -- they carry a trailing `(note)`
    # suffix that would otherwise make them silently vanish, coincidentally matching `_ALL_IDS`,
    # which was never meant to include them -- so compare against the union explicitly rather
    # than let that omission look intentional.
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, (
        f"requirement table missing/extra ids: {result.stdout}"
    )
    skip_ids = _CANCEL_IDS | _CAPABILITY_GATED_IDS
    for req_id in skip_ids:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised/unadvertised):\n{result.stdout}"
    for req_id, status in statuses.items():
        if req_id in skip_ids:
            continue
        assert status == "PASS", f"{req_id} is {status}, expected PASS for the conforming fixture:\n{result.stdout}"
    assert "NOT TESTED" not in result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_conforming_full_agent_passes_everything_with_cancel_prompt_hang():
    """`conforming_full.py` advertises `loadSession: true`, every `sessionCapabilities` marker,
    modes, config options, every `promptCapabilities`, and the auth surface -- so every
    CAPABILITY-tier id (plus the two capability-gated ADVISORY ids) should PASS instead of
    SKIPPING. `--cancel-prompt __hang__` is required: it's the only prompt text `_base.py`'s
    `_handle_prompt` withholds a response for, so it's what lets ACP-CANCEL-001/002 and
    ACP-CLOSE-002 actually exercise their cancellation/close-race logic instead of SKIPPING as
    "not exercised". `--auth-method tck` is required for ACP-AUTH-003 to PASS instead of SKIP,
    since `conforming_full.py` advertises an `authMethods` entry with that id. `--allow-logout`
    is required for ACP-AUTH-004 to PASS instead of SKIP -- calling `logout` for real is opt-in
    (see `test_conforming_full_agent_without_allow_logout_only_skips_auth_004` below for the
    default-off behaviour).

    `ACP-AUTH-005` (AUTH-A1) is the one ADVISORY id that legitimately SKIPs here rather than
    PASSing: it only concerns an agent that advertises *no* `authMethods`, and
    `conforming_full.py` deliberately advertises one -- that is inapplicability, not a
    conformance gap, exactly like `ACP-AUTH-003` SKIPping without `--auth-method`. `ACP-ERROR-006`
    likewise SKIPs: it probes only unadvertised gated methods, and this fixture advertises all."""
    result = _run_cli(
        "conforming_full.py", cancel_prompt="__hang__", auth_method="tck", allow_logout=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, (
        f"requirement table missing/extra ids: {result.stdout}"
    )
    # The subagent rows SKIP too: `conforming_full.py` exposes no child (`exposes_subagent.py`
    # and `replays_subagent_history.py` exercise them, `cancellable_subagent.py` the cancel rows).
    not_applicable = {"ACP-AUTH-005", "ACP-ERROR-006"} | _SUBAGENT_IDS | _SUBAGENT_CANCEL_IDS
    not_applicable |= _SUBAGENT_PROBE_IDS | _SUBAGENT_STATE_IDS
    for req_id, status in statuses.items():
        if req_id in not_applicable:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED (not applicable):\n{result.stdout}"
            continue
        assert status == "PASS", f"{req_id} is {status}, expected PASS for conforming_full.py:\n{result.stdout}"
    assert "NOT TESTED" not in result.stdout
    assert all(
        status != "SKIPPED" for req_id, status in statuses.items() if req_id not in not_applicable
    ), result.stdout


def test_conforming_full_agent_without_allow_logout_only_skips_auth_004():
    """Acceptance criterion: the same `conforming_full.py --auth-method tck` run, but WITHOUT
    `--allow-logout`, must SKIP ONLY `ACP-AUTH-004` in addition to the baseline's own SKIP
    (`ACP-AUTH-005`/`ACP-ERROR-006`, per
    `test_conforming_full_agent_passes_everything_with_cancel_prompt_hang` above) -- every other id keeps the exact same status. Calling `logout` for real is opt-in
    (v2's `ACP-AUTH-004` gates `auth/logout` the same way); a SKIPPED CAPABILITY does not affect the verdict."""
    result = _run_cli(
        "conforming_full.py", cancel_prompt="__hang__", auth_method="tck", allow_logout=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, (
        f"requirement table missing/extra ids: {result.stdout}"
    )
    expected_skips = {"ACP-AUTH-004", "ACP-AUTH-005", "ACP-ERROR-006"} | _SUBAGENT_IDS | _SUBAGENT_CANCEL_IDS
    expected_skips |= _SUBAGENT_PROBE_IDS | _SUBAGENT_STATE_IDS
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS without --allow-logout:\n{result.stdout}"
