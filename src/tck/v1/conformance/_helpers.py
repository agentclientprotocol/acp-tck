"""Shared helpers for conformance tests."""

from __future__ import annotations

import asyncio
import contextlib
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Literal

import pytest

from tck.common.harness import AgentLaunch, AgentProcess, AgentTimeout, Direction, TranscriptEntry
from tck.common.plugin import (
    current_auth_method_id,
    current_initialize_auth_methods,
    record_test_property,
    register_active_process,
    skip_if_login_times_out,
)
from tck.v1.protocol import AUTHENTICATION_REQUIRED, METHOD_NOT_FOUND, PROTOCOL_VERSION
from tck.v1.validation import validate_against_def


@contextlib.asynccontextmanager
async def connected_agent(
    launch: AgentLaunch,
    *,
    handshake: bool = True,
    authenticate: bool = True,
    client_capabilities: dict[str, Any] | None = None,
) -> AsyncIterator[AgentProcess]:
    """Spawn a fresh `AgentProcess` for `launch`, optionally perform an `initialize` handshake,
    yield it, and always close it.

    Registers the process with the plugin's failure-diagnostics tracker (`tck.common.plugin`) so a
    test failure attaches its transcript and stderr to the pytest report, regardless of which
    requirement(s) the test is checking.

    When `handshake` and `authenticate` are true and `--tck-auth-method` was given
    (`current_auth_method_id()`), an `authenticate` call for that method id is sent right after
    `initialize` (or the test SKIPs, see `unusable_auth_method_reason`, if that id is not
    advertised or is a `terminal` method) -- this lets every existing/new test that calls
    `new_session()` afterwards just work against an agent that requires authentication before
    `session/new`, without each test having to know about auth at all. Note: this auto-authenticate step only fires for `handshake=True` callers --
    `test_initialize.py::test_full_exchange_validates_against_schema` deliberately drives its
    own `initialize` with `handshake=False` and is out of scope for auth-gating (it never
    exercises an auth-gated fixture). A caller that must observe the agent unauthenticated
    (`auth/status`, ACP-AUTH-007) passes `authenticate=False` to keep the handshake but skip
    this step.

    A login that never answers (it may be interactive and pending) SKIPs with `AUTH-GATED:`
    rather than failing, see `skip_if_login_times_out`.
    """
    async with AgentProcess(launch) as agent:
        register_active_process(agent)
        if handshake:
            req_id = await agent.send_request(
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "clientCapabilities": client_capabilities
                    if client_capabilities is not None
                    else {},
                },
            )
            init_entry = await agent.wait_for_response(req_id, timeout=launch.startup_timeout)
            method_id = current_auth_method_id() if authenticate else None
            if method_id is not None:
                init_msg = init_entry.parsed if isinstance(init_entry.parsed, dict) else {}
                init_result = init_msg.get("result")
                auth_methods = init_result.get("authMethods") if isinstance(init_result, dict) else None
                reason = unusable_auth_method_reason(auth_methods, method_id)
                if reason is not None:
                    pytest.skip(f"AUTH-GATED: {reason} -- check --tck-auth-method")
                auth_id = await agent.send_request("authenticate", {"methodId": method_id})
                with skip_if_login_times_out("authenticate", method_id, launch.startup_timeout):
                    auth_entry = await agent.wait_for_response(auth_id, timeout=launch.startup_timeout)
                auth_msg = auth_entry.parsed
                # `authenticate` succeeding is never a MANDATORY assertion -- a real agent may
                # legitimately reject bad/expired/cancelled credentials. An error response here
                # means the TCK can't exercise session-dependent tests with this --auth-method,
                # so they SKIP with a clear reason instead of failing on an AssertionError.
                if not (isinstance(auth_msg, dict) and isinstance(auth_msg.get("result"), dict)):
                    detail = (
                        auth_msg.get("error") if isinstance(auth_msg, dict) else None
                    ) or auth_entry.text
                    pytest.skip(
                        f"AUTH-GATED: authenticate with methodId={method_id!r} failed: {detail!r} "
                        "-- check --tck-auth-method"
                    )
        yield agent


def unusable_auth_method_reason(auth_methods: Any, method_id: str) -> str | None:
    """Why `authenticate` must not be called with `method_id` given the agent's advertised
    `authMethods`, or `None` if it may. The id must be one the agent advertised, and clients
    MUST NOT pass a `terminal` method to `authenticate`
    (`docs/protocol/v1/draft/authentication.mdx:153,187-188`)."""
    entries = auth_methods if isinstance(auth_methods, list) else []
    match = next(
        (m for m in entries if isinstance(m, dict) and m.get("id") == method_id), None
    )
    if match is None:
        return f"methodId={method_id!r} is not one of the ids advertised in initialize's authMethods"
    if match.get("type") == "terminal":
        return (
            f"methodId={method_id!r} is a terminal auth method, which a client must not pass "
            "to authenticate"
        )
    return None


def skip_if_auth_gated(entry: TranscriptEntry) -> None:
    """Skip the current test, with a message pointing at `--auth-method`, if `entry` (a
    `session/new` response) is the `AUTHENTICATION_REQUIRED` (`-32000`) error.

    v1 never requires an agent to gate `session/new` behind authentication (it's a MAY, not a
    MUST), so this is not itself a conformance failure; but it does mean the TCK cannot exercise
    session/prompt-dependent requirements against this agent unless the harness operator
    supplies a valid `--auth-method <id>`. The message is prefixed with the literal marker
    string `AUTH-GATED:` so `tck.common.plugin` can detect this specific reason (as opposed to
    an ordinary capability-not-advertised skip) and set `Verdict.blocked_by_auth`.

    Only excuses the `-32000` when the cached `initialize` result actually advertised at least
    one `authMethods` entry -- an agent that advertises none and still returns
    `-32000` has no defined remedy; left as an ordinary, un-excused failure (see
    `ACP-AUTH-005`), not something the TCK can route around.
    """
    msg = entry.parsed
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


async def new_session(agent: AgentProcess, cwd: Path, *, timeout: float | None = None) -> str:
    """Send `session/new` with an absolute `cwd` and no MCP servers; return the `sessionId`
    from the response.

    Raises `AssertionError` with a protocol-level message (not a bare `TypeError`/`KeyError`)
    if the response is not a well-formed success -- callers see a diagnosis, not a Python
    traceback, when the agent errors or replies with a malformed shape.

    SKIPs (via `skip_if_auth_gated`) rather than failing when the agent requires authentication
    and no `--auth-method` was configured."""
    req_id = await agent.send_request("session/new", {"cwd": str(cwd), "mcpServers": []})
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/new did not return a result object: {entry.text!r}"
    )
    session_id = msg["result"].get("sessionId")
    assert isinstance(session_id, str), f"session/new result has no string sessionId: {msg['result']!r}"
    return session_id


