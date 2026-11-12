#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's reported `cwd` and
`additionalDirectories` entry are relative paths. Both fields are bare strings in the schema, so
every update is schema-valid and `ACP-SUBAGENT-015` passes: FAILs exactly `ACP-SUBAGENT-006`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import exposes_subagent  # noqa: E402
from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class RelativeSubagentCwdAgent(ExposesSubagentAgent):
    def _report_child_placement(self, session_id, child_id):
        self._emit(
            session_id,
            {
                "sessionUpdate": "subagent_update",
                "sessionId": child_id,
                "cwd": "work/child",
                "additionalDirectories": [exposes_subagent._CHILD_DIR, "../shared"],
            },
        )


def main() -> None:
    RelativeSubagentCwdAgent(agent_name="tck-fixture-relative-subagent-cwd").run()


if __name__ == "__main__":
    main()
