#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that on `session/cancel` for the
cancellable child the parent's turn ends first (`idle`, `end_turn`) and only then the child asks
permission for its work and waits: it reports `idle` with `stopReason: "cancelled"` only if the
client answers `cancelled`, as a client that has cancelled the child must (RFD "Pending permission
and elicitation requests"), and ends `end_turn` if the request is answered with an option. The TCK
reads that request after the parent's turn ended, so it must still answer it, and with `cancelled`:
`ACP-SUBAGENT-016` and `-017` PASS. Within the `-k` scope of the `test_subagent_controls.py`
module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildAsksAfterTurnEndsAgent(CancellableSubagentAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._awaiting: tuple[Any, str] | None = None  # (parent, child) of the open request

    def _cancel_child(self, parent: Any, child_id: str) -> None:
        self._hanging_sessions.pop(parent, None)
        self._send_idle_update(parent, "end_turn")
        self._awaiting = (parent, child_id)
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-perm",
                "method": "session/request_permission",
                "params": {
                    "sessionId": child_id,
                    "title": "Allow the child to finish this?",
                    "options": [{"optionId": "allow-once", "name": "Allow", "kind": "allow_once"}],
                },
            }
        )

    def _handle_response(self, message: dict[str, Any]) -> None:
        if self._awaiting is None or message.get("id") != f"{self._awaiting[1]}-perm":
            super()._handle_response(message)
            return
        parent, child_id = self._awaiting
        self._awaiting = None
        result = message.get("result")
        answer = result.get("outcome") if isinstance(result, dict) else None
        cancelled = isinstance(answer, dict) and answer.get("outcome") == "cancelled"
        self._stop_child(parent, child_id, "cancelled" if cancelled else "end_turn")


def main() -> None:
    ChildAsksAfterTurnEndsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
