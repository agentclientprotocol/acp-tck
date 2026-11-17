#!/usr/bin/env python3
"""Non-conforming fixture: sends a markdown `plan_update` whose `path` is relative.

FAILs `ACP-PLAN-003` (a markdown plan's `path` is an absolute native path). The plan is
schema-valid -- `AbsolutePath` is a bare string in the schema -- so nothing else FAILs.

`_send_rich_turn_updates` is overridden outright, so the other patch rows SKIP "no <variant>
observed".
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RelativeMarkdownPlanPathAgent(ConformingAgent):
    def _send_rich_turn_updates(self, session_id: Any) -> None:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "plan_update",
                "plan": {
                    "type": "markdown",
                    "planId": "plan-0001",
                    "content": "## Steps",
                    "path": "PLAN.md",
                },
            },
        )


def main() -> None:
    RelativeMarkdownPlanPathAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
