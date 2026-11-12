#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, plus a third child, `<id>-child-bg`, announced as
`running` after the parent's last snapshot and never mentioned in a `background` list until the
parent's own cancellation `idle` lists it. It is background work that keeps running when the parent
is cancelled (RFD:1075-1087), and the agent skips only the SHOULD that re-sends the state when its
list changes (prompt-lifecycle.mdx:205): before that `idle` no list names the child, so a client
cannot tell it from foreground work. `ACP-SUBAGENT-202` must not FAIL (the cascade still stops the
other two children and the row PASSes on them); nothing FAILs. With `--cancel-prompt __hang__`,
within the `-k` scope of the `test_subagent_controls.py` module.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class AnnouncesBackgroundChildAfterSnapshotAgent(CancellableSubagentAgent):
    def _start_cancellable_work(self, session_id: Any) -> None:
        super()._start_cancellable_work(session_id)
        self._spawn_child(session_id, f"{session_id}-child-bg", cancellable=False)

    def _cascade_cancel(self, session_id: Any) -> None:
        for child_id in list(self._running_children.get(session_id, [])):
            if child_id.endswith("-child-bg"):
                self._background[session_id] = [{"type": "subagent", "sessionId": child_id}]
            else:
                self._stop_child(session_id, child_id)


def main() -> None:
    AnnouncesBackgroundChildAfterSnapshotAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
