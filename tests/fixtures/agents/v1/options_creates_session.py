#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `list`, and every
`session/options` call creates a session (it shows up in `session/list`). It otherwise answers
like a conforming agent. Violates ACP-OPTIONS-002 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"options": {}, "list": {}}}


class OptionsCreatesSessionAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") is None and isinstance(params.get("cwd"), str):
            self._session_count += 1
            self._sessions[f"sess-{self._session_count:04d}"] = {"cwd": params["cwd"], "history": []}
        super()._handle_options(msg_id, params)


def main() -> None:
    OptionsCreatesSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-options-creates-session"
    ).run()


if __name__ == "__main__":
    main()