def skip_if_version_mismatch(init_result: dict[str, Any]) -> None:
    """Skip with the `VERSION-MISMATCH: ` marker (`tck.common.plugin`'s `_VERSION_MISMATCH_MARKER`
    substring, scanned by `_build_report()` to set `Verdict.blocked_by_version_mismatch`) unless
    `init_result`'s negotiated `protocolVersion` is this suite's own `PROTOCOL_VERSION` (1).

    An agent negotiating a different version isn't thereby "broken" -- `ACP-INIT-001`/`003`
    judge the negotiation outcome itself normally. But tests asserting v1-shape requirements on
    that result (`ACP-INIT-002`/`004`, `ACP-SCHEMA-001`/`002`, `ACP-META-001`, `ACP-PROMPT-001`)
    can't honestly judge a result the agent never claimed was v1-shaped; call this right after
    such a test has its own `init_result` in hand, before evaluating any v1-shape assertion."""
    negotiated = init_result.get("protocolVersion")
    if negotiated != PROTOCOL_VERSION:
        pytest.skip(
            f"VERSION-MISMATCH: negotiated protocolVersion={negotiated!r}, expected "
            f"{PROTOCOL_VERSION!r} -- this agent does not speak v1, so its result cannot be "
            "judged against v1-only shape requirements"
        )


# RFC 3986 scheme (two or more characters, so a Windows drive path `C:\x` is not read as a
# URI); `file:` further needs an RFC 8089 absolute path (`file:///p`, `file://host/p`, `file:/p`,
# `file:c:/p`).
_URI_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]+):")
_FILE_ABSOLUTE_PATH_RE = re.compile(r"^file:(//[^/]*/|/(?!/)|[A-Za-z]:/)", re.IGNORECASE)


def is_absolute_uri(uri: Any) -> bool:
    """Whether `uri` is absolute for ACP-PLAN-001: an RFC 3986 URI with a scheme, and for the
    `file` scheme an RFC 8089 absolute path. The spec leaves "absolute" undefined; this is the
    TCK's reading."""
    if not isinstance(uri, str):
        return False
    match = _URI_SCHEME_RE.match(uri)
    if match is None:
        return False
    if match.group(1).lower() == "file":
        return _FILE_ABSOLUTE_PATH_RE.match(uri) is not None
    return True


def quiet_period(timeout: float) -> float:
    """The heuristic "nothing more is coming" wait used by tests that conclude absence (e.g. "no
    response to a notification"). Derived from `--tck-timeout` rather than a hard-coded
    sub-second constant, so it scales on a slow/loaded machine; clamped so it's never flaky-short
    nor dominates the suite's runtime."""
    return max(0.5, min(2.0, timeout / 10))


HISTORY_KINDS = frozenset(
    {"user_message_chunk", "agent_message_chunk", "agent_thought_chunk", "tool_call", "tool_call_update"}
)
"""`sessionUpdate` kinds that carry conversation content: what `session/load` replays before
its response, what `session/resume` must not replay, and the "content or tool call updates" that
must not follow a cancelled prompt's response. Session-state kinds (`session_info_update`,
`available_commands_update`, `usage_update`, ...) may be sent any time a session exists
(`docs/protocol/v1/draft/prompt-turn.mdx:38`), so they are never judged by ordering rules."""


def session_update_kind(entry: TranscriptEntry, session_id: str | None = None) -> str | None:
    """The `params.update.sessionUpdate` of `entry` if it is a `session/update` notification
    (for `session_id`, when given), else `None`."""
    msg = entry.parsed
    if not (isinstance(msg, dict) and msg.get("method") == "session/update"):
        return None
    params = msg.get("params")
    if not isinstance(params, dict):
        return None
    if session_id is not None and params.get("sessionId") != session_id:
        return None
    update = params.get("update")
    kind = update.get("sessionUpdate") if isinstance(update, dict) else None
    return kind if isinstance(kind, str) else None


def is_response_line(entry: TranscriptEntry) -> bool:
    """True if `entry` is a reply: a JSON-RPC object without `method`, even a malformed one
    missing `id`/`result`/`error`.

    The rule "a notification gets no response" checks use. JSON-RPC 2.0 §4.1 forbids only
    *replies* to a notification. The agent's own notifications and agent -> client requests
    carry `method`, are not replies, and may arrive at any time after `initialize`. A non-JSON
    line is not a reply either; the transport rows judge it."""
    return isinstance(entry.parsed, dict) and "method" not in entry.parsed


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
    """True if `entry` is a message the agent initiated on its own: a JSON-RPC object carrying
    `method` (a notification or an agent -> client request). It may arrive at any time after
    `initialize`, so it is never the reply a check is waiting for."""
    return isinstance(entry.parsed, dict) and "method" in entry.parsed


async def next_reply_line(agent: AgentProcess, timeout: float) -> TranscriptEntry:
    """Return the first line within `timeout` that is not agent-initiated
    (`is_agent_initiated`), for the caller to judge as the reply it waits for. Anything else --
    a response object, but also a non-JSON or otherwise malformed line -- is returned as-is.
    Skipped lines stay in `agent.pending()`, and an agent -> client request among them is left
    unanswered. `AgentTimeout`/`AgentExited` propagate."""
    return await agent.wait_for_message(lambda entry: not is_agent_initiated(entry), timeout=timeout)


def cancel_race_peek(timeout: float) -> float:
    """Like `quiet_period`, but for the much shorter peek `run_prompt` does right after an
    update and before committing to send `session/cancel` (see its docstring) -- this only
    needs to be long enough to catch a response that is already sitting in the pipe, not to
    conclude general absence, so it stays a small fraction of `quiet_period`."""
    return max(0.05, min(0.5, timeout / 50))


PermissionPolicy = Literal["allow", "reject_once", "unknown_option", "cancelled"]
"""How `run_prompt` answers `session/request_permission` (until `session/cancel` is sent):
`allow` (the default) selects `allow_once`, else `allow_always`, else `reject_once`;
`reject_once` selects `reject_once`. When the policy's kinds are not offered it never picks
another option (a `*_always` would persist an approval or a standing deny in the operator's
agent): it sends `session/cancel` and answers `cancelled`. `unknown_option` selects an
`optionId` the agent never offered; `cancelled` answers the `cancelled` outcome without sending
`session/cancel`."""

