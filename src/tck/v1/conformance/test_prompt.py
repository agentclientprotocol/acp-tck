"""Prompt-turn conformance: ACP-PROMPT-001..004."""

from __future__ import annotations

import re
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.common.plugin import capability_is_supported
from tck.v1.protocol import STOP_REASONS
from tck.v1.validation import validate_agent_message

from ._helpers import (
    connected_agent,
    new_session,
    run_prompt,
    session_update_kind,
    skip_if_version_mismatch,
)


@pytest.mark.requirement("ACP-PROMPT-001")
async def test_text_only_prompt_resolves_with_a_valid_stop_reason(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PROMPT-001. Checks version mismatch first: a v1-shaped stopReason can't be judged
    against an agent that never negotiated v1."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "hello"}],
            timeout=agent_launch.default_timeout,
        )
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict) and "result" in msg, f"session/prompt did not succeed: {msg!r}"
        stop_reason = msg["result"].get("stopReason")
        assert stop_reason in STOP_REASONS, f"invalid stopReason: {stop_reason!r}"


@pytest.mark.requirement("ACP-PROMPT-002")
async def test_updates_validate_and_carry_the_right_session_id(agent_launch, tmp_path):
    """ACP-PROMPT-002. An agent that emits zero `session/update` notifications is still
    conforming -- Req 1 only requires it be *able* to send them, not that it does. This test
    passes vacuously when `turn.updates` is empty; it only fails on a malformed or
    misattributed update.
    """
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "hello"}],
            timeout=agent_launch.default_timeout,
        )

        for _, entry in turn.updates:
            update_msg = entry.parsed
            assert isinstance(update_msg, dict), f"session/update line did not parse: {entry.raw!r}"
            issues = validate_agent_message(update_msg)
            assert not issues, f"session/update failed schema validation: {issues!r}"
            carried_session_id = (update_msg.get("params") or {}).get("sessionId")
            assert carried_session_id == session_id, (
                f"session/update carried sessionId {carried_session_id!r}, expected {session_id!r}"
            )


@pytest.mark.requirement("ACP-PROMPT-003")
async def test_resource_link_content_block_is_accepted(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PROMPT-003. Checks version mismatch first, like ACP-PROMPT-001."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [
                {"type": "text", "text": "have a look at this"},
                {"type": "resource_link", "uri": "file:///tmp/tck-example.txt", "name": "example.txt"},
            ],
            timeout=agent_launch.default_timeout,
        )
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"a prompt with a resource_link block must still succeed: {msg!r}"
        )
        stop_reason = msg["result"].get("stopReason")
        assert stop_reason in STOP_REASONS, f"invalid stopReason: {stop_reason!r}"


# POSIX absolute, Windows drive-absolute (`C:\` or `C:/`), or UNC (`\\server\share`).
_ABSOLUTE_PATH_RE = re.compile(r"^(/|[A-Za-z]:[\\/]|\\\\)")


def _tool_call_paths(update: dict[str, Any]) -> list[str]:
    """Every file path a `tool_call`/`tool_call_update` carries: `locations[].path` and the
    `path` of each `diff` content item."""
    paths = []
    for location in update.get("locations") or []:
        if isinstance(location, dict) and "path" in location:
            paths.append(location["path"])
    for item in update.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "diff" and "path" in item:
            paths.append(item["path"])
    return paths


@pytest.mark.requirement("ACP-PROMPT-004")
async def test_emitted_file_paths_are_absolute(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PROMPT-004. Sends a file-flavoured prompt (with a real file in `cwd`) to give the
    agent a reason to report tool-call locations, then scans every agent-sent message on the
    connection, plus a `session/list` result when `list` is advertised. Passes vacuously when
    no path is emitted."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    (tmp_path / "README.md").write_text("# TCK sample\n\nA file for the agent to read.\n")
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "Read the file README.md in the current directory and summarize it."}],
            timeout=agent_launch.default_timeout,
        )
        emitted: list[Any] = []
        for entry in agent.transcript:
            if entry.direction is Direction.RECEIVED and session_update_kind(entry) in (
                "tool_call",
                "tool_call_update",
            ):
                emitted += _tool_call_paths(entry.parsed["params"]["update"])
        if init_result is not None and capability_is_supported(
            init_result, "agentCapabilities.sessionCapabilities.list"
        ):
            list_id = await agent.send_request("session/list", {})
            list_entry = await agent.wait_for_response(list_id, timeout=agent_launch.default_timeout)
            # A failed or malformed list is ACP-LIST-001's finding; only paths are judged here.
            result = list_entry.parsed.get("result") if isinstance(list_entry.parsed, dict) else None
            sessions = result.get("sessions") if isinstance(result, dict) else None
            if isinstance(sessions, list):
                emitted += [info["cwd"] for info in sessions if isinstance(info, dict) and "cwd" in info]

        relative = [path for path in emitted if not (isinstance(path, str) and _ABSOLUTE_PATH_RE.match(path))]
        assert not relative, f"agent emitted non-absolute file path(s): {relative!r}"
