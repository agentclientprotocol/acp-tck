#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that `session/cancel` for a child that
advertises `capabilities.cancel` is silently ignored (RFD:1089-1093): the child keeps reporting
`running`. FAILs exactly `ACP-SUBAGENT-016`; the parent and the sibling are untouched
(`ACP-SUBAGENT-017` PASSes). Within the `-k` scope of the `test_subagent_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildCancelIgnoredAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        pass


def main() -> None:
    ChildCancelIgnoredAgent(agent_name="tck-fixture-child-cancel-ignored").run()


if __name__ == "__main__":
    main()