UNKNOWN_PERMISSION_OPTION_ID = "_tck_unoffered_option"
"""The `optionId` the `unknown_option` policy selects (`_`-prefixed per the extensibility rule)."""


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
    """The outcome of one `session/prompt` turn driven by `run_prompt`."""

    response_entry: TranscriptEntry
    """The transcript entry for the `session/prompt` response."""
    updates: list[tuple[int, TranscriptEntry]] = field(default_factory=list)
    """`(transcript_index, entry)` for every `session/update` notification observed, in the
    order they arrived on the wire -- and therefore strictly before `response_entry`, since
    they were read off the same stdout stream before the matching response line."""
    client_requests_seen: list[TranscriptEntry] = field(default_factory=list)
    """Every agent -> client request the mock client had to answer during the turn:
    `session/request_permission` (answered normally) plus anything else (`fs/*`, `terminal/*`,
    `elicitation/create`, ...), which gets `-32601` since our client advertised
    `clientCapabilities: {}` -- `test_client_capabilities.py` turns "the agent called an
    unadvertised method" into its own negative tests using this list."""
    cancelled_at_index: int | None = None
    """The transcript index at which `run_prompt` sent `session/cancel` (for `on_cancel`, or by
    an unsatisfiable permission policy -- see `permission_cancels`), or `None` if `on_cancel` was false or
    the prompt resolved before a cancel was ever sent (a race the TCK cannot always avoid -- see
    `test_cancel.py`)."""
    action_response: TranscriptEntry | None = None
    """The response to `on_action`'s request, if `on_action` was given and fired (see
    `run_prompt`'s docstring) -- `None` if `on_action` was not given, or was given but the
    prompt resolved before it ever fired."""
    action_sent_at_index: int | None = None
    """The transcript index at which `on_action`'s request was sent, mirroring
    `cancelled_at_index` -- `None` if `on_action` was not given or never fired."""
    permission_fallbacks: list[str] = field(default_factory=list)
    """A note per `session/request_permission` answered with other than the preferred option
    kind (`permission_outcome`); also recorded as the `acp_tck_permission_fallback` property."""
    permission_cancels: list[str] = field(default_factory=list)
    """A note per `session/request_permission` the policy could not satisfy (none of its option
    kinds offered): the mock client sent `session/cancel` and answered `cancelled` instead. Also
    recorded as the `acp_tck_permission_fallback` property."""


def client_cancelled(agent: AgentProcess, session_id: str, since: int) -> bool:
    """Whether the TCK has sent `session/cancel` for `session_id` at or after transcript index
    `since`, whoever sent it (this turn's trigger or a driver on the same connection)."""
    for entry in agent.transcript[since:]:
        message = entry.parsed
        if (
            entry.direction is Direction.SENT
            and isinstance(message, dict)
            and message.get("method") == "session/cancel"
            and isinstance(message.get("params"), dict)
            and message["params"].get("sessionId") == session_id
        ):
            return True
    return False


