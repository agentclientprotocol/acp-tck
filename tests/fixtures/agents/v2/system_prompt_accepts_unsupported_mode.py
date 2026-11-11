#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.systemPrompt` and applies any
`systemPrompt.mode`, including an unsupported one, instead of returning an error
(session-setup.mdx:474). Non-text content is still rejected. It persists sessions so the
`session/resume` probe's control resume succeeds on a fresh process.

FAILs exactly `ACP-SYSPROMPT-002` (both its `session/new` and `session/resume` probes).
`ACP-SYSPROMPT-003` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SystemPromptAcceptsUnsupportedModeAgent(ConformingAgent):
    def _system_prompt_rejection(self, system_prompt: Any) -> str | None:
        if isinstance(system_prompt, dict):
            system_prompt = {**system_prompt, "mode": "append"}
        return super()._system_prompt_rejection(system_prompt)


def main() -> None:
    SystemPromptAcceptsUnsupportedModeAgent(
        capabilities={"session": {"systemPrompt": {}}}, persist_sessions=True
    ).run()


if __name__ == "__main__":
    main()
