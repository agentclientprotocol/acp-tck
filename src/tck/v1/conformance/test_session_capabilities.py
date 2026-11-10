"""Capability-conditional session-method conformance: `session/load`, `session/resume`,
`session/list`, `session/delete`, `session/archive`/`session/unarchive`, `session/close`,
`additionalDirectories`, and `systemPrompt` (ACP-LOAD-001..003, ACP-RESUME-001/002,
ACP-LIST-001..003, ACP-DELETE-001..003, ACP-ARCHIVE-001..006, ACP-CLOSE-001..003,
ACP-ADDDIRS-001, ACP-SYSPROMPT-001..003).

Every test here is gated by `@pytest.mark.capability(...)`, including the ADVISORY-tier ones
(`ACP-LOAD-003`, `ACP-LIST-003`, `ACP-DELETE-002`, `ACP-CLOSE-003`): per `tck.common.plugin._tck_capability_gate`,
the marker's SKIP-if-unadvertised effect is independent of the bound `Requirement`'s tier, so gating an
ADVISORY requirement this way doesn't violate `Requirement.capability`'s "must be `None` for
non-CAPABILITY tiers" invariant (checked in `tck.v1.requirements`).
"""

from __future__ import annotations

import contextlib

import pytest

from tck.common.harness import AgentExited, AgentTimeout
from tck.common.plugin import capability_is_supported
from tck.v1.protocol import AUTHENTICATION_REQUIRED, INVALID_PARAMS, RESOURCE_NOT_FOUND, STOP_REASONS
from tck.v1.validation import validate_agent_response

from ._helpers import (
    HISTORY_KINDS,
    connected_agent,
    new_session,
    quiet_period,
    run_prompt,
    session_update_kind,
    skip_if_auth_gated,
    skip_if_version_mismatch,
)


# --- session/load ---


@pytest.mark.requirement("ACP-LOAD-001")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_load_succeeds_and_validates(agent_launch, tmp_path):
    """ACP-LOAD-001."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent, session_id, [{"type": "text", "text": "hello"}], timeout=agent_launch.default_timeout
        )

        req_id = await agent.send_request(
            "session/load",
            {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []},
        )
        # A load may legitimately replay history before its response -- drain it like
        # `run_prompt` does, rather than assuming the very next line is the response.
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/load did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/load", msg)
        assert not issues, f"session/load result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-LOAD-002")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_load_replays_before_responding_and_nothing_after(agent_launch, tmp_path):
    """ACP-LOAD-002. The "before" half is structural: `wait_for_response` reads line-by-line
    and stops at the matching response, so anything already seen arrived first. This test
    adds the "after" half: no further history-kind update (`HISTORY_KINDS`) for this session
    may arrive within a quiet period once the response is in hand. Session-state updates
    (e.g. `available_commands_update`) are allowed outside a turn and are ignored."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent, session_id, [{"type": "text", "text": "hello"}], timeout=agent_launch.default_timeout
        )

        req_id = await agent.send_request(
            "session/load",
            {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []},
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/load did not succeed: {entry.text!r}"
        )

        def _is_history_update_for_this_session(candidate_entry) -> bool:
            return session_update_kind(candidate_entry, session_id) in HISTORY_KINDS

        # An agent that exits promptly rather than staying connected through the quiet period
        # raises AgentExited on EOF, not AgentTimeout -- still "no late update arrived," not a
        # defect this requirement is about.
        with pytest.raises((AgentTimeout, AgentExited)):
            await agent.wait_for_message(
                _is_history_update_for_this_session,
                timeout=quiet_period(agent_launch.default_timeout),
            )