async def run_prompt(
    agent: AgentProcess,
    session_id: str,
    blocks: list[dict[str, Any]],
    *,
    on_cancel: bool = False,
    on_action: Callable[[], Awaitable[Any]] | None = None,
    cancel_wait: float = 0.5,
    permission: PermissionPolicy = "allow",
    extra_params: dict[str, Any] | None = None,
    timeout: float,
) -> PromptTurn:
    """Drive one `session/prompt` turn, acting as a minimal mock ACP client for whatever the
    agent sends meanwhile, until the prompt's own response arrives.

    While waiting:
    - `session/request_permission` is answered per `permission` (see `PermissionPolicy`;
      options are picked by `kind`, never by position), or `{"outcome": {"outcome":
      "cancelled"}}` once `session/cancel` has been sent for this turn
      (`docs/protocol/v1/draft/prompt-turn.mdx:641`).
    - any other agent -> client request (`fs/*`, `terminal/*`, `elicitation/create`, ...) gets
      `-32601`, since the mock client advertised `clientCapabilities: {}`; the request is also
      recorded on `PromptTurn.client_requests_seen`.
    - `session/update` notifications are recorded in order.

    If `on_cancel` is true, `session/cancel` is sent for `session_id` as soon as either the
    first `session/update` arrives or `cancel_wait` seconds have elapsed, whichever is first --
    an agent that emits nothing before responding is still a valid target for cancellation, it
    is just unlikely the cancel will land while the turn is still in flight (see `test_cancel.py`
    for how the resulting race is handled).

    `on_action`, if given, is a zero-argument async callable fired at that same trigger point
    (instead of, or alongside, `on_cancel`'s `session/cancel`) -- it must send whatever request
    it wants (e.g. `session/close`) and return the id used. Whatever else the agent sends while
    the mock client is waiting for the prompt's own response -- including that action's own
    response, and any agent -> client request the action's send provokes (e.g. resolving an
    in-flight `session/request_permission` as cancelled) -- is still handled by this same
    dispatcher: nothing sent during an in-flight prompt turn is ever silently dropped. The
    action's response comes back as `PromptTurn.action_response`.

    A subtlety: an agent that emits an update and then *immediately* replies may already have
    written its response before we decide to cancel -- we just haven't read it yet. To keep
    `cancelled_at_index` honest, we give a brief (`cancel_race_peek(timeout)`) look for the
    response right after an update and before committing to cancel; if it's already there, we
    return it with `cancelled_at_index=None` (a race), as if it arrived before cancel was ever
    considered.

    `extra_params`, if given, is merged into the `session/prompt` request's own params
    (e.g. `{"_meta": {...}}` for ACP-META-001) -- it never overrides `sessionId`/`prompt`.
    """
    params = {"sessionId": session_id, "prompt": blocks}
    if extra_params:
        params.update(extra_params)
    turn_start = len(agent.transcript)
    prompt_id = await agent.send_request("session/prompt", params)
    updates: list[tuple[int, TranscriptEntry]] = []
    client_requests_seen: list[TranscriptEntry] = []
    permission_fallbacks: list[str] = []
    permission_cancels: list[str] = []
    cancelled_at_index: int | None = None
    action_response: TranscriptEntry | None = None
    action_sent_at_index: int | None = None
    action_id: Any = None
    trigger_armed = on_cancel or on_action is not None
    trigger_sent = False

    loop = asyncio.get_running_loop()
    overall_deadline = loop.time() + timeout
    trigger_deadline = loop.time() + cancel_wait if trigger_armed else None
    peek_timeout = cancel_race_peek(timeout)

    async def _fire_trigger() -> None:
        nonlocal trigger_sent, cancelled_at_index, action_id, action_sent_at_index
        if trigger_sent:
            return
        trigger_sent = True
        if on_cancel and cancelled_at_index is None:
            await agent.send_notification("session/cancel", {"sessionId": session_id})
            cancelled_at_index = len(agent.transcript) - 1
        if on_action is not None:
            action_id = await on_action()
            action_sent_at_index = len(agent.transcript) - 1

    async def _handle_one(entry: TranscriptEntry) -> PromptTurn | None:
        """Dispatch one already-read line. Returns the finished `PromptTurn` if `entry` was the
        prompt's own response, else `None` after doing whatever mock-client bookkeeping it
        implies (recording an update, answering a permission/other request, or recording the
        `on_action` request's own response)."""
        nonlocal action_response, cancelled_at_index
        msg = entry.parsed
        if not isinstance(msg, dict):
            return None
        if entry.matches_id(prompt_id):
            if action_id is not None and action_response is None:
                # The prompt's own response arrived before the `on_action` request's response --
                # a valid ordering (no claim is made about relative order). Give the action's
                # response the same short already-in-the-pipe-or-not look `cancel_race_peek`
                # gives an update, so it isn't lost just because we're about to return.
                try:
                    peek_entry = await agent.read_line(timeout=peek_timeout)
                except AgentTimeout:
                    pass
                else:
                    await _handle_one(peek_entry)
            return PromptTurn(
                entry,
                updates,
                client_requests_seen,
                cancelled_at_index,
                action_response,
                action_sent_at_index,
                permission_fallbacks,
                permission_cancels,
            )
        if action_id is not None and entry.matches_id(action_id):
            action_response = entry
            return None

        index = agent.transcript.index(entry)
        method = msg.get("method")
        if method == "session/update":
            updates.append((index, entry))
            return None

        if method == "session/request_permission" and "id" in msg:
            req_params = msg.get("params")
            if not isinstance(req_params, dict):
                req_params = {}
            options = req_params.get("options") or []
            target = req_params.get("sessionId")
            # A request of another session (a subagent's) is never cancelled through the
            # prompted session: `session/cancel` for it would end this turn.
            for_this_session = not isinstance(target, str) or target == session_id
            if (for_this_session and (trigger_sent or cancelled_at_index is not None)) or (
                isinstance(target, str) and client_cancelled(agent, target, turn_start)
            ):
                # Once `session/cancel` (by this turn or by a driver on the same connection) or
                # the `on_action` request (e.g. `session/close`) has fired for the request's
                # session, a real client resolves an in-flight permission prompt as cancelled
                # rather than picking an option on the user's behalf (`prompt-turn.mdx:641`;
                # Active Subagents RFD, "Pending permission and elicitation requests").
                # Cancelling one session does not resolve another's requests.
                outcome: dict[str, Any] = {"outcome": "cancelled"}
            else:
                outcome, note = _answer_permission(options, permission)
                if note is not None and outcome["outcome"] == "cancelled" and not for_this_session:
                    # No option can be selected; this client sends no `session/cancel` for a
                    # subagent, so only this request is declined.
                    permission_fallbacks.append(f"{note}; answered cancelled for session {target!r}")
                elif note is not None and outcome["outcome"] == "cancelled":
                    # The policy's option kinds were not offered: cancel the turn first, then
                    # answer `cancelled` (`prompt-turn.mdx:641`).
                    await agent.send_notification("session/cancel", {"sessionId": session_id})
                    cancelled_at_index = len(agent.transcript) - 1
                    permission_cancels.append(note)
                elif note is not None:
                    permission_fallbacks.append(note)
            await agent.send_message(
                {"jsonrpc": "2.0", "id": msg["id"], "result": {"outcome": outcome}}
            )
            client_requests_seen.append(entry)
            return None

        if method is not None and "id" in msg:
            # Any other agent -> client request: our mock client advertised no capabilities.
            client_requests_seen.append(entry)
            await agent.send_message(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "error": {"code": METHOD_NOT_FOUND, "message": "Method not found"},
                }
            )
            return None

        # Any other agent-authored notification (e.g. `elicitation/complete`) -- not our concern
        # here, ignore and keep waiting for the prompt's own response.
        return None

    # Lines read while waiting on `initialize`/`session/new` (or, in principle, an earlier
    # `read_line` of the caller's own) sit in `pending()` and would otherwise be invisible to
    # ACP-PROMPT-002 / ACP-CANCEL-002 -- process them exactly like freshly-read lines before
    # ever blocking on the network.
    for pending_entry in agent.pending():
        pending_result = await _handle_one(pending_entry)
        if pending_result is not None:
            return pending_result

    while True:
        now = loop.time()
        remaining = overall_deadline - now
        if remaining <= 0:
            raise AgentTimeout(
                f"session/prompt {prompt_id!r} did not resolve within {timeout}s",
                agent.transcript,
                stderr=agent.stderr_text(),
            )

        if trigger_armed and not trigger_sent:
            wait_remaining = trigger_deadline - now  # type: ignore[operator]
            read_timeout = (
                min(remaining, wait_remaining) if wait_remaining > 0 else min(remaining, 0.05)
            )
        else:
            read_timeout = remaining

        try:
            entry = await agent.read_line(timeout=read_timeout)
        except AgentTimeout:
            if trigger_armed and not trigger_sent:
                await _fire_trigger()
                continue
            raise

        result = await _handle_one(entry)
        if result is not None:
            return result

        if (
            trigger_armed
            and not trigger_sent
            and isinstance(entry.parsed, dict)
            and entry.parsed.get("method") == "session/update"
        ):
            try:
                peek_entry = await agent.read_line(timeout=peek_timeout)
            except AgentTimeout:
                await _fire_trigger()
            else:
                peek_result = await _handle_one(peek_entry)
                if peek_result is not None:
                    return peek_result
                await _fire_trigger()


async def answer_post_turn_requests(agent: AgentProcess, entry: TranscriptEntry, *, since: int) -> None:
    """Answer the agent -> client requests in `entry`, a line read after `run_prompt` returned,
    as `run_prompt` would have: `session/request_permission` per the `allow` policy (`cancelled`
    for a session the TCK sent `session/cancel` for at or after transcript index `since`),
    anything else `-32601` (the mock client advertises no capabilities). A subagent may ask
    after the parent's turn ended, and the agent may wait for the answer."""
    if entry.direction is not Direction.RECEIVED:
        return
    parsed = entry.parsed
    for message in parsed if isinstance(parsed, list) else [parsed]:
        if not isinstance(message, dict) or "method" not in message or "id" not in message:
            continue
        if message["method"] == "session/request_permission":
            params = message.get("params")
            if not isinstance(params, dict):
                params = {}
            target = params.get("sessionId")
            if isinstance(target, str) and client_cancelled(agent, target, since):
                outcome: dict[str, Any] = {"outcome": "cancelled"}
            else:
                outcome, _note = _answer_permission(params.get("options") or [], "allow")
            await agent.send_message(
                {"jsonrpc": "2.0", "id": message["id"], "result": {"outcome": outcome}}
            )
        else:
            await agent.send_message(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {"code": METHOD_NOT_FOUND, "message": "Method not found"},
                }
            )


