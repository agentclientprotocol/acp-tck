"""INFORMATIONAL-tier probes: ACP-INFO-PARSE-001, ACP-INFO-INVALIDREQ-001.

`error.mdx` assigns `-32700` to non-JSON input and `-32600` to a message that is not a valid
request object, but requires no reply -- and `transports.mdx` forbids a client from sending
either. Real SDKs disagree in practice, so neither probe asserts on the probed behaviour: each
deliberately breaks that client rule only to record what the agent actually does, via
`record_property`, for a human reading the report. (They can still FAIL if the prerequisite
`initialize` handshake itself fails; that is a real conformance problem the probe correctly
surfaces, not a probe bug.) Each uses its own throwaway `connected_agent` so a bad reaction (if
any) cannot contaminate a later test's connection.

Concluding "the agent stayed silent" uses `quiet_period()`, not the full `--tck-timeout` -- a
v1 TCK must not fail an agent for skipping malformed/non-envelope input (the reference SDK does
exactly that), and must be prepared for "no response at all" without burning the full
per-response deadline to conclude it. The agent's own notifications or requests in that window
are not a reply and are skipped (`_helpers.next_reply_line`).
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentExited, AgentTimeout
from tck.v1.protocol import PROTOCOL_VERSION

from ._helpers import connected_agent, new_session, next_reply_line, quiet_period


async def _probe_connection_usable_after(agent, tmp_path, timeout: float) -> str:
    """Send an ordinary `session/new` and report whether it still gets a normal response."""
    try:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
    except AssertionError:
        return "unusable (session/new did not return a well-formed result)"
    except (AgentTimeout, AgentExited):
        return "unusable (no response / agent exited)"
    else:
        return f"usable (sessionId={session_id!r})"


@pytest.mark.requirement("ACP-INFO-PARSE-001")
async def test_malformed_json_line_behaviour(agent_launch, tmp_path, record_property):
    """ACP-INFO-PARSE-001 (INFORMATIONAL). Sends one line of malformed JSON (not valid JSON at
    all) and records whether the agent: replies with a `-32700`/`id: null` error (JSON-RPC's
    documented-but-not-universal behaviour), replies with something else, or stays silent (the
    reference SDK's documented behaviour -- concluded via `quiet_period()`, not the full
    `--tck-timeout`). Then, using a fresh, ordinary `session/new` on the *same* connection,
    records whether the connection is still usable afterwards. Never asserts on the probed
    behaviour itself."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request(
            "initialize", {"protocolVersion": PROTOCOL_VERSION, "clientCapabilities": {}}
        )
        await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)

        await agent.send_raw(b"{not valid json at all")

        try:
            entry = await next_reply_line(agent, quiet_period(agent_launch.default_timeout))
        except AgentTimeout:
            behaviour = "silent"
        except AgentExited as exc:
            behaviour = f"agent exited (exit_code={exc.exit_code!r})"
        else:
            msg = entry.parsed
            if (
                isinstance(msg, dict)
                and isinstance(msg.get("error"), dict)
                and msg["error"].get("code") == -32700
                and msg.get("id") is None
            ):
                behaviour = "replied -32700 with id:null"
            else:
                behaviour = f"replied: {entry.text!r}"

        connection_usable_after = await _probe_connection_usable_after(
            agent, tmp_path, agent_launch.default_timeout
        )

    record_property("behaviour", behaviour)
    record_property("connection_usable_after", connection_usable_after)


@pytest.mark.requirement("ACP-INFO-INVALIDREQ-001")
async def test_structurally_invalid_request_behaviour(agent_launch, tmp_path, record_property):
    """ACP-INFO-INVALIDREQ-001 (INFORMATIONAL). Same as ACP-INFO-PARSE-001, but for a line that
    *is* valid JSON yet not a JSON-RPC request/notification/response at all (`{"foo": "bar"}`,
    no `jsonrpc`/`method`/`id`). "Silent" is concluded via `quiet_period()`, not the full
    `--tck-timeout`. Never asserts on the probed behaviour itself."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request(
            "initialize", {"protocolVersion": PROTOCOL_VERSION, "clientCapabilities": {}}
        )
        await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)

        await agent.send_raw(b'{"foo": "bar"}')

        try:
            entry = await next_reply_line(agent, quiet_period(agent_launch.default_timeout))
        except AgentTimeout:
            behaviour = "silent"
        except AgentExited as exc:
            behaviour = f"agent exited (exit_code={exc.exit_code!r})"
        else:
            msg = entry.parsed
            if (
                isinstance(msg, dict)
                and isinstance(msg.get("error"), dict)
                and msg["error"].get("code") == -32600
            ):
                behaviour = "replied -32600 (invalid request)"
            else:
                behaviour = f"replied: {entry.text!r}"

        connection_usable_after = await _probe_connection_usable_after(
            agent, tmp_path, agent_launch.default_timeout
        )

    record_property("behaviour", behaviour)
    record_property("connection_usable_after", connection_usable_after)
