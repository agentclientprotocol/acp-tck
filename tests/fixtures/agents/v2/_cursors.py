"""Shared mixin for fixtures that announce session cursors (ACP-CURSOR-001..004).

v2 has no client capability for cursors, so every connection sees them. Each prompt turn announces
a cursor `before` the turn's `user_message` that accepts `session/fork`. The cursor goes into the
session's history right after its message, so a full `session/resume` replay delivers it after the
message with the same `cursorId`. `session/fork` (advertise `session.fork` to use it; the base
rejects an unissued `cursorId` with `-32602`) forks the history before the anchored message (a fork
inherits no cursors). A defect fixture overrides one of the hooks `_new_cursor_id`,
`_anchor_for`, `_replay_history` or `_cursor_rejected`.
"""

from __future__ import annotations

from typing import Any


class CursorsMixin:
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cursor_cuts: dict[Any, dict[str, int]] = {}
        """Per session: each issued `cursorId` and how many history entries lie before its position."""

    @staticmethod
    def _is_cursor(update: dict[str, Any]) -> bool:
        return update.get("sessionUpdate") == "cursor_update"

    def _new_cursor_id(self, session_id: Any) -> str:
        return f"cur-{session_id}-{len(self._cursor_cuts.get(session_id, {})) + 1}"

    def _anchor_for(self, message_id: str) -> dict[str, Any]:
        return {"type": "user_message", "messageId": message_id, "position": "before"}

    def _cursor_rejected(self, session_id: Any, cursor_id: Any) -> bool:
        return cursor_id not in self._cursor_cuts.get(session_id, {})

    def _send_user_message_update(self, session_id: Any, message_id: str, prompt: Any) -> None:
        super()._send_user_message_update(session_id, message_id, prompt)
        history = self._history.setdefault(session_id, [])
        cursor_id = self._new_cursor_id(session_id)
        # The message just recorded is the last non-cursor entry; the cursor sits before it.
        self._cursor_cuts.setdefault(session_id, {})[cursor_id] = (
            sum(1 for entry in history if not self._is_cursor(entry)) - 1
        )
        update = {
            "sessionUpdate": "cursor_update",
            "cursorId": cursor_id,
            "capabilities": {"fork": {}},
            "anchor": self._anchor_for(message_id),
        }
        history.append(update)
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id, cursor_id = params.get("sessionId"), params.get("cursorId")
        before = self._session_count
        super()._handle_fork_session(msg_id, params)
        if self._session_count == before:
            return
        new_id = f"sess-{self._session_count:04d}"
        entries = [entry for entry in self._history[new_id] if not self._is_cursor(entry)]
        cut = self._cursor_cuts.get(source_id, {}).get(cursor_id)
        self._history[new_id] = entries if cut is None else entries[:cut]
