"""Permission-request conformance: ACP-PERM-001/002.

In v1 the agent runs its own tools, so the operation is not on the wire. The probe asks the
agent to create a file in the session `cwd`; when it asks `session/request_permission`, the mock
client answers with the response under test (`run_prompt(permission=...)`) and the file must not
appear. An agent that never asks permission, or offers no `reject_once`, SKIPs (not exercised);
in the latter case the mock client cancels the turn instead of selecting any other option.

ACP-PERM-002 sends a `selected` outcome naming an `optionId` the agent never offered
(`_tck_unoffered_option`). That breaks the client rule that `optionId` names an offered option,
which is allowed here because the spec defines the agent's answer: it SHOULD NOT treat an
unrecognised outcome as approval (`tool-calls.mdx:249`).
"""

from __future__ import annotations

import pytest

from ._helpers import (
    PermissionPolicy,
    connected_agent,
    new_session,
    run_prompt,
    skip_if_version_mismatch,
)

_PROBE_FILE = "tck-permission-probe.txt"
_PROBE_PROMPT = f"Create a file named {_PROBE_FILE} in the current working directory containing the word hello."


async def _run_permission_probe(agent_launch, agent_initialize_result, tmp_path, policy: PermissionPolicy) -> None:
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROBE_PROMPT}],
            permission=policy,
            timeout=agent_launch.default_timeout,
        )
    asked = [
        entry
        for entry in turn.client_requests_seen
        if isinstance(entry.parsed, dict) and entry.parsed.get("method") == "session/request_permission"
    ]
    if not asked:
        pytest.skip("permission probe not exercised: the agent sent no session/request_permission")
    if turn.permission_cancels:
        # No `reject_once` was offered. The mock client cancelled the turn rather than pick
        # another option (which could persist an approval or a standing deny); nothing in the
        # spec requires offering one, so this is not a failure.
        pytest.skip(f"permission probe not exercised: {turn.permission_cancels[0]}")
    assert not (tmp_path / _PROBE_FILE).exists(), (
        f"agent created {_PROBE_FILE} after the permission request was answered with policy "
        f"{policy!r}"
    )


@pytest.mark.requirement("ACP-PERM-001")
async def test_reject_once_is_honoured(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PERM-001. Selecting `reject_once` must stop the operation."""
    await _run_permission_probe(agent_launch, agent_initialize_result, tmp_path, "reject_once")


@pytest.mark.requirement("ACP-PERM-002")
async def test_unrecognised_option_is_not_approval(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PERM-002. An unoffered `optionId` must not be treated as approval."""
    await _run_permission_probe(agent_launch, agent_initialize_result, tmp_path, "unknown_option")
