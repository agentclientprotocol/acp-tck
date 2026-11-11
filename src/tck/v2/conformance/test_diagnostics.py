"""Advisory/informational diagnostics: `ACP-ERROR-001`, `ACP-SHUTDOWN-001`, `ACP-STDERR-001`.
An error object has an integer `code`, a short `message` and optional `data` (`error.mdx:6-10`);
on stdin EOF the agent SHOULD exit once it has finished or stopped its work (transports.mdx:43);
stderr MAY carry UTF-8 logging (transports.mdx:22). All connection-level, `capability=None` --
none needs a turn, and `ACP-SHUTDOWN-001`/`ACP-STDERR-001` need nothing beyond `initialize`."""

from __future__ import annotations

import pytest

from tck.v2 import SPEC

from ._helpers import connected_agent


@pytest.mark.requirement("ACP-ERROR-001")
async def test_error_messages_are_non_empty_single_line(agent_launch):
    """ACP-ERROR-001 (ADVISORY; `error.mdx:9`, `schema/v2/schema.unstable.json#/$defs/Error`).
    Evidence: the reply to an unrecognised method, and the reply to a `session/new` missing its
    required `cwd`."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)

        unknown_id = await agent.send_request("_tck/does_not_exist")
        unknown_entry = await agent.wait_for_response(unknown_id, timeout=agent_launch.default_timeout)

        bad_id = await agent.send_request("session/new", {})  # missing required cwd
        bad_entry = await agent.wait_for_response(bad_id, timeout=agent_launch.default_timeout)

    for what, entry in (("_tck/does_not_exist", unknown_entry), ("session/new (missing cwd)", bad_entry)):
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if not isinstance(error, dict):
            continue  # envelope shape is ACP-JSONRPC-002/004's concern, not this test's
        message = error.get("message")
        if not isinstance(message, str):
            continue
        assert message != "", f"{what}: error.message must not be empty"
        assert "\n" not in message, f"{what}: error.message must not contain a newline: {message!r}"
        # error.data's shape depends on the code (`error.mdx:10`); ACP-ERROR-201 checks the
        # `-32002` shape, nothing is asserted on it here.


@pytest.mark.requirement("ACP-SHUTDOWN-001")
async def test_agent_exits_promptly_after_stdin_close(agent_launch):
    """ACP-SHUTDOWN-001 (ADVISORY -- on stdin EOF the agent SHOULD exit once it has finished or
    stopped its work, `docs/protocol/v2/draft/transports.mdx:43`; no work is in flight here, so
    "finished" holds immediately). Relies on `connected_agent`'s `close()` ladder and reports
    whether the agent exited during the first rung (`AgentProcess.exited_on_stdin_close`)."""
    async with connected_agent(agent_launch) as agent:
        pass

    assert agent.exited_on_stdin_close, (
        "agent did not exit within the grace period after stdin closed; it needed SIGTERM/"
        "SIGKILL to terminate (advisory -- the agent SHOULD exit once it has finished or stopped "
        "its work)"
    )


@pytest.mark.requirement("ACP-STDERR-001")
async def test_stderr_byte_count_is_recorded(agent_launch, record_property):
    """ACP-STDERR-001 (INFORMATIONAL -- the agent MAY write UTF-8 logging to stderr,
    transports.mdx:22, so there is nothing to assert). Always PASSes; exists purely to surface
    stderr chattiness for a human reading the report."""
    async with connected_agent(agent_launch) as agent:
        pass

    stderr_bytes = len(agent.stderr_text().encode("utf-8"))
    record_property("acp_tck_stderr_bytes", stderr_bytes)
