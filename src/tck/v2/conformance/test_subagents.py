"""Subagent announcement ordering, `session` content references, association integrity and
the SHOULDs around them (ACP-SUBAGENT-001..014, -018, -019, -201, -205..207 and ACP-LIST-004).

There is no `initialize` marker for subagents in v2 -- support is baseline and *inferred* from the
agent's traffic, so `Requirement.capability` is the documentation-only `"inferred:subagents"`
string, those tests carry no `@pytest.mark.capability(...)` marker and SKIP themselves when the
agent shows no use of the feature (001: no child session appears; 002: no `session` tool-call
content item appears). Same encoding as `test_slash_commands.py`, hence the same `v2_only_agent`
connection. 019 and `ACP-LIST-004` are gated on the baseline `capabilities.session` marker and SKIP
when no child appears.

The connection is one `session/new`, one prompt turn (`--subagent-prompt`, else `hi`) and a quiet period after it (child traffic
may trail the turn), judged in wire order over everything the agent sent. `session/resume`
replay is not part of it: `ACP-RESUME-209` judges that window, so one defect never FAILs both.
All tests judge the same connection, made once per run (`_connection_transcript`), so an agent
whose turns vary is judged on one turn by every row. A `session` content reference is not child traffic, so
an unknown reference FAILs only 002. 003..005 (self-parent, a client session announced as a child,
a reparented child) are disjoint by construction in `subagent_updates`, as is 006 (absolute
`cwd`/`additionalDirectories`), so one defect FAILs one row; each SKIPs when no `subagent_update`
appears (006: none carries a well-typed directory string; a malformed one is `ACP-PROMPT-002`'s).
007..009 judge `session_message` participants and view links and are disjoint by construction in
`session_messages` (007 equal participants, 008 an outer session that is neither, 009 conflicting
view references). Each SKIPs when it judged nothing: 007/008 when no message has both
participants known, 009 when no two linked views both carry a reference. 011..014 and 201 are
ADVISORY (SHOULDs: the delegated task as an incoming `session_message` rather than a user message,
participants before the first chunk, a child's select restricted to its current value, and v2's
mirroring of a child's state on its parent). An ADVISORY row has no `capability`, so each SKIPs itself
when the agent shows nothing to judge; 011/012 are disjoint by construction in `child_task_reports`
(012 judges only children not told the task as a user message). 205 judges the order of the two
copies of a child's state transition; it pairs the copies only while the two paths agree and stops
at the first difference, so a missing, extra or reordered mirror is 201's and a late one 205's alone.
206 judges the legality of a child's idle `stopReason` (own `state_update` or mirror) and 207 (ADVISORY) that the
idle ending a child's work carries one; the prompted session's own turn-ending idle is `ACP-STATE-203`/`204`'s.

018/019 and `ACP-LIST-004` judge the connection's last, probe phase (`_probe_children`): the
`session/list` and the mutating requests naming an announced child, sent after the transcript the
other rows judge was read. The probes deliberately break a Client MUST NOT (the restricted-methods
allowlist), because the docs define the Agent's answer. 018 judges only an error's code and 019
only a success, so one defect FAILs one row; each SKIPs when no child was announced (018: or no
probe came back as an error). The probe phase also sends one more `session/new`, whose
`sessionId` 004 judges against the announced children.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, TranscriptEntry
from tck.common.plugin import capability_is_supported, register_active_process

from ._helpers import (
    announced_children,
    child_config_selects,
    child_session_traffic,
    child_state_mirrors,
    child_state_order,
    child_stop_reasons,
    child_task_reports,
    drain_quiet,
    new_session,
    quiet_period,
    run_prompt,
    session_content_references,
    session_message_streams,
    session_messages,
    subagent_updates,
    v2_only_agent,
)

_DEFAULT_PROMPT_TEXT = "hi"

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `agent`, `transcript`, `session_id` and `probes`
once it completed, or `error` (the exception it ended with) so every row sees the same outcome."""

_MAX_CHILDREN_PROBED = 2
"""How many announced children (first announced first) receive the mutating probes."""
_MAX_LIST_PAGES = 10
"""How many `session/list` pages are followed through `nextCursor`."""


