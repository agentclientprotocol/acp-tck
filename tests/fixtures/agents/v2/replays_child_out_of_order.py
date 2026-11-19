#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except that a replay sends the child's
recorded messages in reverse order (each message's own updates still in order, its empty primer
first). Replayed child updates must keep their order within each session (subagents.mdx:482), so
it violates ACP-RESUME-226 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from replays_subagent_history import ReplaysSubagentHistoryAgent  # noqa: E402


class ReplaysChildOutOfOrderAgent(ReplaysSubagentHistoryAgent):
    def _replay_child_history(self, child_id: str) -> None:
        by_message: dict[Any, list[dict[str, Any]]] = {}
        for update in self._history.get(child_id, []):
            by_message.setdefault(update.get("messageId"), []).append(update)
        for updates in reversed(list(by_message.values())):
            for update in updates:
                self._notify("session/update", {"sessionId": child_id, "update": update})


def main() -> None:
    ReplaysChildOutOfOrderAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
