"""Shared mixin for fixtures that announce session cursors (ACP-CURSOR-001..004).

Only to a client that advertised `clientCapabilities.session.cursors`, so ACP-CLIENTCAP-009's
`clientCapabilities: {}` connection stays clean. Each prompt turn then reports its agent message
with a `messageId` and announces a cursor `after` it that accepts `session/fork`. Both go into the
session's history, so `session/load` replays each cursor right after its message with the same
`cursorId`. `session/fork` (advertise `sessionCapabilities.fork` to use it) rejects with `-32602` a
`cursorId` the session did not issue; a valid one forks the history up to and including the
anchored message (a fork inherits no cursors). Initial `configOptions` on `session/fork` are
handled like on `session/new` (`_base.py`). A defect fixture overrides one of the hooks
`_new_cursor_id`, `_anchor_for`, `_cursor_update` or `_cursor_rejected`.
"""

from __future__ import annotations

from typing import Any


class CursorsMixin:
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._message_count = 0
        self._cursor_history_index: dict[Any, dict[str, int]] = {}
        """Per session: each issued `cursorId` and the history index of its anchored message."""

    def _cursors_advertised(self) -> bool:
        session_caps = self._client_capabilities.get("session")
        return isinstance(session_caps, dict) and session_caps.get("cursors") is not None

    def _method_advertised(self, method: str) -> bool:
        if method == "session/fork":
            return (self._capabilities.get("sessionCapabilities") or {}).get("fork") is not None
        return super()._method_advertised(method)

    def _new_cursor_id(self, session_id: Any) -> str:
        return f"cur-{session_id}-{len(self._cursor_history_index.get(session_id, {})) + 1}"

    def _anchor_for(self, message_id: str) -> dict[str, Any]:
        return {"type": "agent_message", "messageId": message_id, "position": "after"}

    def _cursor_update(self, cursor_id: str, anchor: dict[str, Any]) -> dict[str, Any]:
        return {
            "sessionUpdate": "cursor_update",
            "cursorId": cursor_id,
            "capabilities": {"fork": {}},
            "anchor": anchor,
        }

    def _cursor_rejected(self, session_id: Any, cursor_id: Any) -> bool:
        return cursor_id not in self._cursor_history_index.get(session_id, {})

    def _send_update(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        if session is None or not self._cursors_advertised():
            super()._send_update(session_id, text)
            return
        self._message_count += 1
        message_id = f"msg-{self._message_count:04d}"
        message = {
            "sessionUpdate": "agent_message_chunk",
            "content": {"type": "text", "text": text},
            "messageId": message_id,
        }
        message_index = len(session["history"])
        self._record_and_notify(session_id, message)
        cursor_id = self._new_cursor_id(session_id)
        self._cursor_history_index.setdefault(session_id, {})[cursor_id] = message_index
        self._record_and_notify(session_id, self._cursor_update(cursor_id, self._anchor_for(message_id)))

    def _record_and_notify(self, session_id: str, update: dict[str, Any]) -> None:
        params = {"sessionId": session_id, "update": update}
        self._sessions[session_id]["history"].append(params)
        self._persist(session_id)
        self._notify("session/update", params)

    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "session/fork":
            self._handle_fork(msg_id, params)
        else:
            super()._handle_request(method, msg_id, params)

    def _handle_fork(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id, cursor_id = params.get("sessionId"), params.get("cursorId")
        source = self._sessions.get(source_id)
        if source is None:
            self._unknown_session(msg_id, source_id)
            return
        if not isinstance(params.get("cwd"), str):
            self._error(msg_id, -32602, "Invalid params: missing 'cwd'")
            return
        if cursor_id is not None and self._cursor_rejected(source_id, cursor_id):
            self._error(msg_id, -32602, f"Invalid params: unknown cursorId {cursor_id!r}")
            return
        if self._refuses_initial_config(msg_id, params):
            return
        cut = self._cursor_history_index.get(source_id, {}).get(cursor_id)
        history = [
            entry
            for entry in (source["history"] if cut is None else source["history"][: cut + 1])
            if entry["update"].get("sessionUpdate") != "cursor_update"
        ]
        self._session_count += 1
        new_id = f"sess-{self._session_count:04d}"
        self._sessions[new_id] = {"cwd": params["cwd"], "history": [dict(e, sessionId=new_id) for e in history]}
        self._persist(new_id)
        self._apply_initial_config(params)
        result: dict[str, Any] = {"sessionId": new_id}
        if self._modes is not None:
            result["modes"] = self._modes
        visible_config = self._visible_config_options()
        if visible_config is not None:
            result["configOptions"] = visible_config
        self._reply(msg_id, result)
