#!/usr/bin/env python3
"""Non-conforming fixture: sends a (valid) `prompt_suggestions_update` on every prompt turn
although the client never advertised `capabilities.session.promptSuggestions`
(prompt-lifecycle.mdx:707). Violates ACP-CLIENTCAP-008 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

SUGGESTIONS = [{"prompt": [{"type": "text", "text": "Run the test suite and fix what breaks"}]}]


class SuggestsUnadvertisedAgent(ConformingAgent):
    def _send_idle_update(self, session_id: Any, stop_reason: str | None) -> None:
        super()._send_idle_update(session_id, stop_reason)
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {"sessionUpdate": "prompt_suggestions_update", "suggestions": SUGGESTIONS},
            },
        )


def main() -> None:
    SuggestsUnadvertisedAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-suggests-unadvertised"
    ).run()


if __name__ == "__main__":
    main()
