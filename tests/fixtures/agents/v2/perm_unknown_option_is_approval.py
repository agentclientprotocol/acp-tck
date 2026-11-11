#!/usr/bin/env python3
"""Non-conforming fixture: asks permission with a `tool_call` subject
(`permission_tool_call=True`), but treats any `selected` outcome as approval, even one naming
an `optionId` it never offered, and reports the tool call `completed`. An unmatched `optionId`
MUST be treated as not approved (tool-calls.mdx:346-347): FAILs exactly `ACP-PERM-002`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermUnknownOptionIsApprovalAgent(AsksPermissionAgent):
    def _approves(self, outcome: dict[str, Any]) -> bool:
        return outcome.get("outcome") == "selected"


def main() -> None:
    PermUnknownOptionIsApprovalAgent(capabilities={"session": {}}, permission_tool_call=True).run()


if __name__ == "__main__":
    main()
