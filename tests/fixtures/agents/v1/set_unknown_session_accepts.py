#!/usr/bin/env python3
"""Non-conforming fixture: advertises modes and a select config option, and answers
`session/set_mode`/`session/set_config_option` naming an unknown session with a success instead
of `-32002` + `data.sessionId`. Violates ACP-ERROR-004 only (its `session/prompt` still gets
`-32002`, so ACP-ERROR-003 passes; it advertises no `loadSession`/`resume`).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

MODES = {
    "currentModeId": "default",
    "availableModes": [
        {"id": "default", "name": "Default"},
        {"id": "yolo", "name": "YOLO"},
    ],
}

CONFIG_OPTIONS = [
    {
        "id": "model",
        "name": "Model",
        "type": "select",
        "currentValue": "fast",
        "options": [{"value": "fast", "name": "Fast"}, {"value": "slow", "name": "Slow"}],
    },
]


class SetUnknownSessionAcceptsAgent(ConformingAgent):
    def _handle_set_mode(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") not in self._sessions:
            self._reply(msg_id, {})
            return
        super()._handle_set_mode(msg_id, params)

    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") not in self._sessions:
            self._reply(msg_id, {"configOptions": self._visible_config_options() or []})
            return
        super()._handle_set_config_option(msg_id, params)


def main() -> None:
    SetUnknownSessionAcceptsAgent(
        agent_name="tck-fixture-set-unknown-session-accepts",
        modes=dict(MODES),
        config_options=[dict(opt) for opt in CONFIG_OPTIONS],
    ).run()


if __name__ == "__main__":
    main()