@pytest.mark.requirement("ACP-LOAD-003")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_load_empty_result_is_object_not_null(agent_launch, tmp_path):
    """ACP-LOAD-003 (ADVISORY). Mandatory schema validation (ACP-LOAD-001) already tolerates a
    literal `null` result for this all-optional-fields response, so this test asserts the
    stricter, non-schema-visible fact directly: the result must be `{}`-shaped, not `null`."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        req_id = await agent.send_request(
            "session/load",
            {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []},
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/load did not succeed: {entry.text!r}"
        )
        assert isinstance(msg["result"], dict), (
            f"session/load result should be an object ({{}}), not {msg['result']!r}"
        )


# --- session/resume ---


@pytest.mark.requirement("ACP-RESUME-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.resume")
async def test_resume_succeeds_and_validates(agent_launch, tmp_path):
    """ACP-RESUME-001."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        req_id = await agent.send_request(
            "session/resume", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/resume did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/resume", msg)
        assert not issues, f"session/resume result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-RESUME-002")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.resume")
async def test_resume_sends_no_history_before_responding(agent_launch, tmp_path):
    """ACP-RESUME-002. Scoped narrowly: only history-kind `sessionUpdate`s (`HISTORY_KINDS`)
    are forbidden before the response; other kinds are not."""

    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent, session_id, [{"type": "text", "text": "hello"}], timeout=agent_launch.default_timeout
        )

        pre_request_index = len(agent.transcript)
        req_id = await agent.send_request(
            "session/resume", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/resume did not succeed: {entry.text!r}"
        )
        response_index = agent.transcript.index(entry)

        offending = [
            candidate_entry.parsed
            for candidate_entry in agent.transcript[pre_request_index:response_index]
            if session_update_kind(candidate_entry, session_id) in HISTORY_KINDS
        ]
        assert not offending, (
            f"session/resume replayed history-kind update(s) before responding: {offending!r}"
        )


# --- session/list ---


@pytest.mark.requirement("ACP-LIST-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.list")
async def test_list_succeeds_and_validates(agent_launch, tmp_path):
    """ACP-LIST-001."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        req_id = await agent.send_request("session/list", {})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/list did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/list", msg)
        assert not issues, f"session/list result failed schema validation: {issues!r}"
        assert isinstance(msg["result"].get("sessions"), list), (
            f"session/list result.sessions is not an array: {msg['result']!r}"
        )


@pytest.mark.requirement("ACP-LIST-002")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.list")
async def test_list_with_unmatched_cwd_filter_returns_empty_array(agent_launch, tmp_path):
    """ACP-LIST-002."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        empty_dir = tmp_path / "no-session-here"
        empty_dir.mkdir()

        req_id = await agent.send_request("session/list", {"cwd": str(empty_dir)})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/list did not succeed: {entry.text!r}"
        )
        assert msg["result"].get("sessions") == [], (
            f"session/list with an unmatched cwd filter must return sessions: [], got "
            f"{msg['result']!r}"
        )


@pytest.mark.requirement("ACP-LIST-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.list")
async def test_list_invalid_cursor_gets_invalid_params(agent_launch, agent_initialize_result):
    """ACP-LIST-003 (ADVISORY). Cursors are opaque, so the TCK cannot prove a made-up one is
    invalid; a `_tck`-prefixed value is simply one no agent will have issued. Probing with it
    breaks the client rule against inventing cursors, but the spec defines the agent's answer
    (`-32602`), so the probe is allowed. A result (the cursor was ignored) or another error code
    is an advisory FAIL."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/list", {"cursor": "_tck-never-issued-cursor"})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED:
            pytest.skip("session/list returned -32000 (authentication required)")
        assert isinstance(error, dict), (
            f"session/list with a never-issued cursor should fail with -32602, but did not "
            f"return an error: {entry.text!r}"
        )
        assert error.get("code") == INVALID_PARAMS, (
            f"session/list with a never-issued cursor should fail with -32602, got "
            f"{error.get('code')!r}: {entry.text!r}"
        )


# --- session/delete ---


async def _close_then_delete(
    agent, session_id: str, init_result, *, timeout: float, tolerate_not_found: bool = False
):
    """Delete `session_id` the way ACP-DELETE-001/003 need: deleting an *active* session is
    implementation-defined (`docs/protocol/v1/draft/session-delete.mdx:90`), so close it first
    when `close` is advertised. Without `close`, an error from deleting the still-active
    session SKIPs, except a `-32002` one when `tolerate_not_found` (clients treat that as a
    successful delete, `session-delete.mdx:87`). Returns the `session/delete` response entry; a
    failed close SKIPs (that is ACP-CLOSE-001's finding)."""
    can_close = init_result is not None and capability_is_supported(
        init_result, "agentCapabilities.sessionCapabilities.close"
    )
    if can_close:
        close_id = await agent.send_request("session/close", {"sessionId": session_id})
        close_entry = await agent.wait_for_response(close_id, timeout=timeout)
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and "result" in close_msg):
            pytest.skip(
                "prerequisite not met: session/close did not succeed (see ACP-CLOSE-001): "
                f"{close_entry.text!r}"
            )
    req_id = await agent.send_request("session/delete", {"sessionId": session_id})
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    refused = isinstance(error, dict) and "result" not in msg
    if refused and tolerate_not_found and error.get("code") == RESOURCE_NOT_FOUND:
        refused = False
    if not can_close and refused:
        pytest.skip(
            "deleting an active session is implementation-defined, and the agent does not "
            f"advertise session/close to end it first: {entry.text!r}"
        )
    return entry


