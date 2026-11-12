"""Shared helpers for the v2 conformance suite.

`connected_agent()`/`new_session()`/`skip_if_version_mismatch()` are the basic connection/session
helpers. `run_prompt()`/`PromptTurn`/`cancel_race_peek()` are the v2 mock-client prompt driver,
the v2 counterpart of `tck.v1.conformance._helpers`'s same-named machinery -- deliberately a
separate, non-shared implementation, because the v2 turn-end contract is fundamentally
different: v1's `session/prompt` response *is* the turn result (carries `stopReason`); v2's
response is only an acceptance receipt (`{messageId}`) sent at insertion time, and the turn's
end is learned solely from a `session/update` `state_update {state: "idle"}` notification.

`skip_if_auth_gated()` is the v2 twin of v1's same-named helper, wired into `new_session()`.

The session-management wire helpers (`resume_session`, `list_sessions`, `close_session`,
`delete_session`, `set_config_option`) and `obtain_resumable_session` address a hard problem:
there is no spec-guaranteed way for a black-box client to obtain a session id it is entitled to
`session/resume`. It tries, in order: (1) resuming the session just created on
this connection; (3) `session/list` then resuming its first entry; (2) `session/close` then
resume -- recording every route's error -- and raises `pytest.skip.Exception` with all three
recorded errors if none succeeds, *unless* `session/resume` itself answered `-32601` (Method not
found) on any attempt, which is instead surfaced as a hard failure (the method is
baseline-mandatory once `capabilities.session` is advertised at all, so `-32601` is
unambiguously non-conformant, never just "this particular id didn't work").
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Literal

import pytest

from tck.common.harness import (
    AgentExited,
    AgentLaunch,
    AgentProcess,
    AgentTimeout,
    Direction,
    TranscriptEntry,
)
from tck.common.plugin import (
    current_auth_method_id,
    current_initialize_auth_methods,
    record_test_property,
    register_active_process,
    skip_if_login_times_out,
)

from .. import SPEC
from ..protocol import (
    AUTHENTICATION_REQUIRED,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    PROTOCOL_VERSION,
    RESOURCE_NOT_FOUND,
)


@contextlib.asynccontextmanager
async def connected_agent(
    launch: AgentLaunch,
    *,
    handshake: bool = True,
    capabilities: dict[str, Any] | None = None,
) -> AsyncIterator[AgentProcess]:
    """Spawn a fresh `AgentProcess` for `launch`, optionally perform an `initialize` handshake,
    yield it, and always close it. Mirrors `tck.v1.conformance._helpers.connected_agent`.

    Registers the process with the plugin's failure-diagnostics tracker (`tck.common.plugin`) so
    a test failure attaches its transcript and stderr to the pytest report.

    When `handshake` is true and `--tck-auth-method` was given (`current_auth_method_id()`), an
    `auth/login` call for that method id is sent right after `initialize` -- v2's renamed
    counterpart of v1's `authenticate` (same `{"methodId": ...}` params shape,
    `schema/v2/schema.unstable.json#/$defs/LoginAuthRequest`). As in v1, a failing `auth/login` here is
    not itself a conformance assertion -- it means the TCK cannot exercise anything
    session-dependent against this agent with the given `--auth-method`, so the test SKIPs with
    a clear reason instead of raising. A login that never answers (it may be interactive and
    pending) SKIPs with `AUTH-GATED:` too, see `skip_if_login_times_out`.
    """
    async with AgentProcess(launch) as agent:
        register_active_process(agent)
        if handshake:
            params = SPEC.initialize_params()
            if capabilities is not None:
                params = {**params, "capabilities": capabilities}
            req_id = await agent.send_request("initialize", params)
            await agent.wait_for_response(req_id, timeout=launch.startup_timeout)
            await login_if_needed(agent, timeout=launch.startup_timeout)
        yield agent


def validate_login_method_id(auth_methods: list[Any], method_id: str) -> dict[str, Any]:
    """Return the `authMethods` entry matching `method_id`, or `pytest.skip(...)` with an
    `AUTH-GATED:` reason if the id is not among `auth_methods` at all, or names a
    `type: "terminal"` entry -- two client MUST NOTs the TCK holds itself to just as strictly as
    it holds the agent under test to its own: sending `auth/login` with a `terminal` `methodId`,
    or with a `methodId` the agent did not advertise, are both client MUST-NOTs (V13). Callers
    that already know `auth_methods` is non-empty (see `login_if_needed`'s own empty-list no-op,
    must-NOT #7) call this right before actually sending `auth/login`.
    """
    matching = next(
        (m for m in auth_methods if isinstance(m, dict) and m.get("methodId") == method_id),
        None,
    )
    if matching is None:
        advertised = [m.get("methodId") for m in auth_methods if isinstance(m, dict)]
        pytest.skip(
            f"AUTH-GATED: --auth-method {method_id!r} is not among this agent's advertised "
            f"authMethods {advertised!r} -- the TCK will not send auth/login with an "
            "unadvertised methodId (client MUST NOT, V13)"
        )
    if matching.get("type") == "terminal":
        pytest.skip(
            f"AUTH-GATED: --auth-method {method_id!r} names a type: 'terminal' authMethods "
            "entry -- the TCK will not send auth/login for it (client MUST NOT, V13); terminal "
            "auth is an out-of-band, client-side relaunch flow the TCK cannot drive"
        )
    return matching


async def login_if_needed(agent: AgentProcess, *, timeout: float | None = None) -> None:
    """Send `auth/login` for `current_auth_method_id()` (`--auth-method`) if one was configured,
    on a connection that is past its own `initialize` response.

    `connected_agent(..., handshake=True)` (the default) already calls this right after its own
    `initialize`; this standalone entry point exists for the several tests that instead perform a
    *manual* `initialize` on a `handshake=False` connection -- e.g. to control
    `skip_if_version_mismatch` themselves (`test_transport.py`, `test_batch.py`,
    `test_session_config.py`, `test_initialize.py`'s ACP-SCHEMA-001 full-exchange test) -- and
    then go on to call `session/new`: without an explicit login step on *that* connection, an
    agent gated behind authentication (e.g. `gated_by_auth.py`) still answers `session/new` with
    `-32000` even though a valid `--auth-method` was given, and `skip_if_auth_gated`'s excuse for
    `-32000` only applies when `current_auth_method_id() is None` -- so the test would fail for
    real instead of either succeeding or SKIPping with a clear reason.

    No-op when no `--auth-method` was given (`current_auth_method_id() is None`), and also when
    the agent's own `initialize` advertised no `authMethods` at all -- the TCK must not send
    `auth/login` in that situation regardless of what `--auth-method` says (must-NOT #7).
    SKIPs -- with an `AUTH-GATED:` reason, via `validate_login_method_id`
    -- if the configured id is not among the advertised `authMethods`, or names a `type:
    "terminal"` entry (must-NOT #12/#13); also SKIPs -- not fails -- if `auth/login` itself does
    not succeed, mirroring `connected_agent`'s own embedded login: a failing login means the TCK
    cannot exercise anything session-dependent against this agent with the given `--auth-method`,
    not that the caller's own requirement failed.
    """
    method_id = current_auth_method_id()
    if method_id is None:
        return
    auth_methods = current_initialize_auth_methods()
    if not auth_methods:
        # V9/must-NOT #7: the client MUST NOT call `auth/login` (or `auth/logout`) at all when
        # `authMethods` is empty -- the agent's response to a call the spec forbids is undefined.
        # Proceed unauthenticated rather than violate that MUST NOT just because a
        # (now-irrelevant) `--auth-method` id was supplied on the command line.
        return
    validate_login_method_id(auth_methods, method_id)
    auth_id = await agent.send_request("auth/login", {"methodId": method_id})
    with skip_if_login_times_out("auth/login", method_id, timeout):
        auth_entry = await agent.wait_for_response(auth_id, timeout=timeout)
    auth_msg = auth_entry.parsed
    if not (isinstance(auth_msg, dict) and isinstance(auth_msg.get("result"), dict)):
        detail = (auth_msg.get("error") if isinstance(auth_msg, dict) else None) or auth_entry.text
        pytest.skip(
            f"AUTH-GATED: auth/login with methodId={method_id!r} failed: {detail!r} "
            "-- check --tck-auth-method"
        )


def skip_if_auth_gated_msg(msg: Any) -> None:
    """Message-shaped core of `skip_if_auth_gated()` below -- operates on an already-parsed
    JSON-RPC response object (`{"error": {...}}` or `{"result": {...}}`) rather than a
    `TranscriptEntry`, so a caller that pulls a `session/new` reply out of something other than a
    single top-level response can still route it through the same auth-gate check
    `new_session()` uses.

    Skips the current test, with a message pointing at `--auth-method`, if `msg` is the
    `AUTHENTICATION_REQUIRED` (`-32000`) error. v2 twin of
    `tck.v1.conformance._helpers.skip_if_auth_gated`.

    v2 never requires an agent to gate `session/new` behind authentication (`-32000` there is
    still only a MAY, same as v1), so this is not itself a conformance failure; but it does mean
    the TCK cannot exercise session-dependent
    requirements against this agent unless the harness operator supplies a valid
    `--auth-method <id>`. The message is prefixed with the literal marker string `AUTH-GATED:`
    so `tck.common.plugin` can detect this specific reason (as opposed to an ordinary
    capability-not-advertised skip) and set `Verdict.blocked_by_auth`.

    Only excuses the `-32000` when the cached `initialize` result actually advertised at least
    one `authMethods` entry (the `ACP-AUTH-005` rule) -- an agent
    that advertises none and still returns `-32000` has no defined remedy; this is left as an
    ordinary, un-excused failure of whatever the caller was asserting, not something the TCK can
    route around.
    """
    if not (
        isinstance(msg, dict)
        and isinstance(msg.get("error"), dict)
        and msg["error"].get("code") == AUTHENTICATION_REQUIRED
        and current_auth_method_id() is None
    ):
        return
    if not current_initialize_auth_methods():
        return  # no advertised authMethods -- not excusable, let the caller's own assert fail
    pytest.skip(
        "AUTH-GATED: session/new returned -32000 (authentication required) and no "
        "--auth-method was given; pass --auth-method <id> (one of the ids advertised in "
        "initialize's authMethods) to test session-dependent requirements against this agent"
    )


def skip_if_auth_gated(entry: TranscriptEntry) -> None:
    """Skip the current test, with a message pointing at `--auth-method`, if `entry` (a
    `session/new` response) is the `AUTHENTICATION_REQUIRED` (`-32000`) error. See
    `skip_if_auth_gated_msg()` above for the full rationale; this is a thin `TranscriptEntry`
    adapter over it for the common single-response case."""
    skip_if_auth_gated_msg(entry.parsed)


async def new_session_result(
    agent: AgentProcess, cwd: Any, *, timeout: float | None = None
) -> dict[str, Any]:
    """Send `session/new` for `cwd` and return the whole result object (`sessionId` plus any
    `configOptions`/`availableCommands`).

    Unlike v1's `new_session`, `mcpServers` is omitted entirely rather than sent as an empty
    list -- v2's `session/new` params require only `cwd` (`schema/v2/schema.unstable.json#/$defs/NewSessionRequest/required`,
    `mcpServers` optional), and omitting it avoids the MCP-capability check.

    SKIPs (via `skip_if_auth_gated`) rather than failing when the agent requires authentication
    and no `--auth-method` was configured.
    """
    req_id = await agent.send_request("session/new", {"cwd": str(cwd)})
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/new did not return a result object: {entry.text!r}"
    )
    session_id = msg["result"].get("sessionId")
    assert isinstance(session_id, str) and session_id, (
        f"session/new result.sessionId must be a non-empty string, got {session_id!r}"
    )
    return msg["result"]


async def new_session(agent: AgentProcess, cwd: Any, *, timeout: float | None = None) -> str:
    """`new_session_result`'s `sessionId`."""
    return (await new_session_result(agent, cwd, timeout=timeout))["sessionId"]


async def resume_session(
    agent: AgentProcess,
    session_id: str,
    cwd: Any,
    *,
    replay_from: Any = None,
    additional_directories: list[str] | None = None,
    mcp_servers: list[dict[str, Any]] | None = None,
    system_prompt: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> tuple[TranscriptEntry, list[tuple[int, TranscriptEntry]]]:
    """Send `session/resume` and collect every `session/update` notification observed on the
    wire before its response arrives, in wire order -- this *is* the replay stream
    `ACP-RESUME-002/202/204..209` need to inspect. `session/resume`'s response is not an acceptance
    receipt (unlike `session/prompt`'s): it carries the actual result directly, so unlike
    `run_prompt` there is no separate turn-end predicate to wait for, just the matching response.

    `replay_from` is sent verbatim -- even a malformed value, which `ACP-RESUME-208` probes on
    purpose -- and omitted when `None`.

    Returns `(response_entry, updates)`. Any agent -> client request arriving meanwhile (none is
    expected during `session/resume`) is simply left unanswered in the transcript for the caller
    to notice -- answering it here would risk masking a genuine defect with an invented outcome.
    """
    params: dict[str, Any] = {"sessionId": session_id, "cwd": str(cwd)}
    if replay_from is not None:
        params["replayFrom"] = replay_from
    if additional_directories is not None:
        params["additionalDirectories"] = additional_directories
    if mcp_servers is not None:
        params["mcpServers"] = mcp_servers
    if system_prompt is not None:
        params["systemPrompt"] = system_prompt
    req_id = await agent.send_request("session/resume", params)

    updates: list[tuple[int, TranscriptEntry]] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout if timeout is not None else None
    while True:
        remaining = (deadline - loop.time()) if deadline is not None else None
        if remaining is not None and remaining <= 0:
            raise AgentTimeout(
                f"session/resume {req_id!r} for session {session_id!r} did not respond within "
                f"{timeout}s",
                agent.transcript,
                stderr=agent.stderr_text(),
            )
        entry = await agent.read_line(timeout=remaining)
        line_index = agent.transcript.index(entry)
        for msg in iter_messages(entry):
            if "method" not in msg and msg.get("id") == req_id:
                return entry, updates
            if msg.get("method") == "session/update":
                updates.append((line_index, entry))
        # Anything else observed on the wire while waiting (an unrelated notification, a
        # malformed line) is not this helper's concern; keep waiting for the response.


async def drain_quiet(agent: AgentProcess, quiet: float) -> list[TranscriptEntry]:
    """Read whatever the agent sends for up to `quiet` seconds and return everything observed
    (`session/update` notifications and anything else alike) -- the generic "nothing more is
    coming" drain `ACP-RESUME-202` uses to confirm no replay update trails the response."""
    collected: list[TranscriptEntry] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + quiet
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            entry = await agent.read_line(timeout=remaining)
        except AgentTimeout:
            break
        collected.append(entry)
    return collected


async def list_sessions(
    agent: AgentProcess,
    *,
    cwd: Any = None,
    cursor: str | None = None,
    archived: Any = None,
    timeout: float | None = None,
) -> TranscriptEntry:
    """Send `session/list` and return its response entry (the caller inspects `.parsed` itself --
    unlike `new_session`, several tests need to see a raw error response too, e.g. a cursor round
    trip is out of scope but an empty-list-vs-error check is not). `archived` is the unstable
    archive filter; omitted from the request when `None`."""
    params: dict[str, Any] = {}
    if cwd is not None:
        params["cwd"] = str(cwd)
    if archived is not None:
        params["archived"] = archived
    if cursor is not None:
        params["cursor"] = cursor
    req_id = await agent.send_request("session/list", params)
    return await agent.wait_for_response(req_id, timeout=timeout)


async def close_session(
    agent: AgentProcess, session_id: str, *, timeout: float | None = None
) -> TranscriptEntry:
    """Send `session/close` for `session_id` and return its response entry."""
    req_id = await agent.send_request("session/close", {"sessionId": session_id})
    return await agent.wait_for_response(req_id, timeout=timeout)


async def delete_session(
    agent: AgentProcess, session_id: str, *, timeout: float | None = None
) -> TranscriptEntry:
    """Send `session/delete` for `session_id` and return its response entry."""
    req_id = await agent.send_request("session/delete", {"sessionId": session_id})
    return await agent.wait_for_response(req_id, timeout=timeout)


async def set_config_option(
    agent: AgentProcess,
    session_id: str,
    config_id: str,
    *,
    type: str,
    value: Any,
    timeout: float | None = None,
) -> TranscriptEntry:
    """Send `session/set_config_option` (
    `schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest`:
    `sessionId`+`configId` plus a `type`/`value` pair, e.g. `type="boolean", value=True` or
    `type="id", value=<SessionConfigValueId>`) and return its response entry."""
    params = {"sessionId": session_id, "configId": config_id, "type": type, "value": value}
    req_id = await agent.send_request("session/set_config_option", params)
    return await agent.wait_for_response(req_id, timeout=timeout)


def assert_unknown_session_error(entry: TranscriptEntry, method: str, session_id: str) -> None:
    """Assert `entry` is the `error.mdx:54-56` answer to a session-scoped request naming a
    session that is not active: error `-32002` with `data.sessionId` equal to `session_id`. A
    success, a wrong code and a missing or wrong `data.sessionId` are reported together. Shared
    by `ACP-ERROR-003` and `ACP-ERROR-004`; the schema's `Other` error-data branch accepts any
    `data`, so the shape is checked here."""
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    assert isinstance(error, dict), (
        f"{method} for session {session_id!r}, which is not active, should fail with -32002 and "
        f"data.sessionId={session_id!r}, but did not return an error: {entry.text!r}"
    )
    problems = []
    if error.get("code") != RESOURCE_NOT_FOUND:
        problems.append(f"expected code -32002, got {error.get('code')!r}")
    data = error.get("data")
    if not isinstance(data, dict):
        problems.append(f"expected error.data to be an object with sessionId, got {data!r}")
    elif data.get("sessionId") != session_id:
        problems.append(f"expected data.sessionId={session_id!r}, got {data.get('sessionId')!r}")
    assert not problems, f"{method} for an inactive session: {'; '.join(problems)} ({entry.text!r})"


async def _route_just_created(
    agent: AgentProcess, cwd: Any, timeout: float | None
) -> str:
    """Route (1): the session `session/new` just created on this same fresh connection."""
    return await new_session(agent, cwd, timeout=timeout)


async def _route_after_close(
    agent: AgentProcess, cwd: Any, timeout: float | None
) -> str:
    """Route (2): create a session, `session/close` it, then attempt to resume the closed id."""
    session_id = await new_session(agent, cwd, timeout=timeout)
    await close_session(agent, session_id, timeout=timeout)
    return session_id


_LIST_ROUTE_MAX_PAGES = 5


def same_dir(listed: Any, cwd: Any) -> bool:
    """True if `listed` is an absolute path naming the same directory as `cwd` (resolved, so
    e.g. macOS `/var` vs `/private/var` compare equal)."""
    if not isinstance(listed, str) or not Path(listed).is_absolute():
        return False
    return Path(listed).resolve() == Path(cwd).resolve()


async def _route_from_list(
    agent: AgentProcess, cwd: Any, timeout: float | None
) -> str:
    """Route (3), tried last: a `session/list` entry whose `cwd` is the TCK's own `cwd`, resumed
    with that same `cwd` (resume is only defined when the request `cwd` matches the session's,
    session-setup.mdx:439).

    Safety: `cwd` is a per-test temporary directory, so a session listed under it was created by
    the TCK. Entries with any other `cwd` -- possibly the operator's own saved sessions -- are
    skipped, never resumed or prompted into. The request carries the `cwd` filter, but the
    entries are re-checked client-side because an agent may ignore the filter. Follows
    `nextCursor` for a few pages, then gives up.

    A fresh connection has no session of its own, so this only succeeds against an agent that
    persists sessions across connections -- the ones routes (1)/(2) created earlier in the same
    test. Raises if no matching entry is found."""
    cursor: str | None = None
    for _ in range(_LIST_ROUTE_MAX_PAGES):
        entry = await list_sessions(agent, cwd=cwd, cursor=cursor, timeout=timeout)
        msg = entry.parsed
        result = msg.get("result") if isinstance(msg, dict) else None
        sessions = result.get("sessions") if isinstance(result, dict) else None
        if not isinstance(sessions, list):
            raise RuntimeError(f"session/list returned no usable sessions array: {entry.text!r}")
        for listed in sessions:
            if not isinstance(listed, dict) or not same_dir(listed.get("cwd"), cwd):
                continue
            session_id = listed.get("sessionId")
            if isinstance(session_id, str) and session_id:
                return session_id
        # Only an omitted or `null` `nextCursor` ends the results; `""` is a valid cursor
        # (session-list.mdx:154).
        cursor = result.get("nextCursor")
        if not isinstance(cursor, str):
            break
    raise RuntimeError(f"session/list has no session created in the TCK's own cwd {str(cwd)!r}")


async def _attempt_resumable_route(
    launch: AgentLaunch,
    cwd: Any,
    timeout: float | None,
    errors: list[str],
    route_setup: Callable[[AgentProcess, Any, float | None], Awaitable[str]],
) -> tuple[AgentProcess, str, TranscriptEntry, contextlib.AsyncExitStack] | None:
    """Try one route of `obtain_resumable_session` on its own fresh connection. Returns
    `(agent, session_id, resume_response_entry, stack)` -- with the connection
    detached from local cleanup via `stack.pop_all()` -- on success, so the caller can keep it
    open; `None` on any failure, with the connection already closed and the failure appended to
    `errors`.

    A `-32601` from `session/resume` itself is not a route failure to record and move past:
    `session/resume` is part of the baseline once `capabilities.session` is advertised at all
    (session-setup.mdx:144-145), so this is unconditionally a conformance failure and is
    raised via `pytest.fail(...)` immediately, regardless of which route surfaced it.
    """
    attempt_stack = contextlib.AsyncExitStack()
    try:
        agent = await attempt_stack.enter_async_context(connected_agent(launch))
        session_id = await route_setup(agent, cwd, timeout)
        req_id = await agent.send_request(
            "session/resume", {"sessionId": session_id, "cwd": str(cwd)}
        )
        entry = await agent.wait_for_response(req_id, timeout=timeout)
    except pytest.skip.Exception:
        await attempt_stack.aclose()
        raise
    except Exception as exc:  # noqa: BLE001 -- record and let the next route try
        errors.append(repr(exc))
        await attempt_stack.aclose()
        return None

    msg = entry.parsed
    if isinstance(msg, dict) and isinstance(msg.get("result"), dict):
        return agent, session_id, entry, attempt_stack.pop_all()

    if isinstance(msg, dict) and isinstance(msg.get("error"), dict):
        code = msg["error"].get("code")
        await attempt_stack.aclose()
        if code == METHOD_NOT_FOUND:
            pytest.fail(
                "session/resume answered -32601 Method not found -- session/resume is "
                "part of the baseline once capabilities.session is advertised at all, so "
                "this is a hard failure of ACP-RESUME-001, not a route-specific SKIP"
            )
        errors.append(f"session/resume error: {msg['error']!r}")
        return None

    await attempt_stack.aclose()
    errors.append(f"malformed session/resume response: {entry.text!r}")
    return None


@contextlib.asynccontextmanager
async def obtain_resumable_session(
    launch: AgentLaunch, cwd: Any, *, timeout: float | None = None
) -> AsyncIterator[tuple[AgentProcess, str, TranscriptEntry, Any]]:
    """Yield `(agent, session_id, resume_response_entry, resume_cwd)` for a connected,
    initialized agent, a session id this helper found `session/resume` accepts, the response
    entry from the successful probe call that proved it (`ACP-RESUME-001` uses this directly
    rather than issuing a second, redundant `session/resume` for the same id), and the `cwd`
    that probe used -- always `cwd` itself, since resume requires the session's own `cwd` and
    every route only ever resumes a session the TCK created in `cwd`.

    No route for obtaining a legally resumable session id is spec-guaranteed. Tries, in order,
    each on its own fresh connection: (1) resuming the session `session/new` just created on this
    same connection; (2) creating a session, `session/close`-ing it, then resuming it; (3) a
    `session/list` entry created in `cwd` (see `_route_from_list` -- last, and only matching
    `cwd`, so the operator's own saved sessions are never touched; it only succeeds against an
    agent that persists sessions across connections, such as the ones routes (1)/(2) created
    earlier in this same call). `pytest.skip(...)`s with all three routes' recorded errors if none
    succeeds -- *unless* `session/resume` itself ever answered `-32601`, which is instead a hard
    `pytest.fail(...)` (see `_attempt_resumable_route`).

    The yielded connection is whichever attempt succeeded; a caller that needs a *second*
    `session/resume` call with different params (e.g. a specific `replayFrom`) is free to issue
    one against the same session/connection.
    """
    errors: list[str] = []
    result = None
    for route_setup in (_route_just_created, _route_after_close, _route_from_list):
        result = await _attempt_resumable_route(launch, cwd, timeout, errors, route_setup)
        if result is not None:
            break
    if result is None:
        pytest.skip(
            "no resumable session obtainable via any of the three routes (create-then-resume, "
            "close-then-resume, list-then-resume): " + "; ".join(errors)
        )
    agent, session_id, entry, stack = result
    try:
        yield agent, session_id, entry, cwd
    finally:
        await stack.aclose()


@contextlib.asynccontextmanager
async def v2_only_agent(
    agent_launch: AgentLaunch,
    *,
    capabilities: dict[str, Any] | None = None,
    yield_result: bool = False,
    require_session: bool = False,
) -> AsyncIterator[Any]:
    """Shared "fresh connection, manual `initialize` routed through `SPEC.initialize_params()`,
    `VERSION-MISMATCH:` skip unless the agent actually negotiated v2, then `login_if_needed`"
    pattern used by every module that must control its own `initialize`/
    `skip_if_version_mismatch` call instead of `connected_agent`'s default v2-negotiating
    handshake -- `test_batch.py`, `test_session_config.py`, `test_authentication.py`,
    `test_transport.py`.

    Yields the connected `AgentProcess`, or `(agent, init_result)` when `yield_result=True` (for
    callers that need to inspect the negotiated result, e.g. a capabilities marker).
    `require_session=True` SKIPs like the capability gate unless `capabilities.session` is
    advertised, for callers that use `session/*` without a capability marker."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        params = SPEC.initialize_params()
        if capabilities is not None:
            params = {**params, "capabilities": capabilities}
        req_id = await agent.send_request("initialize", params)
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.startup_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not return a result object: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])
        if require_session and not advertises_session(msg["result"]):
            pytest.skip("capability 'capabilities.session' not advertised by the agent under test")
        await login_if_needed(agent, timeout=agent_launch.startup_timeout)
        if yield_result:
            yield agent, msg["result"]
        else:
            yield agent


def iter_messages(entry: TranscriptEntry) -> list[dict[str, Any]]:
    """Flatten one transcript entry into the list of dict-shaped JSON-RPC messages it carries:
    `[entry.parsed]` for an ordinary object line, every dict element of an array line, or `[]`
    for anything else (a parse failure, a bare scalar line, ...).

    ACP v2 has no batches, so an array line is itself non-conformant -- `ACP-TRANSPORT-001`
    judges that. It is flattened here only so every other row can still read what it carries
    (an agent that batches fails the TRANSPORT row, not every prompt row). A non-dict element
    is dropped: there is nothing meaningful to dispatch."""
    parsed = entry.parsed
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def agent_requests(transcript: list[TranscriptEntry]) -> list[dict[str, Any]]:
    """Every request the agent sent (a received object with `method` and `id`), in wire order.
    An `id: null` or non-scalar id still counts as a request, so the caller can judge it."""
    return [
        msg
        for entry in transcript
        if entry.direction is Direction.RECEIVED
        for msg in iter_messages(entry)
        if "method" in msg and "id" in msg
    ]


def is_response_line(entry: TranscriptEntry) -> bool:
    """True if `entry` carries a reply: any JSON-RPC object without `method`, bare or inside an
    array line, even a malformed one missing `id`/`result`/`error`.

    The one rule every "a notification gets no response" check uses. ACP and JSON-RPC 2.0
    §4.1/§6 forbid only *replies* to a notification. The agent's own notifications and agent ->
    client requests carry `method`, are not replies, and may arrive at any time after
    `initialize`. A non-JSON line is not a reply either; the transport rows judge it."""
    return any("method" not in msg for msg in iter_messages(entry))


async def first_response_within(agent: AgentProcess, quiet: float) -> TranscriptEntry | None:
    """Wait up to `quiet` seconds for a reply (`is_response_line`) and return it, or `None` if
    none arrived. Agent-initiated messages read meanwhile are skipped and left in
    `agent.pending()`. An agent -> client request among them is left unanswered, like in every
    other wait outside `run_prompt`: the check is about what the agent sends, not about driving
    it further. `AgentExited` propagates."""
    try:
        return await agent.wait_for_message(is_response_line, timeout=quiet)
    except AgentTimeout:
        return None


def is_agent_initiated(entry: TranscriptEntry) -> bool:
    """True if `entry` is a single JSON-RPC object carrying `method` -- a notification or an
    agent -> client request the agent initiated on its own. Such a line may arrive at any time
    after `initialize`, so it is never the reply a check is waiting for.

    Always False for an array: ACP v2 has no batches, so an array is never an agent-initiated
    message, and a probe waiting for its reply must see it instead of skipping past it."""
    parsed = entry.parsed
    return isinstance(parsed, dict) and "method" in parsed


async def next_reply_line(agent: AgentProcess, timeout: float) -> TranscriptEntry:
    """Return the first line within `timeout` that is not agent-initiated
    (`is_agent_initiated`), for the caller to judge as the reply it waits for. Anything else --
    a response object, but also an array or a non-JSON or otherwise malformed line -- is
    returned as-is, so the caller still judges the reply's shape. Skipped lines stay in
    `agent.pending()`, and an agent -> client request among them is left unanswered. `AgentTimeout`/`AgentExited` propagate."""
    return await agent.wait_for_message(lambda entry: not is_agent_initiated(entry), timeout=timeout)


async def probe_behaviour(
    read: Awaitable[TranscriptEntry],
    on_reply: Callable[[TranscriptEntry], str],
) -> str:
    """Run one already-started read `read` and classify the outcome as "silent" / "agent exited
    (exit_code=...)" / whatever `on_reply` returns for a reply that did arrive.

    Shared by the near-identical "did the agent stay silent, exit, or reply" INFORMATIONAL
    probes across `test_informational.py` and `test_cancel.py` -- only the
    common `AgentTimeout`/`AgentExited` ladder is identical between them; each site still
    supplies its own read call (a specific
    `wait_for_response`/`wait_for_message`/`read_line`, each with its own predicate/timeout) and
    its own `on_reply` classifier, since what counts as "a reply" differs (a JSON-RPC
    error/result split vs. a raw-text dump)."""
    try:
        entry = await read
    except AgentTimeout:
        return "silent"
    except AgentExited as exc:
        return f"agent exited (exit_code={exc.exit_code!r})"
    else:
        return on_reply(entry)


def update_of(entry: TranscriptEntry) -> dict[str, Any] | None:
    """Extract the `update` payload from a `session/update` transcript entry, or `None` if the
    entry is not a well-formed `session/update` notification."""
    msg = entry.parsed
    if not isinstance(msg, dict) or msg.get("method") != "session/update":
        return None
    params = msg.get("params")
    if not isinstance(params, dict):
        return None
    update = params.get("update")
    return update if isinstance(update, dict) else None


def skip_if_version_mismatch(init_result: dict[str, Any]) -> None:
    """Skip with the `VERSION-MISMATCH: ` marker (`tck.common.plugin`'s `_VERSION_MISMATCH_MARKER`
    substring, scanned by `_build_report()` to set `Verdict.blocked_by_version_mismatch`) unless
    `init_result`'s negotiated `protocolVersion` is this suite's own `PROTOCOL_VERSION` (2).

    An agent that honestly negotiates down to a lower version (e.g. a v1-only agent answering `1`
    to a v2 client -- see `ACP-INIT-201`) is not thereby
    "broken": the negotiation itself is judged normally by `ACP-INIT-001`/`003`/`201`/`202`/`208`, which
    only ever assert on the negotiation outcome, never on the *shape* of the result payload. But
    a test that goes on to assert v2-only shape requirements against that same result -- `info`
    being REQUIRED (`ACP-INIT-004`), capability markers being objects (`ACP-INIT-204`), or the
    exchange validating against the v2 schema (`ACP-SCHEMA-001`) -- cannot honestly judge a
    result the agent never claimed was v2-shaped; call this right after such a test has its own
    `init_result` in hand, before evaluating any v2-shape assertion.

    Unlike `tck.common.plugin`'s `_tck_capability_gate`, which only runs for
    `@pytest.mark.capability(...)`-marked tests sharing the session-scoped
    `agent_initialize_result` fixture, every test in `test_initialize.py` spawns its own fresh
    process and sends its own `initialize` (so a probe's connection state is never inherited
    from the cached handshake) -- so this has to be called explicitly rather than picked up by
    an autouse fixture.
    """
    negotiated = init_result.get("protocolVersion")
    if negotiated != PROTOCOL_VERSION:
        pytest.skip(
            f"VERSION-MISMATCH: negotiated protocolVersion={negotiated!r}, expected "
            f"{PROTOCOL_VERSION!r} -- this agent does not speak v2, so its result cannot be "
            "judged against v2-only shape requirements"
        )


def advertises_session(init_result: dict[str, Any] | None) -> bool:
    """Whether an `initialize` result advertises `capabilities.session` (object marker: present
    and non-null). Only `initialize` is unconditional in v2, so a test that is not
    `capabilities.session`-gated must not call `session/*` methods unless this holds; it falls
    back to `_`-prefixed probe traffic instead. A v1-shaped result has no `capabilities`."""
    capabilities = init_result.get("capabilities") if isinstance(init_result, dict) else None
    return isinstance(capabilities, dict) and capabilities.get("session") is not None


def cancel_race_peek(timeout: float) -> float:
    """Like v1's `cancel_race_peek` (same formula, deliberately re-implemented rather than
    imported): a short, bounded look for a line that may already be sitting in the pipe, used by
    `run_prompt` right after it decides the turn has ended, to give a trailing/out-of-order
    response (e.g. `on_action`'s) one last chance to be captured before returning."""
    return max(0.05, min(0.5, timeout / 50))


def quiet_period(timeout: float) -> float:
    """v2 twin of v1's `quiet_period` (identical formula, deliberately re-implemented rather than
    imported -- honest duplication, not shared machinery): the heuristic "nothing more is
    coming" wait used by probes that conclude absence (e.g. `ACP-INFO-PARSE-001`'s "did the
    agent reply at all") -- derived from `--tck-timeout` rather than a hard-coded sub-second
    constant, clamped to a sane range."""
    return max(0.5, min(2.0, timeout / 10))


# Stop reasons an agent may have reached on its own just before reading the trigger.
_RACE_PLAUSIBLE_STOP_REASONS = frozenset({"end_turn", "max_tokens", "max_turn_requests", "refusal"})


def race_plausible(stop_reason) -> bool:
    return (
        stop_reason is None
        or stop_reason in _RACE_PLAUSIBLE_STOP_REASONS
        or (isinstance(stop_reason, str) and stop_reason.startswith("_"))
    )


def response_error(turn) -> dict | None:
    msg = turn.response_entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error if isinstance(error, dict) else None


def skip_if_turn_end_race_not_exercised(
    agent,
    turn,
    record_property,
    *,
    race_window: float,
    trigger_at_index: int | None,
    trigger_method: str,
    verb: str,
    property_prefix: str,
) -> None:
    """Shared race gate for the rows triggered by `session/cancel`, `session/close` or
    `session/delete` mid-turn; see `test_cancel.py`'s module docstring for the rules. Only ever
    SKIPs or returns; never asserts."""
    if trigger_at_index is None:
        pytest.skip(f"{verb} not exercised: the turn ended before {trigger_method} could be sent")
    record_property(f"acp_tck_{property_prefix}_state_at_trigger", turn.state_at_cancel)
    if response_error(turn) is not None and turn.response_index < trigger_at_index:
        pytest.skip(
            f"{verb} not exercised: session/prompt was rejected before {trigger_method} was sent"
        )
    if turn.idle_update is None:
        return  # error response with no foreground work: judged by the caller
    stop_reason = turn.stop_reason
    if stop_reason == "cancelled" or not race_plausible(stop_reason):
        return
    trigger_timestamp = agent.transcript[trigger_at_index].timestamp
    elapsed_ms = (turn.idle_update.timestamp - trigger_timestamp) * 1000
    record_property(f"acp_tck_{property_prefix}_race_window_ms", f"{race_window * 1000:.0f}")
    if elapsed_ms < race_window * 1000:
        record_property(f"acp_tck_{property_prefix}_race_ms", f"{elapsed_ms:.0f}")
        pytest.skip(
            f"{verb} not exercised: idle arrived {elapsed_ms:.0f} ms after {trigger_method} "
            f"(within the race window) with stopReason {stop_reason!r} -- the agent may simply "
            "have finished before reading it"
        )


ACTIVE_STATES = frozenset({"running", "requires_action"})
"""The foreground-active `state_update.state` values (prompt-lifecycle.mdx:152,1073). Work may
start directly in `requires_action` (:1080-1082), so both count as "active"."""


def is_active_state(state: Any) -> bool:
    """Whether `state` is in `ACTIVE_STATES`; a non-string (even unhashable) value never is."""
    return isinstance(state, str) and state in ACTIVE_STATES


def session_state_update(msg: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    """The `update` payload if `msg` is a `session/update` `state_update` for `session_id`, else
    `None`. A child session's state (announced via `subagent_update`) is never the parent's."""
    if msg.get("method") != "session/update":
        return None
    params = msg.get("params")
    if not isinstance(params, dict) or params.get("sessionId") != session_id:
        return None
    update = params.get("update")
    if isinstance(update, dict) and update.get("sessionUpdate") == "state_update":
        return update
    return None


BACKGROUND_ID_FIELDS = {"terminal": "terminalId", "tool_call": "toolCallId", "subagent": "sessionId"}
"""The id field of each defined `background` item type (`#/$defs/BackgroundWork`)."""


def background_keys(update: dict[str, Any]) -> set[tuple[str, str]] | None:
    """`(type, id)` of every defined-type item in a `state_update`'s `background` list, or
    `None` when the list is omitted, `null` or not an array: not reported
    (prompt-lifecycle.mdx:203-204). Items of other types, or without a string id, are left out."""
    items = update.get("background")
    if not isinstance(items, list):
        return None
    keys = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        field_name = BACKGROUND_ID_FIELDS.get(item_type) if isinstance(item_type, str) else None
        if field_name is not None and isinstance(item.get(field_name), str):
            keys.add((item["type"], item[field_name]))
    return keys


def last_known_background(agent: AgentProcess, session_id: str) -> set[tuple[str, str]] | None:
    """`background_keys` of the last `state_update` for `session_id` already read on this
    connection, or `None` if there is none or it did not report a list."""
    keys = None
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            update = session_state_update(msg, session_id)
            if update is not None:
                keys = background_keys(update)
    return keys


def permission_subject_keys(params: dict[str, Any]) -> set[tuple[str, str]]:
    """The `background` keys a `session/request_permission`'s `subject` references: a
    `tool_call` subject's `toolCall.toolCallId`, or a `command` subject's `toolCallId`/
    `terminalId` (tool-calls.mdx:268)."""
    subject = params.get("subject")
    if not isinstance(subject, dict):
        return set()
    keys = set()
    if subject.get("type") == "tool_call":
        tool_call = subject.get("toolCall")
        if isinstance(tool_call, dict) and isinstance(tool_call.get("toolCallId"), str):
            keys.add(("tool_call", tool_call["toolCallId"]))
    elif subject.get("type") == "command":
        if isinstance(subject.get("toolCallId"), str):
            keys.add(("tool_call", subject["toolCallId"]))
        if isinstance(subject.get("terminalId"), str):
            keys.add(("terminal", subject["terminalId"]))
    return keys


def last_known_state(agent: AgentProcess, session_id: str) -> Any:
    """The `state` of the last `state_update` for `session_id` already read on this connection,
    or `None` if none was. Seeds `run_prompt`'s notion of "active" so a prompt sent while earlier
    (e.g. agent-initiated) foreground work is still running is not misjudged."""
    state = None
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            update = session_state_update(msg, session_id)
            if update is not None:
                state = update.get("state")
    return state


PermissionPolicy = Literal["allow", "reject_once", "unknown_option", "unknown_outcome", "cancelled"]
"""How `run_prompt` answers `session/request_permission` (until `session/cancel` is sent):
`allow` (the default) selects `allow_once`, else `allow_always`, else `reject_once`;
`reject_once` selects `reject_once`. When the policy's kinds are not offered it never picks
another option (a `*_always` would persist an approval or a standing deny in the operator's
agent): it sends `session/cancel` and answers `cancelled`. `unknown_option` selects an
`optionId` the agent never offered; `unknown_outcome` answers a `_`-prefixed custom outcome
(`UNKNOWN_PERMISSION_OUTCOME`); `cancelled` answers the `cancelled` outcome without sending
`session/cancel`."""

UNKNOWN_PERMISSION_OPTION_ID = "_tck_unoffered_option"
"""The `optionId` the `unknown_option` policy selects (`_`-prefixed per the extensibility rule)."""

UNKNOWN_PERMISSION_OUTCOME = "_tck_unknown"
"""The `outcome` the `unknown_outcome` policy answers. A legal custom value: the outcome is an
open enum (`#/$defs/RequestPermissionOutcome`, `other` branch) and `_` marks an extension."""


def permission_outcome(options: Any, policy: PermissionPolicy) -> tuple[dict[str, Any], str | None]:
    """The `RequestPermissionOutcome` for `policy`, plus a note when the preferred option kind
    was not offered (else `None`). Options are picked by `kind`, never by position.

    `allow`: `allow_once`, else `allow_always` (noted), else `reject_once` (noted).
    `reject_once`: `reject_once` only. Neither ever selects a `*_always` it was not asked for:
    with none of its kinds offered it answers `cancelled` *with a note*, and the caller must
    then send `session/cancel` first, as a conforming client does before answering a pending
    permission request `cancelled`. Tolerates malformed options."""
    if policy == "cancelled":
        return {"outcome": "cancelled"}, None
    if policy == "unknown_option":
        return {"outcome": "selected", "optionId": UNKNOWN_PERMISSION_OPTION_ID}, None
    if policy == "unknown_outcome":
        return {"outcome": UNKNOWN_PERMISSION_OUTCOME}, None
    candidates = [o for o in options if isinstance(o, dict)] if isinstance(options, list) else []

    def first_of_kind(kind: str) -> dict[str, Any] | None:
        return next((o for o in candidates if o.get("kind") == kind), None)

    if policy == "reject_once":
        preferences = [("reject_once", None)]
        missing = "agent offered no reject_once option"
    else:
        preferences = [
            ("allow_once", None),
            ("allow_always", "allow_always selected (allow_once not offered)"),
            ("reject_once", "reject_once selected (no allow option offered)"),
        ]
        missing = "agent offered no allow_once, allow_always or reject_once option"
    for kind, note in preferences:
        chosen = first_of_kind(kind)
        if chosen is not None:
            return {"outcome": "selected", "optionId": chosen.get("optionId")}, note
    return {"outcome": "cancelled"}, missing


def _answer_permission(options: Any, policy: PermissionPolicy) -> tuple[dict[str, Any], str | None]:
    """`permission_outcome`, recording any fallback note on the current test's report entry."""
    outcome, note = permission_outcome(options, policy)
    if note is not None:
        record_test_property("acp_tck_permission_fallback", note)
    return outcome, note


@dataclass(frozen=True)
class PromptTurn:
    """The outcome of one v2 `session/prompt` turn driven by `run_prompt`.

    Unlike v1's `PromptTurn` (whose `response_entry` *is* the turn result), v2's response is only
    an acceptance receipt -- the turn's outcome is learned from `state_update` notifications.
    """

    session_id: str
    response_entry: TranscriptEntry
    """The `session/prompt` response (the acceptance receipt, or a JSON-RPC error)."""
    response_index: int
    """Transcript line index of `response_entry`."""
    message_id: str | None
    """The response result's `messageId` if it is a string; `None` otherwise."""
    idle_update: TranscriptEntry | None
    """The `session/update` carrying the turn-ending idle, or `None` when the turn ended with an
    error response and no foreground work (`terminated_by == "error"`)."""
    idle_index: int | None = None
    """Transcript line index of `idle_update` (an array line's own index)."""
    stop_reason: Any = None
    """The turn-ending idle's `stopReason` exactly as sent (missing and `null` both read as
    `None`); validity is the caller's job."""
    terminated_by: str = "idle"
    """`"idle"` (an idle after an active state), `"idle_without_active"` (the confirmed fallback:
    a stopReason-bearing idle with no active state before it), or `"error"`."""
    active_seen: bool = False
    """Whether the session was active at any point: `running`/`requires_action` observed during
    the turn, or already the last known state when the prompt was sent."""
    requires_action_seen: bool = False
    states: list[tuple[int, dict[str, Any]]] = field(default_factory=list)
    """`(transcript_index, update)` for every `state_update` of `session_id` during the turn."""
    updates: list[tuple[int, TranscriptEntry]] = field(default_factory=list)
    """`(transcript_index, entry)` for every `session/update` observed during the turn, in wire
    order, whatever `sessionId` it carried (`ACP-PROMPT-002` judges attribution)."""
    client_requests_seen: list[TranscriptEntry] = field(default_factory=list)
    """Every agent -> client request (answered by the mock client) and every agent -> client
    notification other than `session/update` (e.g. `$/cancel_request`, or an undefined method,
    for `ACP-CLIENTCAP-202`) observed during the turn."""
    permission_requests: list[tuple[int, TranscriptEntry]] = field(default_factory=list)
    """`(transcript_index, entry)` for every `session/request_permission` observed during the
    turn, whatever `sessionId` it carried, so it can be merged with `updates` in wire order."""
    cancelled_at_index: int | None = None
    """Transcript index of the `session/cancel` sent for this turn, or `None` if none was."""
    state_at_cancel: Any = None
    """The session's last known `state` when the trigger (cancel or `on_action`) fired. With
    `cancel_after_action`, the state when `on_action` fired, before the delayed cancel."""
    held_permission: TranscriptEntry | None = None
    """In `hold_permission` mode, the `session/request_permission` that was pending, unanswered,
    when the trigger fired."""
    held_cancel_request_index: int | None = None
    """Transcript index of the first agent `$/cancel_request` naming `held_permission` that
    `run_prompt` read while the request was still unanswered, before or after the turn-ending
    idle."""
    held_answered_on: str | None = None
    """What made `run_prompt` answer `held_permission` `cancelled`: `"cancel_request"` (the agent
    withdrew it), `"turn_end"` (the turn ended with it still pending), `"timeout"` (the turn had
    not ended by the deadline), or `None` if it was never answered."""
    action_response: TranscriptEntry | None = None
    """The response to `on_action`'s request, if it fired and was answered within the turn."""
    action_sent_at_index: int | None = None
    """Transcript index at which `on_action`'s request was sent."""
    permission_fallbacks: list[str] = field(default_factory=list)
    """A note per `session/request_permission` answered with other than the preferred option
    kind (`permission_outcome`), including one for listed background work that the policy could
    not satisfy (answered `cancelled`, no `session/cancel`); also recorded as the
    `acp_tck_permission_fallback` property."""
    permission_cancels: list[str] = field(default_factory=list)
    """A note per other `session/request_permission` the policy could not satisfy: the mock
    client sent `session/cancel` and answered `cancelled` instead. Also recorded as the
    `acp_tck_permission_fallback` property."""


async def run_prompt(
    agent: AgentProcess,
    session_id: str,
    blocks: list[dict[str, Any]],
    *,
    on_cancel: bool = False,
    on_action: Callable[[], Awaitable[Any]] | None = None,
    cancel_wait: float = 0.5,
    cancel_meta: dict[str, Any] | None = None,
    hold_permission: bool = False,
    cancel_after_action: float | None = None,
    permission: PermissionPolicy = "allow",
    extra_params: dict[str, Any] | None = None,
    timeout: float,
) -> PromptTurn:
    """Drive one v2 `session/prompt` turn to its end, acting as a minimal mock client.

    The response is only an acceptance receipt; the turn's end is learned from `state_update`s
    for `session_id` (a child session's states never count). Every wait is bounded by `timeout`;
    an agent that never reaches a turn end raises `AgentTimeout`.

    **Turn-end predicate.** `active` starts as "the session's last known state is `running` or
    `requires_action`" and becomes true on either state during the turn. Then, once the response
    has been read:
    - the first `idle` after an active state ends the turn, whatever its `stopReason` (it is
      SHOULD, and may be omitted; prompt-lifecycle.mdx:936) -- `terminated_by="idle"`. The idle
      may arrive before or after the response (:372). One read before the response is only a
      candidate: it ends the turn once `quiet_period(timeout)` passes after the response with no
      active state, and an active state voids it, because it may end earlier work rather than
      this prompt's (a prompt sent during active work may be held until that work ends,
      :382-384);
    - an error response with no active state ends the turn after a short peek finds none
      (a rejection with no foreground work needs no state transition, :390) --
      `terminated_by="error"`. If work is active, the driver keeps waiting for the idle the
      agent still owes (:390,969);
    - fallback for agents that never report an active state: an `idle` carrying a `stopReason`
      ends the turn once `quiet_period(timeout)` passes with no active state after it and after
      the response -- `terminated_by="idle_without_active"`. An active state inside that window
      voids it, since repeated idle snapshots may carry the previous stopReason (:1084-1087).
    `unknown` and custom states are recorded but neither start nor end a turn.

    The trigger (`on_cancel`/`on_action`) fires on the first transition to an active state, after
    a short race-aware peek, or once `cancel_wait` elapses. With `hold_permission=True` (needs a
    trigger), it instead fires when the first `session/request_permission` for `session_id`
    arrives, and that request is held: left unanswered, because after `session/cancel` the agent
    must stop waiting for it (prompt-lifecycle.mdx:1177,1188-1189). It is answered `cancelled`
    only when the agent withdraws it with `$/cancel_request` (the client then answers it,
    cancellation.mdx:20; tool-calls.mdx:326), when the turn ends (after `quiet_period(timeout)`
    for a late `$/cancel_request`), or when `timeout` expires with the turn still open: then the
    driver answers it and waits `quiet_period(timeout)` more, so a caller can tell "ended only
    once answered" (`held_answered_on == "timeout"`) from "never ended" (`AgentTimeout`).
    `cancel_wait` remains the fallback trigger.

    With `on_cancel`, `on_action` and `cancel_after_action` all set, the trigger fires only
    `on_action`. `session/cancel` follows once the action's response arrives or
    `cancel_after_action` seconds pass, unless the turn has ended by then (`cancelled_at_index`
    then stays `None`). Until it is sent, permission requests are answered per `permission`.

    While waiting, `session/request_permission` is answered per `permission` (see
    `PermissionPolicy`; options are picked by `kind`, never by position), or `cancelled` for the
    prompted session once the trigger has fired; any other
    agent -> client request gets `-32601` (the mock client advertises no capabilities).
    A request whose `subject` names an item in the session's latest `background` list is
    background work, which `session/cancel` does not cover (prompt-lifecycle.mdx:1173,1177;
    tool-calls.mdx:268): it is never held and is always answered per `permission`, and if the
    policy's kinds are not offered it is answered `cancelled` without `session/cancel`. A
    `state_update` that omits the list leaves none known (:204).

    v2 lets a client prompt in any state (prompt-lifecycle.mdx:382), but `run_prompt` cannot
    attribute an idle to one of several outstanding prompts, so callers serialize prompts per
    session. A second prompt during the turn is sent raw, as `on_action` (see
    `prompt_during_active_work`).
    """
    seed_state = last_known_state(agent, session_id)
    latest_background = last_known_background(agent, session_id)
    params = {"sessionId": session_id, "prompt": blocks}
    if extra_params:
        params.update(extra_params)
    prompt_id = await agent.send_request("session/prompt", params)

    loop = asyncio.get_running_loop()
    overall_deadline = loop.time() + timeout
    peek_timeout = cancel_race_peek(timeout)
    confirm_window = quiet_period(timeout)

    response_entry: TranscriptEntry | None = None
    response_index: int | None = None
    response_at: float | None = None
    response_error = False
    message_id: str | None = None
    active = is_active_state(seed_state)
    active_seen = active
    requires_action_seen = False
    last_state = seed_state
    states: list[tuple[int, dict[str, Any]]] = []
    idle_update: TranscriptEntry | None = None
    idle_index: int | None = None
    stop_reason: Any = None
    terminated_by: str | None = None
    # (entry, line_index, stopReason, arrival time) of a stopReason-bearing idle with no active
    # state before it -- see the fallback in the docstring.
    provisional: tuple[TranscriptEntry, int, Any, float] | None = None
    # (entry, line_index, stopReason) of an idle after an active state read before the response:
    # the candidate turn end (see the docstring).
    early_idle: tuple[TranscriptEntry, int, Any] | None = None
    error_end_deadline: float | None = None
    updates: list[tuple[int, TranscriptEntry]] = []
    client_requests_seen: list[TranscriptEntry] = []
    permission_requests: list[tuple[int, TranscriptEntry]] = []
    permission_fallbacks: list[str] = []
    permission_cancels: list[str] = []
    cancelled_at_index: int | None = None
    state_at_cancel: Any = None
    held_permission: TranscriptEntry | None = None
    held_cancel_request_index: int | None = None
    held_answered_on: str | None = None
    action_response: TranscriptEntry | None = None
    action_sent_at_index: int | None = None
    action_id: Any = None

    trigger_armed = on_cancel or on_action is not None
    trigger_on_active = trigger_armed and not hold_permission
    trigger_sent = False
    trigger_deadline = loop.time() + cancel_wait
    delay_cancel = on_cancel and on_action is not None and cancel_after_action is not None
    # When the delayed `session/cancel` is due (set once `on_action` fired).
    cancel_due: float | None = None

    async def _send_cancel() -> None:
        nonlocal cancelled_at_index
        cancel_params: dict[str, Any] = {"sessionId": session_id}
        if cancel_meta is not None:
            cancel_params["_meta"] = cancel_meta
        await agent.send_notification("session/cancel", cancel_params)
        cancelled_at_index = len(agent.transcript) - 1

    async def _fire_trigger() -> None:
        nonlocal trigger_sent, state_at_cancel, action_id, action_sent_at_index, cancel_due
        if trigger_sent:
            return
        trigger_sent = True
        state_at_cancel = last_state
        if on_cancel and cancelled_at_index is None and not delay_cancel:
            await _send_cancel()
        if on_action is not None:
            action_id = await on_action()
            action_sent_at_index = len(agent.transcript) - 1
            if delay_cancel:
                assert cancel_after_action is not None
                cancel_due = loop.time() + cancel_after_action

    async def _send_delayed_cancel_if_due() -> None:
        if cancel_due is None or cancelled_at_index is not None:
            return
        if action_response is not None or loop.time() >= cancel_due:
            await _send_cancel()

    def _cancel_pending() -> bool:
        """Whether a delayed `session/cancel` has yet to be sent."""
        return delay_cancel and cancelled_at_index is None

    async def _send_permission_answer(request_id: Any, outcome: dict[str, Any]) -> None:
        await agent.send_message(
            {"jsonrpc": "2.0", "id": request_id, "result": {"outcome": outcome}}
        )

    async def _answer_held(reason: str) -> None:
        """Answer the held permission request `cancelled`, once."""
        nonlocal held_answered_on
        if held_permission is None or held_answered_on is not None:
            return
        held_answered_on = reason
        await _send_permission_answer(held_permission.parsed["id"], {"outcome": "cancelled"})

    def _names_held(msg: dict[str, Any]) -> bool:
        """Whether `msg` (a `$/cancel_request`) names the held request's id, type included."""
        if held_permission is None:
            return False
        params = msg.get("params")
        if not isinstance(params, dict) or "requestId" not in params:
            return False
        request_id = params["requestId"]
        held_id = held_permission.parsed["id"]
        return type(request_id) is type(held_id) and request_id == held_id

    def _pending_end_deadline() -> float | None:
        """When a not-yet-final turn end (early idle, error peek or fallback idle) becomes
        final."""
        if response_entry is None or idle_update is not None:
            return None
        if early_idle is not None:
            assert response_at is not None
            return response_at + confirm_window
        if active:
            return None
        if response_error:
            return error_end_deadline
        if provisional is not None:
            assert response_at is not None
            return max(provisional[3], response_at) + confirm_window
        return None

    def _try_end() -> bool:
        nonlocal idle_update, idle_index, stop_reason, terminated_by
        if response_entry is None:
            return False
        if idle_update is not None:
            return True
        deadline = _pending_end_deadline()
        if deadline is None or loop.time() < deadline:
            return False
        if early_idle is not None:
            idle_update, idle_index, stop_reason = early_idle
            terminated_by = "idle"
        elif response_error:
            terminated_by = "error"
        else:
            assert provisional is not None
            idle_update, idle_index, stop_reason, _ = provisional
            terminated_by = "idle_without_active"
        return True

    async def _handle_one(entry: TranscriptEntry) -> None:
        """Dispatch one line. An array line is non-conformant (`ACP-TRANSPORT-001` judges it)
        but is still dispatched element by element, through synthetic per-item entries sharing
        the line's raw/timestamp, so the agent fails only that row; their recorded index is the
        line's own."""
        line_index = agent.transcript.index(entry)
        raw_msg = entry.parsed
        if isinstance(raw_msg, list):
            for item in raw_msg:
                if isinstance(item, dict):
                    await _handle_message(replace(entry, parsed=item), line_index)
        elif isinstance(raw_msg, dict):
            await _handle_message(entry, line_index)

    async def _handle_message(entry: TranscriptEntry, line_index: int) -> None:
        nonlocal response_entry, response_index, response_at, response_error, message_id
        nonlocal active, active_seen, requires_action_seen, last_state, provisional, early_idle
        nonlocal idle_update, idle_index, stop_reason, terminated_by, error_end_deadline
        nonlocal action_response, held_permission, cancelled_at_index, held_cancel_request_index
        nonlocal latest_background
        msg = entry.parsed
        if entry.matches_id(prompt_id):
            response_entry, response_index, response_at = entry, line_index, loop.time()
            if "error" in msg:
                response_error = True
                error_end_deadline = loop.time() + peek_timeout
            else:
                result = msg.get("result")
                if isinstance(result, dict) and isinstance(result.get("messageId"), str):
                    message_id = result["messageId"]
            return
        if action_id is not None and entry.matches_id(action_id):
            action_response = entry
            return

        method = msg.get("method")
        if method == "session/update":
            updates.append((line_index, entry))
            update = session_state_update(msg, session_id)
            if update is None:
                return
            state = update.get("state")
            states.append((line_index, update))
            last_state = state
            latest_background = background_keys(update)
            if is_active_state(state):
                active = active_seen = True
                requires_action_seen = requires_action_seen or state == "requires_action"
                provisional = None
                early_idle = None
            elif state == "idle" and idle_update is None:
                sr = update.get("stopReason")
                if active:
                    if early_idle is not None:
                        pass  # a repeated snapshot; the candidate stands
                    elif response_entry is None:
                        early_idle = (entry, line_index, sr)
                    else:
                        idle_update, idle_index, stop_reason = entry, line_index, sr
                        terminated_by = "idle"
                elif sr is not None and provisional is None:
                    provisional = (entry, line_index, sr, loop.time())
            return

        if method == "session/request_permission" and "id" in msg:
            client_requests_seen.append(entry)
            permission_requests.append((line_index, entry))
            req_params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            for_this_session = req_params.get("sessionId") == session_id
            for_background = for_this_session and bool(
                latest_background and permission_subject_keys(req_params) & latest_background
            )
            for_foreground = for_this_session and not for_background
            if hold_permission and not trigger_sent and for_foreground:
                held_permission = entry
                await _fire_trigger()
                return  # left unanswered; see `_answer_held`
            cancelled = (trigger_sent and not _cancel_pending()) or cancelled_at_index is not None
            if cancelled and for_foreground:
                outcome: dict[str, Any] = {"outcome": "cancelled"}
            else:
                outcome, note = _answer_permission(req_params.get("options"), permission)
                if note is not None and outcome["outcome"] == "cancelled" and for_background:
                    # `session/cancel` does not cover listed background work
                    # (prompt-lifecycle.mdx:1173,1177), so only this request is declined
                    # (tool-calls.mdx:340).
                    permission_fallbacks.append(note)
                elif note is not None and outcome["outcome"] == "cancelled":
                    # The policy's option kinds were not offered: cancel the request's session
                    # first, then answer `cancelled` without waiting for `$/cancel_request`
                    # (prompt-lifecycle.mdx:1177). The turn then drains to its `idle` like any
                    # other cancelled turn.
                    target = req_params.get("sessionId")
                    await agent.send_notification(
                        "session/cancel",
                        {"sessionId": target if isinstance(target, str) else session_id},
                    )
                    if for_this_session:
                        cancelled_at_index = len(agent.transcript) - 1
                    permission_cancels.append(note)
                elif note is not None:
                    permission_fallbacks.append(note)
            await _send_permission_answer(msg["id"], outcome)
            return

        if method is not None and "id" in msg:
            client_requests_seen.append(entry)
            await agent.send_message(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "error": {"code": METHOD_NOT_FOUND, "message": "Method not found"},
                }
            )
            return

        if method is not None:
            client_requests_seen.append(entry)
            if method == "$/cancel_request" and _names_held(msg):
                # One read after the TCK already answered the request is not a withdrawal.
                if held_cancel_request_index is None and held_answered_on is None:
                    held_cancel_request_index = line_index
                await _answer_held("cancel_request")

    def _clamped(seconds: float) -> float:
        # A non-positive value still resolves: `read_line` forwards it to `asyncio.wait_for`,
        # which then checks once without blocking.
        return min(seconds, overall_deadline - loop.time())

    ended = False
    while not ended:
        now = loop.time()
        remaining = overall_deadline - now
        if remaining <= 0:
            if held_permission is not None and held_answered_on is None:
                # Answer once, then allow a short grace only to tell "ended once answered" from
                # "never ended".
                await _answer_held("timeout")
                overall_deadline = loop.time() + confirm_window
                continue
            detail = ""
            if held_answered_on == "timeout":
                detail = (
                    ", not even after its held session/request_permission was answered "
                    "`cancelled` at the deadline"
                )
            raise AgentTimeout(
                f"session/prompt {prompt_id!r} on session {session_id!r} did not reach a "
                f"turn end within {timeout}s{detail}",
                agent.transcript,
                stderr=agent.stderr_text(),
            )
        read_timeout = remaining
        if trigger_armed and not trigger_sent:
            wait_remaining = trigger_deadline - now
            read_timeout = min(read_timeout, wait_remaining if wait_remaining > 0 else 0.05)
        end_deadline = _pending_end_deadline()
        if end_deadline is not None:
            read_timeout = min(read_timeout, max(0.0, end_deadline - now))
        if cancel_due is not None and _cancel_pending():
            read_timeout = min(read_timeout, max(0.0, cancel_due - now))

        try:
            entry = await agent.read_line(timeout=read_timeout)
        except AgentTimeout:
            if trigger_armed and not trigger_sent and loop.time() >= trigger_deadline:
                await _fire_trigger()
            ended = _try_end()
            if not ended:
                await _send_delayed_cancel_if_due()
            continue

        was_active = active
        await _handle_one(entry)
        ended = _try_end()
        if not ended:
            await _send_delayed_cancel_if_due()

        if not ended and trigger_on_active and not trigger_sent and active and not was_active:
            # Race-aware peek: a turn end already sitting in the pipe is read before acting, so
            # an agent that finished first is not misjudged as having ignored the trigger.
            try:
                peek_entry = await agent.read_line(timeout=_clamped(peek_timeout))
            except AgentTimeout:
                await _fire_trigger()
            else:
                await _handle_one(peek_entry)
                ended = _try_end()
                if not ended:
                    await _fire_trigger()

    assert response_entry is not None and response_index is not None and terminated_by is not None

    if held_permission is not None and held_answered_on is None:
        # The turn ended with the request still pending. A `$/cancel_request` may still follow
        # the idle (it has no ordering rule); give it `confirm_window`, then answer anyway.
        grace_end = loop.time() + confirm_window
        while held_answered_on is None and (left := grace_end - loop.time()) > 0:
            try:
                entry = await agent.read_line(timeout=left)
            except AgentTimeout:
                break
            await _handle_one(entry)
        await _answer_held("turn_end")

    if terminated_by != "error" and action_id is not None and action_response is None:
        # One short trailing peek for `on_action`'s response arriving just after the turn ended.
        try:
            peek_entry = await agent.read_line(timeout=_clamped(peek_timeout))
        except AgentTimeout:
            pass
        else:
            await _handle_one(peek_entry)

    return PromptTurn(
        session_id=session_id,
        response_entry=response_entry,
        response_index=response_index,
        message_id=message_id,
        idle_update=idle_update,
        idle_index=idle_index,
        stop_reason=stop_reason,
        terminated_by=terminated_by,
        active_seen=active_seen,
        requires_action_seen=requires_action_seen,
        states=states,
        updates=updates,
        client_requests_seen=client_requests_seen,
        permission_requests=permission_requests,
        cancelled_at_index=cancelled_at_index,
        state_at_cancel=state_at_cancel,
        held_permission=held_permission,
        held_cancel_request_index=held_cancel_request_index,
        held_answered_on=held_answered_on,
        action_response=action_response,
        action_sent_at_index=action_sent_at_index,
        permission_fallbacks=permission_fallbacks,
        permission_cancels=permission_cancels,
    )


def session_events(turn: PromptTurn) -> list[tuple[int, str, dict[str, Any]]]:
    """The prompted session's `session/update` payloads (`"update"`) and
    `session/request_permission` params (`"permission"`) from `turn`, in wire order, as
    `(transcript_index, kind, payload)`. Clients apply a `tool_call` subject in the order it was
    received relative to updates (tool-calls.mdx:270-273). A child session's traffic is left
    out: entity ids are per session."""
    events: list[tuple[int, str, dict[str, Any]]] = []
    for index, entry in turn.updates:
        params = entry.parsed.get("params") if isinstance(entry.parsed, dict) else None
        if isinstance(params, dict) and params.get("sessionId") == turn.session_id:
            if isinstance(params.get("update"), dict):
                events.append((index, "update", params["update"]))
    for index, entry in turn.permission_requests:
        params = entry.parsed.get("params") if isinstance(entry.parsed, dict) else None
        if isinstance(params, dict) and params.get("sessionId") == turn.session_id:
            events.append((index, "permission", params))
    events.sort(key=lambda event: event[0])  # stable: one array line keeps its own order
    return events


def tool_call_report(kind: str, payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]] | None:
    """`(toolCallId, source, fields)` if a `session_events` event reports a tool call, else
    `None`. Three things report one, and each creates it on a first-seen id: a
    `tool_call_update` (`fields` is the update), a `tool_call_content_chunk` (no tool-call fields
    of its own, so `fields` is `{}`; tool-calls.mdx:198-200), and a `tool_call` permission
    subject (`fields` is its `toolCall`, applied like an update; :270-273). A report without a
    non-empty string id is `ACP-PATCH-204`'s concern and yields `None`."""
    if kind == "permission":
        subject = payload.get("subject")
        if not isinstance(subject, dict) or subject.get("type") != "tool_call":
            return None
        fields = subject.get("toolCall")
        source = "permission subject"
    else:
        source = payload.get("sessionUpdate")
        if source == "tool_call_update":
            fields = payload
        elif source == "tool_call_content_chunk":
            fields = {"toolCallId": payload.get("toolCallId")}
        else:
            return None
    if not isinstance(fields, dict):
        return None
    tool_call_id = fields.get("toolCallId")
    if not isinstance(tool_call_id, str) or not tool_call_id:
        return None
    return tool_call_id, source, {} if source == "tool_call_content_chunk" else fields


FINAL_TOOL_CALL_STATUSES = frozenset({"completed", "failed", "cancelled"})
"""The tool-call statuses that are final (tool-calls.mdx:423)."""


def _advertises_cancel(capabilities: Any) -> bool:
    """Whether a `capabilities` patch value advertises `cancel`: only an object `cancel` does
    (tool-calls.mdx:440). A malformed value means no controls (`#/$defs/ToolCallCapabilities`)."""
    return isinstance(capabilities, dict) and isinstance(capabilities.get("cancel"), dict)


@dataclass
class TrackedToolCall:
    status: Any = "pending"
    cancel: bool = False


@dataclass
class TrackedTerminal:
    exited: bool = False
    cancel: bool = False


@dataclass
class PatchTracker:
    """The effective tool-call and terminal state of one session, built by `apply`ing its
    `session_events` in wire order. Patch rules (tool-calls.mdx:102-108,440,587): an omitted field
    is unchanged, `null` resets it to its default (`status` `pending`, no `capabilities`, no
    `exitStatus`), and a concrete value replaces it. Violations are collected, not raised."""

    tool_calls: dict[str, TrackedToolCall] = field(default_factory=dict)
    terminals: dict[str, TrackedTerminal] = field(default_factory=dict)
    status_violations: list[str] = field(default_factory=list)
    """A status back to `pending`, or a change after a final status (tool-calls.mdx:421,423)."""
    cancel_violations: list[str] = field(default_factory=list)
    """`cancel` still advertised by a final tool call or an exited terminal (:440,600)."""
    cancel_seen: bool = False

    def apply(self, kind: str, payload: dict[str, Any]) -> None:
        report = tool_call_report(kind, payload)
        if report is not None:
            self._apply_tool_call(*report)
        elif kind == "update" and payload.get("sessionUpdate") in ("terminal_update", "terminal_output_chunk"):
            terminal_id = payload.get("terminalId")
            if isinstance(terminal_id, str) and terminal_id:
                self._apply_terminal(terminal_id, payload)

    def _apply_tool_call(self, tool_call_id: str, source: str, fields: dict[str, Any]) -> None:
        tool_call = self.tool_calls.setdefault(tool_call_id, TrackedToolCall())
        if "status" in fields:
            old = tool_call.status
            new = "pending" if fields["status"] is None else fields["status"]
            if old in FINAL_TOOL_CALL_STATUSES and new != old:
                self.status_violations.append(
                    f"tool call {tool_call_id!r} changed from final status {old!r} to {new!r} "
                    f"(via {source})"
                )
            elif new == "pending" and old != "pending":
                self.status_violations.append(
                    f"tool call {tool_call_id!r} went back from {old!r} to 'pending' (via {source})"
                )
            tool_call.status = new
        if "capabilities" in fields:
            tool_call.cancel = _advertises_cancel(fields["capabilities"])
            self.cancel_seen = self.cancel_seen or tool_call.cancel
        if tool_call.cancel and tool_call.status in FINAL_TOOL_CALL_STATUSES:
            self.cancel_violations.append(
                f"tool call {tool_call_id!r} still advertises capabilities.cancel with final "
                f"status {tool_call.status!r} (via {source})"
            )

    def _apply_terminal(self, terminal_id: str, update: dict[str, Any]) -> None:
        terminal = self.terminals.setdefault(terminal_id, TrackedTerminal())
        if update.get("sessionUpdate") != "terminal_update":
            return  # an output chunk patches no field
        if "exitStatus" in update:
            terminal.exited = isinstance(update["exitStatus"], dict)
        if "capabilities" in update:
            terminal.cancel = _advertises_cancel(update["capabilities"])
            self.cancel_seen = self.cancel_seen or terminal.cancel
        if terminal.cancel and terminal.exited:
            self.cancel_violations.append(
                f"terminal {terminal_id!r} still advertises capabilities.cancel after reporting "
                f"exitStatus"
            )


SECOND_PROMPT_TEXT = "hi"
"""The text of `prompt_during_active_work`'s second prompt."""


@dataclass(frozen=True)
class ActiveWorkPrompt:
    """The outcome of `prompt_during_active_work`."""

    turn: PromptTurn
    """The first prompt's turn; its `on_action` sent the second prompt."""
    second_id: Any
    second_response: TranscriptEntry | None
    """The second prompt's response, or `None` if none arrived in time."""
    second_response_index: int | None
    outcome: str | None
    """What the agent did with the second prompt while the first prompt's work was active:
    `"inserted"` (a success before `session/cancel`), `"rejected"` (an error before it), or
    `"held"` (still unanswered when `session/cancel` was sent). `None` when not exercised."""
    not_exercised: str | None
    """Why the scenario does not show a prompt sent during active work, else `None`."""

    @property
    def second_error(self) -> dict[str, Any] | None:
        msg = self.second_response.parsed if self.second_response is not None else None
        error = msg.get("error") if isinstance(msg, dict) else None
        return error if isinstance(error, dict) else None


async def prompt_during_active_work(
    agent: AgentProcess, session_id: str, first_text: str, *, timeout: float
) -> ActiveWorkPrompt:
    """Send a second `session/prompt` while the first prompt's foreground work is active, then
    `session/cancel` (prompt-lifecycle.mdx:382-384,1173).

    The first prompt (`first_text`, normally the cancel prompt) runs through `run_prompt`. The
    second (`SECOND_PROMPT_TEXT`) is its `on_action`, sent raw on the first `running`/
    `requires_action`. `session/cancel` follows once the second prompt is answered or
    `quiet_period(timeout)` passes. A second prompt still unanswered when the first turn ends is
    then awaited for up to `timeout` more.

    The agent reads in order, so a second prompt answered before the first turn ended (and
    before the cancel) was answered while that work was active. One still unanswered at the
    cancel is held, provided the first turn ended only after the cancel. Anything else is
    `not_exercised`: the first work may have ended before the agent read the second prompt.
    Raises `AgentTimeout` if the first turn never ends."""
    second_id: Any = None

    async def _send_second() -> Any:
        nonlocal second_id
        second_id = await agent.send_request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": SECOND_PROMPT_TEXT}]},
        )
        return second_id

    turn = await run_prompt(
        agent,
        session_id,
        [{"type": "text", "text": first_text}],
        on_cancel=True,
        on_action=_send_second,
        cancel_after_action=quiet_period(timeout),
        cancel_wait=timeout / 4,
        timeout=timeout,
    )
    response = turn.action_response
    if response is None and second_id is not None:
        try:
            response = await agent.wait_for_response(second_id, timeout=timeout)
        except AgentTimeout:
            response = None
    response_index = agent.transcript.index(response) if response is not None else None

    def _result(outcome: str | None, not_exercised: str | None) -> ActiveWorkPrompt:
        return ActiveWorkPrompt(
            turn=turn,
            second_id=second_id,
            second_response=response,
            second_response_index=response_index,
            outcome=outcome,
            not_exercised=not_exercised,
        )

    if turn.action_sent_at_index is None:
        return _result(None, "the first prompt's turn ended before a second prompt could be sent")
    if not is_active_state(turn.state_at_cancel):
        return _result(
            None,
            f"the session was {turn.state_at_cancel!r}, not running/requires_action, when the "
            "second prompt was sent",
        )
    end_index = turn.idle_index if turn.idle_index is not None else turn.response_index
    cancel_index = turn.cancelled_at_index
    if response_index is not None and response_index < end_index and (
        cancel_index is None or response_index < cancel_index
    ):
        rejected = isinstance(response.parsed, dict) and "error" in response.parsed
        return _result("rejected" if rejected else "inserted", None)
    if cancel_index is None:
        return _result(
            None,
            "the first prompt's work ended on its own before the second prompt was answered",
        )
    if response_index is not None and response_index < cancel_index:
        return _result(None, "the first prompt's work ended before the second prompt was answered")
    if end_index < cancel_index:
        return _result(None, "the first prompt's work ended before session/cancel was sent")
    return _result("held", None)


_USER_MESSAGE_UPDATES = frozenset({"user_message", "user_message_chunk"})


async def assert_prompt_rejected_not_inserted(
    agent: AgentProcess,
    session_id: str,
    blocks: list[dict[str, Any]],
    *,
    what: str,
    timeout: float,
) -> None:
    """Send a prompt the agent must refuse and assert it was answered `-32602` and not inserted
    (prompt-lifecycle.mdx:313,388). Shared by `ACP-PROMPT-211` and `ACP-PROMPTCAP-201`.

    The prompt goes through `run_prompt` on a fresh session, so any `user_message`/
    `user_message_chunk` or `running`/`requires_action` update for that session means it was
    inserted (an accepted prompt also fails the "error" check; both are reported). A
    rejection owes no state transition (:390), so a short `quiet_period` after the response
    catches late updates too. `what` names the probe in the failure message."""
    turn = await run_prompt(agent, session_id, blocks, timeout=timeout)
    entry = turn.response_entry
    skip_if_auth_gated(entry)
    late = await drain_quiet(agent, quiet_period(timeout))
    problems = []
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    if not isinstance(error, dict):
        problems.append("the prompt was accepted instead of answered with an error")
    elif error.get("code") != INVALID_PARAMS:
        problems.append(f"expected error code -32602, got {error.get('code')!r}")
    seen = [e for _, e in turn.updates] + late
    for observed in seen:
        for message in iter_messages(observed):
            params = message.get("params")
            if message.get("method") != "session/update" or not isinstance(params, dict):
                continue
            update = params.get("update")
            if params.get("sessionId") != session_id or not isinstance(update, dict):
                continue
            kind = update.get("sessionUpdate")
            if kind in _USER_MESSAGE_UPDATES:
                problems.append(f"a {kind} update was emitted for it (it was inserted)")
            elif kind == "state_update" and is_active_state(update.get("state")):
                problems.append(f"state {update.get('state')!r} was reported for it (it was inserted)")
    assert not problems, f"{what}: {'; '.join(dict.fromkeys(problems))} ({entry.text!r})"
