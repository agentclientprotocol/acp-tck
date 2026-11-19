#!/usr/bin/env python3
"""Non-conforming fixture: when the client advertised `clientCapabilities.plan`, sends a markdown
`plan_update` whose `path` is relative on every prompt turn. Sends nothing plan-related
otherwise (so ACP-CLIENTCAP-006 stays clean). Violates ACP-PLAN-003 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsRelativePlanMarkdownPathAgent(EmitsUpdateAgent):
    _only_with_client_capability = "plan"
    _update = {
        "sessionUpdate": "plan_update",
        "plan": {"type": "markdown", "planId": "p", "content": "## Steps", "path": "PLAN.md"},
    }


def main() -> None:
    EmitsRelativePlanMarkdownPathAgent(agent_name="tck-fixture-emits-relative-plan-markdown-path").run()


if __name__ == "__main__":
    main()