# --- subagents (`clientCapabilities.subagents`, unstable) ---
#
# Judged over one connection that advertises `subagents` (`test_subagents.py`). v1 has no
# child-addressed `state_update` stream: a child's work state is only the `state` of the parent's
# `subagent_update`.


def _wire_messages_indexed(
    transcript: list[TranscriptEntry],
    client_sessions: set[str],
    replay: tuple[int, int] | None = None,
) -> Iterator[tuple[int, dict[str, Any], str, dict[str, Any], set[str]]]:
    """Walk the agent's requests and notifications in wire order, tracking which sessions are
    known (`SubagentUpdate`): the client's own, plus every child a `subagent_update` sent on an
    already-known session announces. Yields `(index, msg, method, params, known)` per message
    with a `method`, `index` being its transcript position; `known` is the set *before* the
    message, and the message's own announcement is applied once the consumer resumes. Responses
    are skipped.

    `replay` is the `[start, end)` transcript range of a `session/load` exchange. Inside it `known`
    starts over from `client_sessions`: a client loading a session on a fresh connection has not
    seen earlier announcements, so only those made within the exchange count for it (Active
    Subagents RFD, "Child announcements precede child traffic"). Announcements made inside the
    range still count for traffic after it."""
    live = set(client_sessions)
    scoped: set[str] | None = None
    for index, entry in enumerate(transcript):
        msg = entry.parsed
        if entry.direction is not Direction.RECEIVED or not isinstance(msg, dict):
            continue
        method = msg.get("method")
        if not isinstance(method, str):
            continue
        if replay is not None and replay[0] <= index < replay[1]:
            if scoped is None:
                scoped = set(client_sessions)
            known = scoped
        else:
            known = live
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        yield index, msg, method, params, known
        update = params.get("update") if method == "session/update" else None
        if (
            isinstance(update, dict)
            and update.get("sessionUpdate") == "subagent_update"
            and isinstance(update.get("sessionId"), str)
            and isinstance(params.get("sessionId"), str)
        ):
            # Inside a replay the scoped set is stricter than `live`; each grows on its own.
            for tracked in (known, live):
                if params["sessionId"] in tracked:
                    tracked.add(update["sessionId"])


def _wire_messages(
    transcript: list[TranscriptEntry], client_sessions: set[str]
) -> Iterator[tuple[dict[str, Any], str, dict[str, Any], set[str]]]:
    """`_wire_messages_indexed` over the whole connection, without positions or a replay scope."""
    for _index, msg, method, params, known in _wire_messages_indexed(transcript, client_sessions):
        yield msg, method, params, known


def _in_replay(replay: tuple[int, int] | None, index: int) -> bool:
    return replay is not None and replay[0] <= index < replay[1]


def child_session_traffic(
    transcript: list[TranscriptEntry],
    client_sessions: set[str],
    replay: tuple[int, int] | None = None,
) -> tuple[set[str], list[str]]:
    """Replay the agent's traffic in wire order and judge the announcement rule (`SubagentUpdate`):
    a child's announcing `subagent_update`, sent on a known session, precedes every request or
    notification bearing the child's session ID.

    `client_sessions` are the sessions the client created; they start out known. `replay` is the
    transcript range of a `session/load` exchange (`_wire_messages_indexed`). Traffic inside it is
    judged against the announcements made inside it, even if an earlier turn announced the child
    (Active Subagents RFD: replayed child updates keep "child announcements precede child
    traffic"). A `session_message`'s `senderSessionId`/`recipientSessionId` inside it are
    historical addresses, not announcements, and are neither judged nor counted as children (a
    recorded directed message may be replayed with its participants when the other participant's
    association is unavailable).

    Returns `(children, problems)`: every session ID the client did not create that the rule
    judged (announced or not) and one message per violation. A session ID counts as carried when
    it is the `params.sessionId` of any agent message with a `method` (a `session/update`
    notification, a `session/request_permission`, `fs/*`, `terminal/*` or `elicitation/create`
    request, ...) or a live `session_message` update's `senderSessionId`/`recipientSessionId`. A
    `subagent_update` announces its own `sessionId` only when it is itself sent on a known
    session. A `session` tool-call content reference is not traffic carrying the child's ID
    (`session_content_references` judges it). Responses are not judged."""
    children: set[str] = set()
    problems: list[str] = []

    def carry(session_id: Any, what: str, known: set[str], replaying: bool) -> None:
        if not isinstance(session_id, str):
            return
        if session_id not in client_sessions:
            children.add(session_id)
        if session_id not in known:
            problems.append(
                f"{what} carries session ID {session_id!r}, which no earlier `subagent_update` "
                f"on a known session announced"
                + (" within this `session/load` replay (Active RFD)" if replaying else "")
                + f" (known: {sorted(known)!r})"
            )

    for index, msg, method, params, known in _wire_messages_indexed(
        transcript, client_sessions, replay
    ):
        replaying = _in_replay(replay, index)
        update = params.get("update") if method == "session/update" else None
        update = update if isinstance(update, dict) else {}
        kind = update.get("sessionUpdate")
        what = f"{method} {kind}" if kind else method
        if "id" in msg:
            what = f"request {what} (id {msg['id']!r})"

        carry(params.get("sessionId"), what, known, replaying)
        if kind == "subagent_update":
            if isinstance(update.get("sessionId"), str) and update["sessionId"] not in client_sessions:
                children.add(update["sessionId"])
        elif kind == "session_message" and not replaying:
            carry(update.get("senderSessionId"), f"{what} senderSessionId", known, replaying)
            carry(update.get("recipientSessionId"), f"{what} recipientSessionId", known, replaying)
    return children, problems


