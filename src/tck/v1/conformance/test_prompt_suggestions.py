"""Prompt-suggestion conformance: ACP-SUGGEST-001..004.

All four rules only apply once the client advertised `clientCapabilities.session.promptSuggestions`,
which every other connection in this suite leaves out (ACP-CLIENTCAP-008 depends on that). So the
rows share one connection that advertises `promptSuggestions: {}` and nothing else (no `image`,
`audio` or `embeddedContext` opt-in, so only `text` and `resource_link` blocks are allowed):
`session/new`, a prompt turn, a quiet period (an agent typically sends its list after the
response), a second prompt turn, a quiet period (the window of ACP-SUGGEST-003), `session/load`
when `loadSession` is advertised, and a last quiet period. It is made once per run and every row
judges the same traffic. Suggestions are unstable and optional ("An Agent is never required to
send one"), so an agent that sends none passes ACP-SUGGEST-001/002 vacuously and SKIPs the other
two. A prompt turn that outlasts `--timeout` FAILs every row, like any broken setup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.common.plugin import capability_is_supported, register_active_process
from tck.v1.validation import validate_against_def

from ._helpers import (
    connected_agent,
    new_session,
    quiet_period,
    run_prompt,
    session_update_kind,
    skip_if_version_mismatch,
)

_FIRST_PROMPT_TEXT = "Summarize what you can help me with in this project."
_SECOND_PROMPT_TEXT = "Thanks. What would you suggest we do next in this project?"
_ALLOWED_BLOCK_TYPES = ("text", "resource_link")
"""The content blocks a suggestion may hold when the client advertised `promptSuggestions: {}`
and no per-type opt-in (`docs/protocol/v1/draft/prompt-turn.mdx:404`)."""

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `connection` once it completed, or `error` (the
exception it ended with), so every row sees the same outcome."""


@dataclass(frozen=True)
class SuggestionsConnection:
    transcript: list
    session_id: str
    second_prompt_at: int
    """The transcript index of the second `session/prompt` request."""
    second_prompt_accepted: bool
    window_end: int
    """The transcript length at the end of the quiet period after the second turn."""
    load: tuple[int, int] | None
    """The `[start, end)` transcript range of the `session/load` exchange (request to response,
    or to where the wait for the response stopped), `None` when none was sent."""


async def _drain(agent, seconds: float) -> None:
    try:
        await agent.wait_for_message(lambda _entry: False, timeout=seconds)
    except (AgentTimeout, AgentExited):
        pass


async def _make_connection(agent_launch, init_result, tmp_path) -> SuggestionsConnection:
    timeout = agent_launch.default_timeout
    quiet = quiet_period(timeout)
    async with connected_agent(
        agent_launch, client_capabilities={"session": {"promptSuggestions": {}}}
    ) as agent:
        register_active_process(agent)
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _FIRST_PROMPT_TEXT}], timeout=timeout)
        await _drain(agent, quiet)
        second_prompt_at = len(agent.transcript)
        second = await run_prompt(
            agent, session_id, [{"type": "text", "text": _SECOND_PROMPT_TEXT}], timeout=timeout
        )
        accepted = isinstance(second.response_entry.parsed, dict) and "result" in second.response_entry.parsed
        await _drain(agent, quiet)
        window_end = len(agent.transcript)
        load = None
        if init_result is not None and capability_is_supported(
            init_result, "agentCapabilities.loadSession", boolean=True
        ):
            start = len(agent.transcript)
            load_id = await agent.send_request(
                "session/load", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
            )
            try:
                await agent.wait_for_response(load_id, timeout=timeout)
            except (AgentTimeout, AgentExited):
                pass  # ACP-LOAD-001's finding; judge the traffic seen
            load = (start, len(agent.transcript))
            await _drain(agent, quiet)
    return SuggestionsConnection(
        list(agent.transcript), session_id, second_prompt_at, accepted, window_end, load
    )


