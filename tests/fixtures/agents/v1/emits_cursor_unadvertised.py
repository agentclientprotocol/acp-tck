#!/usr/bin/env python3
"""Non-conforming fixture: sends a `cursor_update` on every prompt turn although the client never
advertised `clientCapabilities.session.cursors`. Violates ACP-CLIENTCAP-009 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsCursorAgent(EmitsUpdateAgent):
    _update = {
        "sessionUpdate": "cursor_update",
        "cursorId": "cur-1",
        "capabilities": {"fork": {}},
        "anchor": {"type": "user_message", "messageId": "msg-1", "position": "before"},
    }


def main() -> None:
    EmitsCursorAgent(agent_name="tck-fixture-emits-cursor-unadvertised").run()


if __name__ == "__main__":
    main()