@dataclass(frozen=True)
class ChildProbe:
    """One mutating request naming an announced child, and the reply: the JSON-RPC response
    object, or `None` when none arrived (the agent exited or did not answer in time)."""

    method: str
    child: str
    response: dict[str, Any] | None

    @property
    def error_code(self) -> Any:
        error = self.response.get("error") if self.response else None
        return error.get("code") if isinstance(error, dict) else None

    @property
    def errored(self) -> bool:
        return bool(self.response) and isinstance(self.response.get("error"), dict)

    @property
    def succeeded(self) -> bool:
        return bool(self.response) and "result" in self.response and "error" not in self.response


@dataclass(frozen=True)
class ChildProbes:
    """What the probe phase learned. `children` is every announced child; `probes` the requests
    sent for the first few of them; `listed` the session IDs `session/list` returned over the
    pages followed, `None` when it was not sent or its first page was not a list result;
    `new_session` the `sessionId` of the later `session/new`, `None` when it did not return one."""

    children: tuple[str, ...] = ()
    probes: tuple[ChildProbe, ...] = ()
    listed: frozenset[str] | None = None
    new_session: str | None = None


async def _ask(agent, method: str, params: dict[str, Any], timeout: float) -> dict[str, Any] | None:
    """Send a request and return the response object, or `None` when the agent exited, did not
    answer within `timeout` or sent a non-object reply."""
    try:
        request_id = await agent.send_request(method, params)
        entry = await agent.wait_for_response(request_id, timeout=timeout)
    except (AgentTimeout, AgentExited):
        return None
    return entry.parsed if isinstance(entry.parsed, dict) else None


async def _probe_children(
    agent, init_result, tmp_path, timeout: float, transcript: list[TranscriptEntry], session_id: str
) -> ChildProbes:
    """The probe phase described in the module docstring, over the children `transcript`
    announced, in this order: `session/list`, one `session/new`, then for each of the first two
    children `session/resume`, `session/delete` (when `capabilities.session.delete` is
    advertised) and, last, `session/close`. It stops asking once the agent stops answering."""
    children = announced_children(transcript, {session_id})
    if not children:
        return ChildProbes()

    listed: set[str] | None = None
    answering = True
    cursor = None
    seen_cursors: set[str] = set()
    for _page in range(_MAX_LIST_PAGES):
        reply = await _ask(agent, "session/list", {} if cursor is None else {"cursor": cursor}, timeout)
        answering = reply is not None
        result = reply.get("result") if reply else None
        sessions = result.get("sessions") if isinstance(result, dict) else None
        if not isinstance(sessions, list):
            break
        listed = (listed or set()) | {
            item["sessionId"]
            for item in sessions
            if isinstance(item, dict) and isinstance(item.get("sessionId"), str)
        }
        cursor = result.get("nextCursor")
        if not isinstance(cursor, str) or cursor in seen_cursors:
            break
        seen_cursors.add(cursor)

    new_session = None
    if answering:
        reply = await _ask(agent, "session/new", {"cwd": str(tmp_path)}, timeout)
        answering = reply is not None
        created = reply.get("result") if reply else None
        created_id = created.get("sessionId") if isinstance(created, dict) else None
        new_session = created_id if isinstance(created_id, str) else None

    methods: list[tuple[str, dict[str, Any]]] = [("session/resume", {"cwd": str(tmp_path)})]
    if capability_is_supported(init_result, "capabilities.session.delete"):
        methods.append(("session/delete", {}))
    methods.append(("session/close", {}))
    probes: list[ChildProbe] = []
    for method, extra in methods:
        for child in children[:_MAX_CHILDREN_PROBED]:
            if not answering:
                break
            response = await _ask(agent, method, {"sessionId": child, **extra}, timeout)
            probes.append(ChildProbe(method, child, response))
            answering = response is not None
    return ChildProbes(
        tuple(children), tuple(probes), None if listed is None else frozenset(listed), new_session
    )


