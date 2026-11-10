#!/usr/bin/env python3
"""Non-conforming fixture: when the client advertised `clientCapabilities.plan`, sends a
`plan_update` file plan with a relative `uri` on every prompt turn. Sends nothing plan-related
otherwise (so ACP-CLIENTCAP-006 stays clean). Violates ACP-PLAN-001 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsRelativePlanFileUriAgent(EmitsUpdateAgent):
    _only_with_client_capability = "plan"
    _update = {
        "sessionUpdate": "plan_update",
        "plan": {"type": "file", "planId": "p", "uri": "plan.md"},
    }


def main() -> None:
    EmitsRelativePlanFileUriAgent(agent_name="tck-fixture-emits-relative-plan-file-uri").run()


if __name__ == "__main__":
    main()
