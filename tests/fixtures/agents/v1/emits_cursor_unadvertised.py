#!/usr/bin/env python3
"""Non-conforming fixture: sends a `cursor_update` on every prompt turn although the client never
advertised `clientCapabilities.session.cursors`. Violates ACP-CLIENTCAP-009 only: on the connection
that does advertise it, the agent announces well-formed cursors (`_cursors.py`).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsCursorAgent(CursorsMixin, EmitsUpdateAgent):
    _update = {
        "sessionUpdate": "cursor_update",
        "cursorId": "cur-1",
        "capabilities": {"fork": {}},
        "anchor": {"type": "user_message", "messageId": "msg-1", "position": "before"},
    }

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        if self._cursors_advertised():
            ConformingAgent._handle_prompt(self, msg_id, params)
        else:
            super()._handle_prompt(msg_id, params)


def main() -> None:
    EmitsCursorAgent(agent_name="tck-fixture-emits-cursor-unadvertised").run()


if __name__ == "__main__":
    main()