async def _connection_transcript(
    request: pytest.FixtureRequest, agent_launch, tmp_path
) -> tuple[list[TranscriptEntry], str]:
    """`(transcript, session_id)` of one `session/new`, one prompt turn and a quiet period.

    Made by the first test that asks and reused by the rest, so a model-driven agent runs one
    turn and every row judges that same traffic. A probe phase (`_probe_children`) follows, after
    the transcript was read. A SKIP or error that ended the connection is re-raised for each row.
    Each test registers the agent process, so a FAIL attaches its transcript."""
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    prompt_text = request.config.getoption("tck_subagent_prompt") or _DEFAULT_PROMPT_TEXT
    if "error" in cache:
        raise cache["error"]
    if "agent" in cache:
        register_active_process(cache["agent"])
        return list(cache["transcript"]), cache["session_id"]
    try:
        async with v2_only_agent(agent_launch, require_session=True, yield_result=True) as (agent, init_result):
            timeout = agent_launch.default_timeout
            session_id = await new_session(agent, tmp_path, timeout=timeout)
            await run_prompt(agent, session_id, [{"type": "text", "text": prompt_text}], timeout=timeout)
            await drain_quiet(agent, quiet_period(timeout))
            transcript = list(agent.transcript)
            probes = await _probe_children(agent, init_result, tmp_path, timeout, transcript, session_id)
            cache.update(agent=agent, transcript=transcript, session_id=session_id, probes=probes)
    except BaseException as exc:
        cache["error"] = exc
        raise
    return list(cache["transcript"]), cache["session_id"]


async def _connection_probes(request: pytest.FixtureRequest, agent_launch, tmp_path) -> ChildProbes:
    """The probe phase's findings on the run's one connection (see `_connection_transcript`)."""
    await _connection_transcript(request, agent_launch, tmp_path)
    return request.config.stash[_CONNECTION_KEY]["probes"]


def _summary(problems: list[str]) -> str:
    return "; ".join(problems[:3]) + (
        f" (and {len(problems) - 3} more)" if len(problems) > 3 else ""
    )


