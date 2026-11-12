#!/usr/bin/env python3
"""Conforming fixture: during each turn it announces a child session with `subagent_update` on
the prompted session, then exchanges a `session_message` with the child in both views (outgoing
on the parent, incoming on the child), announces the delegation with a completed
tool call whose content is a `session` reference to the child, has the child ask for permission
with a `session/request_permission` carrying the child's `sessionId`, and streams the child's own
`running` -> `agent_message_chunk` -> `idle(end_turn)` under that `sessionId`. After the parent's
turn has ended, the child sends one more `agent_message_chunk` (child work outlives the parent's
turn). The association stays one tree: the child is later patched under the same parent with an
absolute `cwd` and `additionalDirectories`, and announces one nested child of its own (also with
an absolute `cwd`). Everything is legal once announced, and the child's idle must not end the
parent's turn: must PASS `ACP-PROMPT-002/203`, `ACP-SUBAGENT-001..006` and `ACP-STATE-201..205`
like `conforming.py` (the mock client answers the child's permission request; it is not awaited).

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
        self._announce_nested_child(child_id)
        self._send_session_messages(session_id, child_id)
        self._send_session_reference(session_id, child_id)
        self._send_update(child_id, {"sessionUpdate": "state_update", "state": "running"})
        self._child_permission_step(child_id)
        self._send_update(
            child_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": f"{child_id}-msg",
                "content": {"type": "text", "text": "child output"},
            },
        )
        self._send_update(
            child_id, {"sessionUpdate": "state_update", "state": "idle", "stopReason": "end_turn"}
        )
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
        """The delegated task, in both views: outgoing on the parent, incoming on the child."""
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-task-out",
                "recipientSessionId": child_id,
                "content": [{"type": "text", "text": "please help"}],
            },
        )
        self._send_update(
            child_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-task-in",
                "senderSessionId": session_id,
                "content": [{"type": "text", "text": "please help"}],
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
