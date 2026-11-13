#!/usr/bin/env python3
"""Conforming fixture: `conforming.py`, except that for a client that advertised
`clientCapabilities.subagents` it exposes a child session during each turn, and sends nothing of
the kind to any other client (so it still PASSes `ACP-CLIENTCAP-007` on the default connection).

During each turn it announces a child with `subagent_update` on the prompted session, reports the
child's placement (an absolute `cwd` and `additionalDirectories`) and its configuration (a select
restricted to its current value), announces one nested child on the child, exchanges a
`session_message` with the child in both views (outgoing on the parent, incoming on the child,
each naming both participants and the other view) and a streamed follow-up (participants before
the chunk), reports the spawn with a completed tool call whose content is a `session` reference to
the child, reports the child `running` on the parent's `subagent_update.state`, has the child ask
for permission with a `session/request_permission` carrying the child's `sessionId`, then ask
again to spawn the nested child with a `toolCall` carrying a `session` reference, and sends the
child's own `agent_message_chunk` before reporting it `idle(end_turn)`. After the prompt response
the child sends one more chunk (child work outlives the parent's turn). Everything is legal once
announced: must PASS `ACP-SUBAGENT-001..009`, `-011..015` (`_SUBAGENT_IDS` in
`tests/v1/test_cli.py`). The mock client answers the permission requests; the child's is not
awaited.

With `replay_on_load` (see `replays_subagent_history.py`) `session/load` also replays every
subagent update it sent (never a request).

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
    replay_on_load = False

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._child_count = 0
        self._turn_child: str | None = None  # the child of the turn in flight, until it ends
        self._subagent_log: list[tuple[str, dict[str, Any]]] = []

    def _exposes_subagents(self, session_id: Any) -> bool:
        return session_id in self._sessions and "subagents" in self._client_capabilities

    def _emit(self, session_id: Any, update: dict[str, Any]) -> None:
        self._subagent_log.append((session_id, update))
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if self._exposes_subagents(session_id):
            self._child_count += 1
            child_id = f"{session_id}-child-{self._child_count}"
            self._turn_child = child_id
            self._spawn_child(session_id, child_id)
        super()._handle_prompt(msg_id, params)
        child_id, self._turn_child = self._turn_child, None
        if child_id is not None:
            self._notify(
                "session/update",
                {
                    "sessionId": child_id,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": "child output after the parent's turn"},
                    },
                },
            )

    def _spawn_child(self, session_id: Any, child_id: str) -> None:
        self._announce_child(session_id, child_id)
        self._report_child_placement(session_id, child_id)
        self._report_child_config(child_id)
        self._announce_nested_child(child_id)
        self._send_session_messages(session_id, child_id)
        self._send_session_reference(session_id, child_id)
        self._send_child_state(session_id, child_id, {"state": "running"})
        self._child_permission_step(child_id)
        self._send_child_spawn_permission_request(child_id)
        self._emit(
            child_id,
            {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": "child output"}},
        )
        self._send_child_state(session_id, child_id, {"state": "idle", "stopReason": "end_turn"})
        self._after_child_output(session_id, child_id)

    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if self.replay_on_load and self._exposes_subagents(session_id):
            for target, update in self._replayed_updates(list(self._subagent_log)):
                self._notify("session/update", {"sessionId": target, "update": update})
        super()._handle_load(msg_id, params)

    def _replayed_updates(
        self, logged: list[tuple[str, dict[str, Any]]]
    ) -> list[tuple[str, dict[str, Any]]]:
        """What `session/load` replays: every subagent update sent so far, in order."""
        return logged

    def _announce_child(self, session_id: Any, child_id: str) -> None:
        if self.announce_child:
            self._emit(
                session_id,
                {"sessionUpdate": "subagent_update", "sessionId": child_id, "title": "helper"},
            )

    def _report_child_placement(self, session_id: Any, child_id: str) -> None:
        """A patch for the announced child under the same parent: where the Agent placed it."""
        if self.announce_child:
            self._emit(
                session_id,
                {
                    "sessionUpdate": "subagent_update",
                    "sessionId": child_id,
                    "cwd": _CHILD_DIR,
                    "additionalDirectories": [_CHILD_DIR],
                },
            )

    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        """The child's work state, which v1 reports only as the parent association's `state`."""
        if self.announce_child:
            self._emit(
                session_id, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": state}
            )

    def _report_child_config(self, child_id: str) -> None:
        """The child's configuration after its announcement: a select restricted to its current
        value, as for a child that permits no Client-initiated change."""
        if self.announce_child:
            self._emit(
                child_id,
                {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [self._child_select_option()],
                },
            )

    def _child_select_option(self) -> dict[str, Any]:
        return {
            "id": "child_model",
            "name": "Model",
            "type": "select",
            "currentValue": "m1",
            "options": [{"value": "m1", "name": "Model one"}],
        }

    def _after_child_output(self, session_id: Any, child_id: str) -> None:
        """Hook: what the child sends once it has produced its output and gone idle."""

    def _announce_nested_child(self, child_id: str) -> None:
        """The child spawns a subagent of its own: announced on the child, its immediate parent."""
        if self.announce_child:
            self._emit(
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
        self._emit(
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
        self._emit(
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
        self._emit(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": out_id,
                **participants,
                "recipientMessageId": in_id,
                "content": content,
            },
        )
        self._emit(
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
        self._emit(
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
        """The child asks to spawn its own child: a `toolCall` carrying the `session` reference.
        Skipped when the nested child goes unannounced, so those violators keep to their one
        defect."""
        if not self.announce_child:
            return
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-spawn-perm",
                "method": "session/request_permission",
                "params": {
                    "sessionId": child_id,
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
                    "toolCall": {
                        "toolCallId": f"{child_id}-tool",
                        "title": "Run the child's command",
                        "kind": "execute",
                        "status": "pending",
                    },
                    "options": [
                        {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                    ],
                },
            }
        )


def main() -> None:
    ExposesSubagentAgent(agent_name="tck-fixture-exposes-subagent").run()


if __name__ == "__main__":
    main()