def session_content_references(
    transcript: list[TranscriptEntry],
    client_sessions: set[str],
    replay: tuple[int, int] | None = None,
) -> tuple[list[str], list[str]]:
    """Replay the agent's traffic in wire order and judge the `session` content rule
    (`docs/protocol/v1/draft/tool-calls.mdx` "Sessions (unstable)"): a `session` `ToolCallContent`
    item names a session already known, through ordinary session setup (`client_sessions`) or a
    `subagent_update` announcement on a known session.

    A reference inside `replay`, the transcript range of a `session/load` exchange, is a
    historical address: a replayed reference to a session that is not available follows the
    historical replay rules (Active Subagents RFD), so it is neither judged nor counted.

    Returns `(references, problems)`: the `sessionId` of every `session` item judged, in wire
    order, and one message per reference to a session not yet known. Items are read from a
    `tool_call` / `tool_call_update` `content` array and a `session/request_permission`
    request's `toolCall.content` array."""
    references: list[str] = []
    problems: list[str] = []
    for index, _msg, method, params, known in _wire_messages_indexed(
        transcript, client_sessions, replay
    ):
        if _in_replay(replay, index):
            continue
        update = params.get("update") if method == "session/update" else None
        update = update if isinstance(update, dict) else {}
        kind = update.get("sessionUpdate")
        container: Any = None
        where = ""
        if method == "session/request_permission":
            container, where = params.get("toolCall"), "session/request_permission toolCall"
        elif kind in ("tool_call", "tool_call_update"):
            container, where = update, f"session/update {kind}"
        items = container.get("content") if isinstance(container, dict) else None
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict) or item.get("type") != "session":
                continue
            target = item.get("sessionId")
            if not isinstance(target, str):
                continue
            references.append(target)
            if target not in known:
                problems.append(
                    f"{where} content references session {target!r}, which is neither a session "
                    f"the client created nor announced by an earlier `subagent_update` on a known "
                    f"session (known: {sorted(known)!r})"
                )
    return references, problems


_SUBAGENT_SHAPE_KINDS = {"subagent_update", "session_message", "session_message_chunk"}


def subagent_shape_issues(transcript: list[TranscriptEntry]) -> tuple[int, list[str]]:
    """Validate the subagent-specific parts of what the agent sent against the v1 schema: the
    `update` of a `session/update` of kind `subagent_update`, `session_message` or
    `session_message_chunk` (`SessionUpdate`, so a malformed `subagent_update.state`
    (`StateUpdate`) is among the issues), and each `session` item in the `content` of a
    `tool_call`/`tool_call_update` update or a `session/request_permission` request's `toolCall`
    (`ToolCallContent`). Nothing else of the carrying message is validated: a defect in the rest
    of a tool call, a permission request or the notification envelope belongs to the schema rows
    that judge those messages (`ACP-PROMPT-002`, `ACP-SCHEMA-001`).

    Returns `(judged, problems)`: how many such updates and `session` items were seen and one
    message per issue."""
    judged = 0
    problems: list[str] = []
    for entry in transcript:
        msg = entry.parsed
        if entry.direction is not Direction.RECEIVED or not isinstance(msg, dict):
            continue
        method = msg.get("method")
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        outer = params.get("sessionId")
        update = params.get("update") if method == "session/update" else None
        update = update if isinstance(update, dict) else {}
        kind = update.get("sessionUpdate")
        if kind in _SUBAGENT_SHAPE_KINDS:
            judged += 1
            for issue in validate_against_def("SessionUpdate", update):
                problems.append(
                    f"session/update {kind} (params.sessionId {outer!r}) is invalid at "
                    f"{issue.path or '/'}: {issue.message}"
                )
            continue
        if method == "session/request_permission":
            container, where = params.get("toolCall"), "session/request_permission toolCall"
        elif kind in ("tool_call", "tool_call_update"):
            container, where = update, f"session/update {kind}"
        else:
            continue
        content = container.get("content") if isinstance(container, dict) else None
        for position, item in enumerate(content if isinstance(content, list) else []):
            if not isinstance(item, dict) or item.get("type") != "session":
                continue
            judged += 1
            for issue in validate_against_def("ToolCallContent", item):
                problems.append(
                    f"{where} content[{position}] (a `session` item, params.sessionId "
                    f"{outer!r}) is invalid at {issue.path or '/'}: {issue.message}"
                )
    return judged, problems


def is_absolute_path(value: Any) -> bool:
    """True if `value` is a string that is an absolute path in the native syntax of the machine
    the agent runs on (`AbsolutePath`): POSIX `/...`, a Windows drive path or a UNC path. It is not
    a URI, and a rooted-but-driveless Windows path (`\\dir`) or `C:dir` is not absolute."""
    return isinstance(value, str) and (
        PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()
    )


@dataclass
class SubagentUpdates:
    """What `subagent_updates` found: the `updates` seen (`sessionId` of the child and the outer
    session each was sent on, in wire order) and, per rule, the violations."""

    updates: list[tuple[str, str]] = field(default_factory=list)
    self_parented: list[str] = field(default_factory=list)
    client_sessions_announced: list[str] = field(default_factory=list)
    reparented: list[str] = field(default_factory=list)
    relative_paths: list[str] = field(default_factory=list)
    reported_directories: bool = False


def subagent_updates(
    transcript: list[TranscriptEntry], client_sessions: set[str]
) -> SubagentUpdates:
    """Replay the agent's traffic in wire order and judge the `subagent_update` association
    rules (`SubagentUpdate`): the outer `sessionId` is the immediate parent of `update.sessionId`.

    The three association rules are disjoint by construction, so one defect FAILs one row. A
    child equal to its own parent is `self_parented`, whatever session that is. Otherwise a child
    that is a session the client created is `client_sessions_announced`. Otherwise, on a known
    parent, a child already announced under another parent is `reparented` (a cycle is a
    reparenting whose new parent descends from the child). Reparenting is judged only for an update
    sent on a known session; one sent on an unknown session is `child_session_traffic`'s to judge.
    Every update's `cwd` and `additionalDirectories` entries are checked for `relative_paths`
    regardless, but only well-typed (string) values: a malformed one is a schema defect
    (`subagent_shape_issues`), and `reported_directories` counts only the strings judged."""
    result = SubagentUpdates()
    parents: dict[str, str] = {}
    for _msg, method, params, known in _wire_messages(transcript, client_sessions):
        update = params.get("update") if method == "session/update" else None
        if not isinstance(update, dict) or update.get("sessionUpdate") != "subagent_update":
            continue
        outer, child = params.get("sessionId"), update.get("sessionId")
        if not isinstance(outer, str) or not isinstance(child, str):
            continue
        result.updates.append((child, outer))
        if child == outer:
            result.self_parented.append(
                f"subagent_update on session {outer!r} announces that same session as its own child; "
                f"the association cannot refer to itself (Active RFD)"
            )
        elif child in client_sessions:
            result.client_sessions_announced.append(
                f"subagent_update on session {outer!r} announces session {child!r}, which the "
                f"client created, as a child; a child's ID is unique to its session (Active RFD)"
            )
        elif outer in known:
            old = parents.setdefault(child, outer)
            if old != outer:
                ancestor, cycle = outer, False
                while ancestor in parents and not cycle:  # parents is acyclic by construction
                    ancestor = parents[ancestor]
                    cycle = ancestor == child
                result.reparented.append(
                    f"subagent_update on session {outer!r} announces {child!r}, already a child "
                    f"of {old!r}"
                    + (" (the new parent descends from it: a cycle)" if cycle else "")
                    + "; a child keeps one immediate parent (Active RFD)"
                )
        for field_name in ("cwd", "additionalDirectories"):
            value = update.get(field_name)
            # A value of the wrong type (a non-string `cwd`, a non-list `additionalDirectories`,
            # a non-string entry) is a schema defect: not judged here.
            if field_name == "additionalDirectories":
                items = value if isinstance(value, list) else []
            else:
                items = [value]
            for item in items:
                if not isinstance(item, str):
                    continue
                result.reported_directories = True
                if not is_absolute_path(item):
                    result.relative_paths.append(
                        f"subagent_update for {child!r} reports {field_name} {item!r}, "
                        f"which is not an absolute path"
                    )
    return result