@pytest.mark.requirement("ACP-DELETE-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.delete")
async def test_delete_existing_session_succeeds(agent_launch, agent_initialize_result, tmp_path):
    """ACP-DELETE-001. See `_close_then_delete` for the active-session handling. When the TCK
    closed the session first, a `-32002` answer is a successful delete (`session-delete.mdx:87`;
    ACP-DELETE-002 judges the SHOULD). Without `close`, any error SKIPs, `-32002` included."""
    init_result = agent_initialize_result.result
    closed_first = init_result is not None and capability_is_supported(
        init_result, "agentCapabilities.sessionCapabilities.close"
    )
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        entry = await _close_then_delete(
            agent,
            session_id,
            init_result,
            timeout=agent_launch.default_timeout,
            tolerate_not_found=closed_first,
        )
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if closed_first and isinstance(error, dict) and error.get("code") == RESOURCE_NOT_FOUND:
            return
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/delete did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/delete", msg)
        assert not issues, f"session/delete result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-DELETE-002")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.delete")
async def test_delete_unknown_session_succeeds_silently(agent_launch):
    """ACP-DELETE-002 (ADVISORY). No `session/new` is ever sent -- this sessionId was never
    created on this connection."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/delete", {"sessionId": "tck-never-created-session"}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"deleting an unknown sessionId should succeed silently, got: {entry.text!r}"
        )


_MAX_LIST_PAGES = 10


@pytest.mark.requirement("ACP-DELETE-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.delete")
async def test_deleted_session_is_absent_from_list(agent_launch, agent_initialize_result, tmp_path):
    """ACP-DELETE-003. Lists with a `cwd` filter, so the pages hold only this test's session,
    and follows `nextCursor` up to `_MAX_LIST_PAGES` pages. A `-32002` answer to the delete
    counts as a successful delete (`session-delete.mdx:87`), so the list check still runs;
    ACP-DELETE-001 judges whether that answer is acceptable."""
    init_result = agent_initialize_result.result
    list_path = "agentCapabilities.sessionCapabilities.list"
    if init_result is None or not capability_is_supported(init_result, list_path):
        pytest.skip(f"capability {list_path!r} not advertised by the agent under test")
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        delete_entry = await _close_then_delete(
            agent,
            session_id,
            init_result,
            timeout=agent_launch.default_timeout,
            tolerate_not_found=True,
        )
        delete_msg = delete_entry.parsed
        delete_error = delete_msg.get("error") if isinstance(delete_msg, dict) else None
        delete_gone = isinstance(delete_error, dict) and delete_error.get("code") == RESOURCE_NOT_FOUND
        if not (isinstance(delete_msg, dict) and "result" in delete_msg) and not delete_gone:
            pytest.skip(
                "prerequisite not met: session/delete did not succeed (see ACP-DELETE-001): "
                f"{delete_entry.text!r}"
            )

        listed_ids: list = []
        cursor = None
        for _ in range(_MAX_LIST_PAGES):
            params = {"cwd": str(tmp_path)}
            if cursor is not None:
                params["cursor"] = cursor
            req_id = await agent.send_request("session/list", params)
            entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
            msg = entry.parsed
            assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
                f"session/list did not succeed: {entry.text!r}"
            )
            sessions = msg["result"].get("sessions")
            assert isinstance(sessions, list), (
                f"session/list result.sessions is not an array: {msg['result']!r}"
            )
            listed_ids += [info.get("sessionId") for info in sessions if isinstance(info, dict)]
            cursor = msg["result"].get("nextCursor")
            if not isinstance(cursor, str):
                break
        assert session_id not in listed_ids, (
            f"deleted session {session_id!r} still appears in session/list: {listed_ids!r}"
        )


# --- session/archive and session/unarchive (unstable) ---

_ARCHIVE_PATH = "agentCapabilities.sessionCapabilities.archive"
_UNKNOWN_SESSION_ID = "tck-never-created-session"
# An `archived` filter value no agent supports: `_`-prefixed values are the implementation-extension
# space (`schema/v1/schema.unstable.json#/$defs/SessionArchiveFilter`), so the probe does not
# squat on a value ACP may define later.
_UNSUPPORTED_ARCHIVE_FILTER = "_tck-unsupported-archived-filter"


def _require_sibling_capabilities(init_result, *names: str) -> None:
    """SKIP unless every `sessionCapabilities.<name>` is advertised (archive tests that also
    need `list`/`delete`, which `@pytest.mark.capability` cannot express)."""
    for name in names:
        path = f"agentCapabilities.sessionCapabilities.{name}"
        if init_result is None or not capability_is_supported(init_result, path):
            pytest.skip(f"capability {path!r} not advertised by the agent under test")


_ARCHIVE_FILTER_RFD = (
    " (Draft RFD docs/rfds/session-archive.mdx:112: an agent that advertises `archive` MUST "
    "support all three `archived` values, `exclude`, `include` and `only`)"
)


async def _list_sessions(agent, cwd, archived, *, timeout: float) -> list[dict]:
    """Every `SessionInfo` from `session/list` for `cwd` (and `archived`, unless `None`),
    following `nextCursor` up to `_MAX_LIST_PAGES` pages. Asserts each page succeeds."""
    sessions: list[dict] = []
    cursor = None
    for _ in range(_MAX_LIST_PAGES):
        params = {"cwd": str(cwd)}
        if archived is not None:
            params["archived"] = archived
        if cursor is not None:
            params["cursor"] = cursor
        req_id = await agent.send_request("session/list", params)
        entry = await agent.wait_for_response(req_id, timeout=timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list (archived={archived!r}) did not succeed: {entry.text!r}"
            + (_ARCHIVE_FILTER_RFD if archived in ("include", "only") else "")
        )
        page = msg["result"].get("sessions")
        assert isinstance(page, list), f"session/list result.sessions is not an array: {msg['result']!r}"
        sessions += [info for info in page if isinstance(info, dict)]
        cursor = msg["result"].get("nextCursor")
        if not isinstance(cursor, str):
            break
    return sessions


def _ids(sessions: list[dict]) -> list:
    return [info.get("sessionId") for info in sessions]


async def _archive_call(agent, method: str, session_id: str, *, timeout: float):
    req_id = await agent.send_request(method, {"sessionId": session_id})
    return await agent.wait_for_response(req_id, timeout=timeout)


def _assert_archive_succeeded(entry, method: str, what: str) -> None:
    msg = entry.parsed
    assert isinstance(msg, dict) and "result" in msg, f"{method} of {what} did not succeed: {entry.text!r}"
    issues = validate_agent_response(method, msg)
    assert not issues, f"{method} result failed schema validation: {issues!r}"


async def _delete_quietly(agent, session_id: str, init_result, *, timeout: float) -> None:
    """Best-effort cleanup so the test does not leave a session in a real agent's store. The
    outcome is ignored: ACP-DELETE-* judge `session/delete`."""
    if init_result is None or not capability_is_supported(
        init_result, "agentCapabilities.sessionCapabilities.delete"
    ):
        return
    with contextlib.suppress(AgentTimeout, AgentExited):
        req_id = await agent.send_request("session/delete", {"sessionId": session_id})
        await agent.wait_for_response(req_id, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-001")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_requires_list_capability(agent_initialize_result):
    """ACP-ARCHIVE-001. Judged from the `initialize` result; the marker already SKIPs an agent
    that does not advertise `archive`."""
    init_result = agent_initialize_result.result
    assert init_result is not None, (
        f"cannot evaluate advertised capabilities: initialize failed: "
        f"{agent_initialize_result.error_message}"
    )
    assert capability_is_supported(init_result, "agentCapabilities.sessionCapabilities.list"), (
        "agent advertises sessionCapabilities.archive but not sessionCapabilities.list: "
        f"{(init_result.get('agentCapabilities') or {}).get('sessionCapabilities')!r}"
    )


@pytest.mark.requirement("ACP-ARCHIVE-002")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_listed_sessions_carry_boolean_archived(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-002. Lists with a `cwd` filter, so the pages hold only this test's session.
    Checks the default view, then (if `session/archive` works; ACP-ARCHIVE-003 judges it) the
    `only` view, so an agent that sets the flag only on unarchived sessions is caught."""
    init_result = agent_initialize_result.result
    _require_sibling_capabilities(init_result, "list")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            listed = await _list_sessions(agent, tmp_path, None, timeout=timeout)
            if not listed:
                pytest.skip("session/list returned no session to inspect")
            missing = _ids([info for info in listed if not isinstance(info.get("archived"), bool)])
            assert not missing, f"listed sessions without a boolean `archived`: {missing!r}"

            archived = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            if isinstance(archived.parsed, dict) and "result" in archived.parsed:
                only = await _list_sessions(agent, tmp_path, "only", timeout=timeout)
                missing = _ids([info for info in only if not isinstance(info.get("archived"), bool)])
                assert not missing, (
                    f"sessions listed under archived=only without a boolean `archived`: {missing!r}"
                )
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-003")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_and_unarchive_round_trip(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-003. Checks membership in the default and `only` views (all pages, filtered
    by `cwd`); the `archived` flag itself is ACP-ARCHIVE-002's. An agent that does not list the
    fresh session at all SKIPs: the views cannot be compared."""
    init_result = agent_initialize_result.result
    _require_sibling_capabilities(init_result, "list")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            if session_id not in _ids(await _list_sessions(agent, tmp_path, None, timeout=timeout)):
                pytest.skip("the new session is not listed by session/list, so archive views cannot be compared")

            archived = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            _assert_archive_succeeded(archived, "session/archive", "an existing session")
            default_ids = _ids(await _list_sessions(agent, tmp_path, None, timeout=timeout))
            assert session_id not in default_ids, (
                f"archived session {session_id!r} still appears in the default session/list view: "
                f"{default_ids!r}"
            )
            only_ids = _ids(await _list_sessions(agent, tmp_path, "only", timeout=timeout))
            assert session_id in only_ids, (
                f"archived session {session_id!r} is missing from archived=only: {only_ids!r}"
            )

            unarchived = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(unarchived, "session/unarchive", "an archived session")
            default_ids = _ids(await _list_sessions(agent, tmp_path, None, timeout=timeout))
            assert session_id in default_ids, (
                f"unarchived session {session_id!r} is missing from the default session/list view: "
                f"{default_ids!r}"
            )
            only_ids = _ids(await _list_sessions(agent, tmp_path, "only", timeout=timeout))
            assert session_id not in only_ids, (
                f"unarchived session {session_id!r} still appears under archived=only: {only_ids!r}"
            )
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-004")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_unsupported_archived_filter_gets_invalid_params(agent_launch, agent_initialize_result):
    """ACP-ARCHIVE-004. The spec names the code (`-32602`) as a MUST, so a different error is a
    FAIL too, as is a result (the agent fell back to `exclude`). The probe value is
    `_`-prefixed (see `_UNSUPPORTED_ARCHIVE_FILTER`). `-32000` SKIPs."""
    _require_sibling_capabilities(agent_initialize_result.result, "list")
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/list", {"archived": _UNSUPPORTED_ARCHIVE_FILTER})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED:
            pytest.skip("session/list returned -32000 (authentication required)")
        assert isinstance(error, dict), (
            f"session/list with an unsupported archived filter must fail with -32602, but did not "
            f"return an error: {entry.text!r}"
        )
        assert error.get("code") == INVALID_PARAMS, (
            f"session/list with an unsupported archived filter must fail with -32602, got "
            f"{error.get('code')!r}: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-ARCHIVE-005")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_and_unarchive_are_idempotent(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-005. Archive twice, then unarchive twice: each call must succeed. The first
    archive failing SKIPs (ACP-ARCHIVE-003 judges it)."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            first = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            if not (isinstance(first.parsed, dict) and "result" in first.parsed):
                pytest.skip(
                    "prerequisite not met: the first session/archive did not succeed "
                    f"(see ACP-ARCHIVE-003): {first.text!r}"
                )
            again = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            _assert_archive_succeeded(again, "session/archive", "an already-archived session")
            unarchived = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(unarchived, "session/unarchive", "an archived session")
            again = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(again, "session/unarchive", "a not-archived session")
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-005")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_unknown_session_is_an_error(agent_launch):
    """ACP-ARCHIVE-005. Unlike `session/delete`, these do not succeed silently for a session
    that does not exist (`error.mdx:67`). The doc gives the code (`-32002`) without a
    requirement keyword, so only error-vs-success is asserted. No `session/new` is ever sent."""
    async with connected_agent(agent_launch) as agent:
        for method in ("session/archive", "session/unarchive"):
            entry = await _archive_call(
                agent, method, _UNKNOWN_SESSION_ID, timeout=agent_launch.default_timeout
            )
            msg = entry.parsed
            assert isinstance(msg, dict) and "error" in msg and "result" not in msg, (
                f"{method} of a never-created session must fail, not succeed silently: "
                f"{entry.text!r}"
            )


@pytest.mark.requirement("ACP-ARCHIVE-006")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_deleted_session_is_absent_under_every_archived_filter(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ARCHIVE-006. Closes the gap ACP-DELETE-003 leaves (it checks only the default view):
    an agent that implements delete as archive hides the session there but not under
    `include`/`only`. As for ACP-DELETE-003, a `-32002` answer to the delete counts as success.
    An agent that does not list the fresh session before the delete SKIPs, as ACP-ARCHIVE-003
    does: its disappearance would otherwise be vacuous."""
    init_result = agent_initialize_result.result
    _require_sibling_capabilities(init_result, "delete", "list")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        listed_before = _ids(await _list_sessions(agent, tmp_path, "include", timeout=timeout))
        if session_id not in listed_before:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)
            pytest.skip("the new session is not listed by session/list, so its deletion cannot be observed")
        delete_entry = await _close_then_delete(
            agent, session_id, init_result, timeout=timeout, tolerate_not_found=True
        )
        delete_msg = delete_entry.parsed
        delete_error = delete_msg.get("error") if isinstance(delete_msg, dict) else None
        deleted = (isinstance(delete_msg, dict) and "result" in delete_msg) or (
            isinstance(delete_error, dict) and delete_error.get("code") == RESOURCE_NOT_FOUND
        )
        if not deleted:
            pytest.skip(
                "prerequisite not met: session/delete did not succeed (see ACP-DELETE-001): "
                f"{delete_entry.text!r}"
            )
        for archived in ("exclude", "include", "only"):
            listed = _ids(await _list_sessions(agent, tmp_path, archived, timeout=timeout))
            assert session_id not in listed, (
                f"deleted session {session_id!r} still appears under archived={archived!r}: {listed!r}"
            )


