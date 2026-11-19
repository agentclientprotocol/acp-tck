"""Unit tests for `is_absolute_path` as ACP-PLAN-003 reads a markdown plan's `path` (a native
path, not a URI), and for `conforming_full.py`'s plan emission that makes ACP-PLAN-002/003/004 pass
non-vacuously."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from tck.common.harness import AgentLaunch, AgentProcess, Direction
from tck.v1.conformance._helpers import is_absolute_path, new_session, run_prompt, session_update_kind

_FIXTURES = Path(__file__).parent.parent / "fixtures" / "agents" / "v1"


@pytest.mark.parametrize(
    "path",
    ["/tmp/PLAN.md", "/", "C:\\plans\\PLAN.md", "C:/plans/PLAN.md", "\\\\server\\share\\PLAN.md"],
)
def test_absolute_native_paths(path):
    assert is_absolute_path(path)


@pytest.mark.parametrize(
    "path",
    ["PLAN.md", "./PLAN.md", "../PLAN.md", "file:///tmp/PLAN.md", "https://example.com/PLAN.md", "\\PLAN.md", "", None, 42],
)
def test_non_absolute_native_paths(path):
    assert not is_absolute_path(path)


def _plan_updates(client_capabilities: dict, tmp_path) -> list[dict]:
    async def go():
        launch = AgentLaunch(
            command=[sys.executable, str(_FIXTURES / "conforming_full.py")],
            startup_timeout=2.0,
            default_timeout=2.0,
        )
        async with AgentProcess(launch) as agent:
            init_id = await agent.send_request(
                "initialize", {"protocolVersion": 1, "clientCapabilities": client_capabilities}
            )
            await agent.wait_for_response(init_id, timeout=2.0)
            session_id = await new_session(agent, tmp_path, timeout=2.0)
            await run_prompt(agent, session_id, [{"type": "text", "text": "plan"}], timeout=2.0)
            return [
                entry.parsed["params"]["update"]
                for entry in agent.transcript
                if entry.direction is Direction.RECEIVED
                and session_update_kind(entry) == "plan_update"
            ]

    return asyncio.run(go())


def test_conforming_full_sends_plan_updates_only_when_plan_is_advertised(tmp_path):
    with_plan = _plan_updates({"plan": {}}, tmp_path)
    assert {update["plan"]["type"] for update in with_plan} == {"items", "markdown"}
    assert all(
        is_absolute_path(u["plan"]["path"]) for u in with_plan if u["plan"]["type"] == "markdown"
    )
    assert _plan_updates({}, tmp_path) == []
