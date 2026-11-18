#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that `session/close` and
`session/delete` naming an announced child succeed with `{}`; `session/load` still gets `-32602`.
FAILs exactly `ACP-SUBAGENT-019` (CAPABILITY); `ACP-SUBAGENT-018` judges only the `session/load`
error code and PASSes. Within the `-k` scope of `test_subagents` and `test_client_capabilities`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ChildCloseSucceedsAgent(ExposesSubagentFullAgent):
    def _answer_child_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method in ("session/close", "session/delete"):
            self._reply(msg_id, {})
        else:
            super()._answer_child_request(method, msg_id, params)


def main() -> None:
    ChildCloseSucceedsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-child-close-succeeds").run()


if __name__ == "__main__":
    main()
