#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`, except that it exposes a child only for a turn whose
prompt is the `__subagent__` text block (what `--subagent-prompt __subagent__` sends). Any other
prompt, the built-in subagent-turn text included, gets `conforming.py`'s turn, so a run shows
whether the custom prompt text reached the agent: with it every `_SUBAGENT_IDS` row PASSes
(`tests/v1/test_cli.py`), without it they SKIP.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ExposesSubagentOnRequestAgent(ExposesSubagentAgent):
    _requested = False

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        prompt = params.get("prompt")
        self._requested = isinstance(prompt, list) and any(
            isinstance(block, dict) and block.get("text") == "__subagent__" for block in prompt
        )
        super()._handle_prompt(msg_id, params)

    def _exposes_subagents(self, session_id: Any) -> bool:
        return self._requested and super()._exposes_subagents(session_id)


def main() -> None:
    ExposesSubagentOnRequestAgent(agent_name="tck-fixture-exposes-subagent-on-request").run()


if __name__ == "__main__":
    main()
