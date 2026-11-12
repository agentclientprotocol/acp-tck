#!/usr/bin/env python3
"""Non-conforming fixture: advertises `loadSession`, `sessionCapabilities.resume` and
`sessionCapabilities.systemPrompt`; `session/new` and `session/load` reject an unusable
`systemPrompt`, but `session/resume` ignores an unsupported mode and resumes the session anyway.
Violates ACP-SYSPROMPT-002 only (the non-text content probe is still refused on resume).
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


class SystemPromptResumeIgnoresModeAgent(ConformingAgent):
    _persist_sessions = True

    def _handle_resume(self, msg_id: Any, params: dict[str, Any]) -> None:
        system_prompt = params.get("systemPrompt")
        if isinstance(system_prompt, dict) and system_prompt.get("mode") not in ("append", "override"):
            params = {key: value for key, value in params.items() if key != "systemPrompt"}
        super()._handle_resume(msg_id, params)


def main() -> None:
    SystemPromptResumeIgnoresModeAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-system-prompt-resume-ignores-mode"
    ).run()


if __name__ == "__main__":
    main()
