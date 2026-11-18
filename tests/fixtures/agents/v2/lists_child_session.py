#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that `session/list` returns every
announced child next to the sessions the client created. FAILs exactly `ACP-LIST-004`
(CAPABILITY). Within the `-k` scope of `test_subagents`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ListsChildSessionAgent(ExposesSubagentFullAgent):
    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        sessions = [
            {"sessionId": session_id, "cwd": cwd} for session_id, cwd in self._sessions.items()
        ]
        sessions += [
            {"sessionId": child, "cwd": str(Path(__file__).parent)}
            for child in sorted(self._announced_children)
        ]
        self._reply(msg_id, {"sessions": sessions})


def main() -> None:
    ListsChildSessionAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-lists-child-session").run()


if __name__ == "__main__":
    main()
