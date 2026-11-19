"""Prompt idempotency keys: ACP-PROMPT-212..219.

`session/prompt` may carry an `idempotencyKey` (prompt-lifecycle.mdx:330-333,417-473). An agent
that advertises `capabilities.session` MUST support it (:439), so every row but the ADVISORY
`ACP-PROMPT-216` is `capabilities.session`-gated. The retry rows send the first prompt through
`run_prompt` and the retry through `send_prompt_attempt`, because a retry that starts no work
never ends in the `idle` `run_prompt` waits for.

"No second insertion" is judged as: the retry gets the original `messageId` and no
`user_message`/`user_message_chunk` update for another message follows it within a
`quiet_period`. An update repeating the original id is not an insertion.
"""

from __future__ import annotations

import uuid

import pytest

from tck.common.harness import AgentTimeout, Direction

from ._helpers import (
    assert_prompt_rejected_not_inserted,
    connected_agent,
    list_sessions,
    new_session,
    prompt_during_active_work,
    resume_session,
    retry_problems,
    run_prompt,
    send_prompt_attempt,
    user_message_ids,
)

_TEXT = "hi"
_OTHER_TEXT = "a different prompt"
UNKNOWN_CONTENT_TYPE = "_tck_unknown"


def _blocks(text: str = _TEXT) -> list[dict]:
    return [{"type": "text", "text": text}]


def _new_key() -> str:
    return str(uuid.uuid4())


async def _first_prompt(agent, session_id, key, timeout, text=_TEXT) -> str:
    """Send the keyed first prompt through `run_prompt` and return its `messageId`. A key the
    agent cannot take is `ACP-PROMPT-212`'s failure ("MUST support the key", :439)."""
    turn = await run_prompt(
        agent, session_id, _blocks(text), extra_params={"idempotencyKey": key}, timeout=timeout
    )
    assert turn.message_id is not None, (
        "a prompt with a valid idempotencyKey (a UUID) must be accepted: an agent that advertises "
        f"capabilities.session MUST support the key (prompt-lifecycle.mdx:439), got "
        f"{turn.response_entry.text!r}"
    )
    return turn.message_id


@pytest.mark.requirement("ACP-PROMPT-212")
@pytest.mark.capability("capabilities.session")
async def test_retry_with_same_key_returns_original_message_id(agent_launch, tmp_path):
    """ACP-PROMPT-212. After a keyed prompt was inserted as message M, sending it again with the
    same `idempotencyKey` (a new JSON-RPC id) gets a success carrying M and inserts no second
    message (prompt-lifecycle.mdx:452,457,465). The first prompt is judged by `ACP-PROMPT-203`;
    an error for it here FAILs, since a valid key MUST be supported (:439). Judged on the same
    connection, where the agent retains the message or, if it does not, must still recognize
    the key while the session is active (:466)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        key = _new_key()
        original = await _first_prompt(agent, session_id, key, timeout)
        retry = await send_prompt_attempt(
            agent, session_id, _blocks(), idempotency_key=key, timeout=timeout
        )
    problems = retry_problems(retry, session_id, original)
    assert not problems, (
        f"a retry of message {original!r} with the same idempotencyKey: {'; '.join(problems)} "
        f"({retry.response_entry.text!r})"
    )


@pytest.mark.requirement("ACP-PROMPT-213")
@pytest.mark.capability("capabilities.session")
async def test_malformed_idempotency_key_is_rejected_without_insertion(agent_launch, tmp_path):
    """ACP-PROMPT-213. An `idempotencyKey` that is not a string of 1 to 255 characters (`""`, 256
    characters, the number `42`) is answered `-32602`, is not treated as omitted, and nothing is
    inserted (prompt-lifecycle.mdx:333,441). A client never sends such a key; the probe breaks
    that rule on purpose because the spec defines the agent's answer. "Not inserted" means no
    user-message update and no active state follows, judged through a short quiet period."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        for label, key in (("an empty", ""), ("a 256-character", "k" * 256), ("a numeric", 42)):
            await assert_prompt_rejected_not_inserted(
                agent,
                session_id,
                _blocks(),
                what=f"a prompt with {label} idempotencyKey ({key!r:.20})",
                timeout=timeout,
                extra_params={"idempotencyKey": key},
            )


