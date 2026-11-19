#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that the child's `running` snapshot
reports the state `working`, which is neither a protocol state nor `_`-prefixed. The schema accepts
any string as an unrecognized state, so `ACP-SUBAGENT-015` PASSes: FAILs exactly `ACP-SUBAGENT-020`
(ADVISORY). Within the `-k` scope of `test_subagents` and `test_client_capabilities`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ChildCustomStateAgent(ExposesSubagentFullAgent):
    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        if state.get("state") == "running":
            state = {"state": "working"}
        super()._send_child_state(session_id, child_id, state)


def main() -> None:
    ChildCustomStateAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-child-custom-state").run()


if __name__ == "__main__":
    main()
