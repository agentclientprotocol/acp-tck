#!/usr/bin/env python3
"""Non-conforming fixture: advertises `loadSession` and `sessionCapabilities.systemPrompt`;
`session/new` and `session/resume` reject an unusable `systemPrompt`, but `session/load` drops a
non-text content block unnoticed and loads the session anyway. Violates ACP-SYSPROMPT-003 only
(the unsupported-mode probe is still refused on load).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {
    "loadSession": True,
    "sessionCapabilities": {"resume": {}, "systemPrompt": {}},
}


class SystemPromptLoadIgnoresContentAgent(ConformingAgent):
    _persist_sessions = True

    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        system_prompt = params.get("systemPrompt")
        if isinstance(system_prompt, dict) and system_prompt.get("mode") == "append":
            params = {key: value for key, value in params.items() if key != "systemPrompt"}
        super()._handle_load(msg_id, params)


def main() -> None:
    SystemPromptLoadIgnoresContentAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-system-prompt-load-ignores-content"
    ).run()


if __name__ == "__main__":
    main()