@pytest.mark.requirement("ACP-PROMPT-214")
@pytest.mark.capability("capabilities.session")
async def test_reused_key_with_a_different_prompt_never_inserts_a_second_message(
    agent_launch, tmp_path
):
    """ACP-PROMPT-214. The same `idempotencyKey` sent with a different prompt is answered as a
    retry (the original `messageId`) or, if the agent notices the difference, with `-32602`; it
    never inserts a second message, and after a `-32602` the key stays recorded for the first
    prompt: the original prompt sent again with the key gets the original `messageId`
    (prompt-lifecycle.mdx:444,457). A client MUST NOT send a key with a different prompt; the
    probe breaks that rule on purpose because the spec defines the agent's answer."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        key = _new_key()
        original = await _first_prompt(agent, session_id, key, timeout)
        reused = await send_prompt_attempt(
            agent, session_id, _blocks(_OTHER_TEXT), idempotency_key=key, timeout=timeout
        )
        error = reused.error
        if error is not None:
            assert error.get("code") == -32602, (
                "a recorded key sent with a different prompt may only be answered as a retry or "
                f"with -32602 (prompt-lifecycle.mdx:457), got {reused.response_entry.text!r}"
            )
            inserted = user_message_ids(reused.entries, session_id) - {original}
            assert not inserted, (
                f"the -32602 reply was followed by a user-message update for {sorted(inserted)!r}"
            )
            again = await send_prompt_attempt(
                agent, session_id, _blocks(), idempotency_key=key, timeout=timeout
            )
            problems = retry_problems(again, session_id, original)
            assert not problems, (
                "after a -32602 for a reused key the key stays recorded for the first prompt "
                f"(prompt-lifecycle.mdx:457), but the original prompt sent again: "
                f"{'; '.join(problems)} ({again.response_entry.text!r})"
            )
            return
    problems = retry_problems(reused, session_id, original)
    assert not problems, (
        f"a recorded key sent with a different prompt: {'; '.join(problems)} "
        f"({reused.response_entry.text!r})"
    )


def _outcome(entry) -> tuple:
    """`("ok", messageId)` or `("error", code)` for a prompt response."""
    msg = entry.parsed if isinstance(entry.parsed, dict) else {}
    if isinstance(msg.get("error"), dict):
        return ("error", msg["error"].get("code"))
    result = msg.get("result")
    return ("ok", result.get("messageId") if isinstance(result, dict) else None)


@pytest.mark.requirement("ACP-PROMPT-215")
@pytest.mark.capability("capabilities.session")
async def test_retries_of_a_held_prompt_get_the_same_outcome(agent_launch, tmp_path, cancel_prompt_text):
    """ACP-PROMPT-215. In `ACP-PROMPT-209`'s scenario, a second prompt carrying an
    `idempotencyKey` is sent twice back to back while the first prompt's work is active. The
    agent does not hold a second prompt for the key: it answers the retry together with the
    first request, with the same outcome (prompt-lifecycle.mdx:453). Both requests succeed with
    one `messageId` (inserted, once) or both get the same error (`-32800` after the TCK's
    `session/cancel`, :404,1446). A mixed outcome, two messages, or one request left unanswered
    FAILs. SKIPs as `ACP-PROMPT-209` does (the first work may have ended before the agent read
    the second prompt), when the second prompt was rejected (that row's finding), and when
    neither request was answered (`ACP-CANCEL-214`'s)."""
    timeout = agent_launch.default_timeout
    key = _new_key()
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            scenario = await prompt_during_active_work(
                agent, session_id, cancel_prompt_text, timeout=timeout, idempotency_key=key
            )
        except AgentTimeout:
            pytest.skip("the first prompt's turn never ended -- see ACP-STATE-202/ACP-CANCEL-001")
        received = [e for e in agent.transcript if e.direction is Direction.RECEIVED]
    if scenario.not_exercised is not None:
        pytest.skip(f"prompt during active work not exercised: {scenario.not_exercised}")
    if scenario.outcome == "rejected":
        pytest.skip("the second prompt was rejected while work was active -- ACP-PROMPT-209's finding")
    first, retry = scenario.second_response, scenario.retry_response
    if first is None and retry is None:
        pytest.skip("neither request with the key was answered -- see ACP-CANCEL-214")
    assert first is not None and retry is not None, (
        "the two requests for one idempotencyKey must be answered together, but only one was "
        f"answered within {timeout}s: first={None if first is None else first.text!r}, "
        f"retry={None if retry is None else retry.text!r}"
    )
    first_outcome, retry_outcome = _outcome(first), _outcome(retry)
    assert first_outcome == retry_outcome, (
        "two held requests for one idempotencyKey must get the same outcome "
        f"(prompt-lifecycle.mdx:453), got {first.text!r} and {retry.text!r}"
    )
    others = user_message_ids(received, session_id) - {scenario.turn.message_id}
    allowed = {first_outcome[1]} if first_outcome[0] == "ok" else set()
    assert others <= allowed, (
        "at most one message is inserted for the key, and only if the requests succeeded, but "
        f"user-message updates for {sorted(others)!r} were sent (outcome {first_outcome!r})"
    )


@pytest.mark.requirement("ACP-PROMPT-216")
@pytest.mark.capability("capabilities.session")
async def test_idempotency_key_is_not_echoed(agent_launch, tmp_path):
    """ACP-PROMPT-216 (ADVISORY). The agent does not echo an `idempotencyKey` in session updates,
    `session/list` results or replayed history (prompt-lifecycle.mdx:459). The key is a random
    UUID, so any occurrence in a line the agent sent is an echo. Reads every line of a
    connection that sends a keyed prompt, its retry, `session/list` and a `session/resume` with
    `replayFrom: start` (the resume is best effort: an agent that refuses it is judged on the
    rest)."""
    timeout = agent_launch.default_timeout
    key = _new_key()
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await _first_prompt(agent, session_id, key, timeout)
        await send_prompt_attempt(agent, session_id, _blocks(), idempotency_key=key, timeout=timeout)
        await list_sessions(agent, cwd=tmp_path, timeout=timeout)
        await resume_session(
            agent, session_id, tmp_path, replay_from={"type": "start"}, timeout=timeout
        )
    echoed = [
        entry.text
        for entry in agent.transcript
        if entry.direction is Direction.RECEIVED and key in entry.text
    ]
    assert not echoed, f"the idempotencyKey {key!r} was echoed by the agent: {echoed[:3]!r}"


@pytest.mark.requirement("ACP-PROMPT-217")
@pytest.mark.capability("capabilities.session")
async def test_key_is_scoped_to_its_session(agent_launch, tmp_path):
    """ACP-PROMPT-217. An `idempotencyKey` is scoped to the session named by `sessionId`: the
    same key and prompt sent in another session is a new submission, answered with a success
    whose `messageId` is then inserted there, not as a retry of the first session's message
    (prompt-lifecycle.mdx:461). The ids are not compared, because they are only unique within a
    session; the second session must instead show a user-message update for the id it returned."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        first_session = await new_session(agent, tmp_path, timeout=timeout)
        second_session = await new_session(agent, tmp_path, timeout=timeout)
        key = _new_key()
        await _first_prompt(agent, first_session, key, timeout)
        other = await send_prompt_attempt(
            agent, second_session, _blocks(), idempotency_key=key, timeout=timeout
        )
    assert other.error is None and other.message_id is not None, (
        "the same idempotencyKey in another session is a new submission and must be accepted: "
        f"{other.response_entry.text!r}"
    )
    assert other.message_id in user_message_ids(other.entries, second_session), (
        f"the prompt sent in a second session with a key already used in another session was "
        f"answered with messageId {other.message_id!r}, but no user-message update for it "
        "followed in that session: it was treated as a retry of the other session's message "
        "(prompt-lifecycle.mdx:461)"
    )


@pytest.mark.requirement("ACP-PROMPT-218")
@pytest.mark.capability("capabilities.session")
async def test_key_is_recognized_across_connections(agent_launch, tmp_path):
    """ACP-PROMPT-218. A key outlives the connection that first carried it for as long as the
    agent retains the message (prompt-lifecycle.mdx:465,471): a keyed prompt is inserted as
    message M on one process; on a fresh process, after `initialize` and `session/resume` with
    `replayFrom: start`, the same prompt sent again with the key gets M and inserts nothing. A
    message the agent does not retain may be forgotten with its key (:467), so this SKIPs when
    the fresh process cannot resume the session, or when its replay does not carry M."""
    timeout = agent_launch.default_timeout
    key = _new_key()
    async with connected_agent(agent_launch) as first:
        session_id = await new_session(first, tmp_path, timeout=timeout)
        original = await _first_prompt(first, session_id, key, timeout)
    async with connected_agent(agent_launch) as second:
        resumed, replay = await resume_session(
            second, session_id, tmp_path, replay_from={"type": "start"}, timeout=timeout
        )
        if not (isinstance(resumed.parsed, dict) and "result" in resumed.parsed):
            pytest.skip(
                f"a fresh connection could not resume the session ({resumed.text!r}), so the agent "
                "does not show that it retains it -- see the ACP-RESUME rows"
            )
        if original not in user_message_ids([entry for _, entry in replay], session_id):
            pytest.skip(
                f"the replay on the fresh connection does not carry message {original!r}, so the "
                "agent may have discarded it, and with it the key (prompt-lifecycle.mdx:467)"
            )
        retry = await send_prompt_attempt(
            second, session_id, _blocks(), idempotency_key=key, timeout=timeout
        )
    problems = retry_problems(retry, session_id, original)
    assert not problems, (
        f"after a reconnect, a retry of the retained message {original!r} with the same "
        f"idempotencyKey: {'; '.join(problems)} ({retry.response_entry.text!r})"
    )


@pytest.mark.requirement("ACP-PROMPT-219")
@pytest.mark.capability("capabilities.session")
async def test_rejected_prompt_leaves_its_key_unused(agent_launch, tmp_path):
    """ACP-PROMPT-219. An error response means the message was not inserted and the agent
    records nothing for the key, so the same prompt can be sent again with the same key
    (prompt-lifecycle.mdx:451,456). A keyed prompt with a `_tck_unknown` content block is
    rejected (`ACP-PROMPT-211`'s probe; it SKIPs here if the agent accepts it), then a valid
    prompt with the same key must succeed and be inserted: a user-message update for the
    returned `messageId` follows."""
    timeout = agent_launch.default_timeout
    key = _new_key()
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        rejected = await send_prompt_attempt(
            agent,
            session_id,
            [*_blocks(), {"type": UNKNOWN_CONTENT_TYPE, "payload": "tck"}],
            idempotency_key=key,
            timeout=timeout,
        )
        if rejected.error is None:
            pytest.skip(
                f"the prompt with an unknown {UNKNOWN_CONTENT_TYPE!r} block was accepted -- "
                "ACP-PROMPT-211 judges that"
            )
        valid = await send_prompt_attempt(
            agent, session_id, _blocks(), idempotency_key=key, timeout=timeout
        )
    assert valid.error is None and valid.message_id is not None, (
        "a prompt rejected before insertion leaves its idempotencyKey unused, so the same key "
        f"with a valid prompt must be accepted: {valid.response_entry.text!r}"
    )
    assert valid.message_id in user_message_ids(valid.entries, session_id), (
        f"the valid prompt was answered with messageId {valid.message_id!r}, but no user-message "
        "update for it followed: the key recorded for the rejected prompt was treated as a "
        "retry (prompt-lifecycle.mdx:456)"
    )
