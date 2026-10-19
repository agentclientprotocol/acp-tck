#!/usr/bin/env python3
"""Non-conforming fixture: sends an (unstable) `plan_update` on every prompt turn although the
client never advertised `clientCapabilities.plan`. Violates ACP-CLIENTCAP-006 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsPlanUpdateAgent(EmitsUpdateAgent):
    _update = {
        "sessionUpdate": "plan_update",
        "plan": {"type": "markdown", "planId": "plan-1", "content": "1. Read the code"},
    }


def main() -> None:
    EmitsPlanUpdateAgent(agent_name="tck-fixture-emits-plan-update-unadvertised").run()


if __name__ == "__main__":
    main()
