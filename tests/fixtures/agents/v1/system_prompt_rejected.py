#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.systemPrompt` but rejects every
`systemPrompt`, even `append` mode with text content, which every advertising agent supports.
Violates ACP-SYSPROMPT-001 only; ACP-SYSPROMPT-002/003 still PASS (they expect an error).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"systemPrompt": {}}}


class SystemPromptRejectedAgent(ConformingAgent):
    def _system_prompt_error(self, system_prompt: Any) -> str | None:
        return None if system_prompt is None else "systemPrompt is not supported"


def main() -> None:
    SystemPromptRejectedAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-system-prompt-rejected").run()


if __name__ == "__main__":
    main()