@pytest.mark.requirement("ACP-SUBAGENT-001")
async def test_child_session_traffic_follows_its_announcement(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-001. Over the whole connection -- turn and quiet period alike -- no
    `session/update`, agent -> client request or `session_message` participant names a session
    ID the client did not create before a `subagent_update` on a known session announced it.
    SKIPs when the agent sends no such ID at all."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    children, problems = child_session_traffic(transcript, {session_id})
    if not children:
        pytest.skip("the agent exposed no subagent: no session ID the client did not create")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-002")
async def test_session_content_names_a_known_session(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-002. Every `session` tool-call content item names a session the client
    created or one an earlier `subagent_update` on a known session announced. SKIPs when no
    `session` content item appears."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    references, problems = session_content_references(transcript, {session_id})
    if not references:
        pytest.skip("the agent emitted no `session` tool-call content item")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-003")
async def test_subagent_update_never_makes_a_session_its_own_parent(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-003. No `subagent_update` has the same `sessionId` as the session it is sent
    on. SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.self_parented, _summary(found.self_parented)


@pytest.mark.requirement("ACP-SUBAGENT-004")
async def test_subagent_update_never_announces_a_client_created_session(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-004. No `subagent_update` announces, as a child of another session, a session
    the client created with `session/new`, and a later `session/new` (the probe phase's) never
    returns an announced child's ID (`subagents.mdx:80-83`: the Agent MUST NOT reuse a child's ID
    for an unrelated session). SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.client_sessions_announced, _summary(found.client_sessions_announced)
    probes = await _connection_probes(request, agent_launch, tmp_path)
    assert probes.new_session not in probes.children, (
        f"session/new returned {probes.new_session!r}, the ID of a child session an earlier "
        f"`subagent_update` announced; a child's ID is not reused for an unrelated session"
    )


@pytest.mark.requirement("ACP-SUBAGENT-005")
async def test_announced_child_keeps_its_one_parent(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-005. A child announced on a known session is never announced again on a
    different session, which would reparent it (or close a cycle). SKIPs when the agent sends no
    `subagent_update`."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.reparented, _summary(found.reparented)


@pytest.mark.requirement("ACP-SUBAGENT-006")
async def test_subagent_update_directories_are_absolute(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-006. Every `subagent_update.cwd` and `additionalDirectories` entry is an
    absolute path. SKIPs when no `subagent_update` reports a string for either (a value of the wrong
    type is `ACP-PROMPT-002`'s)."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.reported_directories:
        pytest.skip("no `subagent_update` reported `cwd` or `additionalDirectories`")
    assert not found.relative_paths, _summary(found.relative_paths)


@pytest.mark.requirement("ACP-SUBAGENT-007")
async def test_session_message_participants_differ(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-007. When both `senderSessionId` and `recipientSessionId` of a
    `session_message` are known, they identify different sessions. SKIPs when no
    `session_message` has both participants known."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.participants_judged:
        pytest.skip("no `session_message` had both `senderSessionId` and `recipientSessionId` known")
    assert not found.same_participants, _summary(found.same_participants)


@pytest.mark.requirement("ACP-SUBAGENT-008")
async def test_session_message_outer_session_is_a_participant(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-008. When both participants of a `session_message` are known and differ,
    `params.sessionId` is one of them. SKIPs when no `session_message` has both participants
    known."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.participants_judged:
        pytest.skip("no `session_message` had both `senderSessionId` and `recipientSessionId` known")
    assert not found.foreign_outer, _summary(found.foreign_outer)


@pytest.mark.requirement("ACP-SUBAGENT-009")
async def test_session_message_views_reference_each_other(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-009. When both views of one message carry `senderMessageId` /
    `recipientMessageId`, each names the other's `messageId`. SKIPs when no two such views are
    linked."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.links_judged:
        pytest.skip("no two linked `session_message` views both carried a reference")
    assert not found.unlinked_views, _summary(found.unlinked_views)


@pytest.mark.requirement("ACP-SUBAGENT-011")
async def test_child_task_is_not_a_user_message(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-011. An announced child has no `user_message`/`user_message_chunk` before its
    first agent output. SKIPs when no announced child produces agent output or has one."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_task_reports(transcript, {session_id})
    if not found.started and not found.user_message_tasks:
        pytest.skip("no announced child produced agent output")
    assert not found.user_message_tasks, _summary(found.user_message_tasks)


@pytest.mark.requirement("ACP-SUBAGENT-012")
async def test_child_task_is_an_incoming_session_message_before_its_output(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-012. An announced child's first agent output is preceded by an incoming
    `session_message` whose `senderSessionId` is its parent, or that names no sender (an Agent
    with no evidence of the sender omits it, `subagents.mdx:265`). A task reported as a user
    message is `ACP-SUBAGENT-011`'s. SKIPs when no announced child that was not told the task as a user
    message produces agent output."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_task_reports(transcript, {session_id})
    if not found.judged:
        pytest.skip("no announced child produced agent output without a user-message task")
    assert not found.unreported, _summary(found.unreported)


@pytest.mark.requirement("ACP-SUBAGENT-013")
async def test_session_message_participants_precede_the_first_chunk(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-013. A streamed `session_message` has a participant ID stored by its first
    chunk, unless none is ever supplied. SKIPs when no `session_message_chunk` appears."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = session_message_streams(transcript, {session_id})
    if not found.streamed:
        pytest.skip("the agent sent no `session_message_chunk`")
    assert not found.late_participants, _summary(found.late_participants)


@pytest.mark.requirement("ACP-SUBAGENT-014")
async def test_child_select_offers_only_its_current_value(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-014. A select option in a `config_option_update` for an announced child
    offers no value but the current one. SKIPs when no such select is reported."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_config_selects(transcript, {session_id})
    if not found.selects:
        pytest.skip("the agent reported no select config option for an announced child")
    assert not found.with_choices, _summary(found.with_choices)


@pytest.mark.requirement("ACP-SUBAGENT-201")
async def test_child_state_is_mirrored_on_the_parent(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-201. Each state an announced child reports in its own `state_update` is also
    the `state` of a `subagent_update` for it on its parent, in order. SKIPs when no announced
    child reports a `state_update`."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_state_mirrors(transcript, {session_id})
    if not found.judged:
        pytest.skip("no announced child reported a `state_update`")
    assert not found.unmirrored, _summary(found.unmirrored)


@pytest.mark.requirement("ACP-SUBAGENT-205")
async def test_both_copies_of_a_child_state_precede_a_later_transition(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-205. Per announced child, each two consecutive transitions both reported on
    the child's own `state_update` and mirrored on its parent (paired in order up to the first
    difference between the paths, which is `ACP-SUBAGENT-201`'s) have both copies of the first
    before the first copy of the second, on either path (`subagents.mdx:351`). SKIPs when no
    announced child has two paired transitions."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_state_order(transcript, {session_id})
    if not found.judged:
        pytest.skip("no announced child reported two state transitions on both its own stream and its parent")
    assert not found.out_of_order, _summary(found.out_of_order)


@pytest.mark.requirement("ACP-SUBAGENT-206")
async def test_child_idle_stop_reason_is_defined_or_underscore_prefixed(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-206. Each `stopReason` an announced child reports on an idle snapshot (its own
    `state_update`, or mirrored on its parent) is a defined constant or begins with `_`: the
    turn-ending idle of the prompted session is `ACP-STATE-203`'s. SKIPs when no announced child
    reports one."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_stop_reasons(transcript, {session_id})
    if not found.reported:
        pytest.skip("no announced child reported a `stopReason` on an idle snapshot")
    assert not found.invalid, _summary(found.invalid)


@pytest.mark.requirement("ACP-SUBAGENT-207")
async def test_child_idle_that_ends_its_work_carries_a_stop_reason(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-207 (ADVISORY). The first idle after an announced child's own `running` or
    `requires_action` carries a non-null `stopReason`: the turn-ending idle of the prompted
    session is `ACP-STATE-204`'s. SKIPs when no announced child reports an active state and then
    an idle."""
    transcript, session_id = await _connection_transcript(request, agent_launch, tmp_path)
    found = child_stop_reasons(transcript, {session_id})
    if not found.ended:
        pytest.skip("no announced child went from an active state to idle in its own `state_update`s")
    assert not found.missing, _summary(found.missing)


def _probe_summary(probes: list[ChildProbe], what: str) -> str:
    return _summary([f"{probe.method} for child {probe.child!r} {what}" for probe in probes])


@pytest.mark.requirement("ACP-SUBAGENT-018")
async def test_request_naming_a_child_is_rejected_as_invalid_params(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-018 (ADVISORY). After the judged transcript, the TCK sends `session/resume`,
    `session/delete` (when advertised) and `session/close` naming each of the first two announced
    children. This deliberately breaks a Client MUST NOT, because the docs define the Agent's
    answer to exactly that input: any such request gets `-32602` (`error.mdx:58`,
    `subagents.mdx:380`). Only mutating methods are probed (the RFD leaves read-only operations
    their normal semantics). Judged for a probe that came back as an error; a success is
    `ACP-SUBAGENT-019`'s. SKIPs without an announced child or when no probe was answered with an
    error."""
    probes = await _connection_probes(request, agent_launch, tmp_path)
    if not probes.children:
        pytest.skip("the agent announced no child session")
    errored = [probe for probe in probes.probes if probe.errored]
    if not errored:
        pytest.skip("no probe naming a child was answered with an error")
    wrong = [probe for probe in errored if probe.error_code != -32602]
    assert not wrong, _summary(
        [
            f"{probe.method} for child {probe.child!r} got error {probe.error_code!r}, not "
            f"-32602 (Invalid params)"
            for probe in wrong
        ]
    )


@pytest.mark.requirement("ACP-SUBAGENT-019")
@pytest.mark.capability("capabilities.session")
async def test_close_and_delete_of_a_child_do_not_succeed(request, agent_launch, tmp_path):
    """ACP-SUBAGENT-019. The `session/close` (and, when advertised, `session/delete`) probe naming
    an announced child (see `ACP-SUBAGENT-018`, whose probe deliberately breaks a Client MUST
    NOT) is not answered with a success: the docs say they do not report success for a child
    (`subagents.mdx:380`). Any error passes here, whatever its code. SKIPs without an announced
    child or when no probe was answered."""
    probes = await _connection_probes(request, agent_launch, tmp_path)
    if not probes.children:
        pytest.skip("the agent announced no child session")
    answered = [
        probe
        for probe in probes.probes
        if probe.method in ("session/close", "session/delete") and probe.response is not None
    ]
    if not answered:
        pytest.skip("no `session/close` or `session/delete` probe naming a child was answered")
    succeeded = [probe for probe in answered if probe.succeeded]
    assert not succeeded, _probe_summary(succeeded, "reported success; a child is not closed or deleted")


@pytest.mark.requirement("ACP-LIST-004")
@pytest.mark.capability("capabilities.session")
async def test_session_list_does_not_return_an_announced_child(request, agent_launch, tmp_path):
    """ACP-LIST-004. `session/list`, sent after the turn and quiet period of the subagents
    connection (`params: {}`, `nextCursor` followed for at most ten pages), returns no session an
    earlier `subagent_update` announced as a child (`subagents.mdx:381`). SKIPs without an
    announced child or when the list did not answer with a `sessions` array (`ACP-LIST-001`'s
    finding)."""
    probes = await _connection_probes(request, agent_launch, tmp_path)
    if not probes.children:
        pytest.skip("the agent announced no child session")
    if probes.listed is None:
        pytest.skip("`session/list` did not return a `sessions` array")
    leaked = [child for child in probes.children if child in probes.listed]
    assert not leaked, _summary(
        [f"session/list returned the announced child session {child!r}" for child in leaked]
    )
