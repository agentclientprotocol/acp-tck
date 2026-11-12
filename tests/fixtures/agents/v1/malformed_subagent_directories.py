#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's reported `cwd` is a number
and its `additionalDirectories` an object. The schema rejects both, so FAILs
`ACP-SUBAGENT-015`; the values are not paths to judge, so `ACP-SUBAGENT-006` does not FAIL as
well (it judges the nested child's well-typed `cwd` instead).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class MalformedSubagentDirectoriesAgent(ExposesSubagentAgent):
    def _report_child_placement(self, session_id, child_id):
        self._emit(
            session_id,
            {
                "sessionUpdate": "subagent_update",
                "sessionId": child_id,
                "cwd": 5,
                "additionalDirectories": {"0": "/work"},
            },
        )


def main() -> None:
    MalformedSubagentDirectoriesAgent(agent_name="tck-fixture-malformed-subagent-directories").run()


if __name__ == "__main__":
    main()
