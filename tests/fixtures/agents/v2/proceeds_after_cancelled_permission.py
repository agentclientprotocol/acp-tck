#!/usr/bin/env python3
"""Non-conforming fixture: asks permission with a `tool_call` subject
(`permission_tool_call=True`), but on a `cancelled` outcome it proceeds and reports the tool
call `completed`. After a `cancelled` outcome the agent MUST NOT proceed (tool-calls.mdx:340):
FAILs exactly `ACP-PERM-203`. An unoffered `optionId` is still not approval, so `ACP-PERM-002`
PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class ProceedsAfterCancelledPermissionAgent(AsksPermissionAgent):
    def _permission_tool_call_status(self, outcome: Any) -> str:
        if outcome == "cancelled":
            return "completed"
        return super()._permission_tool_call_status(outcome)


def main() -> None:
    ProceedsAfterCancelledPermissionAgent(capabilities={"session": {}}, permission_tool_call=True).run()


if __name__ == "__main__":
    main()
