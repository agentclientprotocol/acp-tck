#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), except the
delegated task reaches the child as an incoming `session_message` only after the child has
produced its output (and gone idle), not before. Nothing is reported as a user message, so FAILs
exactly `ACP-SUBAGENT-012` (an ADVISORY row: the verdict is unchanged).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildTaskAfterOutputAgent(ExposesSubagentAgent):
    def _send_delegated_task(self, session_id, child_id):
        pass  # sent after the child's output, below

    def _after_child_output(self, session_id, child_id):
        super()._send_delegated_task(session_id, child_id)


def main() -> None:
    ChildTaskAfterOutputAgent(agent_name="tck-fixture-child-task-after-output").run()


if __name__ == "__main__":
    main()
