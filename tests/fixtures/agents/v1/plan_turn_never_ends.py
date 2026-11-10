#!/usr/bin/env python3
"""Conforming fixture: when the client advertised `clientCapabilities.plan`, sends a valid file
`plan_update` and then never resolves the prompt (a long real turn outlasting `--timeout`).
ACP-PLAN-001/002 judge the updates seen so far and PASS rather than FAIL on the timeout. Prompts
on connections without `plan` are answered normally.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class PlanTurnNeverEndsAgent(ConformingAgent):
    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions or "plan" not in self._client_capabilities:
            super()._handle_prompt(msg_id, params)
            return
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "plan_update",
                    "plan": {"type": "file", "planId": "p", "uri": "file:///tmp/plan.md"},
                },
            },
        )


def main() -> None:
    PlanTurnNeverEndsAgent(agent_name="tck-fixture-plan-turn-never-ends").run()


if __name__ == "__main__":
    main()
