#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that `session/delete` naming an
announced child succeeds with `{}`; `session/resume` and `session/close` still get `-32602`. The
`session/delete` probe is sent only to an agent that advertises `capabilities.session.delete`, which
this fixture does. FAILs exactly `ACP-SUBAGENT-019` (CAPABILITY). Within the `-k` scope of
`test_subagents`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ChildDeleteSucceedsAgent(ExposesSubagentFullAgent):
    def _answer_child_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "session/delete":
            self._reply(msg_id, {})
        else:
            super()._answer_child_request(method, msg_id, params)


def main() -> None:
    ChildDeleteSucceedsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-child-delete-succeeds").run()


if __name__ == "__main__":
    main()
