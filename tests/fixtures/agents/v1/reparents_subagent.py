#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child and its nested child are announced
first), plus a `subagent_update` sent on the nested child that announces the child again: the
child gets a second, different parent, one of its own descendants (a cycle). Every message is on
a known session and schema-valid, so `ACP-SUBAGENT-001` passes: FAILs exactly
`ACP-SUBAGENT-005`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReparentsSubagentAgent(ExposesSubagentAgent):
    def _announce_nested_child(self, child_id):
        super()._announce_nested_child(child_id)
        self._emit(f"{child_id}-nested", {"sessionUpdate": "subagent_update", "sessionId": child_id})


def main() -> None:
    ReparentsSubagentAgent(agent_name="tck-fixture-reparents-subagent").run()


if __name__ == "__main__":
    main()
