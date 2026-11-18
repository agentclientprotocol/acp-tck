#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that it treats an announced child like
an unknown session and answers every Client-initiated request naming it with `-32002` instead of
`-32602`. Nothing succeeds, so FAILs exactly `ACP-SUBAGENT-018` (ADVISORY); `ACP-SUBAGENT-019`
(an error, whatever its code) PASSes. Within the `-k` scope of `test_subagents`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ChildCloseWrongCodeAgent(ExposesSubagentFullAgent):
    def _answer_child_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        self._unknown_session(msg_id, params.get("sessionId"))


def main() -> None:
    ChildCloseWrongCodeAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-child-close-wrong-code").run()


if __name__ == "__main__":
    main()
