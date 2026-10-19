#!/usr/bin/env python3
"""Non-conforming fixture: sends an (unstable) `subagent_update` on every prompt turn although
the client never advertised `clientCapabilities.subagents`. Violates ACP-CLIENTCAP-007 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsSubagentUpdateAgent(EmitsUpdateAgent):
    _update = {"sessionUpdate": "subagent_update", "sessionId": "child-0001", "title": "Researcher"}


def main() -> None:
    EmitsSubagentUpdateAgent(agent_name="tck-fixture-emits-subagent-update-unadvertised").run()


if __name__ == "__main__":
    main()
