#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: a prompt arriving while a `__hang__`
prompt is still running is rejected with `-32603` ("busy") instead of being inserted or held.
Agents MUST NOT reject a prompt only because foreground work is active: FAILs exactly
`ACP-PROMPT-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsPromptWhileBusyAgent(ConformingAgent):
    def _prompt_while_busy(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error: busy")


def main() -> None:
    RejectsPromptWhileBusyAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