# --- session/close ---


@pytest.mark.requirement("ACP-CLOSE-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")
async def test_close_idle_session_succeeds(agent_launch, tmp_path):
    """ACP-CLOSE-001."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        req_id = await agent.send_request("session/close", {"sessionId": session_id})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/close did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/close", msg)
        assert not issues, f"session/close result failed schema validation: {issues!r}"


async def _close(agent, session_id: str, *, timeout: float):
    req_id = await agent.send_request("session/close", {"sessionId": session_id})
    return await agent.wait_for_response(req_id, timeout=timeout)


def _assert_close_succeeded_idempotently(entry, what: str) -> None:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    assert not isinstance(error, dict), (
        f"session/close of {what} should succeed with the empty result (closing is idempotent), "
        f"but returned error {error.get('code')!r}: {entry.text!r}"
    )
    assert isinstance(msg, dict) and "result" in msg, (
        f"session/close of {what} did not return a result: {entry.text!r}"
    )
    issues = validate_agent_response("session/close", msg)
    assert not issues, f"session/close result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-CLOSE-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")
async def test_close_already_closed_session_succeeds(agent_launch, agent_initialize_result, tmp_path):
    """ACP-CLOSE-003 (ADVISORY). A second `session/close` for the same id must answer like the
    first. The first close failing SKIPs (ACP-CLOSE-001 judges it). A `-32002` answer is
    an ADVISORY FAIL: clients tolerate it, but the agent SHOULD return the empty result."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        first = await _close(agent, session_id, timeout=agent_launch.default_timeout)
        first_msg = first.parsed
        if not (isinstance(first_msg, dict) and "result" in first_msg):
            pytest.skip(
                "prerequisite not met: the first session/close did not succeed "
                f"(see ACP-CLOSE-001): {first.text!r}"
            )
        second = await _close(agent, session_id, timeout=agent_launch.default_timeout)
        _assert_close_succeeded_idempotently(second, "an already-closed session")