@dataclass
class SessionMessages:
    """What `session_messages` found: how many `session_message` upserts were seen, how many
    messages had both participants known (`participants_judged`, what `ACP-SUBAGENT-007`/`-008`
    judge), how many view links had both sides carrying a reference (`links_judged`,
    `ACP-SUBAGENT-009`) and, per rule, the violations."""

    count: int = 0
    participants_judged: int = 0
    links_judged: int = 0
    same_participants: list[str] = field(default_factory=list)
    foreign_outer: list[str] = field(default_factory=list)
    unlinked_views: list[str] = field(default_factory=list)


def _patched(stored: str | None, update: dict[str, Any], key: str) -> str | None:
    """The stored value of a nullable string patch field: omitted leaves it, `null` clears it, a
    string replaces it. Anything else is malformed (a schema defect) and counts as unknown."""
    if key not in update:
        return stored
    value = update[key]
    return value if isinstance(value, str) else None


def session_messages(
    transcript: list[TranscriptEntry], client_sessions: set[str]
) -> SessionMessages:
    """Replay the agent's `session_message` upserts in wire order and judge the participant and
    link consistency rules (Active Subagents RFD, "Session-directed messages"). A message is the
    transcript entry `(params.sessionId, messageId)`, and its participants and references follow
    the patch convention across upserts (omitted keeps, `null` clears, a value replaces).

    The participant rules are judged once both participant IDs are stored and are disjoint by
    construction: equal participants are `same_participants`, whatever the outer session is;
    different ones whose outer session is neither are `foreign_outer`. The link rule is judged on
    the final stored state: a view's `recipientMessageId` names a view in the recipient's
    transcript and its `senderMessageId` one in the sender's, and when that view was reported and
    references back, the two must name each other, else `unlinked_views` (also when the referenced
    view's own sender or recipient is a third session). A referenced view that was not reported,
    or has no reference of its own, is not judged. `session_message_chunk`
    carries no identity."""
    result = SessionMessages()
    views: dict[tuple[str, str], dict[str, str | None]] = {}
    seen: set[tuple[str, str, str]] = set()
    with_participants: set[tuple[str, str]] = set()
    for _msg, method, params, _known in _wire_messages(transcript, client_sessions):
        update = params.get("update") if method == "session/update" else None
        if not isinstance(update, dict) or update.get("sessionUpdate") != "session_message":
            continue
        outer, message_id = params.get("sessionId"), update.get("messageId")
        if not isinstance(outer, str) or not isinstance(message_id, str):
            continue
        result.count += 1
        view = views.setdefault(
            (outer, message_id),
            {"sender": None, "recipient": None, "sender_msg": None, "recipient_msg": None},
        )
        for name, key in (
            ("sender", "senderSessionId"),
            ("recipient", "recipientSessionId"),
            ("sender_msg", "senderMessageId"),
            ("recipient_msg", "recipientMessageId"),
        ):
            view[name] = _patched(view[name], update, key)
        sender, recipient = view["sender"], view["recipient"]
        if sender is None or recipient is None:
            continue
        with_participants.add((outer, message_id))
        if sender == recipient:
            if ("same", outer, message_id) not in seen:
                seen.add(("same", outer, message_id))
                result.same_participants.append(
                    f"session_message {message_id!r} on session {outer!r} has {sender!r} as both "
                    f"senderSessionId and recipientSessionId; they must identify different "
                    f"sessions (Active RFD)"
                )
        elif outer not in (sender, recipient) and ("foreign", outer, message_id) not in seen:
            seen.add(("foreign", outer, message_id))
            result.foreign_outer.append(
                f"session_message {message_id!r} is sent on session {outer!r}, which is neither "
                f"its sender {sender!r} nor its recipient {recipient!r}; the outer sessionId "
                f"must be one of them (Active RFD)"
            )

    result.participants_judged = len(with_participants)
    for (outer, message_id), view in views.items():
        # (this view's session / message reference, the other view's reference back)
        for session_key, ref_key, back_ref, back_name in (
            ("recipient", "recipient_msg", "sender_msg", "senderMessageId"),
            ("sender", "sender_msg", "recipient_msg", "recipientMessageId"),
        ):
            target_session, target_id = view[session_key], view[ref_key]
            if target_session is None or target_id is None or target_session == outer:
                continue
            other = views.get((target_session, target_id))
            if other is None or other[back_ref] is None:
                continue
            result.links_judged += 1
            if other[back_ref] == message_id:
                continue
            result.unlinked_views.append(
                f"session_message {message_id!r} on session {outer!r} names {target_id!r} on "
                f"session {target_session!r} as its other view, but that view's {back_name} "
                f"is {other[back_ref]!r}; the two views must name each other (Active RFD)"
            )
    return result


_CHILD_OUTPUT_KINDS = {"agent_message_chunk", "agent_thought_chunk"}


@dataclass
class ChildTasks:
    """What `child_task_reports` found: how many announced children began agent output
    (`started`), how many of those were not told the task as a user message (`judged`, what
    `ACP-SUBAGENT-012` judges) and, per rule, the violations."""

    started: int = 0
    judged: int = 0
    user_message_tasks: list[str] = field(default_factory=list)
    unreported: list[str] = field(default_factory=list)


