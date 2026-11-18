#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except that the parent's mirrors of the child's
`state_update`s are held back until the child's `idle`: the child reports `running` then `idle` on
its own session, and only then do the mirrors (`running`, then `idle`) reach the parent. Every
state is mirrored, in order, so `ACP-SUBAGENT-201` PASSes, but the child's `idle` arrives before
the `running` transition's mirror: FAILs exactly `ACP-SUBAGENT-205`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class LateChildStateMirrorAgent(ExposesSubagentAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._held_mirrors: list[dict[str, Any]] = []

    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        self._send_update(child_id, {"sessionUpdate": "state_update", **state})
        self._held_mirrors.append(state)
        if state["state"] == "idle":
            for held in self._held_mirrors:
                self._send_update(
                    session_id, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": held}
                )
            self._held_mirrors = []


def main() -> None:
    LateChildStateMirrorAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
