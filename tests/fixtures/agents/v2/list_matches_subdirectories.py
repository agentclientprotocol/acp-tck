#!/usr/bin/env python3
"""Non-conforming fixture: `session/list` matches the `cwd` filter by prefix, so a session in a
subdirectory of the filter is returned too, though only sessions in that same directory match.

FAILs exactly `ACP-LIST-203` (its subdirectory session comes back under the parent filter).
`ACP-LIST-202` is unaffected: the filter it uses names a directory nothing lives under.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ListMatchesSubdirectoriesAgent(ConformingAgent):
    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        rejection = self._list_cwd_rejection(params.get("cwd")) or self._list_cursor_rejection(
            params.get("cursor")
        )
        if rejection is not None:
            self._error(msg_id, -32602, f"Invalid params: {rejection}")
            return
        cwd_filter = params.get("cwd")
        sessions = [
            {"sessionId": session_id, "cwd": cwd}
            for session_id, cwd in {**self._closed_sessions, **self._sessions}.items()
            if cwd_filter is None or cwd == cwd_filter or cwd.startswith(cwd_filter.rstrip("/") + "/")
        ]
        self._reply(msg_id, {"sessions": sessions})


def main() -> None:
    ListMatchesSubdirectoriesAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
