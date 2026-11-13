#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, advertising `loadSession`, but `session/load`
is never answered. The load is `ACP-LOAD-001`'s finding. The `ACP-SUBAGENT-*` rows do not depend
on it and judge the turn's traffic as usual: within their `-k` scope every one PASSes and none
FAILs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SubagentsLoadNeverAnswersAgent(ExposesSubagentAgent):
    def _handle_load(self, msg_id, params):
        """Never answers."""


def main() -> None:
    SubagentsLoadNeverAnswersAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-subagents-load-never-answers"
    ).run()


if __name__ == "__main__":
    main()
