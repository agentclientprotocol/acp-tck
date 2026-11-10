#!/usr/bin/env python3
"""Non-conforming fixture: when the client advertised `clientCapabilities.plan`, still sends the
baseline `plan` update instead of `plan_update` on every prompt turn. Sends nothing plan-related
otherwise (so ACP-CLIENTCAP-006 stays clean). Violates ACP-PLAN-002 only, which is ADVISORY.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class SendsPlanDespitePlanCapabilityAgent(EmitsUpdateAgent):
    _only_with_client_capability = "plan"
    _update = {
        "sessionUpdate": "plan",
        "entries": [{"content": "Read the code", "priority": "medium", "status": "pending"}],
    }


def main() -> None:
    SendsPlanDespitePlanCapabilityAgent(agent_name="tck-fixture-sends-plan-despite-plan-capability").run()


if __name__ == "__main__":
    main()
