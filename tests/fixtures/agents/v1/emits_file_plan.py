#!/usr/bin/env python3
"""Non-conforming fixture: when the client advertised `clientCapabilities.plan`, sends a legacy `file`
`plan_update` (a plan type the protocol no longer defines) on every prompt turn. Sends nothing
plan-related otherwise (so ACP-CLIENTCAP-006 stays clean). Violates ACP-PLAN-004 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsFilePlanAgent(EmitsUpdateAgent):
    _only_with_client_capability = "plan"
    _update = {
        "sessionUpdate": "plan_update",
        "plan": {"type": "file", "planId": "p", "uri": "file:///tmp/plan.md"},
    }


def main() -> None:
    EmitsFilePlanAgent(agent_name="tck-fixture-emits-file-plan").run()


if __name__ == "__main__":
    main()