async def suggestions_connection(request, agent_launch, agent_initialize_result, tmp_path) -> SuggestionsConnection:
    """The connection described in the module docstring, made by the first row that asks and
    reused by the rest. An error or SKIP that ended it is re-raised for each row. An agent that
    did not negotiate v1 SKIPs (`VERSION-MISMATCH:`)."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "connection" not in cache:
        try:
            cache["connection"] = await _make_connection(agent_launch, init_result, tmp_path)
        except BaseException as exc:
            cache["error"] = exc
            raise
    return cache["connection"]


def _suggestion_updates(connection: SuggestionsConnection) -> list[tuple[int, Any, Any]]:
    """`(transcript_index, sessionId, suggestions)` of every `prompt_suggestions_update` the agent
    sent on the connection."""
    updates = []
    for index, entry in enumerate(connection.transcript):
        if entry.direction is Direction.RECEIVED and session_update_kind(entry) == "prompt_suggestions_update":
            params = entry.parsed["params"]
            update = params.get("update")
            updates.append((index, params.get("sessionId"), update.get("suggestions")))
    return updates


def _live_list(updates: list[tuple[int, Any, Any]], session_id: str, before: int) -> list | None:
    """The suggestion list current for `session_id` just before transcript index `before`: that
    of its last update, `None` if there was none."""
    current = None
    for index, update_session, suggestions in updates:
        if index < before and update_session == session_id and isinstance(suggestions, list):
            current = suggestions
    return current


def _suggestions(updates: list[tuple[int, Any, Any]]) -> list[dict]:
    return [
        suggestion
        for _, _, suggestions in updates
        if isinstance(suggestions, list)
        for suggestion in suggestions
        if isinstance(suggestion, dict)
    ]


def _prompt_blocks(suggestion: dict) -> list:
    prompt = suggestion.get("prompt")
    return prompt if isinstance(prompt, list) else []


@pytest.mark.requirement("ACP-SUGGEST-001")
async def test_suggestion_prompts_are_valid_text_or_resource_link(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUGGEST-001. See module docstring. A suggestion that is not an object or has no valid
    `prompt` fails the schema check; a block of another type fails the content-type check."""
    connection = await suggestions_connection(request, agent_launch, agent_initialize_result, tmp_path)
    updates = _suggestion_updates(connection)
    invalid = [
        f"{repr(suggestion)[:200]}: {issue.message}"
        for _, _, suggestions in updates
        if isinstance(suggestions, list)
        for suggestion in suggestions
        for issue in validate_against_def("PromptSuggestion", suggestion)
    ]
    disallowed = sorted(
        {
            str(block.get("type"))
            for suggestion in _suggestions(updates)
            for block in _prompt_blocks(suggestion)
            if isinstance(block, dict) and block.get("type") not in _ALLOWED_BLOCK_TYPES
        }
    )
    assert not invalid, "ACP-SUGGEST-001: suggestion is not valid as a `prompt`: " + "; ".join(invalid)
    assert not disallowed, (
        f"ACP-SUGGEST-001: suggestion holds {disallowed!r} content although the client advertised "
        "only `session.promptSuggestions: {}` (text and resource_link blocks)"
    )


@pytest.mark.requirement("ACP-SUGGEST-002")
async def test_no_suggestion_of_blank_text(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-SUGGEST-002. See module docstring. A suggestion is blank when it has at least one block
    and every block is `text` that is empty or whitespace-only; an empty `prompt` is ACP-SUGGEST-001's."""
    connection = await suggestions_connection(request, agent_launch, agent_initialize_result, tmp_path)
    blank = [
        suggestion
        for suggestion in _suggestions(_suggestion_updates(connection))
        if (blocks := _prompt_blocks(suggestion))
        and all(
            isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
            and not block["text"].strip()
            for block in blocks
        )
    ]
    assert not blank, f"ACP-SUGGEST-002: suggestion whose only content is empty or whitespace text: {blank!r}"


@pytest.mark.requirement("ACP-SUGGEST-003")
async def test_accepted_prompt_replaces_or_withdraws_a_non_empty_list(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUGGEST-003. `inferred:promptSuggestions`: SKIPs itself when the agent sent no non-empty
    list before the second prompt (it does not use suggestions), or did not accept that prompt.
    Otherwise any `prompt_suggestions_update` for the session from the second request to the end of
    the quiet period after its turn counts as the replacement or withdrawal; the spec sets no
    deadline, the window is the TCK's."""
    connection = await suggestions_connection(request, agent_launch, agent_initialize_result, tmp_path)
    updates = _suggestion_updates(connection)
    current = _live_list(updates, connection.session_id, connection.second_prompt_at)
    if not current:
        pytest.skip("no non-empty suggestion list was sent before the second prompt: nothing to replace")
    if not connection.second_prompt_accepted:
        pytest.skip("the second session/prompt was not accepted (an error response): nothing to replace")
    after = [
        suggestions
        for index, update_session, suggestions in updates
        if connection.second_prompt_at < index < connection.window_end
        and update_session == connection.session_id
    ]
    assert after, (
        "ACP-SUGGEST-003: a non-empty suggestion list was current when a session/prompt was accepted, "
        "but no prompt_suggestions_update replaced or withdrew it before the end of that turn plus a "
        "quiet period"
    )


@pytest.mark.requirement("ACP-SUGGEST-004")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_suggestions_are_not_replayed_on_load(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-SUGGEST-004. Judges the `session/load` exchange (request to response). SKIPs when no
    non-empty list was seen live: an agent that sends no suggestions has nothing to replay."""
    connection = await suggestions_connection(request, agent_launch, agent_initialize_result, tmp_path)
    if connection.load is None:
        pytest.skip("no session/load was sent")
    updates = _suggestion_updates(connection)
    start, end = connection.load
    if not any(
        isinstance(suggestions, list) and suggestions for index, _, suggestions in updates if index < start
    ):
        pytest.skip("no suggestion was seen live: nothing could be replayed")
    replayed = [index for index, _, _ in updates if start <= index < end]
    assert not replayed, (
        f"ACP-SUGGEST-004: {len(replayed)} prompt_suggestions_update(s) sent inside the session/load exchange "
        "(suggestions are not conversation history and are not replayed)"
    )
