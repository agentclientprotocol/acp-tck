#!/usr/bin/env python3
"""A conforming fixture that sends session-state updates outside a turn, which the spec allows
any time a session exists: `session_info_update` right after every `session/prompt` response
(including a cancelled one) and `available_commands_update` right after every `session/load`
response. ACP-CANCEL-002 and ACP-LOAD-002 only constrain content and tool call updates, so both
still PASS. Run with `--cancel-prompt __hang__` so the cancellation is actually exercised.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"loadSession": True}


class LateStateUpdatesAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # request id -> session id, for the prompt/load responses still owed a late update
        self._late_update_session: dict[Any, Any] = {}

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        super()._reply(msg_id, result)
        session_id = self._late_update_session.pop(msg_id, None)
        if session_id is None:
            return
        if "stopReason" in result:
            update = {"sessionUpdate": "session_info_update", "title": "TCK sample session"}
        else:
            update = {"sessionUpdate": "available_commands_update", "availableCommands": []}
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") in self._sessions:
            self._late_update_session[msg_id] = params["sessionId"]
        super()._handle_prompt(msg_id, params)

    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._late_update_session[msg_id] = params.get("sessionId")
        super()._handle_load(msg_id, params)


def main() -> None:
    LateStateUpdatesAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-late-state-updates").run()


if __name__ == "__main__":
    main()
