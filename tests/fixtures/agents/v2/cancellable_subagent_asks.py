#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except each child, once announced and running,
asks for permission with a `session/request_permission` carrying its own `sessionId`, which it does
not wait for. When a child is stopped (its own cancel, or the parent's cascade), it first cancels
its still-unanswered requests with `$/cancel_request` and only then reports `idle` with
`stopReason: "cancelled"` (subagents.mdx:417,421). Must PASS `ACP-SUBAGENT-204` (both children's
requests are held and withdrawn) and everything `cancellable_subagent.py` does, under
`--cancel-prompt __hang__`. The `_`-hooks below are the seams the violator fixtures override.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class CancellableSubagentAsksAgent(CancellableSubagentAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._child_requests: dict[str, list[str]] = {}  # child -> its unanswered request ids

    def _spawn_child(self, session_id: Any, child_id: str, *, cancellable: bool) -> None:
        super()._spawn_child(session_id, child_id, cancellable=cancellable)
        request_id = f"{child_id}-perm"
        self._child_requests.setdefault(child_id, []).append(request_id)
        self._write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
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

    def _handle_response(self, message: dict[str, Any]) -> None:
        for child_id, pending in self._child_requests.items():
            if message.get("id") in pending:
                pending.remove(message["id"])
                self._child_request_answered(child_id)
                return
        super()._handle_response(message)

    def _child_request_answered(self, child_id: str) -> None:
        """Hook: the client answered one of the child's requests."""

    def _stop_child(self, parent: Any, child_id: str, stop_reason: str = "cancelled") -> None:
        self._withdraw_child_requests(child_id)
        super()._stop_child(parent, child_id, stop_reason)

    def _withdraw_child_requests(self, child_id: str) -> None:
        """Hook: stopping the child's work cancels its pending permission requests."""
        for request_id in self._child_requests.get(child_id, []):
            self._notify("$/cancel_request", {"requestId": request_id})
        self._child_requests[child_id] = []


def main() -> None:
    CancellableSubagentAsksAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
