#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent_asks.py`, except `session/cancel` for the
cancellable child stops it only once its pending permission request is answered: the Agent does not
wait for a child's pending requests before it reports the child's state (subagents.mdx:421). The TCK
answers the held request after `timeout / 2` and the child then confirms, so `ACP-SUBAGENT-016`
PASSes and `ACP-SUBAGENT-204` FAILs: exactly that row, within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent_asks import CancellableSubagentAsksAgent  # noqa: E402


class ChildCancelWaitsForPermissionAgent(CancellableSubagentAsksAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._stopping: dict[str, Any] = {}  # child -> parent, for a cancel waiting on a request

    def _cancel_child(self, parent: Any, child_id: str) -> None:
        if self._child_requests.get(child_id):
            self._stopping[child_id] = parent
        else:
            super()._cancel_child(parent, child_id)

    def _child_request_answered(self, child_id: str) -> None:
        parent = self._stopping.pop(child_id, None)
        if parent is not None and child_id in self._running_children.get(parent, []):
            self._stop_child(parent, child_id)


def main() -> None:
    ChildCancelWaitsForPermissionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
