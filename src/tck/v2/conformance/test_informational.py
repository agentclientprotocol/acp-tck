"""INFORMATIONAL-tier probes: ACP-INFO-CONCURRENT-201, ACP-INFO-PARSE-001 and
ACP-INFO-INVALIDREQ-001.

None asserts on the probed behaviour itself -- each just records what the agent does via
`record_property`. The spec defines no reply to the malformed and invalid lines (`error.mdx`
only assigns `-32700`/`-32600`, and `transports.mdx:24` forbids the client to send them);
`ACP-ERROR-204` judges the shape of a `-32700` reply. They can still FAIL if the prerequisite
handshake (`initialize`/`session/new`) itself fails; that's a real conformance problem, not a
probe bug. CONCURRENT-201 is gated on `capabilities.session` even though its `Requirement` is
INFORMATIONAL (`capability=None` on the registry entry -- see `tck.v2.requirements`'s module
docstring for why the marker and registry fields are independent). PARSE-001/INVALIDREQ-001 carry
no such marker; their `_probe_connection_usable_after` helper swallows a `session/new` failure
into an "unusable" string instead.

Concluding "the agent stayed silent" uses `quiet_period()`, not the full timeout. In the
parse/invalid-request probes, the agent's own notifications or requests in that window are not a
reply and are skipped (`_helpers.next_reply_line`).
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentExited, AgentTimeout
from tck.v2 import SPEC

from ._helpers import (
    connected_agent,
    new_session,
    next_reply_line,
    probe_behaviour,
    prompt_during_active_work,
    quiet_period,
)

def _classify_reply(entry) -> str:
    """`on_reply` for the two raw-transport probes (malformed JSON line / structurally invalid
    request)."""
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    if isinstance(error, dict):
        return f"replied with error code {error.get('code')!r}"
    else:
        return f"replied: {entry.text!r}"


async def _probe_connection_usable_after(agent, tmp_path, timeout: float) -> str:
    """Send an ordinary `session/new` and report whether it still gets a normal response.
    v2 twin of `tck.v1.conformance.test_informational._probe_connection_usable_after`."""
    try:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
    except AssertionError:
        return "unusable (session/new did not return a well-formed result)"
    except pytest.skip.Exception:
        return "unusable (session/new is auth-gated)"
    except (AgentTimeout, AgentExited):
        return "unusable (no response / agent exited)"
    else:
        return f"usable (sessionId={session_id!r})"


@pytest.mark.requirement("ACP-INFO-CONCURRENT-201")
@pytest.mark.capability("capabilities.session")
async def test_concurrent_prompt_behaviour(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-INFO-CONCURRENT-201 (INFORMATIONAL). Runs `ACP-PROMPT-209`'s scenario (a second
    prompt on the first `running`/`requires_action` of a cancel-prompt turn, then
    `session/cancel`) and records whether the second prompt was inserted right away, rejected,
    or held, and how a held one was answered after the cancel. Which of these the agent does is
    up to it (prompt-lifecycle.mdx:382). Never asserts; SKIPs when not exercised."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            scenario = await prompt_during_active_work(
                agent, session_id, cancel_prompt_text, timeout=timeout
            )
        except AgentTimeout:
            pytest.skip("the first prompt's turn never ended -- see ACP-STATE-202/ACP-CANCEL-001")
    if scenario.not_exercised is not None:
        pytest.skip(f"prompt during active work not exercised: {scenario.not_exercised}")
    record_property("behaviour", scenario.outcome)
    if scenario.outcome == "held":
        error = scenario.second_error
        if scenario.second_response is None:
            answer = "unanswered"
        elif error is not None:
            answer = f"error code {error.get('code')!r}"
        else:
            answer = "success"
        record_property("held_prompt_answer_after_cancel", answer)


@pytest.mark.requirement("ACP-INFO-PARSE-001")
async def test_malformed_json_line_behaviour(agent_launch, tmp_path, record_property):
    """ACP-INFO-PARSE-001 (INFORMATIONAL). Sends a line that is not
    valid JSON at all after a normal `initialize`, and records how the agent reacts: a JSON-RPC
    error, silence, or an exit. Never asserts on the behaviour itself; still records whether the
    connection is usable afterwards for a human reading the report."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        await agent.wait_for_response(init_id, timeout=agent_launch.startup_timeout)

        await agent.send_raw(b"{not valid json at all")
        behaviour = await probe_behaviour(
            next_reply_line(agent, quiet_period(agent_launch.default_timeout)),
            _classify_reply,
        )

        usable_after = await _probe_connection_usable_after(
            agent, tmp_path, agent_launch.default_timeout
        )

    record_property("behaviour", behaviour)
    record_property("connection_usable_after", usable_after)


@pytest.mark.requirement("ACP-INFO-INVALIDREQ-001")
async def test_structurally_invalid_request_behaviour(agent_launch, tmp_path, record_property):
    """ACP-INFO-INVALIDREQ-001 (INFORMATIONAL). Sends a
    well-formed-JSON line that is not a valid JSON-RPC envelope at all (no `jsonrpc`/`method`)
    after a normal `initialize`, and records how the agent reacts. Never asserts on the
    behaviour itself; still records whether the connection is usable afterwards."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        await agent.wait_for_response(init_id, timeout=agent_launch.startup_timeout)

        await agent.send_raw(b'{"foo": "bar"}')
        behaviour = await probe_behaviour(
            next_reply_line(agent, quiet_period(agent_launch.default_timeout)),
            _classify_reply,
        )

        usable_after = await _probe_connection_usable_after(
            agent, tmp_path, agent_launch.default_timeout
        )

    record_property("behaviour", behaviour)
    record_property("connection_usable_after", usable_after)