def child_task_reports(transcript: list[TranscriptEntry], client_sessions: set[str]) -> ChildTasks:
    """Replay the agent's traffic in wire order and judge how each announced child is told its
    task (`docs/protocol/v1/draft/prompt-turn.mdx` "Session-directed messages (unstable)"; Active
    Subagents RFD, "Delegated tasks"). The task starts the child's work, so only what the child's
    transcript holds before its first agent output (`agent_message_chunk` or
    `agent_thought_chunk`) is judged.

    The two rules are disjoint by construction. A `user_message_chunk` there is
    `user_message_tasks`. Otherwise a child whose first output was not preceded by an incoming
    `session_message` (outer `sessionId` the child, `senderSessionId` its immediate parent, the
    parent being the session that first announced it; the sender is stored across upserts of the
    `messageId`) is `unreported`. A child that never produces output is not judged, and a child
    already in `user_message_tasks` is left out of `judged`."""
    result = ChildTasks()
    parents: dict[str, str] = {}
    senders: dict[tuple[str, str], str | None] = {}
    tasked: set[str] = set()  # children told the task, either way
    started: set[str] = set()
    user_message_children: set[str] = set()  # `ACP-SUBAGENT-011`'s, not judged by 012
    for _msg, method, params, known in _wire_messages(transcript, client_sessions):
        update = params.get("update") if method == "session/update" else None
        outer = params.get("sessionId")
        if not isinstance(update, dict) or not isinstance(outer, str):
            continue
        kind = update.get("sessionUpdate")
        if kind == "subagent_update":
            child = update.get("sessionId")
            if (
                isinstance(child, str)
                and outer in known
                and child != outer
                and child not in client_sessions
            ):
                parents.setdefault(child, outer)
            continue
        if outer not in parents or outer in started:
            continue
        if kind == "user_message_chunk":
            tasked.add(outer)
            user_message_children.add(outer)
            result.user_message_tasks.append(
                f"child {outer!r} has a {kind} before its first agent output; the task a parent "
                f"gives a child is a `session_message`, not the user's"
            )
        elif kind == "session_message" and isinstance(update.get("messageId"), str):
            key = (outer, update["messageId"])
            senders[key] = _patched(senders.get(key), update, "senderSessionId")
            if senders[key] == parents[outer]:
                tasked.add(outer)
        elif kind in _CHILD_OUTPUT_KINDS:
            started.add(outer)
            result.started += 1
            if outer not in user_message_children:
                result.judged += 1
            if outer not in tasked:
                result.unreported.append(
                    f"child {outer!r} produced agent output before an incoming `session_message` "
                    f"from its parent {parents[outer]!r}"
                )
    return result


@dataclass
class SessionMessageStreams:
    """What `session_message_streams` found: how many session-directed messages were streamed (got
    a `session_message_chunk`) and the ones whose participants came only after the first chunk."""

    streamed: int = 0
    late_participants: list[str] = field(default_factory=list)


def session_message_streams(
    transcript: list[TranscriptEntry], client_sessions: set[str]
) -> SessionMessageStreams:
    """Replay the agent's `session_message` / `session_message_chunk` updates in wire order and
    judge the participant-ordering rule (`docs/protocol/v1/draft/prompt-turn.mdx`
    "Session-directed messages (unstable)"): participant IDs go on the first `session_message`
    when available, before the first chunk of a streamed message.

    A message is `(params.sessionId, messageId)`. Whether the participants were available
    cannot be seen, so a message is flagged only when it is streamed, none of its participant IDs
    was stored when its first chunk arrived (no upsert yet, or one without them) and some upsert
    for it supplies one later, evidence that the agent knew them. A message that never names a
    participant, or has one stored at its first chunk, is not flagged. Participant IDs follow the
    patch convention across upserts (omitted keeps, `null` clears)."""
    result = SessionMessageStreams()
    stored: dict[tuple[str, str], tuple[str | None, str | None]] = {}
    at_first_chunk: dict[tuple[str, str], bool] = {}
    later: set[tuple[str, str]] = set()
    for _msg, method, params, _known in _wire_messages(transcript, client_sessions):
        update = params.get("update") if method == "session/update" else None
        outer = params.get("sessionId")
        if not isinstance(update, dict) or not isinstance(outer, str):
            continue
        kind = update.get("sessionUpdate")
        message_id = update.get("messageId")
        if kind not in ("session_message", "session_message_chunk") or not isinstance(message_id, str):
            continue
        key = (outer, message_id)
        if kind == "session_message_chunk":
            if key not in at_first_chunk:
                at_first_chunk[key] = any(value is not None for value in stored.get(key, (None, None)))
            continue
        sender, recipient = stored.get(key, (None, None))
        sender = _patched(sender, update, "senderSessionId")
        recipient = _patched(recipient, update, "recipientSessionId")
        stored[key] = (sender, recipient)
        if key in at_first_chunk and not at_first_chunk[key] and (sender or recipient):
            later.add(key)
    for key, had_participants in at_first_chunk.items():
        result.streamed += 1
        if not had_participants and key in later:
            result.late_participants.append(
                f"session_message {key[1]!r} on session {key[0]!r} was streamed with "
                f"`session_message_chunk` before any `session_message` upsert named its participants; "
                f"participant IDs go on the first message when available (Active RFD)"
            )
    return result


@dataclass
class ChildConfigSelects:
    """What `child_config_selects` found: how many select options a child reported and the ones
    that offer a value other than the current one."""

    selects: int = 0
    with_choices: list[str] = field(default_factory=list)


def child_config_selects(
    transcript: list[TranscriptEntry], client_sessions: set[str]
) -> ChildConfigSelects:
    """Replay the agent's traffic in wire order and judge the child configuration rule (Active
    Subagents RFD, "Child configuration"): a select option in a `config_option_update` for an
    announced child offers only its current value, because no Client-initiated configuration
    change is permitted on a child. Values are counted across option groups. Updates for a
    session the client created, or for a child not yet announced (`child_session_traffic`'s), are
    not judged, and neither are boolean options."""
    result = ChildConfigSelects()
    for _msg, method, params, known in _wire_messages(transcript, client_sessions):
        update = params.get("update") if method == "session/update" else None
        outer = params.get("sessionId")
        if (
            not isinstance(update, dict)
            or update.get("sessionUpdate") != "config_option_update"
            or outer not in known
            or outer in client_sessions
            or not isinstance(update.get("configOptions"), list)
        ):
            continue
        for option in update["configOptions"]:
            if not isinstance(option, dict) or option.get("type") != "select":
                continue
            entries = option.get("options")
            if not isinstance(entries, list) or not entries:
                continue
            values = []
            for entry in entries:
                nested = entry.get("options") if isinstance(entry, dict) else None
                values.extend(nested if isinstance(nested, list) else [entry])
            values = [item.get("value") for item in values if isinstance(item, dict)]
            result.selects += 1
            extra = [value for value in values if value != option.get("currentValue")]
            if extra:
                result.with_choices.append(
                    f"config_option_update for child {outer!r}: select {option.get('id')!r} "
                    f"has current value {option.get('currentValue')!r} but also offers {extra!r}; "
                    f"a child permits no Client-initiated configuration change (Active RFD)"
                )
    return result