@pytest.mark.requirement("ACP-CLOSE-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")
async def test_close_unknown_session_succeeds(agent_launch, agent_initialize_result):
    """ACP-CLOSE-003 (ADVISORY). No `session/new` is ever sent -- this sessionId was never
    created on this connection."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        entry = await _close(agent, "tck-never-created-session", timeout=agent_launch.default_timeout)
        _assert_close_succeeded_idempotently(entry, "a never-created session")


@pytest.mark.requirement("ACP-CLOSE-002")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")
async def test_close_in_flight_prompt_resolves_cancelled(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CLOSE-002. Mirrors `test_cancel.py`'s SKIP-vs-FAIL race handling, but sends a
    `session/close` *request* instead of a `session/cancel` *notification* at the same timing
    heuristic. No claim is made about response ordering -- both are awaited independently.

    Driven through `run_prompt`'s `on_action` hook rather than a hand-rolled read loop, so any
    agent -> client request the agent sends while the close is in flight gets answered instead
    of deadlocking the test.
    """
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        async def _send_close() -> str:
            close_id = "tck-close"
            await agent.send_request("session/close", {"sessionId": session_id}, id=close_id)
            return close_id

        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_action=_send_close,
            timeout=agent_launch.default_timeout,
        )

        close_response_entry = turn.action_response
        if close_response_entry is None:
            pytest.skip(
                "close-cancellation not exercised: prompt turn completed before session/close "
                "could be sent"
            )
        close_msg = close_response_entry.parsed
        if not (isinstance(close_msg, dict) and "result" in close_msg):
            # An error-shaped session/close response is ACP-CLOSE-001's finding to make, not
            # this test's -- asserting it here too would double-report the same defect against
            # both requirements.
            pytest.skip(
                "prerequisite not met: session/close did not succeed (see ACP-CLOSE-001): "
                f"{close_response_entry.text!r}"
            )

        closed_at_index = turn.action_sent_at_index
        prompt_response_entry = turn.response_entry
        prompt_msg = prompt_response_entry.parsed
        if isinstance(prompt_msg, dict) and "result" in prompt_msg:
            stop_reason = prompt_msg["result"].get("stopReason")
            if stop_reason != "cancelled" and stop_reason in STOP_REASONS:
                race_window = quiet_period(agent_launch.default_timeout)
                close_timestamp = agent.transcript[closed_at_index].timestamp
                elapsed_ms = (prompt_response_entry.timestamp - close_timestamp) * 1000
                record_property("acp_tck_close_race_window_ms", f"{race_window * 1000:.0f}")
                if elapsed_ms < race_window * 1000:
                    record_property("acp_tck_close_race_ms", f"{elapsed_ms:.0f}")
                    pytest.skip(
                        f"close-cancellation not exercised: prompt response arrived "
                        f"{elapsed_ms:.0f} ms after session/close; agent may have finished "
                        "before reading it"
                    )

        assert isinstance(prompt_msg, dict) and "result" in prompt_msg, (
            f"session/close on an in-flight prompt must resolve it with a success result, not "
            f"an error: {prompt_msg!r}"
        )
        stop_reason = prompt_msg["result"].get("stopReason")
        assert stop_reason == "cancelled", (
            f"expected stopReason 'cancelled' after session/close on an in-flight prompt, got "
            f"{stop_reason!r}"
        )


