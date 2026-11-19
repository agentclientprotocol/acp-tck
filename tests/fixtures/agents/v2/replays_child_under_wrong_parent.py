#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except that a replay also announces the
child's own nested child, with its own `replay_complete`, directly on the resumed session, though
the child announced it. Replayed child updates must keep their known parent (subagents.mdx:482,
476), so it violates ACP-RESUME-226 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from replays_subagent_history import ReplaysSubagentHistoryAgent  # noqa: E402


class ReplaysChildUnderWrongParentAgent(ReplaysSubagentHistoryAgent):
    def _send_child_replay_complete(self, child_id: str) -> None:
        super()._send_child_replay_complete(child_id)
        nested_id = f"{child_id}-nested"
        parent_id = self._parent_of.get(child_id)
        self._notify(
            "session/update",
            {
                "sessionId": parent_id,
                "update": {"sessionUpdate": "subagent_update", "sessionId": nested_id, "title": "sub-helper"},
            },
        )
        self._send_replay_complete(nested_id)


def main() -> None:
    ReplaysChildUnderWrongParentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
