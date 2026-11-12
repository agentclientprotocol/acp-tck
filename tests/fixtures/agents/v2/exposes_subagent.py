#!/usr/bin/env python3
"""Conforming fixture: during each turn it announces a child session with `subagent_update` on
the prompted session, then exchanges a `session_message` with the child in both views (outgoing
on the parent, incoming on the child, each naming both participants and the other view),
announces the delegation with a completed tool call whose content is a `session` reference to the
child, has the child ask for permission with a `session/request_permission` carrying the child's `sessionId`, then ask again to spawn its own child
with one whose `tool_call` subject carries a `session` reference, and streams the child's own
`running` -> `agent_message_chunk` -> `idle(end_turn)` under that `sessionId`. After the parent's
turn has ended, the child sends one more `agent_message_chunk` (child work outlives the parent's
turn). The association stays one tree: the child is later patched under the same parent with an
absolute `cwd` and `additionalDirectories`, and announces one nested child of its own (also with
an absolute `cwd`). Everything is legal once announced, and the child's idle must not end the
parent's turn: must PASS `ACP-PROMPT-002/203`, `ACP-SUBAGENT-001..009`, `-011..014` and `-201` and
`ACP-STATE-201..205` like `conforming.py`, and also exercises the rows that need a subagent, a
permission request or `session` content (`_SUBAGENT_EXERCISED_IDS` in `tests/v2/test_cli.py`). The
mock client answers the permission requests; the child's is not awaited.

The `_`-hooks below are the seams the violator fixtures override.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


_CHILD_DIR = str(Path(__file__).resolve().parent)  # absolute on every platform


class ExposesSubagentAgent(ConformingAgent):
    announce_child = True
    _mirrors_child_state = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._child_count = 0
        self._turn_child: str | None = None  # the child of the turn in flight, until it ends

    def _mid_turn_action(self, session_id: Any) -> bool:
        self._child_count += 1
        child_id = f"{session_id}-child-{self._child_count}"
        self._turn_child = child_id
        self._announce_child(session_id, child_id)
        self._report_child_placement(session_id, child_id)
        self._report_child_config(child_id)
        self._announce_nested_child(child_id)
        self._send_session_messages(session_id, child_id)
        self._send_session_reference(session_id, child_id)
        self._send_child_state(session_id, child_id, {"state": "running"})
        self._child_permission_step(child_id)
        self._send_child_spawn_permission_request(child_id)
        self._send_update(
            child_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": f"{child_id}-msg",
                "content": {"type": "text", "text": "child output"},
            },
        )
        self._send_child_state(session_id, child_id, {"state": "idle", "stopReason": "end_turn"})
        self._after_child_output(session_id, child_id)
        return False

    def _announce_child(self, session_id: Any, child_id: str) -> None:
        if self.announce_child:
            self._send_update(
                session_id,
                {"sessionUpdate": "subagent_update", "sessionId": child_id, "title": "helper"},
            )

    def _report_child_placement(self, session_id: Any, child_id: str) -> None:
        """A patch for the announced child under the same parent: where the Agent placed it."""
        if self.announce_child:
            self._send_update(
                session_id,
                {
                    "sessionUpdate": "subagent_update",
                    "sessionId": child_id,
                    "cwd": _CHILD_DIR,
                    "additionalDirectories": [_CHILD_DIR],
                },
            )

    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        """The child's own `state_update`, then its mirror on the parent's `subagent_update.state`
        (an unannounced child has no association to carry one)."""
        self._send_update(child_id, {"sessionUpdate": "state_update", **state})
        if self.announce_child and self._mirrors_child_state:
            self._send_update(
                session_id, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": state}
            )

    def _report_child_config(self, child_id: str) -> None:
        """The child's configuration after its announcement: a select restricted to its current
        value, as for a child that permits no Client-initiated change."""
        if self.announce_child:
            self._send_update(
                child_id,
                {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [self._child_select_option()],
                },
            )

    def _child_select_option(self) -> dict[str, Any]:
        return {
            "configId": "child_model",
            "name": "Model",
            "type": "select",
            "currentValue": "m1",
            "options": [{"value": "m1", "name": "Model one"}],
        }

    def _after_child_output(self, session_id: Any, child_id: str) -> None:
        """Hook: what the child's turn sends once it has produced its output and gone idle."""

    def _announce_nested_child(self, child_id: str) -> None:
        """The child spawns a subagent of its own: announced on the child, its immediate parent."""
        if self.announce_child:
            self._send_update(
                child_id,
                {
                    "sessionUpdate": "subagent_update",
                    "sessionId": f"{child_id}-nested",
                    "title": "sub-helper",
                    "cwd": _CHILD_DIR,
                },
            )

    def _send_session_messages(self, session_id: Any, child_id: str) -> None:
        """The delegated task and a streamed follow-up, both before the child's output."""
        self._send_delegated_task(session_id, child_id)
        self._send_streamed_follow_up(session_id, child_id)

    def _send_delegated_task(self, session_id: Any, child_id: str) -> None:
        """The task, in both views: outgoing on the parent, incoming on the child. Both name the
        participants and each other's `messageId`."""
        self._send_session_message_pair(
            session_id, child_id, f"{child_id}-task-out", f"{child_id}-task-in"
        )

    def _send_streamed_follow_up(self, session_id: Any, child_id: str) -> None:
        """A message the parent streams to the child (outgoing view only): the participants go on
        the upsert that precedes the first chunk."""
        message_id = f"{child_id}-follow-up-stream"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": message_id,
                "senderSessionId": session_id,
                "recipientSessionId": child_id,
            },
        )
        self._send_session_message_chunk(session_id, message_id)

    def _send_session_message_chunk(self, session_id: Any, message_id: str) -> None:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message_chunk",
                "messageId": message_id,
                "content": {"type": "text", "text": "and one more thing"},
            },
        )

    def _send_session_message_pair(
        self,
        session_id: Any,
        child_id: str,
        out_id: str,
        in_id: str,
        *,
        incoming_sender_message_id: str | None = None,
    ) -> None:
        """One message from the parent to the child, as its outgoing and its incoming view."""
        content = [{"type": "text", "text": "please help"}]
        participants = {"senderSessionId": session_id, "recipientSessionId": child_id}
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": out_id,
                **participants,
                "recipientMessageId": in_id,
                "content": content,
            },
        )
        self._send_update(
            child_id,
            {
                "sessionUpdate": "session_message",
                "messageId": in_id,
                **participants,
                "senderMessageId": incoming_sender_message_id or out_id,
                "content": content,
            },
        )

    def _send_session_reference(self, session_id: Any, child_id: str) -> None:
        """A tool call that reports the spawn and references the announced child. Skipped when
        the child goes unannounced, so those violators keep to their one defect."""
        if not self.announce_child:
            return
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"{child_id}-spawn",
                "title": "Spawn helper",
                "kind": "other",
                "status": "completed",
                "content": [{"type": "session", "sessionId": self._referenced_session(child_id)}],
            },
        )

    def _referenced_session(self, child_id: str) -> str:
        return child_id

    def _permission_referenced_session(self, child_id: str) -> str:
        return f"{child_id}-nested"

    def _send_child_spawn_permission_request(self, child_id: str) -> None:
        """The child asks to spawn its own child: a `tool_call` subject whose tool call carries the
        `session` reference (v2 puts it at `params.subject.toolCall`, not `params.toolCall`).
        Skipped when the nested child goes unannounced, so those violators keep to their one defect."""
        if not self.announce_child:
            return
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-spawn-perm",
                "method": "session/request_permission",
                "params": {
                    "sessionId": child_id,
                    "title": "Allow spawning a helper?",
                    "subject": {
                        "type": "tool_call",
                        "toolCall": {
                            "toolCallId": f"{child_id}-spawn-ask",
                            "title": "Spawn helper",
                            "kind": "other",
                            "status": "pending",
                            "content": [
                                {
                                    "type": "session",
                                    "sessionId": self._permission_referenced_session(child_id),
                                }
                            ],
                        },
                    },
                    "options": [
                        {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                    ],
                },
            }
        )

    def _child_permission_step(self, child_id: str) -> None:
        self._send_child_permission_request(child_id)

    def _send_child_permission_request(self, child_id: str) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-perm",
                "method": "session/request_permission",
                "params": {
                    "sessionId": child_id,
                    "title": "Allow the child to run this?",
                    "options": [
                        {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                    ],
                },
            }
        )

    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        super()._finish_turn(session_id, stop_reason)
        child_id, self._turn_child = self._turn_child, None
        if child_id is not None:
            self._send_update(
                child_id,
                {
                    "sessionUpdate": "agent_message_chunk",
                    "messageId": f"{child_id}-late",
                    "content": {"type": "text", "text": "child output after the parent's turn"},
                },
            )


def main() -> None:
    ExposesSubagentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
