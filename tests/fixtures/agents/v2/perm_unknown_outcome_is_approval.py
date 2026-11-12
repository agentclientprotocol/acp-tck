#!/usr/bin/env python3
"""Non-conforming fixture: asks permission with a `tool_call` subject
(`permission_tool_call=True`), but treats any outcome it does not understand (anything other
than `selected`/`cancelled`) as approval and reports the tool call `completed`. An agent that
does not understand an outcome MUST NOT treat it as approval (tool-calls.mdx:348-349): FAILs
exactly `ACP-PERM-204`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermUnknownOutcomeIsApprovalAgent(AsksPermissionAgent):
    def _approves(self, outcome: dict[str, Any]) -> bool:
        if outcome.get("outcome") in ("selected", "cancelled"):
            return super()._approves(outcome)
        return True


def main() -> None:
    PermUnknownOutcomeIsApprovalAgent(capabilities={"session": {}}, permission_tool_call=True).run()


if __name__ == "__main__":
    main()