# --- additionalDirectories ---


@pytest.mark.requirement("ACP-ADDDIRS-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.additionalDirectories")
async def test_new_session_with_additional_directories_is_accepted(agent_launch, tmp_path):
    """ACP-ADDDIRS-001."""
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new",
            {
                "cwd": str(tmp_path),
                "mcpServers": [],
                "additionalDirectories": [str(extra_dir)],
            },
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, (
            f"session/new with an additionalDirectories entry did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/new", msg)
        assert not issues, f"session/new result failed schema validation: {issues!r}"


# --- systemPrompt ---
#
# SYSPROMPT-002/003 deliberately send what a client MUST NOT (an unadvertised mode, a non-text
# block): the spec defines the agent's answer to exactly those inputs, so they are legitimate
# probes. "MUST NOT create the session" is only observable as the error itself.


async def _new_session_with_system_prompt(agent, cwd, system_prompt, *, timeout):
    req_id = await agent.send_request(
        "session/new", {"cwd": str(cwd), "mcpServers": [], "systemPrompt": system_prompt}
    )
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    return entry


@pytest.mark.requirement("ACP-SYSPROMPT-001")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.systemPrompt")
async def test_new_session_with_append_system_prompt_is_accepted(agent_launch, tmp_path):
    """ACP-SYSPROMPT-001."""
    async with connected_agent(agent_launch) as agent:
        entry = await _new_session_with_system_prompt(
            agent,
            tmp_path,
            {"mode": "append", "content": [{"type": "text", "text": "Answer concisely."}]},
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/new with an append-mode text systemPrompt did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/new", msg)
        assert not issues, f"session/new result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-SYSPROMPT-002")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.systemPrompt")
