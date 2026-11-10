#!/usr/bin/env python3
"""Non-conforming fixture: honours `reject-once` but treats a `selected` outcome with any
`optionId` it does not recognise as approval. Violates ACP-PERM-002 only (ADVISORY).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from honors_permission import HonorsPermissionAgent  # noqa: E402


class UnknownOptionIsApprovalAgent(HonorsPermissionAgent):
    def _should_run(self, outcome: dict[str, Any]) -> bool:
        return outcome.get("outcome") == "selected" and outcome.get("optionId") != "reject-once"


def main() -> None:
    UnknownOptionIsApprovalAgent(agent_name="tck-fixture-perm-unknown-option-is-approval").run()


if __name__ == "__main__":
    main()
