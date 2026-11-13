#!/usr/bin/env python3
"""Conforming fixture: for a client that advertised `clientCapabilities.subagents` (and sending
nothing of the kind to any other client), its `__hang__` turn announces two running children of
the prompted session, `<id>-child-a` (advertises `capabilities.cancel`) and `<id>-child-b` (does
not), each reporting `running` on the parent's `subagent_update.state`, the only place v1 reports a
child's work state.

- `session/cancel` for child A stops that child only: its snapshot becomes `idle` with
  `stopReason: "cancelled"` (RFD:1069-1073, 1089-1093). A cancel for a child that is no longer
  running is ignored (a cancel racing with ended work does not rewrite its outcome).
- `session/cancel` for the parent also stops every child it is waiting on, before the parent's own
  `cancelled` response (RFD:1075-1087).

Must PASS `ACP-SUBAGENT-016/017` under `--cancel-prompt __hang__`; other prompts expose no child.
The `_`-hooks below are the seams the violator fixtures override.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancellableSubagentAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._parent_of: dict[str, Any] = {}  # child sessionId -> parent sessionId
        self._running_children: dict[Any, list[str]] = {}  # parent -> children still running

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        prompt = params.get("prompt")
        hangs = isinstance(prompt, list) and any(
            isinstance(block, dict) and block.get("text") == "__hang__" for block in prompt
        )
        if hangs and session_id in self._sessions and "subagents" in self._client_capabilities:
            self._spawn_child(session_id, f"{session_id}-child-a", cancellable=True)
            self._spawn_child(session_id, f"{session_id}-child-b", cancellable=False)
        super()._handle_prompt(msg_id, params)

    def _spawn_child(self, session_id: Any, child_id: str, *, cancellable: bool) -> None:
        update: dict[str, Any] = {
            "sessionUpdate": "subagent_update",
            "sessionId": child_id,
            "title": "helper",
        }
        if cancellable:
            update["capabilities"] = {"cancel": {}}
        self._emit(session_id, update)
        self._parent_of[child_id] = session_id
        self._running_children.setdefault(session_id, []).append(child_id)
        self._report_child_state(session_id, child_id, {"state": "running"})

    def _emit(self, session_id: Any, update: dict[str, Any]) -> None:
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _report_child_state(self, parent: Any, child_id: str, state: dict[str, Any]) -> None:
        self._emit(parent, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": state})

    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "session/cancel":
            session_id = params.get("sessionId")
            parent = self._parent_of.get(session_id) if isinstance(session_id, str) else None
            if parent is not None:
                if session_id in self._running_children.get(parent, []):
                    self._cancel_child(parent, session_id)
                return
            self._cascade_cancel(session_id)
        super()._handle_notification(method, params)

    def _cancel_child(self, parent: Any, child_id: str) -> None:
        """Hook: what `session/cancel` for a running child does. It stops that child only."""
        self._stop_child(parent, child_id)

    def _stop_child(self, parent: Any, child_id: str, stop_reason: str = "cancelled") -> None:
        self._running_children[parent].remove(child_id)
        self._report_child_state(parent, child_id, {"state": "idle", "stopReason": stop_reason})

    def _cascade_cancel(self, session_id: Any) -> None:
        """Hook: cancelling the parent also stops the children it is waiting on."""
        for child_id in list(self._running_children.get(session_id, [])):
            self._stop_child(session_id, child_id)


def main() -> None:
    CancellableSubagentAgent(agent_name="tck-fixture-cancellable-subagent").run()


if __name__ == "__main__":
    main()