async def test_new_session_with_unsupported_system_prompt_mode_errors(
    agent_launch, tmp_path, record_property
):
    """ACP-SYSPROMPT-002. Uses a `_`-prefixed mode, which is reserved for implementation-specific
    use, so no agent can legitimately claim to support the TCK's."""
    async with connected_agent(agent_launch) as agent:
        entry = await _new_session_with_system_prompt(
            agent,
            tmp_path,
            {"mode": "_tck_unsupported", "content": [{"type": "text", "text": "Answer concisely."}]},
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("error"), dict), (
            "session/new with an unsupported systemPrompt mode must return an error, got: "
            f"{entry.text!r}"
        )
        record_property("acp_tck_sysprompt_unsupported_mode_error_code", msg["error"].get("code"))


@pytest.mark.requirement("ACP-SYSPROMPT-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.systemPrompt")
async def test_new_session_with_non_text_system_prompt_content_errors(agent_launch, tmp_path):
    """ACP-SYSPROMPT-003."""
    async with connected_agent(agent_launch) as agent:
        entry = await _new_session_with_system_prompt(
            agent,
            tmp_path,
            {
                "mode": "append",
                "content": [
                    {"type": "resource_link", "uri": (tmp_path / "rules.md").as_uri(), "name": "rules.md"}
                ],
            },
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("error"), dict), (
            "session/new with a non-text systemPrompt content block must return an error, got: "
            f"{entry.text!r}"
        )
